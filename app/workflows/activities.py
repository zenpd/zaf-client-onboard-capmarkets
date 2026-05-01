"""Temporal activities — capital markets wealth management onboarding.

Activities are the durable, retriable units of work in Temporal.
Each activity is replayed idempotently on failure.
"""
from __future__ import annotations

import json
from typing import Any

from temporalio import activity

from shared.logger import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Core LangGraph turn execution
# ---------------------------------------------------------------------------

@activity.defn(name="run_agent_turn")
async def run_agent_turn(state: dict[str, Any]) -> dict[str, Any]:
    """Run one conversational turn through the LangGraph onboarding graph.

    Input:  current OnboardingState dict (JSON-serialisable)
    Output: updated OnboardingState dict after graph execution
    """
    from agents.graph import compiled_graph

    # Doc-upload sync: when user just uploaded a document, sync from Redis
    # so that the OCR extraction step fires correctly on the next agent turn.
    last_user_msg = next(
        (m["content"] for m in reversed(state.get("messages", [])) if m.get("role") == "user"),
        "",
    )
    if last_user_msg.startswith("[DOC_UPLOADED]"):
        try:
            from api.dependencies import get_redis_direct
            _redis = await get_redis_direct()
            try:
                _raw = await _redis.get(f"session:{state.get('session_id', '')}")
                if _raw:
                    _rs = json.loads(_raw)
                    state["documents"] = _rs.get("documents", state.get("documents", []))
                    state["completed_steps"] = [
                        s for s in _rs.get("completed_steps", state.get("completed_steps", []))
                        if s not in ("ocr_data_extraction", "document_collection")
                    ]
                    activity.logger.info(
                        "doc_upload_redis_sync session=%s docs=%d",
                        state.get("session_id"), len(state["documents"]),
                    )
            finally:
                await _redis.aclose()
        except Exception as _e:
            activity.logger.warning("doc_upload_redis_sync_failed error=%s", str(_e))

    activity.logger.info(
        "agent_turn_start session=%s journey=%s step=%s",
        state.get("session_id"), state.get("journey_type"), state.get("current_step"),
    )

    result = await compiled_graph.ainvoke(state)
    out = dict(result)

    activity.logger.info(
        "agent_turn_complete session=%s step=%s",
        out.get("session_id"), out.get("current_step"),
    )
    return out


# ---------------------------------------------------------------------------
# Session persistence — Redis (fast reads) and DB (durable audit trail)
# ---------------------------------------------------------------------------

@activity.defn(name="persist_session_to_redis")
async def persist_session_to_redis(session_id: str, state: dict[str, Any]) -> None:
    """Write the latest state snapshot to Redis (TTL = 30 days)."""
    from api.dependencies import get_redis_direct
    redis = await get_redis_direct()
    try:
        await redis.setex(f"session:{session_id}", 86400 * 30, json.dumps(state))
    finally:
        await redis.aclose()


@activity.defn(name="persist_session_to_db")
async def persist_session_to_db(session_id: str, state: dict[str, Any]) -> None:
    """Upsert ClientApplication row into SQLite/PostgreSQL.

    Idempotent — safe to call multiple times; uses SELECT + UPDATE or INSERT.
    """
    try:
        await _upsert_application(session_id, state)
        activity.logger.info("db_persisted session=%s", session_id)
    except Exception as exc:
        activity.logger.warning("db_persist_failed session=%s error=%s", session_id, str(exc))


# ---------------------------------------------------------------------------
# Notification activity
# ---------------------------------------------------------------------------

@activity.defn(name="send_status_notification")
async def send_status_notification(
    session_id: str,
    event: str,
    customer_email: str | None = None,
) -> None:
    """Send an email/SMS status notification. Non-blocking — failure is logged, not raised."""
    log.info("notification_sent", session_id=session_id, event=event, email=customer_email)
    # In production: call SMTP / SMS gateway from shared/config settings


async def _upsert_application(session_id: str, state: dict[str, Any]) -> None:
    from db.base import AsyncSessionLocal
    from db.models import ClientApplication
    from sqlalchemy import select
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ClientApplication).where(ClientApplication.id == session_id)
        )
        app = result.scalar_one_or_none()
        if app is None:
            app = ClientApplication(
                id=session_id,
                application_id=state.get("application_id", session_id),
                journey_type=state.get("journey_type", "individual"),
                client_type=state.get("client_type", "retail"),
            )
            session.add(app)
        app.status = state.get("step_status", "pending")
        app.current_step = state.get("current_step", "triage")
        app.risk_band = (state.get("risk_score") or {}).get("risk_band", "")
        app.routing = state.get("routing_lane", "")
        app.human_review_required = state.get("human_review_required", False)
        app.human_decision = state.get("human_decision")
        app.completed_steps = state.get("completed_steps", [])
        app.state_snapshot = {k: v for k, v in state.items() if not k.startswith("_")}
        await session.commit()
