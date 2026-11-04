from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin
from app.models.media_job_enums import MediaJobStatus


class MediaJob(Base, TimestampMixin):
    __tablename__ = "media_jobs"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_media_jobs_idempotency_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    media_id: Mapped[int] = mapped_column(
        ForeignKey("media.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    idempotency_key: Mapped[str] = mapped_column(String(256), nullable=False)
    pipeline_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[MediaJobStatus] = mapped_column(
        SQLEnum(MediaJobStatus, name="media_job_status_enum"),
        nullable=False,
        default=MediaJobStatus.queued,
        server_default=MediaJobStatus.queued.value,
        index=True,
    )
    lease_owner: Mapped[str | None] = mapped_column(String(128), nullable=True)
    lease_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    last_error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    media = relationship("Media", back_populates="jobs")


def build_media_job_idempotency_key(
    media_id: int,
    pipeline_version: str,
    *,
    category_id: int | None = None,
) -> str:
    """Include category context so category change can enqueue a new job without bumping global pipeline version."""
    version = pipeline_version.strip() or "legacy"
    cat = int(category_id) if category_id is not None else 0
    return f"media:{media_id}:pipeline:{version}:cat:{cat}"
