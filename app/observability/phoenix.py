"""Arize Phoenix — connection info and health check.

Phoenix runs in Azure Container Apps (shared with merchant_onboard):
  Web UI:  https://zaf-phoenix.bravesky-d9f9eeb7.eastus2.azurecontainerapps.io/projects
  OTLP:    https://zaf-phoenix.bravesky-d9f9eeb7.eastus2.azurecontainerapps.io/v1/traces

Tracing is wired up in observability/tracing.py via init_tracing().
"""
from shared.config import get_settings


def get_phoenix_url() -> str:
    """Return the Phoenix Web UI URL for logging / display."""
    s = get_settings()
    scheme = "https" if s.phoenix_port == 443 else "http"
    return f"{scheme}://{s.phoenix_host}:{s.phoenix_port}"


def get_otlp_endpoint() -> str:
    """Return the OTLP HTTP endpoint used by the OTel exporter."""
    s = get_settings()
    scheme = "https" if s.phoenix_port == 443 else "http"
    return f"{scheme}://{s.phoenix_host}/v1/traces"
