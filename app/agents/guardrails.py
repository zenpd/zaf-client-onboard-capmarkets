"""Guardrails — prompt injection detection + PII redaction (BRD NFR-3)."""
from __future__ import annotations
import re
from agents.state import OnboardingState
from shared.logger import get_logger

log = get_logger("agent.guardrails")

_INJECTION_PATTERNS = [
    r"ignore previous instructions",
    r"disregard (your|all) (previous |prior )?instructions",
    r"you are now",
    r"jailbreak",
    r"system prompt",
    r"forget (your|all) (previous |prior )?instructions",
    r"act as if",
    r"new persona",
]

_PII_PATTERNS = {
    "ssn":      r"\b\d{3}-\d{2}-\d{4}\b",
    "card":     r"\b(?:\d{4}[\s-]?){4}\b",
    "passport": r"\b[A-Z]{1,2}\d{6,9}\b",
}


def _detect_injection(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in _INJECTION_PATTERNS)


def _redact_pii(text: str) -> str:
    for label, pattern in _PII_PATTERNS.items():
        text = re.sub(pattern, f"[{label.upper()}-REDACTED]", text)
    return text


def guardrails_node(state: OnboardingState) -> OnboardingState:
    messages = state.get("messages", [])
    if not messages:
        return state
    last = messages[-1]
    if last.get("role") == "user":
        content = last.get("content", "")
        if _detect_injection(content):
            log.warning("guardrails.injection_detected")
            state["error"] = "Prompt injection attempt detected."
            return state
        last["content"] = _redact_pii(content)
    return state
