"""Entity Resolution Agent — BRD Phase 3 / FR-D3: duplicate check."""
from __future__ import annotations
import hashlib
from agents.state import OnboardingState
from shared.helpers import generate_id
from shared.logger import get_logger

log = get_logger("agent.entity_resolution")


def _check_duplicate(name: str, dob: str, id_number: str) -> dict:
    """
    Multi-attribute matching: name + DOB + ID (BRD FR-D3).
    Definite duplicates must block new client creation.
    """
    fingerprint = hashlib.sha256(
        f"{name.lower().strip()}:{dob}:{id_number.strip()}".encode()
    ).hexdigest()
    # Simulated: ~1% definite duplicate, ~2% potential match
    code = int(fingerprint[:2], 16)
    if code < 3:
        status = "definite_match"
    elif code < 9:
        status = "potential_match"
    else:
        status = "clear"
    return {
        "status": status,
        "match_score": 0.99 if status == "definite_match" else (0.7 if status == "potential_match" else 0.0),
        "entity_id": generate_id("ENT"),
        "check_ref": fingerprint[:8].upper(),
    }


def entity_resolution_node(state: OnboardingState) -> OnboardingState:
    log.info("agent.entity_resolution.start")
    profile = state.get("client_profile") or {}
    corp = state.get("corporate_profile") or {}

    name = profile.get("full_name") or corp.get("company_name") or ""
    dob = profile.get("dob") or corp.get("incorporation_date") or ""
    id_number = profile.get("id_number") or corp.get("registration_number") or ""

    result = _check_duplicate(name, dob, id_number)
    status = result["status"]

    state["_entity_resolution"] = result  # type: ignore[assignment]

    if status == "definite_match":
        # BRD FR-D3: definite duplicates block new client creation
        state["human_review_required"] = True
        state["human_review_reason"] = "Definite duplicate client detected — manual reconciliation required (BRD FR-D3)"
        state["routing_lane"] = "hold"  # type: ignore[assignment]
        msg = (
            "🔴 **Duplicate Client Detected**\n\n"
            "Our system has identified a potential existing record matching your details. "
            "Your application has been placed on hold pending review by our client services team. "
            "You will be contacted within 1 business day."
        )
    elif status == "potential_match":
        state["human_review_required"] = True
        state["human_review_reason"] = "Potential duplicate client — human validation required"
        msg = (
            "🟡 **Identity Confirmation Required**\n\n"
            "Our system has identified a possible existing record. "
            "A brief identity confirmation step is required. Our team will be in touch."
        )
    else:
        msg = (
            "✅ **Identity Uniqueness Confirmed**\n\n"
            "No duplicate records found. Proceeding to sanctions and PEP screening…"
        )

    state.setdefault("messages", []).append({
        "role": "assistant", "agent": "entity_resolution", "content": msg,
    })
    state.setdefault("completed_steps", []).append("entity_resolution")
    state["current_step"] = "entity_resolution"
    return state
