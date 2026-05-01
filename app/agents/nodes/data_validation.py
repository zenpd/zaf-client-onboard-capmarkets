"""Data Validation Agent — BRD Phase 3: mandatory field validation."""
from __future__ import annotations
from agents.state import OnboardingState
from shared.logger import get_logger

log = get_logger("agent.data_validation")

_REQUIRED_INDIVIDUAL_FIELDS = [
    ("full_name",    "Full Legal Name"),
    ("dob",          "Date of Birth"),
    ("nationality",  "Nationality"),
    ("email",        "Email Address"),
    ("address",      "Residential Address"),
    ("id_type",      "Identity Document Type"),
    ("id_number",    "Identity Document Number"),
]

_REQUIRED_CORPORATE_FIELDS = [
    ("company_name",          "Company Name"),
    ("registration_number",   "Registration Number"),
    ("incorporation_country", "Country of Incorporation"),
    ("directors",             "Directors"),
    ("ubo_list",              "Ultimate Beneficial Owners"),
]


def data_validation_node(state: OnboardingState) -> OnboardingState:
    log.info("agent.data_validation.start")
    journey = state.get("journey_type", "individual")
    missing: list[str] = []

    if journey in ("individual", "joint"):
        profile = state.get("client_profile") or {}
        for field, label in _REQUIRED_INDIVIDUAL_FIELDS:
            val = profile.get(field)
            if not val or (isinstance(val, dict) and not any(val.values())):
                missing.append(label)
        if journey == "joint" and not profile.get("joint_holder"):
            missing.append("Joint Account Holder Details")
    else:
        corp = state.get("corporate_profile") or {}
        for field, label in _REQUIRED_CORPORATE_FIELDS:
            val = corp.get(field)
            if not val or (isinstance(val, list) and len(val) == 0):
                missing.append(label)

    if missing:
        items = "\n".join(f"  • {f}" for f in missing)
        msg = (
            "⚠️ **Missing Required Information**\n\n"
            "The following fields are required before we can proceed:\n"
            f"{items}\n\n"
            "Please provide the missing details to continue your onboarding."
        )
        state.setdefault("messages", []).append({
            "role": "assistant", "agent": "data_validation", "content": msg,
        })
        # Do NOT advance — BRD FR-R1
        state.setdefault("completed_steps", []).append("data_validation")
        state["current_step"] = "data_validation"
        return state

    msg = (
        "✅ **Data Validation Passed**\n\n"
        "All required fields have been successfully validated. "
        "Proceeding to identity screening…"
    )
    state.setdefault("messages", []).append({
        "role": "assistant", "agent": "data_validation", "content": msg,
    })
    state.setdefault("completed_steps", []).append("data_validation")
    state["current_step"] = "data_validation"
    return state
