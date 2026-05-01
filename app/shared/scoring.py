"""Deterministic risk scoring — no LLM calls, pure rule-based (BRD FR-R3)."""
from __future__ import annotations
from typing import Any

from shared.risk_constants import (
    HIGH_RISK_COUNTRIES, OFFSHORE_COUNTRIES, SECTOR_HIGH_RISK,
    RISK_BAND_THRESHOLDS, SOW_RISK_INDICATORS, STP_RULES,
)


def score_client_risk(
    kyc_result: dict[str, Any],
    client_profile: dict[str, Any],
    documents: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    score = 0.0
    components: dict[str, float] = {}

    # KYC/AML risk
    if kyc_result.get("sanctions_hit"):
        score += 40; components["sanctions_hit"] = 40
    if kyc_result.get("pep_flag"):
        score += 25; components["pep_flag"] = 25
    if kyc_result.get("adverse_media"):
        score += 15; components["adverse_media"] = 15
    kyc_conf = kyc_result.get("confidence", 1.0)
    if kyc_conf < 0.6:
        score += 20; components["low_kyc_confidence"] = 20
    elif kyc_conf < 0.75:
        score += 10; components["medium_kyc_confidence"] = 10

    # Geographic risk
    nationality = (client_profile.get("nationality") or "").upper()
    if nationality in HIGH_RISK_COUNTRIES:
        score += 20; components["high_risk_country"] = 20
    elif nationality in OFFSHORE_COUNTRIES:
        score += 10; components["offshore_country"] = 10

    # Wealth level risk (EDD trigger)
    aum = client_profile.get("investable_assets", 0) or 0
    if aum > 10_000_000:
        score += 15; components["uhnw_edd"] = 15
    elif aum > 1_000_000:
        score += 5; components["hnw_enhanced_scrutiny"] = 5

    # Document quality
    if documents:
        low_ocr = [d for d in documents if d.get("ocr_confidence", 1.0) < 0.85]
        if low_ocr:
            score += 10; components["low_ocr_quality"] = 10

    score = min(score, 100.0)
    return {
        "composite_score": round(score, 2),
        "risk_band": classify_risk_band(score),
        "score_components": components,
    }


def classify_risk_band(score: float) -> str:
    for band, (lo, hi) in RISK_BAND_THRESHOLDS.items():
        if lo <= score < hi:
            return band
    return "critical"


def evaluate_stp_rules(
    kyc_result: dict[str, Any],
    client_profile: dict[str, Any],
    risk_score: dict[str, Any],
    settings_stp_threshold: float = 500_000.0,
) -> dict[str, Any]:
    """BRD FR-R4: STP requires ALL rules to pass simultaneously."""
    passed: list[str] = []
    failed: list[str] = []

    def check(rule: str, condition: bool) -> None:
        (passed if condition else failed).append(rule)

    check("no_sanctions_hit",             not kyc_result.get("sanctions_hit", False))
    check("no_pep_flag",                  not kyc_result.get("pep_flag", False))
    check("no_adverse_media",             not kyc_result.get("adverse_media", False))
    check("kyc_confidence_above_threshold", kyc_result.get("confidence", 0) >= 0.75)
    nationality = (client_profile.get("nationality") or "").upper()
    check("not_high_risk_country",        nationality not in HIGH_RISK_COUNTRIES)
    check("income_within_stp_threshold",
          (client_profile.get("investable_assets") or 0) <= settings_stp_threshold)
    check("id_document_valid",            kyc_result.get("identity_verified", False))
    check("source_of_wealth_verified",    client_profile.get("sow_declared", False))
    check("fatca_crs_complete",           client_profile.get("fatca_completed", False))
    check("data_complete",                bool(client_profile.get("full_name")))
    rband = risk_score.get("risk_band", "high")
    check("risk_score_below_threshold",   rband in ("low", "medium"))

    if failed:
        critical_fails = [r for r in failed if r in ("no_sanctions_hit", "id_document_valid")]
        decision = "INELIGIBLE" if critical_fails else "REQUIRES_REVIEW"
    else:
        decision = "AUTO_APPROVED"

    return {
        "decision": decision,
        "rules_passed": passed,
        "rules_failed": failed,
        "rule_count": len(STP_RULES),
        "pass_count": len(passed),
        "fail_count": len(failed),
    }


def classify_sow_risk(wealth_types: list[str]) -> str:
    if not wealth_types:
        return "high"
    levels = [SOW_RISK_INDICATORS.get(t, "high") for t in wealth_types]
    order = ["low", "medium", "high", "very_high", "critical"]
    return max(levels, key=lambda x: order.index(x) if x in order else 3)
