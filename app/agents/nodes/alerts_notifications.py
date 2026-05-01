"""Alerts & Notifications Agent — BRD Phase 10: KPI update + audit trail."""
from __future__ import annotations
from datetime import datetime, timezone
from agents.state import OnboardingState
from shared.logger import get_logger

log = get_logger("agent.alerts_notifications")


def alerts_notifications_node(state: OnboardingState) -> OnboardingState:
    log.info("agent.alerts_notifications.start")
    now = datetime.now(timezone.utc).isoformat()
    status = state.get("step_status", "completed")
    account = state.get("account_number", "")
    routing = state.get("routing_lane", "standard")
    journey = state.get("journey_type", "individual")

    sent: list[str] = []

    # Determine notification type
    if state.get("human_review_required") and not state.get("human_decision"):
        notification_type = "compliance_review_required"
        sent.extend(["email:client_review_pending", "email:mlro_notification"])
    elif state.get("downstream_posted") and account:
        notification_type = "onboarding_complete"
        sent.extend(["email:welcome_pack", "sms:account_confirmation"])
    elif state.get("error"):
        notification_type = "application_declined"
        sent.append("email:decline_notice")
    else:
        notification_type = "application_update"
        sent.append("email:status_update")

    # BRD FR-AU3: immutable audit event on case closure
    audit_entry = {
        "event": notification_type,
        "notifications_sent": sent,
        "routing_lane": routing,
        "journey_type": journey,
        "timestamp": now,
        "actor": "system",
    }
    state.setdefault("audit_trail", []).append(audit_entry)
    state["notifications_sent"] = sent

    msg = (
        f"📬 **Notifications Dispatched**\n\n"
        f"• **Type:** {notification_type.replace('_', ' ').title()}\n"
        f"• **Sent:** {', '.join(sent)}\n"
        f"• **Audit trail:** Updated at {now[:19]}Z\n\n"
        "Onboarding workflow complete."
    )
    state.setdefault("messages", []).append({
        "role": "assistant", "agent": "alerts_notifications", "content": msg,
    })
    state.setdefault("completed_steps", []).append("alerts_notifications")
    state["current_step"] = "alerts_notifications"
    return state
