"""Source of Wealth Agent — BRD Phase 6: EDD for high-value clients."""
from __future__ import annotations
import json
from langchain_core.messages import HumanMessage, SystemMessage
from agents.state import OnboardingState
from shared.logger import get_logger
from shared.llm import get_llm
from shared.scoring import classify_sow_risk
from shared.risk_constants import SOW_TYPES
from shared.config import get_settings

log = get_logger("agent.source_of_wealth")

_SOW_SYSTEM = """You are the Source of Wealth (EDD) Compliance Agent for a wealth management platform.
Assess legitimacy and documentation quality of declared wealth sources.
Return JSON:
{
  "verification_status": "verified|partial|unverified|flagged",
  "wealth_types": ["employment_income"],
  "documentation_quality": "good|acceptable|insufficient",
  "total_declared_wealth": 0.0,
  "risk_flags": [],
  "edd_required": false,
  "assessment_notes": ""
}
Flag as 'flagged' if: cryptocurrency > 30% of wealth, lottery/gambling source,
undocumented gifts, or declared wealth inconsistent with profile.
"""


def _should_trigger_sow(state: OnboardingState) -> bool:
    settings = get_settings()
    profile = state.get("client_profile") or {}
    kyc = state.get("kyc_result") or {}
    assets = profile.get("investable_assets") or profile.get("annual_income") or 0
    risk = kyc.get("risk_level", "low")
    return (
        assets >= settings.sow_income_threshold
        or risk in ("high", "very_high", "critical")
        or state.get("journey_type") in ("corporate", "trust")
        or state.get("client_type") in ("hnw", "uhnw")
    )


def source_of_wealth_node(state: OnboardingState) -> OnboardingState:
    log.info("agent.source_of_wealth.start")

    if not _should_trigger_sow(state):
        log.info("agent.source_of_wealth.skipped", reason="EDD threshold not met")
        state.setdefault("messages", []).append({
            "role": "assistant", "agent": "source_of_wealth",
            "content": "💼 **Source of Wealth:** Standard profile — no Enhanced Due Diligence required. Proceeding…",
        })
        state.setdefault("completed_steps", []).append("source_of_wealth")
        state["current_step"] = "source_of_wealth"
        return state

    llm = get_llm(max_tokens=512)
    profile = state.get("client_profile") or {}
    corp = state.get("corporate_profile") or {}
    kyc = state.get("kyc_result") or {}

    context = {
        "full_name": profile.get("full_name", ""),
        "annual_income": profile.get("annual_income", 0),
        "investable_assets": profile.get("investable_assets", 0),
        "employment_type": profile.get("employment_type", ""),
        "nationality": profile.get("nationality", ""),
        "kyc_risk_level": kyc.get("risk_level", ""),
        "company_name": corp.get("company_name", ""),
        "annual_turnover": corp.get("annual_turnover", 0),
        "client_type": state.get("client_type", "retail"),
    }
    try:
        resp = llm.invoke([
            SystemMessage(content=_SOW_SYSTEM),
            HumanMessage(content=f"Client context: {json.dumps(context)}"),
        ])
        result = json.loads(resp.content)
    except Exception:
        result = {}

    result.setdefault("verification_status", "partial")
    result.setdefault("wealth_types", ["employment_income"])
    result.setdefault("documentation_quality", "acceptable")
    result.setdefault("total_declared_wealth", profile.get("investable_assets", 0))
    result.setdefault("risk_flags", [])
    result.setdefault("edd_required", False)
    if not result["wealth_types"]:
        result["wealth_types"] = ["employment_income"]

    state["sow_result"] = result  # type: ignore[assignment]

    if result.get("documentation_quality") == "insufficient":
        state["human_review_required"] = True
        state["human_review_reason"] = "Source of wealth documentation insufficient for EDD — BRD Phase 6"

    status = result.get("verification_status", "partial")
    wealth_types = result["wealth_types"]
    risk_level = classify_sow_risk(wealth_types)
    flags = result.get("risk_flags", [])
    doc_quality = result.get("documentation_quality", "acceptable")

    if status in ("verified", "partial") and doc_quality != "insufficient":
        msg = (
            f"💼 **Source of Wealth — {status.capitalize()}**\n\n"
            f"• **Declared Sources:** {', '.join(wealth_types)}\n"
            f"• **Documentation Quality:** {doc_quality.capitalize()}\n"
            f"• **EDD Risk Level:** {risk_level.capitalize()}\n"
            + (f"• **Risk Flags:** {', '.join(flags)}\n" if flags else "")
            + "\nProceeding to risk scoring…"
        )
    else:
        msg = (
            "💼 **Source of Wealth — Enhanced Review Required**\n\n"
            f"• **Status:** {status.capitalize()}\n"
            + (f"• **Flags:** {', '.join(flags)}\n" if flags else "")
            + "\nAdditional SOW documentation is required. "
            "Our EDD team will be in contact."
        )

    state.setdefault("messages", []).append({
        "role": "assistant", "agent": "source_of_wealth", "content": msg,
    })
    state.setdefault("completed_steps", []).append("source_of_wealth")
    state["current_step"] = "source_of_wealth"
    return state
