"""Client Education Agent — BRD Phase 1: explain onboarding process to client."""
from __future__ import annotations
from agents.state import OnboardingState
from shared.logger import get_logger

log = get_logger("agent.client_education")

_JOURNEY_GUIDES = {
    "individual": {
        "title": "Individual / HNW / UHNW Client Onboarding",
        "steps": [
            "📋 Provide personal details (name, DOB, nationality, address)",
            "🪪 Upload identity documents (passport, national ID)",
            "📬 Upload proof of address (utility bill, bank statement)",
            "💰 Declare source of wealth and provide supporting evidence",
            "🛡️ Complete FATCA/CRS self-certification",
            "✅ Identity & sanctions screening (automated)",
            "📊 Risk assessment and portfolio onboarding",
        ],
        "timeline": "Typically 2–5 business days for standard risk profiles.",
    },
    "joint": {
        "title": "Joint Account Onboarding",
        "steps": [
            "📋 Provide details for both account holders",
            "🪪 Upload identity documents for each holder",
            "📬 Proof of address for each holder",
            "💰 Joint Source of Wealth declaration",
            "🛡️ FATCA/CRS for both holders",
            "✅ Screening for all parties",
        ],
        "timeline": "Typically 3–7 business days.",
    },
    "corporate": {
        "title": "Corporate / Institutional Client Onboarding",
        "steps": [
            "🏢 Company registration documents",
            "👥 Director and UBO (Ultimate Beneficial Owner) identification",
            "📜 Certified constitutional documents",
            "💼 Source of funds / corporate financials",
            "🛡️ FATCA/CRS classification",
            "✅ Enhanced KYB/UBO screening",
        ],
        "timeline": "Typically 10–25 business days for complex structures.",
    },
    "trust": {
        "title": "Trust / Foundation Onboarding",
        "steps": [
            "📜 Trust deed and formation documents",
            "👤 Trustee and beneficiary identification",
            "💰 Trust source of funds declaration",
            "🛡️ FATCA/CRS for trust and beneficiaries",
            "✅ Full UBO/control chain screening",
        ],
        "timeline": "Typically 15–25 business days.",
    },
}


def client_education_node(state: OnboardingState) -> OnboardingState:
    log.info("agent.client_education.start")
    journey = state.get("journey_type", "individual")
    guide = _JOURNEY_GUIDES.get(journey, _JOURNEY_GUIDES["individual"])
    client_type = state.get("client_type", "retail")

    steps_text = "\n".join(f"  {s}" for s in guide["steps"])
    msg = (
        f"👋 **Welcome to ZenLabs Wealth Management Onboarding**\n\n"
        f"**Journey:** {guide['title']}\n"
        f"**Client Classification:** {client_type.upper().replace('_', ' ')}\n\n"
        f"**Your onboarding steps:**\n{steps_text}\n\n"
        f"⏱️ **Expected Timeline:** {guide['timeline']}\n\n"
        "All information you provide is protected under our Privacy Policy and "
        "processed in accordance with GDPR / applicable data protection laws. "
        "Let's get started — please proceed to document collection."
    )
    state.setdefault("messages", []).append({
        "role": "assistant", "agent": "client_education", "content": msg,
    })
    state.setdefault("completed_steps", []).append("client_education")
    state["current_step"] = "client_education"
    return state
