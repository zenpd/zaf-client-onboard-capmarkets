"""Triage Agent — BRD Phase 1: classify client type, complexity & routing lane."""
from __future__ import annotations
from datetime import datetime, timezone

from agents.state import OnboardingState
from shared.helpers import generate_id
from shared.risk_constants import HIGH_RISK_COUNTRIES, OFFSHORE_COUNTRIES, SECTOR_HIGH_RISK
from shared.logger import get_logger

log = get_logger("agent.triage")


def _classify_client_type(state: OnboardingState) -> str:
    """Classify: retail | hnw | uhnw | corporate_simple | corporate_complex | trust."""
    journey = state.get("journey_type", "individual")
    if journey in ("corporate", "trust"):
        corp = state.get("corporate_profile") or {}
        ubos = corp.get("ubo_list") or []
        jurisdictions = [u.get("nationality", "") for u in ubos if isinstance(u, dict)]
        multi_jur = len(set(jurisdictions)) > 1
        return "corporate_complex" if multi_jur or len(ubos) > 3 else "corporate_simple"
    profile = state.get("client_profile") or {}
    assets = profile.get("investable_assets") or 0
    if assets >= 5_000_000:
        return "uhnw"
    elif assets >= 1_000_000:
        return "hnw"
    return "retail"


def _score_complexity(state: OnboardingState) -> tuple[float, list[str], str]:
    """
    Deterministic complexity scoring (BRD Phase 6 routing logic).
    Returns (score 0-100, risk indicators, routing lane).
    Routing: stp | standard | enhanced | edd | hold | reject
    """
    score = 0.0
    indicators: list[str] = []
    journey = state.get("journey_type", "individual")
    profile = state.get("client_profile") or {}
    corp = state.get("corporate_profile") or {}

    # Journey-type base complexity
    base = {"individual": 0, "joint": 5, "corporate": 25, "trust": 30}.get(journey, 0)
    score += base

    # Geographic risk
    nationality = (profile.get("nationality") or
                   corp.get("incorporation_country", "")).upper()
    if nationality in HIGH_RISK_COUNTRIES:
        score += 35; indicators.append("high_risk_jurisdiction")
    elif nationality in OFFSHORE_COUNTRIES:
        score += 15; indicators.append("offshore_jurisdiction")

    # PEP status (BRD: PEP acceptance requires named senior management approver)
    if profile.get("pep_status"):
        score += 30; indicators.append("pep_status")

    # Wealth level (EDD triggers)
    assets = profile.get("investable_assets") or 0
    income = profile.get("annual_income") or corp.get("annual_turnover") or 0
    if assets >= 5_000_000 or income >= 1_000_000:
        score += 20; indicators.append("high_value_edd_trigger")
    elif assets >= 1_000_000:
        score += 10; indicators.append("hnw_elevated_scrutiny")

    # Corporate complexity
    ubos = corp.get("ubo_list") or []
    directors = corp.get("directors") or []
    if len(ubos) > 3 or len(directors) > 5:
        score += 10; indicators.append("complex_ownership")

    # High-risk sector
    industry = corp.get("industry_code", "").lower()
    if any(s in industry for s in SECTOR_HIGH_RISK):
        score += 20; indicators.append("high_risk_sector")

    score = min(score, 100.0)

    # BRD routing logic
    if "high_risk_jurisdiction" in indicators:
        routing = "hold"
    elif score >= 75 or "pep_status" in indicators:
        routing = "edd"
    elif score >= 50:
        routing = "enhanced"
    elif score >= 25:
        routing = "standard"
    else:
        routing = "stp"

    return score, indicators, routing


def triage_node(state: OnboardingState) -> OnboardingState:
    log.info("agent.triage.start", journey=state.get("journey_type"))

    client_type = _classify_client_type(state)
    state["client_type"] = client_type  # type: ignore[assignment]

    score, indicators, routing = _score_complexity(state)

    triage_result = {
        "client_type": client_type,
        "routing_lane": routing,
        "complexity_score": round(score, 2),
        "risk_indicators": indicators,
        "triage_notes": f"Client type: {client_type} | Complexity: {score:.0f}/100 | Lane: {routing.upper()}",
        "triage_agent_id": generate_id("TRIAGE"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    state["triage_result"] = triage_result  # type: ignore[assignment]
    state["routing_lane"] = routing  # type: ignore[assignment]
    state["stp_eligible"] = routing == "stp"

    if routing == "hold":
        state["human_review_required"] = True
        state["human_review_reason"] = f"High-risk jurisdiction detected: {', '.join(indicators)}"
        state["mlro_notified"] = True

    state.setdefault("completed_steps", []).append("triage")
    state["current_step"] = "triage"
    return state
