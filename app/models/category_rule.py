from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin
from app.models.category_enums import CategoryRuleType, ModerationAction

if TYPE_CHECKING:
    from app.models.category import Category


class CategoryRule(Base, TimestampMixin):
    """AI routing, dialogue, and moderation rules per category (or global if category_id null)."""

    __tablename__ = "category_ai_rules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    rule_type: Mapped[CategoryRuleType] = mapped_column(
        SQLEnum(CategoryRuleType, name="category_rule_type_enum"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    pattern: Mapped[str | None] = mapped_column(Text, nullable=True)
    action: Mapped[ModerationAction] = mapped_column(
        SQLEnum(ModerationAction, name="moderation_action_enum"),
        nullable=False,
        default=ModerationAction.allow,
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    config: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    category: Mapped[Category | None] = relationship("Category", back_populates="ai_rules")
