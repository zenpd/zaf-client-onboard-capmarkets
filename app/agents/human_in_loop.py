"""Human-in-the-loop escalation handler (BRD FR-H1 to FR-H4)."""
from __future__ import annotations
from agents.state import OnboardingState
from shared.logger import get_logger

log = get_logger("agent.human_in_loop")


def human_review_node(state: OnboardingState) -> OnboardingState:
    """
    Suspends graph execution pending a named human reviewer decision.
    BRD FR-H1: reviewer options restricted to Approve|Reject|RFI|Escalate|EDD.
    BRD FR-H3: PEP acceptance requires named senior management approver.
    """
    log.info(
        "human_in_loop.waiting",
        application_id=state.get("application_id"),
        reason=state.get("human_review_reason"),
    )
    decision = state.get("human_decision")
    if not decision:
        state["current_step"] = "human_review"
        state["step_status"] = "escalated"
        state.setdefault("completed_steps", []).append("human_review")
        reason = state.get("human_review_reason", "additional compliance verification required")
        state.setdefault("messages", []).append({
            "role": "assistant",
            "agent": "human_review",
            "content": (
                "⏳ **Application Under Compliance Review**\n\n"
                f"Your application has been escalated for review by our compliance team ({reason}).\n\n"
                "All regulated decisions are handled by named compliance officers. "
                "You will be notified of the outcome by email. No action is required from you."
            ),
        })
        return state

    if decision == "approve":
        state["human_review_required"] = False
        state["step_status"] = "completed"
        state.setdefault("agent_notes", []).append(
            f"Human reviewer approved. Reason: {state.get('human_review_reason')}")
        state.setdefault("messages", []).append({
            "role": "assistant", "agent": "human_review",
            "content": "✅ **Compliance Review Complete — Approved**\n\nYour application has been approved by our compliance team. Proceeding to account opening…",
        })
    elif decision == "reject":
        state["step_status"] = "failed"
        state["error"] = "Application rejected by compliance reviewer."
        state.setdefault("messages", []).append({
            "role": "assistant", "agent": "human_review",
            "content": "❌ **Application Declined**\n\nUnfortunately your application could not be approved. Please contact our client services team for further details.",
        })
    elif decision == "rfi":
        # BRD FR-H4: RFI pauses SLA clock
        state["step_status"] = "in_progress"
        state.setdefault("agent_notes", []).append("RFI issued by reviewer — awaiting client response.")
        state["human_decision"] = None  # type: ignore[assignment]
        state.setdefault("messages", []).append({
            "role": "assistant", "agent": "human_review",
            "content": "📋 **Request for Information (RFI) Issued**\n\nOur compliance team requires additional information. Please provide the requested documents or clarifications. Your SLA clock has been paused pending your response.",
        })
    elif decision == "escalate_edd":
        state["routing_lane"] = "edd"
        state["human_review_required"] = True
        state["human_review_reason"] = "Escalated to Enhanced Due Diligence"
        state.setdefault("messages", []).append({
            "role": "assistant", "agent": "human_review",
            "content": "🔍 **Enhanced Due Diligence Required**\n\nYour application requires Enhanced Due Diligence review. Our specialist EDD team will contact you within 2 business days.",
        })
    state["completed_steps"] = [s for s in state.get("completed_steps", []) if s != "human_review"]
    return state
