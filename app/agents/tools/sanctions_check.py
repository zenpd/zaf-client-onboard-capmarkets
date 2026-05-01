"""Sanctions screening tool — checks OFAC, UN, EU, HMT lists (BRD Phase 4)."""
from __future__ import annotations
import hashlib
from shared.risk_constants import HIGH_RISK_COUNTRIES, SANCTIONS_LISTS


def run_sanctions_check(
    name: str,
    dob: str = "",
    nationality: str = "",
    id_number: str = "",
) -> dict:
    """
    Deterministic sanctions check.
    In production this calls the vendor screening API (e.g. Refinitiv, LexisNexis).
    BRD FR-R2: a confirmed/high-score match triggers auto case hold + MLRO notification.
    """
    fingerprint = hashlib.sha256(f"{name.lower().strip()}:{dob}:{nationality}".encode()).hexdigest()
    hit = fingerprint[:2] in ("0a", "ff")  # ~1.6% simulated hit rate

    return {
        "lists_checked": SANCTIONS_LISTS,
        "hit": hit,
        "hit_list": ["OFAC"] if hit else [],
        "hit_name": name if hit else "",
        "match_score": 0.95 if hit else 0.0,
        "high_risk_country": nationality.upper() in HIGH_RISK_COUNTRIES,
        "provider_ref": f"SCR-{fingerprint[:8].upper()}",
    }
