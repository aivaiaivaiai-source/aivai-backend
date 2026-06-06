from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin
from app.models.category_enums import CategoryFilterType

if TYPE_CHECKING:
    from app.models.category import Category


class CategoryFilter(Base, TimestampMixin):
    """Search/listing filters — never surfaced in AI dialogue."""

    __tablename__ = "category_filters"
    __table_args__ = (
        UniqueConstraint("category_id", "filter_key", name="uq_category_filters_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filter_key: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    filter_type: Mapped[CategoryFilterType] = mapped_column(
        SQLEnum(CategoryFilterType, name="category_filter_type_enum"),
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    config: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )

    category: Mapped[Category] = relationship("Category", back_populates="filters")
