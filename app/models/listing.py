from __future__ import annotations

from decimal import Decimal
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin
from app.models.enums import Currency, ListingStatus

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.chat import Chat
    from app.models.listing_field_value import ListingFieldValue
    from app.models.media import Media
    from app.models.user import User


class Listing(Base, TimestampMixin):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[Currency] = mapped_column(
        SQLEnum(Currency, name="currency_enum"),
        nullable=False,
    )
    status: Mapped[ListingStatus] = mapped_column(
        SQLEnum(ListingStatus, name="listing_status_enum"),
        nullable=False,
        default=ListingStatus.draft,
        index=True,
    )

    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"),
        index=True,
    )
    uses_placeholder_image: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    is_promoted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        index=True,
    )
    promotion_daily_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    promotion_tier: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        index=True,
    )
    promotion_starts_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    promotion_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    owner: Mapped[User | None] = relationship(
        "User",
        back_populates="listings",
        foreign_keys=[owner_id],
    )
    category: Mapped[Category] = relationship("Category", back_populates="listings")
    images: Mapped[list[Media]] = relationship(
        "Media",
        back_populates="listing",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
        primaryjoin="and_(Listing.id == Media.listing_id, Media.chat_id.is_(None))",
    )
    chats: Mapped[list[Chat]] = relationship(
        "Chat",
        back_populates="listing",
        lazy="selectin",
    )
    field_values: Mapped[list[ListingFieldValue]] = relationship(
        "ListingFieldValue",
        back_populates="listing",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
