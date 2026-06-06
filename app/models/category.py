from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin
from app.models.category_enums import CategoryEntityType

if TYPE_CHECKING:
    from app.models.category_alias import CategoryAlias
    from app.models.category_field import CategoryCoreField, CategoryOptionalField
    from app.models.category_filter import CategoryFilter
    from app.models.category_rule import CategoryRule
    from app.models.listing import Listing


class Category(Base, TimestampMixin):
    __tablename__ = "categories"
    __table_args__ = (
        Index("ix_categories_parent_active_sort", "parent_id", "is_active", "sort_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), unique=True, nullable=False, index=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    entity_type: Mapped[CategoryEntityType] = mapped_column(
        SQLEnum(CategoryEntityType, name="category_entity_type_enum"),
        nullable=False,
        default=CategoryEntityType.general,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, index=True)
    requires_city: Mapped[bool] = mapped_column(nullable=False, default=True)
    ai_dialogue_hint: Mapped[str | None] = mapped_column(Text, nullable=True)

    parent: Mapped[Category | None] = relationship(
        "Category",
        remote_side="Category.id",
        back_populates="children",
    )
    # Self-referential tree: avoid selectin (recursive explosion). Tree built via repository queries.
    children: Mapped[list[Category]] = relationship(
        "Category",
        back_populates="parent",
        lazy="select",
        cascade="save-update, merge",
        passive_deletes=True,
        order_by="Category.sort_order",
    )
    listings: Mapped[list[Listing]] = relationship(
        "Listing",
        back_populates="category",
        lazy="select",
    )
    aliases: Mapped[list[CategoryAlias]] = relationship(
        "CategoryAlias",
        back_populates="category",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    core_fields: Mapped[list[CategoryCoreField]] = relationship(
        "CategoryCoreField",
        back_populates="category",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    optional_fields: Mapped[list[CategoryOptionalField]] = relationship(
        "CategoryOptionalField",
        back_populates="category",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    filters: Mapped[list[CategoryFilter]] = relationship(
        "CategoryFilter",
        back_populates="category",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    ai_rules: Mapped[list[CategoryRule]] = relationship(
        "CategoryRule",
        back_populates="category",
        lazy="select",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
