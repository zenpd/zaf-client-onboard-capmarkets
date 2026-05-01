"""OpenTelemetry + Arize Phoenix tracing initialisation.

Deployed Phoenix (Azure Container Apps):
- Web UI:    https://zaf-phoenix.bravesky-d9f9eeb7.eastus2.azurecontainerapps.io
- OTLP HTTP: https://zaf-phoenix.bravesky-d9f9eeb7.eastus2.azurecontainerapps.io/v1/traces

We use the HTTP exporter + openinference instrumentors so that
LangChain/LangGraph LLM calls appear as proper traces in the
"capmarkets-onboarding" Phoenix project.
"""
import logging
import os
from shared.config import get_settings

log = logging.getLogger("tracing")


def init_tracing() -> None:
    """Configure OTel TracerProvider and instrument FastAPI + LangChain + OpenAI.

    All imports are lazy so missing packages never block app startup.
    """
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        settings = get_settings()

        # Resolve Phoenix collector endpoint.
        # PHOENIX_COLLECTOR_ENDPOINT overrides host:port construction (used in ACA).
        collector_env = os.getenv(
            "PHOENIX_COLLECTOR_ENDPOINT",
            "https://zaf-phoenix.bravesky-d9f9eeb7.eastus2.azurecontainerapps.io",
        ).rstrip("/")
        otlp_endpoint = f"{collector_env}/v1/traces"

        # Resolve project name and API key.
        project_name = os.getenv("PHOENIX_PROJECT_NAME", "capmarkets-onboarding")
        api_key = os.getenv("PHOENIX_API_KEY", settings.arize_phoenix_api_key)

        resource = Resource.create({
            "service.name": "capmarkets-onboard",
            "openinference.project.name": project_name,
        })
        provider = TracerProvider(resource=resource)

        headers = {}
        if api_key:
            headers["authorization"] = f"Bearer {api_key}"

        exporter = OTLPSpanExporter(
            endpoint=otlp_endpoint,
            headers=headers,
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

        log.info("OTel TracerProvider initialised → %s", otlp_endpoint)

    except Exception as e:
        log.warning("OTel init failed (non-fatal): %s", e)
        return

    # ── FastAPI auto-instrumentation ────────────────────────────────────────────────────────────────
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor().instrument()
        log.info("FastAPI instrumented")
    except Exception as e:
        log.warning("FastAPI instrumentation failed: %s", e)

    # ── LangChain / LangGraph auto-instrumentation ──────────────────────────────────────────
    # Produces LLM call spans, agent traces, tool calls in Phoenix
    try:
        from openinference.instrumentation.langchain import LangChainInstrumentor
        LangChainInstrumentor().instrument()
        log.info("LangChain instrumented (openinference)")
    except ImportError:
        log.warning(
            "openinference-instrumentation-langchain not installed — "
            "run: pip install openinference-instrumentation-langchain"
        )
    except Exception as e:
        log.warning("LangChain instrumentation failed: %s", e)

    # ── OpenAI auto-instrumentation ────────────────────────────────────────────────────────────────
    try:
        from openinference.instrumentation.openai import OpenAIInstrumentor
        OpenAIInstrumentor().instrument()
        log.info("OpenAI instrumented (openinference)")
    except ImportError:
        log.warning(
            "openinference-instrumentation-openai not installed — "
            "run: pip install openinference-instrumentation-openai"
        )
    except Exception as e:
        log.warning("OpenAI instrumentation failed: %s", e)


def get_tracer(name: str):
    try:
        from opentelemetry import trace
        return trace.get_tracer(name)
    except Exception:
        return logging.getLogger(name)
