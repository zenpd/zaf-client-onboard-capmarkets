"""Temporal Workflow: ClientOnboardingWorkflow

Durable orchestration of the AI-powered capital markets onboarding process.

Architecture:
  - @workflow.run        → Runs the lifecycle; starts initial turn, waits until done
  - @workflow.update     → process_message() — synchronous request/response per chat turn
  - @workflow.signal     → human_decision_signal() — async review approval/rejection
  - @workflow.query      → get_state(), get_session_summary() — read-only state inspection

Uses the same durable orchestration pattern as merchant_onboard.OnboardingWorkflow.
"""
from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from workflows.activities import (
        run_agent_turn,
        persist_session_to_redis,
        persist_session_to_db,
        send_status_notification,
    )
    from shared.logger import get_logger

log = get_logger(__name__)

_RETRY = RetryPolicy(
    initial_interval=timedelta(seconds=2),
    backoff_coefficient=2.0,
    maximum_attempts=3,
    maximum_interval=timedelta(seconds=30),
)

_TURN_TIMEOUT   = timedelta(minutes=10)
_REVIEW_SLA     = timedelta(days=7)
_SESSION_EXPIRY = timedelta(days=30)

TERMINAL_STEPS = {"onboarding_complete", "completed", "rejected"}


@workflow.defn(name="ClientOnboardingWorkflow")
class ClientOnboardingWorkflow:
    """Durable Temporal workflow for capital markets client onboarding."""

    def __init__(self) -> None:
        self._state: dict[str, Any] = {}
        self._done = False
        self._human_decision: str | None = None

    # ------------------------------------------------------------------
    # Main lifecycle
    # ------------------------------------------------------------------

    @workflow.run
    async def run(self, initial_state: dict[str, Any]) -> dict[str, Any]:
        self._state = initial_state
        wf_id = workflow.info().workflow_id
        self._state["temporal_workflow_id"] = wf_id

        workflow.logger.info(
            "workflow_started wf=%s session=%s journey=%s",
            wf_id, self._state.get("session_id"), self._state.get("journey_type"),
        )

        # Skip if API already ran the first turn synchronously
        if not self._state.get("_initial_turn_done"):
            self._state["_supervisor_count"] = 0
            self._state = await workflow.execute_activity(
                run_agent_turn,
                args=[self._state],
                start_to_close_timeout=_TURN_TIMEOUT,
                retry_policy=_RETRY,
            )
            session_id = self._state.get("session_id", "")
            await workflow.execute_activity(
                persist_session_to_redis,
                args=[session_id, self._state],
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=_RETRY,
            )
            await workflow.execute_activity(
                persist_session_to_db,
                args=[session_id, self._state],
                start_to_close_timeout=timedelta(seconds=15),
                retry_policy=_RETRY,
            )
            if self._state.get("current_step") in TERMINAL_STEPS:
                self._done = True

        try:
            await workflow.wait_condition(lambda: self._done, timeout=_SESSION_EXPIRY)
        except asyncio.TimeoutError:
            workflow.logger.warning("session_expired session=%s", self._state.get("session_id"))
            self._state["error"] = "session_expired"

        workflow.logger.info(
            "workflow_completed session=%s step=%s",
            self._state.get("session_id"), self._state.get("current_step"),
        )
        return self._state

    # ------------------------------------------------------------------
    # Update handler — synchronous request/response per chat turn
    # ------------------------------------------------------------------

    @workflow.update
    async def process_message(self, message: str) -> dict[str, Any]:
        """Process one user message through LangGraph and return new replies."""
        if self._done:
            return {
                "replies": [],
                "step": self._state.get("current_step"),
                "complete": True,
                "awaiting_review": False,
            }

        messages_before = len(
            [m for m in self._state.get("messages", []) if m.get("role") == "assistant"]
        )

        self._state.setdefault("messages", []).append({"role": "user", "content": message})
        self._state["_supervisor_count"] = 0

        # When a document was just uploaded, strip form_automation from completed_steps
        if message.startswith("[DOC_UPLOADED]"):
            self._state["completed_steps"] = [
                s for s in self._state.get("completed_steps", [])
                if s not in ("ocr_data_extraction", "document_collection")
            ]

        self._state = await workflow.execute_activity(
            run_agent_turn,
            args=[self._state],
            start_to_close_timeout=_TURN_TIMEOUT,
            retry_policy=_RETRY,
        )

        # Human review gate
        awaiting_review = (
            self._state.get("human_review_required", False)
            and not self._state.get("human_decision")
        )
        if awaiting_review:
            try:
                await workflow.wait_condition(
                    lambda: self._human_decision is not None,
                    timeout=_REVIEW_SLA,
                )
                if self._human_decision:
                    self._state["human_decision"] = self._human_decision
                    self._human_decision = None
                    self._state["_supervisor_count"] = 0
                    self._state = await workflow.execute_activity(
                        run_agent_turn,
                        args=[self._state],
                        start_to_close_timeout=_TURN_TIMEOUT,
                        retry_policy=_RETRY,
                    )
            except asyncio.TimeoutError:
                self._state["agent_notes"] = self._state.get("agent_notes", []) + [
                    "Review SLA breached — case auto-escalated."
                ]

        _sid = self._state.get("session_id", "")
        await workflow.execute_activity(
            persist_session_to_redis,
            args=[_sid, self._state],
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=_RETRY,
        )
        await workflow.execute_activity(
            persist_session_to_db,
            args=[_sid, self._state],
            start_to_close_timeout=timedelta(seconds=15),
            retry_policy=_RETRY,
        )

        current_step = self._state.get("current_step", "")
        is_complete = current_step in TERMINAL_STEPS
        if is_complete:
            self._done = True

        all_assistant = [m for m in self._state.get("messages", []) if m.get("role") == "assistant"]
        new_replies = all_assistant[messages_before:]

        return {
            "replies": new_replies,
            "step": current_step,
            "complete": is_complete,
            "awaiting_review": awaiting_review and self._human_decision is None,
        }

    # ------------------------------------------------------------------
    # Signal handlers
    # ------------------------------------------------------------------

    @workflow.signal(name="human_decision_signal")
    async def human_decision_signal(self, decision: str) -> None:
        """Signal from compliance officer: approve / reject / more_info."""
        workflow.logger.info("human_decision_received decision=%s", decision)
        self._human_decision = decision

    @workflow.signal(name="session_complete")
    async def session_complete_signal(self) -> None:
        """Signal from API when LangGraph fallback path completes the session."""
        workflow.logger.info("session_complete_signal session=%s", self._state.get("session_id"))
        self._done = True

    # ------------------------------------------------------------------
    # Query handlers
    # ------------------------------------------------------------------

    @workflow.query
    def get_state(self) -> dict[str, Any]:
        """Return full current state snapshot."""
        return self._state

    @workflow.query
    def get_session_summary(self) -> dict[str, Any]:
        """Lightweight summary for dashboards and session lists."""
        s = self._state
        p = s.get("client_profile") or {}
        r = s.get("risk_score") or {}
        hd = s.get("human_decision")
        if s.get("human_review_required") and not hd:
            status = "review"
        elif hd == "approve":
            status = "approved"
        elif hd == "reject":
            status = "rejected"
        elif s.get("current_step") in TERMINAL_STEPS:
            status = "complete"
        else:
            status = "active"
        return {
            "session_id":      s.get("session_id"),
            "application_id":  s.get("application_id"),
            "journey_type":    s.get("journey_type", "individual_hnw"),
            "status":          status,
            "current_step":    s.get("current_step"),
            "completed_steps": s.get("completed_steps", []),
            "client_name":     p.get("full_name") or p.get("client_name") or "Unknown",
            "risk_band":       r.get("risk_band"),
            "routing_lane":    s.get("routing_lane"),
            "client_type":     s.get("client_type"),
            "created_at":      s.get("created_at"),
        }
