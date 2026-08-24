"""Durable storage blob delete queue (Stage 5 orphan reconciliation)."""

from __future__ import annotations

import enum

from sqlalchemy import Enum as SQLEnum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base, TimestampMixin


class MediaStorageCleanupStatus(str, enum.Enum):
    pending = "pending"
    done = "done"
    dead = "dead"


class MediaStorageCleanup(Base, TimestampMixin):
    __tablename__ = "media_storage_cleanup"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    media_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    reason: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[MediaStorageCleanupStatus] = mapped_column(
        SQLEnum(MediaStorageCleanupStatus, name="media_storage_cleanup_status_enum"),
        nullable=False,
        default=MediaStorageCleanupStatus.pending,
        server_default=MediaStorageCleanupStatus.pending.value,
        index=True,
    )
    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
