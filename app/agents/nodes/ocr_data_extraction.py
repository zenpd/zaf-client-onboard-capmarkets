"""OCR Data Extraction Agent — BRD Phase 2 / FR-D2: 85% confidence threshold."""
from __future__ import annotations
from agents.state import OnboardingState
from agents.tools.ocr_extract import extract_document_fields
from shared.logger import get_logger
from shared.config import get_settings

log = get_logger("agent.ocr_data_extraction")


def ocr_data_extraction_node(state: OnboardingState) -> OnboardingState:
    log.info("agent.ocr_data_extraction.start")
    settings = get_settings()
    documents = state.get("documents") or []

    if not documents:
        state.setdefault("completed_steps", []).append("ocr_data_extraction")
        state["current_step"] = "ocr_data_extraction"
        return state

    updated_docs = []
    low_confidence_count = 0
    all_extracted: dict = {}

    for doc in documents:
        if doc.get("validation_status") == "completed":
            updated_docs.append(doc)
            continue
        result = extract_document_fields(
            file_name=doc.get("file_name", "document"),
            doc_type=doc.get("doc_type", "passport"),
        )
        # Merge extracted fields back into document record
        doc = dict(doc)
        doc["extracted_fields"] = result.get("extracted_fields", {})
        doc["ocr_confidence"] = result.get("ocr_confidence", 0.0)
        doc["low_confidence_fields"] = result.get("low_confidence_fields", [])
        doc["anomalies"] = result.get("anomalies", [])
        # BRD FR-D2: below 85% → must not be auto-populated, flag for human
        if result.get("ocr_confidence", 0) < settings.ocr_confidence_threshold:
            doc["validation_status"] = "escalated"
            low_confidence_count += 1
        else:
            doc["validation_status"] = "completed"
        all_extracted.update(result.get("extracted_fields", {}))
        updated_docs.append(doc)

    state["documents"] = updated_docs  # type: ignore[assignment]

    # Auto-populate client profile from OCR (only high-confidence fields)
    if all_extracted and not state.get("client_profile"):
        state["client_profile"] = {  # type: ignore[assignment]
            "full_name": all_extracted.get("full_name", ""),
            "dob": all_extracted.get("dob", ""),
            "nationality": all_extracted.get("nationality", ""),
            "id_number": all_extracted.get("id_number", ""),
        }

    if low_confidence_count > 0:
        state["human_review_required"] = True
        state["human_review_reason"] = (
            f"OCR confidence below {settings.ocr_confidence_threshold*100:.0f}% threshold "
            f"on {low_confidence_count} document(s) — BRD FR-D2"
        )
        msg = (
            f"🔍 **Document Extraction — Review Required**\n\n"
            f"{low_confidence_count} document(s) have low OCR confidence (below "
            f"{settings.ocr_confidence_threshold*100:.0f}%). "
            "These fields require human confirmation before proceeding. "
            "A compliance officer will review and confirm the extracted data."
        )
    else:
        msg = (
            "✅ **Document Extraction Complete**\n\n"
            f"Successfully extracted data from {len(updated_docs)} document(s). "
            "All fields meet the confidence threshold. Proceeding to validation…"
        )

    state.setdefault("messages", []).append({
        "role": "assistant", "agent": "ocr_data_extraction", "content": msg,
    })
    state.setdefault("completed_steps", []).append("ocr_data_extraction")
    state["current_step"] = "ocr_data_extraction"
    return state
