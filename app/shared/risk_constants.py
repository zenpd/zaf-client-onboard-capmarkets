"""Risk constants for Wealth Management / Capital Markets onboarding (BRD-aligned)."""
from __future__ import annotations

# FATF grey/black list and high-risk jurisdictions (ISO 3166-1 alpha-2)
HIGH_RISK_COUNTRIES: frozenset[str] = frozenset({
    "AF", "KP", "IR", "MM", "SY", "YE", "SO", "SS", "VE",
    "PK", "TR", "PH", "MU", "VN", "NG",
})

# Common offshore financial centres
OFFSHORE_COUNTRIES: frozenset[str] = frozenset({
    "KY", "VG", "BVI", "PA", "LI", "GG", "JE", "IM", "MC", "SM",
    "AN", "TC", "BS", "BZ", "SC", "MH",
})

# OFAC / UN / EU / HMT sanctions lists (BRD Phase 4-5)
SANCTIONS_LISTS = ["OFAC", "UN", "EU", "HMT"]

# High-risk sectors (AML — wealth management context)
SECTOR_HIGH_RISK: frozenset[str] = frozenset({
    "gambling", "cryptocurrency", "weapons", "arms",
    "precious_metals", "real_estate", "cash_intensive",
    "money_services", "charities_ngo", "shell_companies",
    "private_equity_unregulated", "political",
})

# Risk score bands (composite 0–100)
RISK_BAND_THRESHOLDS = {
    "low":       (0,  25),
    "medium":    (25, 50),
    "high":      (50, 75),
    "very_high": (75, 90),
    "critical":  (90, 101),
}

# Periodic review frequency by risk band (months)
REVIEW_FREQUENCY: dict[str, int] = {
    "low":       36,
    "medium":    24,
    "high":      12,
    "very_high":  6,
    "critical":   3,
}

# Source of wealth categories (BRD)
SOW_TYPES = [
    "employment_income",
    "business_income",
    "investment_returns",
    "inheritance",
    "property_sale",
    "pension",
    "gifts_donations",
    "lottery_gambling",
    "divorce_settlement",
    "insurance_payout",
    "cryptocurrency",
    "trust_distribution",
    "other",
]

# SOW risk level per type
SOW_RISK_INDICATORS: dict[str, str] = {
    "employment_income":  "low",
    "business_income":    "medium",
    "investment_returns": "low",
    "inheritance":        "medium",
    "property_sale":      "medium",
    "pension":            "low",
    "gifts_donations":    "high",
    "lottery_gambling":   "very_high",
    "divorce_settlement": "medium",
    "insurance_payout":   "low",
    "cryptocurrency":     "high",
    "trust_distribution": "medium",
    "other":              "high",
}

# STP eligibility rules (BRD FR-R4)
STP_RULES = [
    "no_sanctions_hit",
    "no_pep_flag",
    "no_adverse_media",
    "kyc_confidence_above_threshold",
    "not_high_risk_country",
    "not_high_risk_sector",
    "income_within_stp_threshold",
    "no_previous_rejection",
    "id_document_valid",
    "single_nationality",
    "no_edd_triggers",
    "residential_address_verified",
    "fatca_crs_complete",
    "source_of_wealth_verified",
    "data_complete",
    "risk_score_below_threshold",
]
