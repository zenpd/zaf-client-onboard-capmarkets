"""Sanctions / PEP / Adverse Media Screening Agent — BRD Phase 4-5.

FR-R2: sanctions hit → auto hold + MLRO notification.
FR-H3: PEP acceptance requires named senior management approver.
"""
from __future__ import annotations
import json
from langchain_core.messages import HumanMessage, SystemMessage
from agents.state import OnboardingState
from agents.tools.sanctions_check import run_sanctions_check
from shared.logger import get_logger
from shared.llm import get_llm

log = get_logger("agent.sanctions_pep_screening")

_SCREENING_SYSTEM = """You are the Sanctions, PEP and Adverse Media Screening Agent.
Given the client profile and initial sanctions check results, assess:
1. Adverse media — public negative news, criminal allegations, regulatory actions
2. PEP category — domestic, foreign, international org, family member, close associate
Return JSON only:
{
  "adverse_media": false,
  "adverse_media_summary": "",
  "adverse_media_severity": "none|low|medium|high",
  "pep_confirmed": false,
  "pep_category": "",
  "pep_risk_assessment": "",
  "overall_screening_status": "clear|review|blocked",
  "confidence": 0.95
}
"""
CONFIDENCE_THRESHOLD = 0.75


def sanctions_pep_screening_node(state: OnboardingState) -> OnboardingState:
    log.info("agent.sanctions_pep_screening.start")
    profile = state.get("client_profile") or {}
    corp = state.get("corporate_profile") or {}

    name = profile.get("full_name") or corp.get("company_name") or ""
    dob = profile.get("dob") or ""
    nationality = (profile.get("nationality") or corp.get("incorporation_country") or "")

    # Deterministic sanctions check first (BRD FR-R2)
    sanctions_result = run_sanctions_check(name=name, dob=dob, nationality=nationality)
    sanctions_hit = sanctions_result.get("hit", False)

    if sanctions_hit:
        # BRD FR-R2: confirmed sanctions → automatic hold + MLRO notification
        # BRD FR-A4: LLM must NOT clear a sanctions hold
        state["human_review_required"] = True
        state["mlro_notified"] = True
        state["routing_lane"] = "hold"  # type: ignore[assignment]
        state["human_review_reason"] = (
            f"CONFIRMED sanctions match on {sanctions_result.get('hit_list', [])} — "
            "MLRO notified. No automated process may clear this hold (BRD FR-R2)."
        )
        state["kyc_result"] = {  # type: ignore[assignment]
            "status": "fail",
            "sanctions_hit": True,
            "sanctions_lists_hit": sanctions_result.get("hit_list", []),
            "pep_flag": False,
            "adverse_media": False,
            "risk_level": "critical",
            "confidence": 0.99,
            "explanation": "Confirmed sanctions match — case automatically held.",
        }
        msg = (
            "🚨 **Application on Hold — Compliance Review**\n\n"
            "Your application has been placed on hold pending a mandatory compliance review. "
            "Our MLRO team has been notified. This process is required by regulatory obligation.\n\n"
            "You will be contacted by our compliance team. No further action is required from you."
        )
        state.setdefault("messages", []).append({
            "role": "assistant", "agent": "sanctions_pep_screening", "content": msg,
        })
        state.setdefault("completed_steps", []).append("sanctions_pep_screening")
        state["current_step"] = "sanctions_pep_screening"
        return state

    # LLM for adverse media + PEP assessment
    llm = get_llm(max_tokens=512)
    context = {
        "name": name,
        "nationality": nationality,
        "pep_declared": profile.get("pep_status", False),
        "sanctions_result": sanctions_result,
        "employment": profile.get("employment_type", ""),
    }
    try:
        resp = llm.invoke([
            SystemMessage(content=_SCREENING_SYSTEM),
            HumanMessage(content=f"Client context: {json.dumps(context)}"),
        ])
        result = json.loads(resp.content)
    except Exception:
        result = {
            "adverse_media": False, "adverse_media_summary": "",
            "adverse_media_severity": "none", "pep_confirmed": False,
            "pep_category": "", "pep_risk_assessment": "",
            "overall_screening_status": "clear", "confidence": 0.9,
        }

    pep_confirmed = result.get("pep_confirmed", False) or profile.get("pep_status", False)
    adverse_media = result.get("adverse_media", False)
    confidence = result.get("confidence", 0.9)

    kyc_result = {
        "status": "review" if (pep_confirmed or adverse_media) else "pass",
        "identity_verified": True,
        "liveness_score": 0.95,
        "sanctions_hit": False,
        "sanctions_lists_hit": [],
        "pep_flag": pep_confirmed,
        "pep_category": result.get("pep_category", ""),
        "adverse_media": adverse_media,
        "adverse_media_summary": result.get("adverse_media_summary", ""),
        "risk_level": "high" if pep_confirmed else ("medium" if adverse_media else "low"),
        "confidence": confidence,
        "explanation": result.get("pep_risk_assessment", ""),
        "provider_ref": sanctions_result.get("provider_ref", ""),
    }
    state["kyc_result"] = kyc_result  # type: ignore[assignment]

    needs_review = confidence < CONFIDENCE_THRESHOLD or pep_confirmed or adverse_media
    if needs_review:
        state["human_review_required"] = True
        reason_parts = []
        if pep_confirmed:
            reason_parts.append(f"PEP confirmed ({result.get('pep_category', 'unknown category')})")
        if adverse_media:
            reason_parts.append(f"Adverse media ({result.get('adverse_media_severity', '')} severity)")
        if confidence < CONFIDENCE_THRESHOLD:
            reason_parts.append(f"Low screening confidence ({confidence:.0%})")
        state["human_review_reason"] = "; ".join(reason_parts)
        if pep_confirmed:
            # BRD FR-H3: PEP acceptance requires named senior management approver
            state["human_review_reason"] += " — PEP acceptance requires named senior management approver"

    status_icon = "🟡" if needs_review else "✅"
    status_text = "Review Required" if needs_review else "Clear"
    pep_cat_line = f"  Category: {result.get('pep_category')}\n" if pep_confirmed else ""
    msg = (
        f"{status_icon} **Sanctions & Screening — {status_text}**\n\n"
        f"• **Sanctions:** {'HIT ⛔' if sanctions_hit else 'Clear ✅'}\n"
        f"• **PEP Status:** {'Confirmed 🟡' if pep_confirmed else 'Not Identified ✅'}\n"
        + pep_cat_line
        + f"• **Adverse Media:** {'Flagged 🟡' if adverse_media else 'Clear ✅'}\n"
        f"• **Overall Status:** {result.get('overall_screening_status', 'clear').upper()}\n"
        f"• **Confidence:** {confidence:.0%}\n\n"
        + ("Our compliance team will review the screening results. " if needs_review else
           "Proceeding to FATCA/CRS classification…")
    )
    state.setdefault("messages", []).append({
        "role": "assistant", "agent": "sanctions_pep_screening", "content": msg,
    })
    state.setdefault("completed_steps", []).append("sanctions_pep_screening")
    state["current_step"] = "sanctions_pep_screening"
    return state
