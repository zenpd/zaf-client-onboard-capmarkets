"""OnboardingState TypedDict — shared contract across all LangGraph nodes.

Domain: Wealth Management / Capital Markets client onboarding.
BRD: 25-Step Client Onboarding Flow (UC-01) across 10 phases.
"""
from __future__ import annotations
from typing import Any, Literal, Optional
from typing_extensions import TypedDict


# ── Domain types ─────────────────────────────────────────────────────────────
JourneyType  = Literal["individual", "joint", "corporate", "trust"]
ClientType   = Literal["retail", "hnw", "uhnw", "corporate_simple", "corporate_complex", "trust"]
RiskLevel    = Literal["low", "medium", "high", "very_high", "critical"]
StepStatus   = Literal["pending", "in_progress", "completed", "failed", "escalated"]
RoutingLane  = Literal["stp", "standard", "enhanced", "edd", "hold", "reject"]
FATCAStatus  = Literal["us_person", "non_us_person", "undetermined"]
ReviewType   = Literal["annual", "trigger", "risk_based"]


class ClientProfile(TypedDict, total=False):
    """Individual / joint account profile (BRD Phase 1-3)."""
    client_id: str
    full_name: str
    dob: str                   # YYYY-MM-DD
    gender: str
    nationality: str
    country_of_residence: str
    email: str
    phone: str
    address: dict[str, str]
    id_type: str               # passport | national_id | drivers_license
    id_number: str
    tax_id: str                # SSN / TIN / UTR
    fatca_status: str          # FATCAStatus
    crs_country: str
    employment_type: str       # employed | self_employed | business_owner | retired | other
    employer_name: str
    annual_income: float
    investable_assets: float   # AUM classification: retail < $1M, HNW $1-5M, UHNW $5M+
    risk_appetite: str         # conservative | balanced | aggressive | speculative
    investment_experience: str # none | basic | intermediate | advanced | professional
    pep_status: bool
    pep_type: str              # domestic | foreign | international_org | family | close_associate
    high_risk_country: bool
    onboarding_channel: str    # portal | relationship_manager | branch | api
    sow_declared: bool
    fatca_completed: bool
    joint_holder: Optional[dict]  # second client profile for joint accounts


class CorporateProfile(TypedDict, total=False):
    """Corporate / trust entity profile (BRD Phase 1-3)."""
    company_id: str
    company_name: str
    registration_number: str
    lei_number: str            # Legal Entity Identifier
    ein: str
    incorporation_date: str
    incorporation_country: str
    business_type: str         # pvt_ltd | llp | partnership | public | trust | foundation
    registered_address: dict[str, str]
    directors: list[dict]
    ubo_list: list[dict]       # FinCEN/FATF: 25% beneficial ownership threshold
    industry_code: str
    annual_turnover: float
    total_assets: float
    high_risk_sector: bool
    regulated_entity: bool     # FCA / SEC / FINRA registration
    regulator_name: str
    regulator_id: str


class KYCResult(TypedDict, total=False):
    status: Literal["pass", "fail", "review"]
    identity_verified: bool
    liveness_score: float
    sanctions_hit: bool
    sanctions_lists_hit: list[str]
    pep_flag: bool
    pep_category: str
    adverse_media: bool
    adverse_media_summary: str
    duplicate_check: str       # clear | potential_match | definite_match
    entity_resolution_id: str
    risk_level: RiskLevel
    confidence: float
    explanation: str
    provider_ref: str


class AMLResult(TypedDict, total=False):
    status: Literal["clear", "flagged", "blocked"]
    sanctions_lists_checked: list[str]
    hits: list[dict]
    risk_score: float
    override_reason: str
    mlro_notified: bool


class FATCACRSResult(TypedDict, total=False):
    fatca_status: FATCAStatus
    crs_country: str
    tin_provided: bool
    withholding_required: bool
    self_cert_complete: bool
    missing_fields: list[str]


class ContextPack(TypedDict, total=False):
    """BRD FR-D4: versioned immutable context pack for LLM / human review."""
    pack_id: str
    version: int
    created_at: str
    client_profile: dict
    corporate_profile: dict
    kyc_result: dict
    aml_result: dict
    sow_result: dict
    fatca_crs_result: dict
    risk_score: dict
    triage_result: dict
    documents: list
    screening_results: dict
    missing_information: list[str]
    llm_outputs: dict
    reviewer_notes: str


class DocumentInfo(TypedDict, total=False):
    doc_id: str
    doc_type: str
    file_name: str
    extracted_fields: dict[str, Any]
    ocr_confidence: float
    validation_status: StepStatus
    anomalies: list[str]
    low_confidence_fields: list[str]  # BRD FR-D2: fields <85% confidence


class RiskScore(TypedDict, total=False):
    composite_score: float
    risk_band: RiskLevel
    score_components: dict[str, float]
    routing_lane: RoutingLane


class STPEvaluation(TypedDict, total=False):
    decision: Literal["AUTO_APPROVED", "REQUIRES_REVIEW", "INELIGIBLE"]
    rules_passed: list[str]
    rules_failed: list[str]
    rule_count: int
    pass_count: int
    fail_count: int
    evaluation_id: str


class OnboardingState(TypedDict, total=False):
    # ── Session metadata ──────────────────────────────────────────────────────
    session_id: str
    application_id: str
    journey_type: JourneyType
    client_type: ClientType
    created_at: str
    updated_at: str
    temporal_workflow_id: str

    # ── Conversation ──────────────────────────────────────────────────────────
    messages: list[dict]
    current_step: str
    step_status: StepStatus
    completed_steps: list[str]
    failed_steps: list[str]
    agent_notes: list[str]

    # ── Client data ───────────────────────────────────────────────────────────
    client_profile: ClientProfile
    corporate_profile: CorporateProfile
    documents: list[DocumentInfo]

    # ── Compliance / screening results ────────────────────────────────────────
    kyc_result: KYCResult
    aml_result: AMLResult
    fatca_crs_result: FATCACRSResult
    sow_result: dict
    risk_score: RiskScore
    triage_result: dict
    stp_evaluation: STPEvaluation
    context_pack: ContextPack

    # ── Routing ───────────────────────────────────────────────────────────────
    routing_lane: RoutingLane
    stp_eligible: bool

    # ── Human review ─────────────────────────────────────────────────────────
    human_review_required: bool
    human_review_reason: str
    human_decision: Optional[str]
    hitl_flag_count: int
    reviewer_id: str
    mlro_notified: bool

    # ── LLM outputs (BRD FR-A1 — 8 output types) ─────────────────────────────
    llm_case_summary: str
    llm_missing_info: list[str]
    llm_kyc_inconsistencies: list[str]
    llm_sow_assessment: str
    llm_adverse_media_assessment: str
    llm_rfi_draft: str
    llm_compliance_review_summary: str
    llm_next_best_action: str

    # ── Post-decision ─────────────────────────────────────────────────────────
    notifications_sent: list[str]
    downstream_posted: bool
    account_number: str
    client_master_id: str
    audit_trail: list[dict]

    # ── Internal graph control ────────────────────────────────────────────────
    _supervisor_count: int
    _initial_turn_done: bool
    error: Optional[str]
