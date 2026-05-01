"""OCR extraction tool — extracts fields from uploaded documents (BRD FR-D2)."""
from __future__ import annotations
import random
from shared.helpers import generate_id


def extract_document_fields(
    file_name: str,
    file_content: bytes | None = None,
    doc_type: str = "passport",
) -> dict:
    """
    Simulates OCR extraction. In production this calls Azure Form Recognizer / Tesseract.
    BRD FR-D2: fields below 85% confidence flagged for human confirmation.
    """
    base_confidence = 0.92
    fields = {}
    low_confidence_fields = []

    if doc_type in ("passport", "national_id", "drivers_license"):
        fields = {
            "full_name": {"value": "Extracted Name", "confidence": 0.96},
            "dob": {"value": "1980-01-01", "confidence": 0.94},
            "id_number": {"value": generate_id("DOC"), "confidence": 0.90},
            "nationality": {"value": "GB", "confidence": 0.92},
            "expiry_date": {"value": "2030-12-31", "confidence": 0.88},
        }
    elif doc_type == "proof_of_address":
        fields = {
            "full_name": {"value": "Extracted Name", "confidence": 0.91},
            "address_line1": {"value": "123 High St", "confidence": 0.87},
            "city": {"value": "London", "confidence": 0.93},
            "postcode": {"value": "EC1A 1BB", "confidence": 0.89},
            "issue_date": {"value": "2025-01-15", "confidence": 0.80},
        }
    elif doc_type in ("bank_reference", "source_of_wealth"):
        fields = {
            "institution_name": {"value": "Example Bank", "confidence": 0.88},
            "amount": {"value": "500000", "confidence": 0.85},
            "currency": {"value": "USD", "confidence": 0.97},
            "date": {"value": "2025-06-01", "confidence": 0.90},
        }
    else:
        fields = {
            "content": {"value": "Document content extracted", "confidence": 0.82},
        }

    # BRD FR-D2: flag fields below 85% confidence
    low_confidence_fields = [k for k, v in fields.items() if v.get("confidence", 1.0) < 0.85]
    overall_confidence = sum(v.get("confidence", 0.9) for v in fields.values()) / max(len(fields), 1)

    return {
        "doc_id": generate_id("OCR"),
        "file_name": file_name,
        "doc_type": doc_type,
        "extracted_fields": {k: v["value"] for k, v in fields.items()},
        "field_confidences": {k: v["confidence"] for k, v in fields.items()},
        "ocr_confidence": round(overall_confidence, 4),
        "low_confidence_fields": low_confidence_fields,
        "anomalies": ["low_confidence_field"] if low_confidence_fields else [],
        "requires_human_review": overall_confidence < 0.85 or bool(low_confidence_fields),
    }
