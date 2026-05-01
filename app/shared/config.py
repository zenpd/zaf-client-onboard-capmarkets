"""Central configuration — reads from .env via pydantic-settings.

Wealth Management Client Onboarding Platform (Capital Markets).
"""
from __future__ import annotations

from functools import lru_cache
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── App ──────────────────────────────────────────────────────────────────
    app_env: str = "development"
    app_secret_key: str = "change-me"
    log_level: str = "INFO"

    # ── Database / Cache ─────────────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./capmarkets_onboarding.db"
    redis_url: str = "redis://localhost:6379/1"

    # ── Azure OpenAI ─────────────────────────────────────────────────────────
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment: str = "gpt-4.1-mini"
    azure_openai_embedding_deployment: str = "text-embedding-3-small"
    azure_openai_api_version: str = "2025-01-01-preview"

    # ── Azure Key Vault ───────────────────────────────────────────────────────
    azure_keyvault_url: str = "https://zaf-kv-01.vault.azure.net/"
    azure_openai_endpoint_kv_uri: str = ""
    azure_openai_api_key_kv_uri: str = ""
    azure_openai_deployment_kv_uri: str = ""
    database_url_kv_uri: str = ""
    redis_url_kv_uri: str = ""

    # ── Azure / EntraID ───────────────────────────────────────────────────────
    azure_tenant_id: str = ""
    azure_client_id: str = ""
    azure_client_secret: str = ""
    entra_authority: str = "https://login.microsoftonline.com/"
    entra_audience: str = ""

    # ── Arize Phoenix Observability ───────────────────────────────────────────
    phoenix_host: str = "zaf-phoenix.bravesky-d9f9eeb7.eastus2.azurecontainerapps.io"
    phoenix_port: int = 443
    arize_phoenix_api_key: str = ""
    phoenix_admin_email: str = "admin@localhost"
    phoenix_admin_password: str = ""
    phoenix_admin_secret: str = ""

    # KV URIs for Phoenix / Arize
    arize_phoenix_api_key_kv_uri: str = ""
    arize_phoenix_password_kv_uri: str = ""

    # ── Vector DBs ────────────────────────────────────────────────────────────
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""

    # ── Temporal ──────────────────────────────────────────────────────────────
    temporal_host: str = "localhost:7233"
    temporal_namespace: str = "capmarkets-onboarding"
    temporal_task_queue_agents: str = "capmarkets-onboard-agents"
    temporal_task_queue_ingestion: str = "capmarkets-onboard-ingestion"

    # ── Screening vendors (KYC/AML) ───────────────────────────────────────────
    kyc_provider_url: str = ""
    kyc_api_key: str = ""
    aml_provider_url: str = ""
    aml_api_key: str = ""
    sanctions_api_url: str = ""
    sanctions_api_key: str = ""

    # ── Wealth Management Platform integration ────────────────────────────────
    wm_platform_url: str = ""
    wm_platform_api_key: str = ""
    core_banking_url: str = ""
    core_banking_api_key: str = ""
    client_master_url: str = ""
    client_master_api_key: str = ""

    # ── Credit / Bureau ───────────────────────────────────────────────────────
    credit_bureau_url: str = ""
    credit_bureau_key: str = ""

    # ── eSign ─────────────────────────────────────────────────────────────────
    esign_provider: str = "adobe"
    esign_api_url: str = ""
    esign_api_key: str = ""

    # ── Notifications ─────────────────────────────────────────────────────────
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    notification_sms_url: str = ""
    notification_api_key: str = ""

    # ── Observability ─────────────────────────────────────────────────────────
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    langsmith_api_key: str = ""
    langsmith_project: str = "capmarkets-onboarding-agents"

    # ── Compliance thresholds (BRD-aligned) ───────────────────────────────────
    sow_income_threshold: float = 1_000_000.0     # USD — triggers EDD (BRD)
    stp_deposit_threshold: float = 500_000.0      # above this → manual review
    ocr_confidence_threshold: float = 0.85        # BRD FR-D2: 85% OCR confidence
    llm_confidence_threshold: float = 0.75        # below → human review
    pep_annual_income_edd: float = 250_000.0      # PEP + elevated income → EDD

    # ── Retention / audit ─────────────────────────────────────────────────────
    audit_retention_years: int = 7               # BRD FR-AU2

    @model_validator(mode="after")
    def _resolve_kv_secrets(self) -> "Settings":
        """Optionally fetch secrets from Azure Key Vault at startup."""
        kv_pairs = [
            ("azure_openai_endpoint_kv_uri", "azure_openai_endpoint"),
            ("azure_openai_api_key_kv_uri",  "azure_openai_api_key"),
            ("azure_openai_deployment_kv_uri", "azure_openai_deployment"),
            ("database_url_kv_uri",          "database_url"),
            ("redis_url_kv_uri",             "redis_url"),
            ("arize_phoenix_api_key_kv_uri",  "arize_phoenix_api_key"),
            ("arize_phoenix_password_kv_uri", "phoenix_admin_password"),
        ]
        uri_set = any(getattr(self, uri) for uri, _ in kv_pairs)
        if not uri_set:
            return self
        try:
            from azure.identity import DefaultAzureCredential
            from azure.keyvault.secrets import SecretClient
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=self.azure_keyvault_url, credential=credential)
            for uri_field, target_field in kv_pairs:
                uri = getattr(self, uri_field)
                if uri and not getattr(self, target_field):
                    secret_name = uri.split("/")[-1]
                    setattr(self, target_field, client.get_secret(secret_name).value or "")
        except Exception:
            pass
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
