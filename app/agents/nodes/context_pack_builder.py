"""Context Pack Builder — BRD Phase 7 / FR-D4: versioned immutable JSON pack.

FR-D5: PII tokenisation applied before LLM delivery.
FR-D4: versioned, immutable JSON Context Pack built from all validated data.
"""
from __future__ import annotations
from datetime import datetime, timezone
from agents.state import OnboardingState
from shared.helpers import generate_id, redact_pii
from shared.logger import get_logger
import json

log = get_logger("agent.context_pack_builder")


def _tokenise_pii(profile: dict) -> dict:
    """BRD FR-D5: replace PII fields with tokenised placeholders before LLM delivery."""
    sensitive = ("id_number", "tax_id", "ssn", "email", "phone")
    clean = dict(profile)
    for field in sensitive:
        if field in clean and clean[field]:
            clean[field] = f"[TOKENISED-{field.upper()}]"
    return clean


def context_pack_builder_node(state: OnboardingState) -> OnboardingState:
    log.info("agent.context_pack_builder.start")

    client_profile_raw = state.get("client_profile") or {}
    # BRD FR-D5: tokenise PII
    client_profile_clean = _tokenise_pii(client_profile_raw)

    # Assemble missing information list
    missing_info: list[str] = []
    kyc = state.get("kyc_result") or {}
    sow = state.get("sow_result") or {}
    fatca = state.get("fatca_crs_result") or {}
    docs = state.get("documents") or []

    if not kyc.get("identity_verified"):
        missing_info.append("Identity verification incomplete")
    if fatca.get("missing_fields"):
        missing_info.extend(fatca["missing_fields"])
    if sow.get("documentation_quality") == "insufficient":
        missing_info.append("Source of wealth documentation insufficient")
    low_ocr_docs = [d.get("file_name", "doc") for d in docs
                    if d.get("ocr_confidence", 1.0) < 0.85]
    if low_ocr_docs:
        missing_info.append(f"Low OCR confidence: {', '.join(low_ocr_docs)}")

    context_pack = {
        "pack_id": generate_id("CTX"),
        "version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "client_profile": client_profile_clean,      # PII tokenised
        "corporate_profile": state.get("corporate_profile") or {},
        "kyc_result": kyc,
        "aml_result": state.get("aml_result") or {},
        "sow_result": sow,
        "fatca_crs_result": fatca,
        "risk_score": state.get("risk_score") or {},
        "triage_result": state.get("triage_result") or {},
        "routing_lane": state.get("routing_lane", "standard"),
        "documents": [
            {"doc_type": d.get("doc_type"), "status": d.get("validation_status"),
             "ocr_confidence": d.get("ocr_confidence"), "anomalies": d.get("anomalies")}
            for d in docs
        ],
        "missing_information": missing_info,
        "llm_outputs": {},
    }
    state["context_pack"] = context_pack  # type: ignore[assignment]

    msg = (
        f"📦 **Context Pack Assembled** (Pack ID: {context_pack['pack_id']})\n\n"
        f"• **Data sources assembled:** {5 + len(docs)} components\n"
        f"• **Missing information items:** {len(missing_info)}\n"
        f"• **PII tokenisation:** Applied (BRD FR-D5)\n"
        f"• **Routing lane:** {context_pack['routing_lane'].upper()}\n\n"
        "Proceeding to AI review (LLM case analysis)…"
    )
    state.setdefault("messages", []).append({
        "role": "assistant", "agent": "context_pack_builder", "content": msg,
    })
    state.setdefault("completed_steps", []).append("context_pack_builder")
    state["current_step"] = "context_pack_builder"
    return state
