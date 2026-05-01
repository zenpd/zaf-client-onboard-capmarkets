"""Document upload endpoints — with OCR confidence checking (BRD FR-D2)."""
from __future__ import annotations
import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from api.auth import get_current_user
from api.dependencies import get_redis
from agents.tools.ocr_extract import extract_document_fields
from redis.asyncio import Redis
from shared.logger import get_logger

log = get_logger(__name__)
router = APIRouter()

ALLOWED_TYPES = {"pdf", "docx", "doc", "jpg", "jpeg", "png", "tiff"}
MAX_SIZE_MB = 100


@router.post("/upload")
async def upload_document(
    session_id: str = Form(...),
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
):
    # Validate file type
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: .{ext}")

    content = await file.read()
    if len(content) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds {MAX_SIZE_MB}MB limit")

    # OCR extraction
    ocr_result = extract_document_fields(
        file_name=file.filename or "document",
        file_content=content,
        doc_type=doc_type,
    )

    doc_record = {
        "doc_id": str(uuid.uuid4()),
        "doc_type": doc_type,
        "file_name": file.filename,
        "extracted_fields": ocr_result.get("extracted_fields", {}),
        "ocr_confidence": ocr_result.get("ocr_confidence", 0.0),
        "low_confidence_fields": ocr_result.get("low_confidence_fields", []),
        "anomalies": ocr_result.get("anomalies", []),
        "validation_status": (
            "escalated" if ocr_result.get("requires_human_review") else "completed"
        ),
    }

    # Update session state in Redis
    raw = await redis.get(f"session:{session_id}")
    if raw:
        state = json.loads(raw)
        docs = state.get("documents") or []
        docs.append(doc_record)
        state["documents"] = docs
        # Reset doc_collection step so agent re-evaluates
        completed = [s for s in state.get("completed_steps", [])
                     if s not in ("document_collection", "ocr_data_extraction")]
        state["completed_steps"] = completed
        await redis.setex(f"session:{session_id}", 86400 * 30, json.dumps(state))

    return {
        "doc_id":            doc_record["doc_id"],
        "file_name":         file.filename,
        "doc_type":          doc_type,
        "ocr_confidence":    doc_record["ocr_confidence"],
        "requires_review":   ocr_result.get("requires_human_review", False),
        "low_confidence_fields": doc_record["low_confidence_fields"],
        "status":            doc_record["validation_status"],
    }


@router.get("/session/{session_id}")
async def list_documents(
    session_id: str,
    user: dict = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
):
    raw = await redis.get(f"session:{session_id}")
    if not raw:
        raise HTTPException(status_code=404, detail="Session not found")
    state = json.loads(raw)
    return {"documents": state.get("documents", [])}
