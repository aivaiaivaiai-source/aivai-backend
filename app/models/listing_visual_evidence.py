"""Durable local visual evidence job + aggregated result."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base, TimestampMixin
from app.models.visual_evidence_enums import VisualEvidenceStatus


class ListingVisualEvidence(Base, TimestampMixin):
    """
    Object-centric visual evidence for one listing media-set revision.

    NOT category assignment — concepts describe visible objects/scenes only.
    """

    __tablename__ = "listing_visual_evidence"
    __table_args__ = (
        UniqueConstraint(
            "idempotency_key",
            name="uq_listing_visual_evidence_idempotency_key",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    idempotency_key: Mapped[str] = mapped_column(String(256), nullable=False)
    media_set_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    calibration_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[VisualEvidenceStatus] = mapped_column(
        SQLEnum(VisualEvidenceStatus, name="visual_evidence_status_enum"),
        nullable=False,
        default=VisualEvidenceStatus.pending,
        server_default=VisualEvidenceStatus.pending.value,
        index=True,
    )
    observations_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
    )
    top_concepts_json: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
    )
    images_inspected: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    lease_owner: Mapped[str | None] = mapped_column(String(128), nullable=True)
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    queue_wait_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    inference_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processing_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


def build_visual_evidence_idempotency_key(
    listing_id: int,
    media_set_fingerprint: str,
    model_version: str,
    prompt_version: str,
    calibration_version: str | None = None,
) -> str:
    fp = (media_set_fingerprint or "").strip() or "empty"
    model = (model_version or "unknown").strip() or "unknown"
    prompt = (prompt_version or "unknown").strip() or "unknown"
    cal = (calibration_version or "none").strip() or "none"
    return f"listing:{listing_id}:media_set:{fp}:ve:{model}:{prompt}:cal:{cal}"
