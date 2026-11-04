"""Durable media classification job + result (PostgreSQL source of truth)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base, TimestampMixin
from app.models.media_classification_enums import (
    MediaClassificationConfidenceBand,
    MediaClassificationStatus,
)


class MediaClassification(Base, TimestampMixin):
    """
    One classification decision for a listing media-set revision.

    Not a MediaJob — different semantics (listing-level, multi-photo, user confirm).
    """

    __tablename__ = "media_classifications"
    __table_args__ = (
        UniqueConstraint(
            "idempotency_key",
            name="uq_media_classifications_idempotency_key",
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
    classifier_version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[MediaClassificationStatus] = mapped_column(
        SQLEnum(MediaClassificationStatus, name="media_classification_status_enum"),
        nullable=False,
        default=MediaClassificationStatus.pending,
        server_default=MediaClassificationStatus.pending.value,
        index=True,
    )
    confidence_band: Mapped[MediaClassificationConfidenceBand] = mapped_column(
        SQLEnum(
            MediaClassificationConfidenceBand,
            name="media_classification_confidence_band_enum",
        ),
        nullable=False,
        default=MediaClassificationConfidenceBand.none,
        server_default=MediaClassificationConfidenceBand.none.value,
    )
    top_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    candidates_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
    )
    evidence_media_ids: Mapped[list[int]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
    )
    images_inspected: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    selected_category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    predicted_category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_overridden: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")
    lease_owner: Mapped[str | None] = mapped_column(String(128), nullable=True)
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    queue_wait_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    inference_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Future: brand/model/etc. — reserved, unused in Substage 2.
    suggested_attributes_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


def build_classification_idempotency_key(
    listing_id: int,
    media_set_fingerprint: str,
    classifier_version: str,
) -> str:
    version = (classifier_version or "dev").strip() or "dev"
    fp = (media_set_fingerprint or "").strip() or "empty"
    return f"listing:{listing_id}:media_set:{fp}:clf:{version}"
