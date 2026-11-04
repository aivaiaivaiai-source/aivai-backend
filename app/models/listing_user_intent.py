"""Draft listing user intent — separate from description and AI classification."""

from __future__ import annotations

from sqlalchemy import Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base, TimestampMixin
from app.models.listing_user_intent_enums import ListingUserIntentStatus


class ListingUserIntent(Base, TimestampMixin):
    """
    One intent record per listing (1:1).

    Stores raw user phrasing for hybrid classification; not merged into Listing
    to keep AI/resolver metadata out of the core listing row.
    """

    __tablename__ = "listing_user_intents"

    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"),
        primary_key=True,
    )
    raw_intent_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    intent_status: Mapped[ListingUserIntentStatus] = mapped_column(
        SQLEnum(
            ListingUserIntentStatus,
            name="listing_user_intent_status_enum",
        ),
        nullable=False,
        default=ListingUserIntentStatus.missing,
        server_default=ListingUserIntentStatus.missing.value,
    )
    intent_fingerprint: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        default="",
        server_default="",
    )
    intent_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
