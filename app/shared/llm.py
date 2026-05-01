"""Shared LLM factory — returns AzureChatOpenAI configured from settings.

In development mode with no API key, returns a lightweight stub that echoes
a JSON placeholder so agents can still exercise their logic without real LLM calls.
"""
from __future__ import annotations
from langchain_openai import AzureChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from shared.config import get_settings


class _DevStubLLM(BaseChatModel):
    """Minimal stub that returns empty JSON so agent try/except blocks handle gracefully."""

    def _generate(self, messages: list[BaseMessage], **kwargs) -> ChatResult:  # type: ignore[override]
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content="{}"))])

    @property
    def _llm_type(self) -> str:  # type: ignore[override]
        return "dev-stub"


def get_llm(max_tokens: int = 512) -> BaseChatModel:
    settings = get_settings()
    api_key = settings.azure_openai_api_key or ""
    # In dev mode without a real key, return the stub — agents handle empty {} gracefully
    if not api_key or api_key.startswith("<") or settings.app_env == "development" and not api_key:
        return _DevStubLLM()
    endpoint = settings.azure_openai_endpoint
    if '/openai' in endpoint:
        endpoint = endpoint.split('/openai')[0]
    return AzureChatOpenAI(
        azure_endpoint=endpoint,
        azure_deployment=settings.azure_openai_deployment,
        openai_api_key=api_key,
        openai_api_version=settings.azure_openai_api_version,
        max_tokens=max_tokens,
    )
