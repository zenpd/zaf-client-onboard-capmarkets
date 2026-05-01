"""Client onboarding journey endpoints — backed by Temporal for durable execution."""
from __future__ import annotations
import uuid
import json
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from agents.state import OnboardingState, JourneyType
from api.auth import get_current_user
from api.dependencies import get_redis
from redis.asyncio import Redis
from shared.config import get_settings
from shared.logger import get_logger

log = get_logger(__name__)
router = APIRouter()
settings = get_settings()


class StartRequest(BaseModel):
    journey_type: JourneyType
    initial_message: str = "Hello, I'd like to open a wealth management account."


class ResumeRequest(BaseModel):
    session_id: str
    message: str
    form_data: Optional[dict] = None


async def _get_temporal_client():
    try:
        from temporalio.client import Client
        return await Client.connect(settings.temporal_host, namespace=settings.temporal_namespace)
    except Exception as e:
        log.warning("temporal_unavailable", error=str(e))
        return None


@router.post("/start")
async def start_onboarding(
    req: StartRequest,
    user: dict = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
):
    session_id     = str(uuid.uuid4())
    application_id = f"WM-{uuid.uuid4().hex[:8].upper()}"
    workflow_id    = f"capmarkets-onboarding-{session_id}"

    initial_state: OnboardingState = {
        "session_id":            session_id,
        "application_id":        application_id,
        "journey_type":          req.journey_type,
        "messages":              [{"role": "user", "content": req.initial_message}],
        "created_at":            datetime.now(timezone.utc).isoformat(),
        "completed_steps":       [],
        "failed_steps":          [],
        "notifications_sent":    [],
        "agent_notes":           [],
        "human_review_required": False,
        "_supervisor_count":     0,
        "temporal_workflow_id":  workflow_id,
        "audit_trail":           [],
    }

    # Run the first LangGraph turn synchronously so we return replies immediately
    log.info("running_initial_turn", session_id=session_id)
    try:
        from agents.graph import compiled_graph
        result = await compiled_graph.ainvoke(initial_state)
        result_dict = dict(result)
    except Exception as e:
        log.warning("graph_invocation_failed", error=str(e), session_id=session_id)
        if settings.app_env == "development":
            result_dict = dict(initial_state)
            result_dict["messages"].append({
                "role": "assistant",
                "content": (
                    f"Welcome to ZenLabs Wealth Management onboarding. "
                    f"I'm ready to begin your {req.journey_type} account opening. "
                    "Please share your details to get started."
                ),
            })
        else:
            raise HTTPException(status_code=500, detail=str(e))

    result_dict["_initial_turn_done"] = True
    result_dict["temporal_workflow_id"] = workflow_id

    # Persist to Redis immediately
    await redis.setex(f"session:{session_id}", 86400 * 30, json.dumps(result_dict))

    # Persist to DB — non-blocking, best-effort
    try:
        from workflows.activities import _upsert_application
        await _upsert_application(session_id, result_dict)
    except Exception as _dbe:
        log.warning("db_persist_failed_on_start", session_id=session_id, error=str(_dbe))

    new_replies = [m for m in result_dict.get("messages", []) if m.get("role") == "assistant"]

    # Hand off to Temporal for durable subsequent turns (fire-and-forget)
    client = await _get_temporal_client()
    if client:
        try:
            from workflows.client_onboarding_workflow import ClientOnboardingWorkflow
            await client.start_workflow(
                ClientOnboardingWorkflow.run,
                result_dict,
                id=workflow_id,
                task_queue=settings.temporal_task_queue_agents,
            )
            log.info("workflow_started", workflow_id=workflow_id, session_id=session_id)
        except Exception as e:
            log.warning("workflow_start_failed", error=str(e))
    else:
        log.info("temporal_unavailable_fallback", session_id=session_id)

    return {
        "session_id":            session_id,
        "application_id":        application_id,
        "replies":               new_replies,
        "step":                  result_dict.get("current_step"),
        "routing_lane":          result_dict.get("routing_lane", "standard"),
        "completed_steps":       result_dict.get("completed_steps", []),
        "awaiting_review":       result_dict.get("human_review_required", False),
        "temporal_workflow_id":  workflow_id,
    }


