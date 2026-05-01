"""Risk Scoring Agent — BRD Phase 6: deterministic composite risk score.

FR-R3: LLM must not calculate, modify, or override risk scores.
FR-R4: STP routing — all criteria must pass simultaneously.
"""
from __future__ import annotations
from agents.state import OnboardingState
from shared.helpers import generate_id
from shared.scoring import score_client_risk, classify_risk_band, evaluate_stp_rules
from shared.logger import get_logger
from shared.config import get_settings

log = get_logger("agent.risk_scoring")

_ROUTING_LABELS = {
    "stp":      "⚡ Straight-Through Processing",
    "standard": "📋 Standard Review",
    "enhanced": "🔍 Enhanced Review",
    "edd":      "🧐 Enhanced Due Diligence",
    "hold":     "⏸️ Case Hold",
    "reject":   "❌ Reject",
}


def risk_scoring_node(state: OnboardingState) -> OnboardingState:
    """BRD FR-R3: deterministic risk scoring — no LLM involvement."""
    log.info("agent.risk_scoring.start")
    settings = get_settings()

    kyc_result    = state.get("kyc_result") or {}
    client_profile = state.get("client_profile") or {}
    documents     = state.get("documents") or []

    # BRD FR-R3: deterministic, weighted risk score
    risk_score = score_client_risk(
        kyc_result=kyc_result,
        client_profile=client_profile,
        documents=documents,
    )
    risk_score["score_id"] = generate_id("RISK")
    state["risk_score"] = risk_score  # type: ignore[assignment]

    # STP evaluation (BRD FR-R4)
    stp_eval = evaluate_stp_rules(
        kyc_result=kyc_result,
        client_profile=client_profile,
        risk_score=risk_score,
        settings_stp_threshold=settings.stp_deposit_threshold,
    )
    stp_eval["evaluation_id"] = generate_id("STP")
    state["stp_evaluation"] = stp_eval  # type: ignore[assignment]

    # Override routing if triage already set hold
    current_routing = state.get("routing_lane", "")
    if current_routing not in ("hold", "reject"):
        # Determine routing from risk score
        band = risk_score.get("risk_band", "medium")
        pep = kyc_result.get("pep_flag", False)
        sanctions = kyc_result.get("sanctions_hit", False)

        if sanctions:
            routing = "hold"
        elif pep or band == "critical":
            routing = "edd"
        elif band == "very_high":
            routing = "enhanced"
        elif band in ("medium", "high") or stp_eval["decision"] in ("REQUIRES_REVIEW", "INELIGIBLE"):
            routing = "standard" if band == "medium" else "enhanced"
        else:
            routing = "stp"

        state["routing_lane"] = routing  # type: ignore[assignment]
        state["stp_eligible"] = routing == "stp"
    else:
        routing = current_routing

    score = risk_score.get("composite_score", 0)
    band = risk_score.get("risk_band", "medium")
    routing_label = _ROUTING_LABELS.get(routing, routing)
    icon = "🟢" if band == "low" else "🟡" if band == "medium" else "🔴"

    msg = (
        f"{icon} **Risk Assessment Complete**\n\n"
        f"• **Composite Risk Score:** {score:.0f} / 100\n"
        f"• **Risk Band:** {band.replace('_', ' ').upper()}\n"
        f"• **Routing Decision:** {routing_label}\n"
        f"• **STP Eligible:** {'Yes ✅' if state.get('stp_eligible') else 'No ❌'}\n"
        + (f"• **Failed STP Rules:** {', '.join(stp_eval.get('rules_failed', []))}\n"
           if stp_eval.get('rules_failed') else "")
        + "\nProceeding to context pack assembly…"
    )
    state.setdefault("messages", []).append({
        "role": "assistant", "agent": "risk_scoring", "content": msg,
    })
    state.setdefault("completed_steps", []).append("risk_scoring")
    state["current_step"] = "risk_scoring"
    return state
