from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class Review(Base, TimestampMixin):
    __tablename__ = "user_reviews"
    __table_args__ = (
        UniqueConstraint("author_id", "subject_id", name="uq_review_author_subject"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    subject_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    owner_reply: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    author: Mapped[User] = relationship(
        "User",
        foreign_keys=[author_id],
        back_populates="reviews_authored",
    )
    subject: Mapped[User] = relationship(
        "User",
        foreign_keys=[subject_id],
        back_populates="reviews_received",
    )