@router.post("/resume")
async def resume_onboarding(
    req: ResumeRequest,
    user: dict = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
):
    try:
        raw = await redis.get(f"session:{req.session_id}")
    except Exception as e:
        log.error("redis_unavailable", error=str(e))
        raise HTTPException(503, detail="Storage unavailable — ensure Redis is running.")
    if not raw:
        raise HTTPException(404, "Session not found")

    state: dict = json.loads(raw)
    workflow_id = state.get("temporal_workflow_id")
    client = await _get_temporal_client() if workflow_id else None

    # ── Try Temporal update first (durable, ordered) ─────────────────────────
    if client and workflow_id:
        try:
            from workflows.client_onboarding_workflow import ClientOnboardingWorkflow
            handle = client.get_workflow_handle_for(ClientOnboardingWorkflow.run, workflow_id=workflow_id)
            result = await handle.execute_update(
                ClientOnboardingWorkflow.process_message,
                req.message,
                rpc_timeout=timedelta(seconds=5),
            )
            # Refresh Redis snapshot and merge form_data
            try:
                latest = await handle.query(ClientOnboardingWorkflow.get_state)
                if req.form_data:
                    existing_form = latest.get("form_data") or {}
                    existing_form.update({k: v for k, v in req.form_data.items() if v is not None})
                    latest["form_data"] = existing_form
                await redis.setex(f"session:{req.session_id}", 86400 * 30, json.dumps(latest))
            except Exception:
                pass
            return result
        except Exception as e:
            log.warning("temporal_update_failed", workflow_id=workflow_id, error=str(e))

    # ── Fallback: Redis + direct LangGraph ───────────────────────────────────
    log.info("temporal_fallback_resume", session_id=req.session_id)

    if req.form_data:
        existing_form = state.get("form_data") or {}
        existing_form.update({k: v for k, v in req.form_data.items() if v is not None})
        state["form_data"] = existing_form

    if req.message.startswith("[DOC_UPLOADED]"):
        state["completed_steps"] = [
            s for s in state.get("completed_steps", [])
            if s not in ("ocr_data_extraction", "document_collection")
        ]
        log.info("doc_upload_reset_ocr_step", session_id=req.session_id)

    from agents.graph import compiled_graph
    bot_before = sum(1 for m in state.get("messages", []) if m.get("role") == "assistant")
    state.setdefault("messages", []).append({"role": "user", "content": req.message})
    state["_supervisor_count"] = 0
    try:
        result = await compiled_graph.ainvoke(state)
        result_dict = dict(result)
        await redis.setex(f"session:{req.session_id}", 86400 * 30, json.dumps(result_dict))
        try:
            from workflows.activities import _upsert_application
            await _upsert_application(req.session_id, result_dict)
        except Exception as _dbe:
            log.warning("db_persist_failed_on_resume", session_id=req.session_id, error=str(_dbe))

        all_bot = [m for m in result_dict.get("messages", []) if m.get("role") == "assistant"]
        is_complete = result_dict.get("current_step") in ("onboarding_complete", "completed")

        # Signal Temporal workflow to exit cleanly
        if (is_complete or result_dict.get("human_review_required")) and client and workflow_id:
            try:
                from workflows.client_onboarding_workflow import ClientOnboardingWorkflow
                handle = client.get_workflow_handle_for(ClientOnboardingWorkflow.run, workflow_id=workflow_id)
                if is_complete:
                    await handle.signal(ClientOnboardingWorkflow.session_complete_signal)
                    log.info("temporal_session_complete_signalled", workflow_id=workflow_id)
            except Exception as sig_err:
                log.warning("temporal_signal_failed", error=str(sig_err), workflow_id=workflow_id)

        return {
            "session_id":      req.session_id,
            "replies":         all_bot[bot_before:],
            "step":            result_dict.get("current_step"),
            "routing_lane":    result_dict.get("routing_lane", ""),
            "completed_steps": result_dict.get("completed_steps", []),
            "complete":        is_complete,
            "awaiting_review": result_dict.get("human_review_required", False)
                               and not result_dict.get("human_decision"),
            "account_number":  result_dict.get("account_number", ""),
        }
    except Exception as e:
        log.error("langgraph_invocation_failed", error=str(e), session_id=req.session_id)
        crashed_step = state.get("current_step")
        if crashed_step and crashed_step not in state.get("completed_steps", []):
            state.setdefault("completed_steps", []).append(crashed_step)
        fallback_msg = "I'm having trouble processing that step. Please try again — your session progress is saved."
        state.setdefault("messages", []).append({"role": "assistant", "content": fallback_msg})
        try:
            await redis.setex(f"session:{req.session_id}", 86400 * 30, json.dumps(state))
        except Exception:
            pass
        return {
            "replies": [{"role": "assistant", "content": fallback_msg}],
            "step": crashed_step,
            "complete": False,
            "awaiting_review": state.get("human_review_required", False),
        }


@router.get("/session/{session_id}")
async def get_session(
    session_id: str,
    user: dict = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
):
    raw = await redis.get(f"session:{session_id}")
    if not raw:
        raise HTTPException(status_code=404, detail="Session not found")
    state = json.loads(raw)

    # Also try to get latest state from Temporal workflow if running
    workflow_id = state.get("temporal_workflow_id")
    if workflow_id:
        client = await _get_temporal_client()
        if client:
            try:
                from workflows.client_onboarding_workflow import ClientOnboardingWorkflow
                handle = client.get_workflow_handle_for(ClientOnboardingWorkflow.run, workflow_id=workflow_id)
                state = await handle.query(ClientOnboardingWorkflow.get_state)
            except Exception:
                pass  # use Redis state as fallback

    return {
        "session_id":    session_id,
        "application_id": state.get("application_id", ""),
        "journey_type":  state.get("journey_type", ""),
        "client_type":   state.get("client_type", ""),
        "current_step":  state.get("current_step", ""),
        "routing_lane":  state.get("routing_lane", ""),
        "risk_band":     (state.get("risk_score") or {}).get("risk_band", ""),
        "completed_steps": state.get("completed_steps", []),
        "human_review_required": state.get("human_review_required", False),
        "messages":      state.get("messages", []),
        "account_number": state.get("account_number", ""),
        "audit_trail":   state.get("audit_trail", []),
        "temporal_workflow_id": state.get("temporal_workflow_id", ""),
    }

