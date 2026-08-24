from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin
from app.models.image_moderation_enums import MediaModerationStatus
from app.models.media_enums import MediaLifecycleStatus

if TYPE_CHECKING:
    from app.models.chat import Chat
    from app.models.listing import Listing
    from app.models.media_job import MediaJob
    from app.models.message_attachment import MessageAttachment


class Media(Base, TimestampMixin):
    __tablename__ = "media"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chat_id: Mapped[int | None] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    order: Mapped[int] = mapped_column("order", Integer, nullable=False, default=0)
    is_placeholder: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    lifecycle_status: Mapped[MediaLifecycleStatus] = mapped_column(
        SQLEnum(MediaLifecycleStatus, name="media_lifecycle_status_enum"),
        nullable=False,
        default=MediaLifecycleStatus.ready,
        server_default=MediaLifecycleStatus.ready.value,
    )
    client_upload_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    content_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    pipeline_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # Logical blob key for immutable original (Stage 2). URLs remain API-facing.
    original_storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    original_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    display_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    feed_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    thumb_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    moderation_status: Mapped[MediaModerationStatus] = mapped_column(
        SQLEnum(MediaModerationStatus, name="media_moderation_status_enum"),
        nullable=False,
        default=MediaModerationStatus.pending,
        server_default=MediaModerationStatus.approved.value,
    )
    moderation_reason: Mapped[str | None] = mapped_column(String(512), nullable=True)
    moderated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    focus_bbox_left: Mapped[float | None] = mapped_column(Float, nullable=True)
    focus_bbox_top: Mapped[float | None] = mapped_column(Float, nullable=True)
    focus_bbox_width: Mapped[float | None] = mapped_column(Float, nullable=True)
    focus_bbox_height: Mapped[float | None] = mapped_column(Float, nullable=True)
    focus_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    display_storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    feed_storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    thumb_storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    upload_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    upload_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    declared_content_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    declared_content_length: Mapped[int | None] = mapped_column(Integer, nullable=True)

    listing: Mapped[Listing] = relationship("Listing", back_populates="images")
    chat: Mapped[Chat | None] = relationship("Chat", back_populates="media")
    jobs: Mapped[list["MediaJob"]] = relationship(
        "MediaJob",
        back_populates="media",
        passive_deletes=True,
    )
    message_links: Mapped[list["MessageAttachment"]] = relationship(
        "MessageAttachment",
        back_populates="media",
        passive_deletes=True,
    )
