from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.locale import DEFAULT_LOCALE
from app.db.base_class import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.category import Category


class CategoryAlias(Base, TimestampMixin):
    """Natural-language aliases for intent → category resolution."""

    __tablename__ = "category_aliases"
    __table_args__ = (
        UniqueConstraint(
            "alias_normalized",
            "locale",
            name="uq_category_aliases_normalized_locale",
        ),
        Index("ix_category_aliases_compact_locale", "alias_compact", "locale"),
        Index("ix_category_aliases_category_enabled", "category_id", "is_enabled"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    alias: Mapped[str] = mapped_column(String(160), nullable=False)
    alias_normalized: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    alias_compact: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    locale: Mapped[str] = mapped_column(String(8), nullable=False, default=DEFAULT_LOCALE.value)
    weight: Mapped[int] = mapped_column(nullable=False, default=100)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    category: Mapped[Category] = relationship("Category", back_populates="aliases")
