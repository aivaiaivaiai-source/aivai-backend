from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.listing import Listing
    from app.models.vehicle import VehicleBrand, VehicleModel

_SINGLE_VALUE_CHECK = """
(
    (value_text IS NOT NULL)::int +
    (value_int IS NOT NULL)::int +
    (value_decimal IS NOT NULL)::int +
    (value_bool IS NOT NULL)::int +
    (value_date IS NOT NULL)::int +
    (ref_brand_id IS NOT NULL)::int +
    (ref_model_id IS NOT NULL)::int
) = 1
"""


class ListingFieldValue(Base, TimestampMixin):
    __tablename__ = "listing_field_values"
    __table_args__ = (
        UniqueConstraint("listing_id", "field_key", name="uq_listing_field_values_listing_key"),
        CheckConstraint(_SINGLE_VALUE_CHECK, name="ck_listing_field_values_single_value"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    field_key: Mapped[str] = mapped_column(String(64), nullable=False)
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_int: Mapped[int | None] = mapped_column(Integer, nullable=True)
    value_decimal: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    value_bool: Mapped[bool | None] = mapped_column(nullable=True)
    value_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    ref_brand_id: Mapped[int | None] = mapped_column(
        ForeignKey("vehicle_brands.id", ondelete="SET NULL"),
        nullable=True,
    )
    ref_model_id: Mapped[int | None] = mapped_column(
        ForeignKey("vehicle_models.id", ondelete="SET NULL"),
        nullable=True,
    )

    listing: Mapped[Listing] = relationship("Listing", back_populates="field_values")
    ref_brand: Mapped[VehicleBrand | None] = relationship("VehicleBrand")
    ref_model: Mapped[VehicleModel | None] = relationship("VehicleModel")
