"""Shared utility helpers."""
from __future__ import annotations
import re
import uuid
from datetime import date, datetime
from typing import Any


def generate_id(prefix: str = "") -> str:
    short = uuid.uuid4().hex[:12].upper()
    return f"{prefix}-{short}" if prefix else short


def parse_currency(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = re.sub(r"[^\d.\-]", "", str(value))
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def parse_date_string(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%d %b %Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def redact_pii(text: str) -> str:
    """Replace SSN, card numbers, passport numbers with redacted placeholders."""
    text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[SSN-REDACTED]", text)
    text = re.sub(r"\b(?:\d[ -]*?){13,16}\b", "[CARD-REDACTED]", text)
    text = re.sub(r"\b[A-Z]{1,2}\d{6,9}\b", "[PASSPORT-REDACTED]", text)
    return text
