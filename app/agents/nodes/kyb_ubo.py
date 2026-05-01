"""KYB / UBO Agent — BRD Phase 3 corporate journey: UBO identification."""
from __future__ import annotations
import json
from langchain_core.messages import HumanMessage, SystemMessage
from agents.state import OnboardingState
from agents.tools.sanctions_check import run_sanctions_check
from shared.logger import get_logger
from shared.llm import get_llm

log = get_logger("agent.kyb_ubo")

_KYB_SYSTEM = """You are the KYB / UBO Compliance Agent for a wealth management platform.
Analyse the corporate structure and UBO (Ultimate Beneficial Owner) information.
UBO threshold: 25% beneficial ownership (FATF / FinCEN CDD Rule).
Return JSON:
{
  "kyb_status": "pass|fail|review",
  "ubo_count": 0,
  "all_ubos_identified": true,
  "complex_structure": false,
  "multi_jurisdiction": false,
  "risk_level": "low|medium|high|critical",
  "missing_information": [],
  "assessment_notes": "",
  "confidence": 0.9
}"""


def kyb_ubo_node(state: OnboardingState) -> OnboardingState:
    log.info("agent.kyb_ubo.start")
    corp = state.get("corporate_profile") or {}
    ubos = corp.get("ubo_list") or []
    directors = corp.get("directors") or []

    # Screen each UBO for sanctions/PEP
    ubo_hits = []
    for ubo in ubos:
        if isinstance(ubo, dict):
            result = run_sanctions_check(
                name=ubo.get("name", ""),
                dob=ubo.get("dob", ""),
                nationality=ubo.get("nationality", ""),
            )
            if result.get("hit"):
                ubo_hits.append(ubo.get("name", "Unknown"))

    if ubo_hits:
        state["human_review_required"] = True
        state["mlro_notified"] = True
        state["human_review_reason"] = (
            f"Sanctions hit on UBO(s): {', '.join(ubo_hits)} — MLRO notified"
        )

    llm = get_llm(max_tokens=512)
    context = {
        "company_name": corp.get("company_name", ""),
        "business_type": corp.get("business_type", ""),
        "ubos": [u.get("name", "") if isinstance(u, dict) else str(u) for u in ubos],
        "ubo_count": len(ubos),
        "directors": [d.get("name", "") if isinstance(d, dict) else str(d) for d in directors],
        "incorporation_country": corp.get("incorporation_country", ""),
        "ubo_hits": ubo_hits,
    }
    try:
        resp = llm.invoke([
            SystemMessage(content=_KYB_SYSTEM),
            HumanMessage(content=f"Corporate context: {json.dumps(context)}"),
        ])
        result = json.loads(resp.content)
    except Exception:
        result = {
            "kyb_status": "review", "ubo_count": len(ubos),
            "all_ubos_identified": bool(ubos),
            "complex_structure": len(ubos) > 3,
            "multi_jurisdiction": False, "risk_level": "medium",
            "missing_information": [], "assessment_notes": "",
            "confidence": 0.85,
        }

    state["_kyb_result"] = result  # type: ignore[assignment]

    if not result.get("all_ubos_identified"):
        state["human_review_required"] = True
        state["human_review_reason"] = "UBO identification incomplete — cannot proceed without full UBO chain"

    kyb_status = result.get("kyb_status", "review")
    risk = result.get("risk_level", "medium")
    conf = result.get("confidence", 0.9)
    missing = result.get("missing_information", [])

    status_icon = "✅" if kyb_status == "pass" else "🟡"
    msg = (
        f"{status_icon} **KYB / UBO Assessment**\n\n"
        f"• **Status:** {kyb_status.upper()}\n"
        f"• **UBOs Identified:** {result.get('ubo_count', len(ubos))}\n"
        f"• **Complex Structure:** {'Yes' if result.get('complex_structure') else 'No'}\n"
        f"• **Multi-Jurisdiction:** {'Yes' if result.get('multi_jurisdiction') else 'No'}\n"
        f"• **Risk Level:** {risk.capitalize()}\n"
        f"• **Confidence:** {conf:.0%}\n"
        + (f"\n⚠️ **Missing:** {', '.join(missing)}" if missing else "")
        + "\n\nProceeding to FATCA/CRS classification…" if kyb_status == "pass" else
          "\n\nAdditional UBO documentation may be required."
    )
    state.setdefault("messages", []).append({
        "role": "assistant", "agent": "kyb_ubo", "content": msg,
    })
    state.setdefault("completed_steps", []).append("kyb_ubo")
    state["current_step"] = "kyb_ubo"
    return state
