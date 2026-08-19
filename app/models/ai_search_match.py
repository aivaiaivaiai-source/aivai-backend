from __future__ import annotations

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base, TimestampMixin


class AiSearchMatch(Base, TimestampMixin):
    """Dedupes listing notifications per search task."""

    __tablename__ = "ai_search_matches"
    __table_args__ = (
        UniqueConstraint("task_id", "listing_id", name="uq_ai_search_matches_task_listing"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("ai_search_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
