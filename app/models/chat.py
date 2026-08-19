from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.listing import Listing
    from app.models.media import Media
    from app.models.message import Message
    from app.models.user import User


class Chat(Base, TimestampMixin):
    __tablename__ = "chats"
    __table_args__ = (
        UniqueConstraint(
            "listing_id",
            "buyer_id",
            "seller_id",
            name="uq_chat_listing_buyer_seller",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), index=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    listing: Mapped[Listing] = relationship("Listing", back_populates="chats")
    buyer: Mapped[User] = relationship("User", foreign_keys=[buyer_id], back_populates="chats_as_buyer")
    seller: Mapped[User] = relationship(
        "User",
        foreign_keys=[seller_id],
        back_populates="chats_as_seller",
    )
    messages: Mapped[list[Message]] = relationship(
        "Message",
        back_populates="chat",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Message.created_at",
    )
    media: Mapped[list["Media"]] = relationship(
        "Media",
        back_populates="chat",
        passive_deletes=True,
    )
