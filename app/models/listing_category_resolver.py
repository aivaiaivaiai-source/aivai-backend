"""Durable Category Resolver shadow results — suggestion only, no auto-assign."""

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
from app.models.category_resolver_enums import CategoryResolverStatus


class ListingCategoryResolverResult(Base, TimestampMixin):
    """
    Shadow-mode resolver output for one listing input revision.

    Does NOT mutate listing.category_id — evaluation / future confirmation only.
    """

    __tablename__ = "listing_category_resolver_results"
    __table_args__ = (
        UniqueConstraint(
            "idempotency_key",
            name="uq_listing_category_resolver_idempotency_key",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    idempotency_key: Mapped[str] = mapped_column(String(256), nullable=False)
    input_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    catalog_snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    intent_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    intent_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    media_set_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    visual_evidence_id: Mapped[int | None] = mapped_column(
        ForeignKey("listing_visual_evidence.id", ondelete="SET NULL"),
        nullable=True,
    )
    visual_model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    visual_prompt_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    visual_calibration_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resolver_version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[CategoryResolverStatus] = mapped_column(
        SQLEnum(CategoryResolverStatus, name="category_resolver_status_enum"),
        nullable=False,
        default=CategoryResolverStatus.pending,
        server_default=CategoryResolverStatus.pending.value,
        index=True,
    )
    suggested_category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    suggested_slug: Mapped[str | None] = mapped_column(String(160), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    needs_confirmation: Mapped[bool] = mapped_column(nullable=False, default=True, server_default="true")
    candidate_path_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
    alternatives_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
    evidence_summary_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    intent_semantics_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


def build_resolver_idempotency_key(listing_id: int, input_fingerprint: str, resolver_version: str) -> str:
    fp = (input_fingerprint or "empty").strip() or "empty"
    version = (resolver_version or "v0").strip() or "v0"
    return f"listing:{listing_id}:resolver:{version}:{fp}"
