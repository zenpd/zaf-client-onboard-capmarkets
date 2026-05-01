"""FATCA / CRS Classification Agent — BRD Phase 5 / FR-R5.

FR-R5: Missing FATCA/CRS self-certification blocks case progression.
Missing TIN triggers withholding obligation flag.
"""
from __future__ import annotations
from agents.state import OnboardingState
from shared.logger import get_logger

log = get_logger("agent.fatca_crs")


def fatca_crs_node(state: OnboardingState) -> OnboardingState:
    log.info("agent.fatca_crs.start")
    profile = state.get("client_profile") or {}
    corp = state.get("corporate_profile") or {}
    journey = state.get("journey_type", "individual")

    nationality = (profile.get("nationality") or
                   corp.get("incorporation_country") or "GB").upper()
    tax_id = profile.get("tax_id") or corp.get("ein") or ""
    fatca_completed = profile.get("fatca_completed", False)

    # FATCA: is this a US person?
    us_indicators = nationality == "US" or (tax_id and tax_id.startswith("US"))
    fatca_status = "us_person" if us_indicators else "non_us_person"

    # Missing self-certification check (BRD FR-R5)
    missing: list[str] = []
    if not fatca_completed:
        missing.append("FATCA/CRS Self-Certification Form")
    if not tax_id:
        missing.append("Tax Identification Number (TIN/SSN/UTR)")

    withholding_required = bool(missing and fatca_status == "us_person")

    fatca_result = {
        "fatca_status": fatca_status,
        "crs_country": nationality,
        "tin_provided": bool(tax_id),
        "withholding_required": withholding_required,
        "self_cert_complete": fatca_completed,
        "missing_fields": missing,
    }
    state["fatca_crs_result"] = fatca_result  # type: ignore[assignment]

    if missing:
        # BRD FR-R5: missing FATCA/CRS blocks progression
        state["human_review_required"] = True
        state["human_review_reason"] = f"FATCA/CRS incomplete — missing: {', '.join(missing)}"
        items = "\n".join(f"  • {m}" for m in missing)
        msg = (
            "⚠️ **FATCA/CRS — Action Required**\n\n"
            "The following FATCA/CRS requirements are incomplete:\n"
            f"{items}\n\n"
            + ("💡 **Note:** As a US Person, withholding tax obligations apply until "
               "self-certification is completed.\n\n" if withholding_required else "")
            + "Your case cannot progress until these are provided. "
            "Please complete the FATCA/CRS self-certification form."
        )
    else:
        msg = (
            f"✅ **FATCA/CRS Classification Complete**\n\n"
            f"• **FATCA Status:** {fatca_status.replace('_', ' ').title()}\n"
            f"• **CRS Reporting Country:** {nationality}\n"
            f"• **TIN Provided:** {'Yes' if tax_id else 'No'}\n"
            f"• **Self-Certification:** Complete\n\n"
            "Proceeding to source of wealth assessment…"
        )

    state.setdefault("messages", []).append({
        "role": "assistant", "agent": "fatca_crs", "content": msg,
    })
    state.setdefault("completed_steps", []).append("fatca_crs")
    state["current_step"] = "fatca_crs"
    return state
