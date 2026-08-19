from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin
from app.models.enums import PromotionOrderStatus

if TYPE_CHECKING:
    from app.models.listing import Listing
    from app.models.user import User


class PromotionOrder(Base, TimestampMixin):
    """One paid promotion window for a listing. Listing columns cache the active one."""

    __tablename__ = "promotion_orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    daily_rate: Mapped[int] = mapped_column(Integer, nullable=False)
    days: Mapped[int] = mapped_column(Integer, nullable=False)
    discount_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    tier: Mapped[int] = mapped_column(Integer, nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    refunded_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )
    status: Mapped[PromotionOrderStatus] = mapped_column(
        SQLEnum(PromotionOrderStatus, name="promotion_order_status_enum"),
        nullable=False,
        default=PromotionOrderStatus.active,
        index=True,
    )

    listing: Mapped[Listing] = relationship("Listing")
    user: Mapped[User] = relationship("User")
