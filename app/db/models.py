"""ORM models for Capital Markets Client Onboarding."""
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import String, Float, Boolean, DateTime, JSON, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ClientApplication(Base):
    __tablename__ = "client_applications"

    id: Mapped[str]            = mapped_column(String(64), primary_key=True)
    application_id: Mapped[str]= mapped_column(String(64), unique=True, index=True)
    journey_type: Mapped[str]  = mapped_column(String(32), default="individual")
    client_type: Mapped[str]   = mapped_column(String(32), default="retail")   # retail|hnw|uhnw|joint|corporate
    status: Mapped[str]        = mapped_column(String(32), default="pending")
    current_step: Mapped[str]  = mapped_column(String(64), default="triage")
    risk_band: Mapped[str]     = mapped_column(String(32), default="")
    routing: Mapped[str]       = mapped_column(String(32), default="")         # stp|standard|enhanced|edd|hold|reject
    human_review_required: Mapped[bool] = mapped_column(Boolean, default=False)
    human_decision: Mapped[str | None]  = mapped_column(String(32), nullable=True)
    completed_steps: Mapped[dict]       = mapped_column(JSON, default=list)
    state_snapshot: Mapped[dict]        = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime]        = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime]        = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class DocumentRecord(Base):
    __tablename__ = "document_records"

    id: Mapped[str]             = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str]     = mapped_column(String(64), index=True)
    doc_type: Mapped[str]       = mapped_column(String(64))
    file_name: Mapped[str]      = mapped_column(String(256))
    ocr_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    validation_status: Mapped[str] = mapped_column(String(32), default="pending")
    extracted_fields: Mapped[dict] = mapped_column(JSON, default=dict)
    anomalies: Mapped[list]     = mapped_column(JSON, default=list)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int]             = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str]     = mapped_column(String(64), index=True)
    event_type: Mapped[str]     = mapped_column(String(64))
    actor: Mapped[str]          = mapped_column(String(128), default="system")
    payload: Mapped[dict]       = mapped_column(JSON, default=dict)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
