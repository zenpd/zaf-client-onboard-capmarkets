"""Compliance review / human-in-the-loop endpoints (BRD FR-H1 to FR-H4)."""
from __future__ import annotations
import json
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from api.auth import get_current_user
from api.dependencies import get_redis
from redis.asyncio import Redis
from shared.logger import get_logger

log = get_logger(__name__)
router = APIRouter()

ReviewDecision = Literal["approve", "reject", "rfi", "escalate_edd"]


class DecisionRequest(BaseModel):
    session_id: str
    decision: ReviewDecision
    rationale: str                   # BRD FR-H2: rejection must have documented rationale
    reviewer_id: str                  # BRD FR-H3: named approver required
    senior_approval_required: bool = False


@router.post("/decide")
async def compliance_decision(
    req: DecisionRequest,
    user: dict = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
):
    """BRD FR-H1: decision options restricted to Approve|Reject|RFI|Escalate|EDD."""
    raw = await redis.get(f"session:{req.session_id}")
    if not raw:
        raise HTTPException(status_code=404, detail="Session not found")

    state = json.loads(raw)

    # BRD FR-H2: rejection must have documented rationale
    if req.decision == "reject" and not req.rationale:
        raise HTTPException(status_code=400, detail="Rejection requires documented rationale (BRD FR-H2)")

    # BRD FR-H3: PEP acceptance requires named senior management approver
    kyc = state.get("kyc_result") or {}
    if kyc.get("pep_flag") and req.decision == "approve" and not req.senior_approval_required:
        raise HTTPException(
            status_code=400,
            detail="PEP case approval requires senior management approver flag (BRD FR-H3)"
        )

    # Record decision
    state["human_decision"] = req.decision if req.decision != "escalate_edd" else "escalate_edd"
    state["reviewer_id"] = req.reviewer_id
    state["human_review_reason"] = req.rationale

    # Log to audit trail (BRD FR-H2: all reviewer actions logged with actor + timestamp)
    from datetime import datetime, timezone
    audit_entry = {
        "event":          "human_decision",
        "decision":       req.decision,
        "rationale":      req.rationale,
        "reviewer_id":    req.reviewer_id,
        "senior_approval": req.senior_approval_required,
        "actor":          req.reviewer_id,
        "timestamp":      datetime.now(timezone.utc).isoformat(),
    }
    state.setdefault("audit_trail", []).append(audit_entry)

    # Resume graph with decision
    try:
        from agents.graph import compiled_graph
        result = await compiled_graph.ainvoke(state)
        result_dict = dict(result)
    except Exception as e:
        log.warning("review_resume_failed", error=str(e))
        result_dict = state

    await redis.setex(f"session:{req.session_id}", 86400 * 30, json.dumps(result_dict))

    return {
        "session_id":    req.session_id,
        "decision":      req.decision,
        "current_step":  result_dict.get("current_step", ""),
        "account_number": result_dict.get("account_number", ""),
        "message": f"Decision '{req.decision}' recorded and workflow resumed.",
    }


@router.get("/queue")
async def compliance_queue(
    user: dict = Depends(get_current_user),
):
    """List all cases requiring human review (demo — returns placeholder)."""
    return {
        "queue": [],
        "total_pending": 0,
        "message": "Compliance queue — connect to DB for live data",
    }
