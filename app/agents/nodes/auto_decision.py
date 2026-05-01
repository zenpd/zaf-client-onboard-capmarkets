"""Auto-Decision Agent — BRD Phase 8: STP auto-approve or escalate.

BRD FR-R4: STP requires ALL criteria simultaneously; single failure blocks STP.
LLM does not make routing decisions — purely deterministic.
"""
from __future__ import annotations
from agents.state import OnboardingState
from shared.helpers import generate_id
from shared.scoring import evaluate_stp_rules
from shared.logger import get_logger
from shared.config import get_settings

log = get_logger("agent.auto_decision")


def auto_decision_node(state: OnboardingState) -> OnboardingState:
    log.info("agent.auto_decision.start")
    settings = get_settings()

    kyc_result     = state.get("kyc_result") or {}
    client_profile = state.get("client_profile") or {}
    risk_score     = state.get("risk_score") or {}
    routing        = state.get("routing_lane", "standard")

    # If already held/rejected from upstream, skip STP evaluation
    if routing in ("hold", "reject"):
        state.setdefault("completed_steps", []).append("auto_decision")
        state["current_step"] = "auto_decision"
        return state

    evaluation = evaluate_stp_rules(
        kyc_result=kyc_result,
        client_profile=client_profile,
        risk_score=risk_score,
        settings_stp_threshold=settings.stp_deposit_threshold,
    )
    evaluation["evaluation_id"] = generate_id("STP")
    state["stp_evaluation"] = evaluation  # type: ignore[assignment]
    decision = evaluation["decision"]

    if decision == "AUTO_APPROVED":
        state["human_review_required"] = False
        state["human_decision"] = "approve"
        state.setdefault("agent_notes", []).append(
            f"STP auto-approved — all {len(evaluation['rules_passed'])} rules passed."
        )
        msg = (
            "⚡ **Straight-Through Processing — Approved**\n\n"
            f"Your application passed all {len(evaluation['rules_passed'])} automated compliance checks "
            "and has been approved. Proceeding to account creation…"
        )
    elif decision == "INELIGIBLE":
        state["human_review_required"] = True
        state["human_review_reason"] = (
            f"STP ineligible — failed: {', '.join(evaluation['rules_failed'])}"
        )
        msg = (
            "🔎 **Compliance Review Required**\n\n"
            "Your application requires a compliance review. "
            "Our team will assess your case and be in touch shortly. "
            "This typically takes 2–5 business days."
        )
    else:
        state["human_review_required"] = True
        state["human_review_reason"] = (
            f"STP review — failed rules: {', '.join(evaluation['rules_failed'])}"
        )
        msg = (
            "🔎 **Additional Verification Required**\n\n"
            "A few compliance checks require manual verification. "
            "Our team will review your application within 2–3 business days."
        )

    state.setdefault("messages", []).append({
        "role": "assistant", "agent": "auto_decision", "content": msg,
    })
    state.setdefault("completed_steps", []).append("auto_decision")
    state["current_step"] = "auto_decision"
    return state
