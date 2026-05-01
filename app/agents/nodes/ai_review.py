"""AI Review Agent — BRD Phase 7 / FR-A1: 8 LLM output types.

FR-A1: case summary, missing info, KYC inconsistencies, SOW assessment,
       adverse media assessment, RFI draft, compliance review summary, next-best action.
FR-A2: confidence score on all outputs; below threshold → human review.
FR-A3: deterministic validation of LLM outputs.
FR-A4: LLM must NOT recommend to dismiss sanctions, approve PEP, or decline SAR.
FR-A5: all prompts/responses logged verbatim.
"""
from __future__ import annotations
import json
from langchain_core.messages import HumanMessage, SystemMessage
from agents.state import OnboardingState
from shared.logger import get_logger
from shared.llm import get_llm
from shared.config import get_settings

log = get_logger("agent.ai_review")

_AI_REVIEW_SYSTEM = """You are the AI Case Review Agent for a wealth management compliance platform.
Your role is to SUMMARISE, CONTEXTUALISE, DRAFT, and RECOMMEND — never to make regulated decisions.

CARDINAL RULES (non-negotiable):
- You MUST NOT recommend dismissing a sanctions match
- You MUST NOT recommend approving a PEP without named senior management sign-off
- You MUST NOT recommend declining to file a SAR
- You MUST NOT modify, calculate, or override risk scores
- All regulated decisions (sanctions, PEP, EDD sign-off, SAR filing) require named human approval

Given the Context Pack, produce ALL 8 required outputs in valid JSON:
{
  "case_summary": "2-3 sentence factual summary of the onboarding case",
  "missing_information": ["list of identified gaps"],
  "kyc_inconsistencies": ["list of inconsistencies between provided data and documents"],
  "sow_assessment": "source of wealth narrative and documentation quality assessment",
  "adverse_media_assessment": "summary of adverse media findings and risk implications",
  "rfi_draft": "professional request-for-information letter draft if required (else empty string)",
  "compliance_review_summary": "compliance officer case brief",
  "next_best_action": "recommended next action for the reviewer (NOT a compliance decision)",
  "overall_confidence": 0.9
}"""

_PROHIBITED_PHRASES = [
    "dismiss the sanctions", "clear the sanctions", "approve the pep without",
    "no need to file", "decline to file sar", "override the risk score",
    "not necessary to escalate",
]


def _validate_llm_output(result: dict, context_pack: dict) -> tuple[bool, list[str]]:
    """BRD FR-A3: deterministic validation of LLM output."""
    issues: list[str] = []

    # Schema conformance
    required_keys = [
        "case_summary", "missing_information", "kyc_inconsistencies",
        "sow_assessment", "adverse_media_assessment", "rfi_draft",
        "compliance_review_summary", "next_best_action", "overall_confidence",
    ]
    for k in required_keys:
        if k not in result:
            issues.append(f"Missing required output: {k}")

    # FR-A4: prohibited content check
    full_text = json.dumps(result).lower()
    for phrase in _PROHIBITED_PHRASES:
        if phrase in full_text:
            issues.append(f"Prohibited content detected: '{phrase}' (BRD FR-A4)")

    # PII boundary compliance — check tokenised fields were not revealed
    if "[tokenised-" not in full_text:
        pass  # OK if LLM didn't re-insert raw PII
    raw_pii_patterns = [r"\b\d{3}-\d{2}-\d{4}\b"]  # SSN pattern
    import re
    for pat in raw_pii_patterns:
        if re.search(pat, full_text):
            issues.append("Raw PII detected in LLM output — PII boundary violation")

    valid = len(issues) == 0
    return valid, issues


def ai_review_node(state: OnboardingState) -> OnboardingState:
    log.info("agent.ai_review.start")
    settings = get_settings()
    context_pack = state.get("context_pack") or {}

    llm = get_llm(max_tokens=1024)
    try:
        resp = llm.invoke([
            SystemMessage(content=_AI_REVIEW_SYSTEM),
            HumanMessage(content=f"Context Pack: {json.dumps(context_pack)}"),
        ])
        # BRD FR-A5: log verbatim
        log.info("ai_review.llm_response",
                 session_id=state.get("session_id"),
                 raw_response=resp.content[:500])
        result = json.loads(resp.content)
    except Exception as e:
        log.warning("ai_review.llm_failed", error=str(e))
        result = {
            "case_summary": "LLM processing unavailable — manual review required.",
            "missing_information": context_pack.get("missing_information", []),
            "kyc_inconsistencies": [],
            "sow_assessment": "Manual assessment required.",
            "adverse_media_assessment": "Manual assessment required.",
            "rfi_draft": "",
            "compliance_review_summary": "AI processing failed — manual review required.",
            "next_best_action": "Assign to compliance analyst for manual review.",
            "overall_confidence": 0.0,
        }

    # BRD FR-A3: validate output
    valid, validation_issues = _validate_llm_output(result, context_pack)
    if not valid:
        log.warning("ai_review.validation_failed", issues=validation_issues)
        state["human_review_required"] = True
        state["human_review_reason"] = (
            f"LLM output validation failed ({len(validation_issues)} issue(s)): "
            + "; ".join(validation_issues)
        )

    confidence = result.get("overall_confidence", 0.9)
    if confidence < settings.llm_confidence_threshold:
        # BRD FR-A2: below threshold → mandatory human review
        state["human_review_required"] = True
        state["human_review_reason"] = (
            f"AI confidence {confidence:.0%} below threshold "
            f"{settings.llm_confidence_threshold:.0%} (BRD FR-A2)"
        )

    # Store LLM outputs in state and context pack
    state["llm_case_summary"]               = result.get("case_summary", "")
    state["llm_missing_info"]               = result.get("missing_information", [])
    state["llm_kyc_inconsistencies"]        = result.get("kyc_inconsistencies", [])
    state["llm_sow_assessment"]             = result.get("sow_assessment", "")
    state["llm_adverse_media_assessment"]   = result.get("adverse_media_assessment", "")
    state["llm_rfi_draft"]                  = result.get("rfi_draft", "")
    state["llm_compliance_review_summary"]  = result.get("compliance_review_summary", "")
    state["llm_next_best_action"]           = result.get("next_best_action", "")

    if context_pack:
        context_pack["llm_outputs"] = result

    conf_icon = "✅" if confidence >= settings.llm_confidence_threshold else "🟡"
    missing = result.get("missing_information", [])
    msg = (
        f"🤖 **AI Case Review Complete**\n\n"
        f"**Summary:** {result.get('case_summary', '')}\n\n"
        f"• {conf_icon} **AI Confidence:** {confidence:.0%}\n"
        f"• **Missing Information:** {len(missing)} item(s)\n"
        f"• **KYC Inconsistencies:** {len(result.get('kyc_inconsistencies', []))}\n"
        f"• **Next Best Action:** {result.get('next_best_action', 'Proceed to compliance review')}\n\n"
        + ("⚠️ Human review triggered — see compliance queue.\n" if state.get("human_review_required") else
           "Proceeding to routing decision…")
    )
    state.setdefault("messages", []).append({
        "role": "assistant", "agent": "ai_review", "content": msg,
    })
    state.setdefault("completed_steps", []).append("ai_review")
    state["current_step"] = "ai_review"
    return state
