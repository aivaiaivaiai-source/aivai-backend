from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum as SQLEnum, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base, TimestampMixin
from app.models.media_job_enums import MediaOutboxStatus


class MediaOutbox(Base, TimestampMixin):
    """Transactional outbox — PostgreSQL durable enqueue before Redis XADD."""

    __tablename__ = "media_outbox"
    __table_args__ = (
        UniqueConstraint("dedupe_key", name="uq_media_outbox_dedupe_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[MediaOutboxStatus] = mapped_column(
        SQLEnum(MediaOutboxStatus, name="media_outbox_status_enum"),
        nullable=False,
        default=MediaOutboxStatus.pending,
        server_default=MediaOutboxStatus.pending.value,
        index=True,
    )
    dispatched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


def outbox_dedupe_key(job_id: int, *, suffix: str = "enqueue") -> str:
    return f"media_job:{job_id}:{suffix}"
