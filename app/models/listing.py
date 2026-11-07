from __future__ import annotations

from decimal import Decimal
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin
from app.models.enums import Currency, ListingStatus
from app.models.listing_description_mode_enums import ListingDescriptionMode
from app.models.category_selection_enums import CategorySelectionSource
from app.models.category_enums import VehicleExecution

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
    # Nullable: Services V2 may publish with «По договорённости» and no amount.
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[Currency] = mapped_column(
        SQLEnum(Currency, name="currency_enum"),
        nullable=False,
    )
    # Currency V2: publication/repricing FX snapshot (USD→KGS). Not client-owned.
    exchange_rate_snapshot: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 6),
        nullable=True,
    )
    # Currency V2: Search/Sort normalized amount in KGS. Backend-owned.
    normalized_price_kgs: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
        index=True,
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
    # Null allowed for draft until category is confirmed (Media Classification).
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    category_selection_source: Mapped[CategorySelectionSource | None] = mapped_column(
        SQLEnum(CategorySelectionSource, name="category_selection_source_enum"),
        nullable=True,
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
    description_mode: Mapped[ListingDescriptionMode | None] = mapped_column(
        SQLEnum(ListingDescriptionMode, name="listing_description_mode_enum"),
        nullable=True,
    )
    vehicle_execution: Mapped[VehicleExecution | None] = mapped_column(
        SQLEnum(VehicleExecution, name="vehicle_execution_enum", create_type=False),
        nullable=True,
        index=True,
    )
    # Jobs V2: stable create intent (hiring | job_seeking). Null = legacy / non-jobs.
    job_intent: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        index=True,
    )

    owner: Mapped[User | None] = relationship(
        "User",
        back_populates="listings",
        foreign_keys=[owner_id],
    )
    category: Mapped[Category | None] = relationship(
        "Category",
        back_populates="listings",
    )
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
