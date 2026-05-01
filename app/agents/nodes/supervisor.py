"""Supervisor / Orchestration Node — routes across all specialist agents.

BRD 25-Step Process: 10 phases mapped to agent sequence per journey type.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone

from langchain_core.messages import HumanMessage, SystemMessage

from agents.state import OnboardingState, JourneyType
from shared.logger import get_logger
from shared.llm import get_llm

log = get_logger(__name__)

# ── Journey step sequences (BRD 25-Step Flow) ─────────────────────────────────
JOURNEY_STEP_MAP: dict[str, list[str]] = {
    # Individual / Joint: Retail, HNW, UHNW
    "individual": [
        "triage",                   # Phase 1: classify client type, routing
        "client_education",         # Phase 1: channel onboarding guide
        "document_collection",      # Phase 2: checklist generation + upload
        "ocr_data_extraction",      # Phase 2: OCR + field extraction
        "data_validation",          # Phase 3: mandatory field validation
        "entity_resolution",        # Phase 3: duplicate check
        "sanctions_pep_screening",  # Phase 4: OFAC/UN/EU/HMT + PEP + adverse media
        "fatca_crs",                # Phase 5: FATCA/CRS classification
        "source_of_wealth",         # Phase 6: SOW assessment
        "risk_scoring",             # Phase 6: deterministic risk score + routing
        "context_pack_builder",     # Phase 7: assemble Context Pack
        "ai_review",                # Phase 7: LLM processing (8 outputs)
        "auto_decision",            # Phase 8: STP auto-approve or escalate
        "human_review",             # Phase 8-9: human reviewer (if required)
        "account_creation",         # Phase 10: downstream posting (Client Master + CBS + WMP)
        "alerts_notifications",     # Phase 10: confirmation + audit trail
    ],
    "joint": [
        "triage", "client_education", "document_collection", "ocr_data_extraction",
        "data_validation", "entity_resolution", "sanctions_pep_screening", "fatca_crs",
        "source_of_wealth", "risk_scoring", "context_pack_builder", "ai_review",
        "auto_decision", "human_review", "account_creation", "alerts_notifications",
    ],
    "corporate": [
        "triage",
        "client_education",
        "document_collection",
        "ocr_data_extraction",
        "data_validation",
        "entity_resolution",
        "kyb_ubo",                  # Phase 3: UBO identification (≥25% threshold)
        "sanctions_pep_screening",
        "fatca_crs",
        "corporate_risk_scoring",
        "source_of_wealth",
        "risk_scoring",
        "context_pack_builder",
        "ai_review",
        "auto_decision",
        "human_review",
        "account_creation",
        "alerts_notifications",
    ],
    "trust": [
        "triage", "client_education", "document_collection", "ocr_data_extraction",
        "data_validation", "entity_resolution", "kyb_ubo",
        "sanctions_pep_screening", "fatca_crs", "corporate_risk_scoring",
        "source_of_wealth", "risk_scoring", "context_pack_builder", "ai_review",
        "auto_decision", "human_review", "account_creation", "alerts_notifications",
    ],
}


def detect_journey(user_input: str) -> JourneyType | None:
    system_prompt = (
        "Classify the client onboarding journey for a wealth management platform. "
        "Reply with exactly one word: individual | joint | corporate | trust. No explanation."
    )
    llm = get_llm(max_tokens=32)
    resp = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_input),
    ])
    raw = resp.content.strip().lower()
    if raw in ("individual", "joint", "corporate", "trust"):
        return raw  # type: ignore[return-value]
    return None


def supervisor_node(state: OnboardingState) -> OnboardingState:
    """Entrypoint node — initialises or advances the onboarding journey."""
    now = datetime.now(timezone.utc).isoformat()
    state["_supervisor_count"] = state.get("_supervisor_count", 0) + 1

    # ── Guard against runaway loops ────────────────────────────────────────────
    if state.get("_supervisor_count", 0) > 30:
        state["step_status"] = "failed"
        state["error"] = "Supervisor loop limit exceeded."
        return state

    # ── First turn: detect journey type ───────────────────────────────────────
    if not state.get("journey_type"):
        messages = state.get("messages", [])
        user_msgs = [m["content"] for m in messages if m.get("role") == "user"]
        user_input = user_msgs[-1] if user_msgs else ""
        journey = None
        if user_input:
            try:
                journey = detect_journey(user_input)
            except Exception as e:
                log.warning("supervisor.journey_detect_failed", error=str(e))
        if not journey:
            journey = "individual"
        state["journey_type"] = journey
        log.info("supervisor.journey_detected", journey=journey)

    # ── Initialise application metadata ───────────────────────────────────────
    if not state.get("application_id"):
        state["application_id"] = f"WM-{uuid.uuid4().hex[:8].upper()}"
        state["created_at"] = now
        log.info("supervisor.application_created", application_id=state["application_id"])

    # ── Determine next step ───────────────────────────────────────────────────
    journey = state.get("journey_type", "individual")
    steps = JOURNEY_STEP_MAP.get(journey, JOURNEY_STEP_MAP["individual"])
    completed = set(state.get("completed_steps", []))

    next_step = None
    for step in steps:
        if step not in completed:
            next_step = step
            break

    if next_step:
        state["current_step"] = next_step
        state["step_status"] = "in_progress"
        state["updated_at"] = now
    else:
        state["current_step"] = "completed"
        state["step_status"] = "completed"

    # ── Route to human review if flagged ──────────────────────────────────────
    if state.get("human_review_required") and "human_review" not in completed:
        if state.get("human_decision"):
            pass  # decision already made — let normal flow proceed
        else:
            state["current_step"] = "human_review"

    log.info("supervisor.routing", next_step=state.get("current_step"), journey=journey)
    return state


def next_agent(state: OnboardingState) -> str:
    """Conditional edge — returns the name of the next node for LangGraph routing."""
    if state.get("error"):
        return "error_handler"
    current = state.get("current_step", "")
    step_map = {
        "triage":                  "triage",
        "client_education":        "client_education",
        "document_collection":     "document_collection",
        "ocr_data_extraction":     "ocr_data_extraction",
        "data_validation":         "data_validation",
        "entity_resolution":       "entity_resolution",
        "kyb_ubo":                 "kyb_ubo",
        "sanctions_pep_screening": "sanctions_pep_screening",
        "fatca_crs":               "fatca_crs",
        "source_of_wealth":        "source_of_wealth",
        "corporate_risk_scoring":  "corporate_risk_scoring",
        "risk_scoring":            "risk_scoring",
        "context_pack_builder":    "context_pack_builder",
        "ai_review":               "ai_review",
        "auto_decision":           "auto_decision",
        "human_review":            "human_review",
        "account_creation":        "account_creation",
        "alerts_notifications":    "alerts_notifications",
        "completed":               "onboarding_complete",
    }
    return step_map.get(current, "respond_and_wait")
