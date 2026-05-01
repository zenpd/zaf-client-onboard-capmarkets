"""Document Collection Agent — BRD Phase 2: checklist generation (FR-R1)."""
from __future__ import annotations
from agents.state import OnboardingState
from shared.logger import get_logger

log = get_logger("agent.document_collection")

_DOCUMENT_CHECKLISTS = {
    "retail": [
        {"doc_type": "passport", "label": "Passport or National ID", "required": True},
        {"doc_type": "proof_of_address", "label": "Proof of Address (< 3 months)", "required": True},
        {"doc_type": "source_of_wealth", "label": "Source of Wealth Declaration", "required": True},
        {"doc_type": "fatca_form", "label": "FATCA/CRS Self-Certification Form", "required": True},
    ],
    "hnw": [
        {"doc_type": "passport", "label": "Passport or National ID", "required": True},
        {"doc_type": "proof_of_address", "label": "Proof of Address (< 3 months)", "required": True},
        {"doc_type": "source_of_wealth", "label": "Source of Wealth Evidence Pack", "required": True},
        {"doc_type": "bank_reference", "label": "Bank Reference Letter", "required": True},
        {"doc_type": "investment_portfolio", "label": "Investment Portfolio Summary", "required": False},
        {"doc_type": "fatca_form", "label": "FATCA/CRS Self-Certification Form", "required": True},
    ],
    "uhnw": [
        {"doc_type": "passport", "label": "Passport", "required": True},
        {"doc_type": "proof_of_address", "label": "Proof of Address", "required": True},
        {"doc_type": "source_of_wealth", "label": "Source of Wealth Evidence (detailed)", "required": True},
        {"doc_type": "bank_reference", "label": "Bank Reference Letter", "required": True},
        {"doc_type": "professional_reference", "label": "Professional Reference", "required": True},
        {"doc_type": "investment_portfolio", "label": "Current Portfolio / Net Worth Statement", "required": True},
        {"doc_type": "fatca_form", "label": "FATCA/CRS Self-Certification", "required": True},
    ],
    "corporate_simple": [
        {"doc_type": "certificate_of_incorporation", "label": "Certificate of Incorporation", "required": True},
        {"doc_type": "articles_of_association", "label": "Articles of Association / Memorandum", "required": True},
        {"doc_type": "register_of_directors", "label": "Register of Directors", "required": True},
        {"doc_type": "register_of_shareholders", "label": "Register of Shareholders / UBOs", "required": True},
        {"doc_type": "audited_financials", "label": "Latest Audited Financial Statements", "required": True},
        {"doc_type": "fatca_form", "label": "FATCA/CRS Entity Self-Certification", "required": True},
        {"doc_type": "ubo_id", "label": "Passport / ID for each UBO ≥ 25%", "required": True},
    ],
    "corporate_complex": [
        {"doc_type": "certificate_of_incorporation", "label": "Certificate of Incorporation", "required": True},
        {"doc_type": "articles_of_association", "label": "Articles of Association", "required": True},
        {"doc_type": "register_of_directors", "label": "Register of Directors", "required": True},
        {"doc_type": "register_of_shareholders", "label": "Register of Shareholders", "required": True},
        {"doc_type": "ownership_structure", "label": "Full Ownership Structure Chart", "required": True},
        {"doc_type": "audited_financials", "label": "Latest 2 Years Audited Financials", "required": True},
        {"doc_type": "fatca_form", "label": "FATCA/CRS Entity Self-Certification", "required": True},
        {"doc_type": "ubo_id", "label": "ID for each UBO + Directors", "required": True},
        {"doc_type": "regulatory_license", "label": "Regulatory Licence (if applicable)", "required": False},
    ],
    "trust": [
        {"doc_type": "trust_deed", "label": "Trust Deed (certified copy)", "required": True},
        {"doc_type": "trustee_id", "label": "ID for all Trustees", "required": True},
        {"doc_type": "beneficiary_id", "label": "ID for Beneficiaries ≥ 25%", "required": True},
        {"doc_type": "settlor_id", "label": "ID for Settlor", "required": True},
        {"doc_type": "source_of_funds", "label": "Source of Trust Funds", "required": True},
        {"doc_type": "fatca_form", "label": "Trust FATCA/CRS Certification", "required": True},
    ],
}


def document_collection_node(state: OnboardingState) -> OnboardingState:
    log.info("agent.document_collection.start")
    client_type = state.get("client_type", "retail")
    journey = state.get("journey_type", "individual")

    # Select checklist
    checklist = _DOCUMENT_CHECKLISTS.get(client_type,
                _DOCUMENT_CHECKLISTS.get("retail", []))

    # Check what's already uploaded
    uploaded_docs = {d.get("doc_type", "") for d in (state.get("documents") or [])}
    required = [d for d in checklist if d["required"]]
    missing_required = [d for d in required if d["doc_type"] not in uploaded_docs]

    state["_document_checklist"] = checklist  # type: ignore[assignment]

    if missing_required:
        items = "\n".join(f"  • {d['label']}" for d in missing_required)
        msg = (
            "📂 **Document Checklist**\n\n"
            f"**Client Profile:** {client_type.replace('_', ' ').upper()}\n\n"
            "Please upload the following required documents:\n"
            f"{items}\n\n"
            "💡 **Tip:** All documents must be clear, legible, and not expired. "
            "Documents older than 3 months may not be accepted for proof of address."
        )
        state.setdefault("messages", []).append({
            "role": "assistant", "agent": "document_collection", "content": msg,
        })
        # BRD FR-R1: no partial checklists — do not advance
        state.setdefault("completed_steps", []).append("document_collection")
        state["current_step"] = "document_collection"
        return state

    # All required docs present
    msg = (
        "✅ **All Required Documents Received**\n\n"
        f"Your document checklist for {client_type.replace('_', ' ')} onboarding is complete. "
        "Proceeding to OCR extraction and validation…"
    )
    state.setdefault("messages", []).append({
        "role": "assistant", "agent": "document_collection", "content": msg,
    })
    state.setdefault("completed_steps", []).append("document_collection")
    state["current_step"] = "document_collection"
    return state
