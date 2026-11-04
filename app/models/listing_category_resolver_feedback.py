"""Structured feedback when resolver suggestion differs from user choice."""

from __future__ import annotations

import enum

from sqlalchemy import Enum as SQLEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base, TimestampMixin


class CategoryResolverFeedbackOutcome(str, enum.Enum):
    corrected = "corrected"
    accepted_implicitly = "accepted_implicitly"


class ListingCategoryResolverFeedback(Base, TimestampMixin):
    __tablename__ = "listing_category_resolver_feedback"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resolver_result_id: Mapped[int | None] = mapped_column(
        ForeignKey("listing_category_resolver_results.id", ondelete="SET NULL"),
        nullable=True,
    )
    suggested_category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    selected_category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    outcome: Mapped[CategoryResolverFeedbackOutcome] = mapped_column(
        SQLEnum(
            CategoryResolverFeedbackOutcome,
            name="category_resolver_feedback_outcome_enum",
        ),
        nullable=False,
    )
    resolver_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
