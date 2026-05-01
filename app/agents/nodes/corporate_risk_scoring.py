"""Corporate Risk Scoring Agent — for corporate / trust journeys."""
from __future__ import annotations
import json
from langchain_core.messages import HumanMessage, SystemMessage
from agents.state import OnboardingState
from shared.logger import get_logger
from shared.llm import get_llm
from shared.risk_constants import HIGH_RISK_COUNTRIES, SECTOR_HIGH_RISK

log = get_logger("agent.corporate_risk_scoring")

_CORP_RISK_SYSTEM = """You are the Corporate Risk Assessment Agent for wealth management.
Assess AML/compliance risk for corporate and trust clients.
Return JSON:
{
  "risk_level": "low|medium|high|very_high|critical",
  "complex_ownership": false,
  "shell_company_indicators": false,
  "regulated_entity": false,
  "aml_concerns": [],
  "risk_mitigants": [],
  "assessment_notes": "",
  "confidence": 0.9
}"""


def corporate_risk_scoring_node(state: OnboardingState) -> OnboardingState:
    log.info("agent.corporate_risk_scoring.start")
    corp = state.get("corporate_profile") or {}
    kyb = state.get("_kyb_result") or {}

    llm = get_llm(max_tokens=512)
    context = {
        "company_name": corp.get("company_name", ""),
        "business_type": corp.get("business_type", ""),
        "incorporation_country": corp.get("incorporation_country", ""),
        "industry_code": corp.get("industry_code", ""),
        "ubo_count": len(corp.get("ubo_list") or []),
        "multi_jurisdiction": kyb.get("multi_jurisdiction", False),
        "complex_structure": kyb.get("complex_structure", False),
        "regulated": corp.get("regulated_entity", False),
    }
    try:
        resp = llm.invoke([
            SystemMessage(content=_CORP_RISK_SYSTEM),
            HumanMessage(content=f"Corporate context: {json.dumps(context)}"),
        ])
        result = json.loads(resp.content)
    except Exception:
        industry = corp.get("industry_code", "").lower()
        high_sector = any(s in industry for s in SECTOR_HIGH_RISK)
        country = corp.get("incorporation_country", "").upper()
        high_country = country in HIGH_RISK_COUNTRIES
        result = {
            "risk_level": "high" if (high_sector or high_country) else "medium",
            "complex_ownership": len(corp.get("ubo_list") or []) > 3,
            "shell_company_indicators": False,
            "regulated_entity": corp.get("regulated_entity", False),
            "aml_concerns": [], "risk_mitigants": [],
            "assessment_notes": "", "confidence": 0.85,
        }

    state["_corporate_risk"] = result  # type: ignore[assignment]

    if result.get("shell_company_indicators"):
        state["human_review_required"] = True
        state["human_review_reason"] = "Shell company indicators detected — enhanced review required"

    risk = result.get("risk_level", "medium")
    concerns = result.get("aml_concerns", [])
    conf = result.get("confidence", 0.9)
    icon = "🟢" if risk == "low" else "🟡" if risk == "medium" else "🔴"
    msg = (
        f"{icon} **Corporate Risk Assessment**\n\n"
        f"• **Risk Level:** {risk.replace('_', ' ').upper()}\n"
        f"• **Complex Ownership:** {'Yes' if result.get('complex_ownership') else 'No'}\n"
        f"• **Regulated Entity:** {'Yes' if result.get('regulated_entity') else 'No'}\n"
        f"• **Confidence:** {conf:.0%}\n"
        + (f"• **AML Concerns:** {', '.join(concerns)}\n" if concerns else "")
        + "\nProceeding to risk scoring and routing decision…"
    )
    state.setdefault("messages", []).append({
        "role": "assistant", "agent": "corporate_risk_scoring", "content": msg,
    })
    state.setdefault("completed_steps", []).append("corporate_risk_scoring")
    state["current_step"] = "corporate_risk_scoring"
    return state
