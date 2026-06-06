from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin
from app.models.image_moderation_enums import MediaModerationStatus

if TYPE_CHECKING:
    from app.models.listing import Listing
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
    order: Mapped[int] = mapped_column("order", Integer, nullable=False, default=0)
    is_placeholder: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
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

    listing: Mapped[Listing] = relationship("Listing", back_populates="images")
    message_links: Mapped[list["MessageAttachment"]] = relationship(
        "MessageAttachment",
        back_populates="media",
        passive_deletes=True,
    )
