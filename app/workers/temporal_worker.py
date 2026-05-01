"""Temporal Worker — Capital Markets Client Onboarding

Runs the ClientOnboardingWorkflow and all associated activities.

Start alongside the FastAPI server:

    python -m workers.temporal_worker

The worker connects to the Temporal server, registers the workflow and all
activities, then polls the task queue. Run multiple worker processes for
horizontal scaling.

ACA deployment:
  The worker container app uses the same Docker image as the backend but
  overrides CMD to: python -m workers.temporal_worker
  It targets the shared Temporal cluster at:
    temporal-ui.bravesky-d9f9eeb7.eastus2.azurecontainerapps.io (UI)
    TEMPORAL_HOST env var points to the gRPC backend (port 443, TLS)
"""
from __future__ import annotations

import asyncio
import signal
import sys
from datetime import timedelta

from temporalio.api.workflowservice.v1 import RegisterNamespaceRequest
from temporalio.client import Client
from temporalio.service import RPCError, RPCStatusCode
from temporalio.worker import Worker

from observability.tracing import init_tracing
from shared.config import get_settings
from shared.logger import get_logger, setup_logging
from workflows.activities import (
    run_agent_turn,
    persist_session_to_redis,
    persist_session_to_db,
    send_status_notification,
)
from workflows.client_onboarding_workflow import ClientOnboardingWorkflow

log = get_logger(__name__)


async def _ensure_namespace(host: str, namespace: str, *, tls: bool = False) -> None:
    """Create the Temporal namespace if it does not exist.

    Strategy:
      1. Connect to the always-present 'default' namespace.
      2. Try to register the target namespace via workflow_service.
      3. ALREADY_EXISTS → fine, continue.
      4. Any other error → log warning but don't block worker startup.

    Safe to call on every startup, including after Temporal scales from zero.
    """
    try:
        admin = await Client.connect(host, namespace="default", tls=tls)
        await admin.service_client.workflow_service.register_namespace(
            RegisterNamespaceRequest(
                namespace=namespace,
                workflow_execution_retention_period=timedelta(days=30),
            )
        )
        log.info("namespace_created", namespace=namespace)
    except RPCError as exc:
        if exc.status == RPCStatusCode.ALREADY_EXISTS:
            log.info("namespace_already_exists", namespace=namespace)
        else:
            log.warning("namespace_create_failed", namespace=namespace, error=str(exc))
    except Exception as exc:
        log.warning("namespace_create_failed", namespace=namespace, error=str(exc))


async def run_worker() -> None:
    settings = get_settings()

    log.info(
        "worker_connecting",
        temporal_host=settings.temporal_host,
        namespace=settings.temporal_namespace,
        task_queue=settings.temporal_task_queue_agents,
    )

    # ACA serves gRPC over TLS on port 443.
    # When TEMPORAL_HOST contains :443 we enable TLS; otherwise keep plain gRPC.
    use_tls = settings.temporal_host.endswith(":443")

    # Auto-create namespace on every startup — idempotent, safe after scale-from-zero
    await _ensure_namespace(settings.temporal_host, settings.temporal_namespace, tls=use_tls)

    client = await Client.connect(
        settings.temporal_host,
        namespace=settings.temporal_namespace,
        tls=use_tls,
    )

    # Register workflow + all activities on the agents task queue
    async with Worker(
        client,
        task_queue=settings.temporal_task_queue_agents,
        workflows=[ClientOnboardingWorkflow],
        activities=[
            run_agent_turn,
            persist_session_to_redis,
            persist_session_to_db,
            send_status_notification,
        ],
        # Limit concurrent LangGraph turns to avoid hitting LLM rate limits
        max_concurrent_activities=10,
        max_concurrent_workflow_tasks=50,
    ) as worker:
        log.info(
            "worker_started",
            task_queue=settings.temporal_task_queue_agents,
        )

        # Graceful shutdown on SIGINT / SIGTERM
        loop = asyncio.get_running_loop()
        stop_event = asyncio.Event()

        def _stop(*_: object) -> None:
            log.info("worker_shutdown_signal_received")
            stop_event.set()

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, _stop)

        await stop_event.wait()
        log.info("worker_stopped")


def main() -> None:
    setup_logging()
    init_tracing()
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
