from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

# UniqueConstraint still used by CategoryOptionalField.

from app.db.base_class import Base, TimestampMixin
from app.models.category_enums import CategoryFieldType

if TYPE_CHECKING:
    from app.models.category import Category


class _CategoryFieldMixin:
    field_key: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    field_type: Mapped[CategoryFieldType] = mapped_column(
        SQLEnum(CategoryFieldType, name="category_field_type_enum"),
        nullable=False,
    )
    is_required: Mapped[bool] = mapped_column(nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    options: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )
    ai_hint: Mapped[str | None] = mapped_column(Text, nullable=True)


class CategoryCoreField(Base, TimestampMixin, _CategoryFieldMixin):
    """Fields AI must collect in dialogue (only if missing from user text).

    ``create_intent`` scopes Jobs V2 create schemas:
    NULL = default / non-jobs; ``hiring`` / ``job_seeking`` for Работа sectors.
    Unique identity is (category_id, field_key, coalesce(create_intent, '')).
    """

    __tablename__ = "category_core_fields"
    # Uniqueness: ix_category_core_fields_cat_key_intent (migration o3p4q5r6s7t8)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    create_intent: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        index=True,
    )

    category: Mapped[Category] = relationship("Category", back_populates="core_fields")


class CategoryOptionalField(Base, TimestampMixin, _CategoryFieldMixin):
    """Hidden/advanced fields — editable later, not asked in dialogue."""

    __tablename__ = "category_optional_fields"
    __table_args__ = (
        UniqueConstraint("category_id", "field_key", name="uq_category_optional_fields_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    category: Mapped[Category] = relationship("Category", back_populates="optional_fields")
