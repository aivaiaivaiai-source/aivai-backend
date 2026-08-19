from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin
from app.db.types import phone_str

if TYPE_CHECKING:
    from app.models.chat import Chat
    from app.models.listing import Listing
    from app.models.message import Message
    from app.models.notification import Notification
    from app.models.review import Review
    from app.models.saved_search import SavedSearch


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    phone: Mapped[phone_str]
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    balance: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0"),
    )
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    listings: Mapped[list[Listing]] = relationship(
        "Listing",
        back_populates="owner",
        foreign_keys="Listing.owner_id",
        lazy="selectin",
        cascade="save-update, merge",
    )
    saved_searches: Mapped[list[SavedSearch]] = relationship(
        "SavedSearch",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    notifications: Mapped[list[Notification]] = relationship(
        "Notification",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    chats_as_buyer: Mapped[list[Chat]] = relationship(
        "Chat",
        back_populates="buyer",
        foreign_keys="Chat.buyer_id",
        lazy="selectin",
    )
    chats_as_seller: Mapped[list[Chat]] = relationship(
        "Chat",
        back_populates="seller",
        foreign_keys="Chat.seller_id",
        lazy="selectin",
    )
    messages_sent: Mapped[list[Message]] = relationship(
        "Message",
        back_populates="sender",
        foreign_keys="Message.sender_id",
    )
    reviews_received: Mapped[list[Review]] = relationship(
        "Review",
        back_populates="subject",
        foreign_keys="Review.subject_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    reviews_authored: Mapped[list[Review]] = relationship(
        "Review",
        back_populates="author",
        foreign_keys="Review.author_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
