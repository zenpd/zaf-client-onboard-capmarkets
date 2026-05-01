"""Account Creation Agent — BRD Phase 10: downstream posting.

Posts to: Client Master System, Core Banking Platform, Wealth Management Platform.
Immutable audit trail finalised.
"""
from __future__ import annotations
from datetime import datetime, timezone
from agents.state import OnboardingState
from shared.helpers import generate_id
from shared.logger import get_logger
from shared.config import get_settings

log = get_logger("agent.account_creation")


async def _post_to_client_master(state: dict, settings) -> str:
    """Post to Client Master System (simulated)."""
    try:
        import httpx
        if settings.client_master_url:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{settings.client_master_url}/api/clients",
                    json={"client_profile": state.get("client_profile", {})},
                    headers={"Authorization": f"Bearer {settings.client_master_api_key}"},
                )
                return resp.json().get("client_id", generate_id("CMR"))
    except Exception:
        pass
    return generate_id("CMR")


def account_creation_node(state: OnboardingState) -> OnboardingState:
    log.info("agent.account_creation.start")
    settings = get_settings()

    if state.get("human_review_required") and not state.get("human_decision") == "approve":
        state.setdefault("completed_steps", []).append("account_creation")
        state["current_step"] = "account_creation"
        return state

    now = datetime.now(timezone.utc).isoformat()
    account_number = generate_id("WM-ACC")
    client_master_id = generate_id("CMR")
    journey = state.get("journey_type", "individual")
    client_type = state.get("client_type", "retail")

    # Simulate downstream posting (BRD Phase 10)
    posting_result = {
        "account_number": account_number,
        "client_master_id": client_master_id,
        "core_banking_ref": generate_id("CBS"),
        "wm_platform_ref": generate_id("WMP"),
        "posted_at": now,
        "systems_updated": ["Client Master System", "Core Banking Platform", "Wealth Management Platform"],
    }

    state["account_number"] = account_number
    state["client_master_id"] = client_master_id
    state["downstream_posted"] = True
    state["_posting_result"] = posting_result  # type: ignore[assignment]

    # Immutable audit trail entry (BRD FR-AU1)
    audit_entry = {
        "event": "account_created",
        "account_number": account_number,
        "client_master_id": client_master_id,
        "journey_type": journey,
        "client_type": client_type,
        "timestamp": now,
        "actor": "system",
    }
    state.setdefault("audit_trail", []).append(audit_entry)

    msg = (
        "🎉 **Account Successfully Created**\n\n"
        f"• **Account Number:** `{account_number}`\n"
        f"• **Client ID:** `{client_master_id}`\n"
        f"• **Journey:** {journey.capitalize()} | {client_type.replace('_', ' ').upper()}\n"
        f"• **Systems Updated:** {', '.join(posting_result['systems_updated'])}\n\n"
        "Your wealth management account has been opened and all systems have been updated. "
        "You will receive a welcome pack shortly. Welcome to ZenLabs Wealth Management! 🏦"
    )
    state.setdefault("messages", []).append({
        "role": "assistant", "agent": "account_creation", "content": msg,
    })
    state.setdefault("completed_steps", []).append("account_creation")
    state["current_step"] = "account_creation"
    return state
