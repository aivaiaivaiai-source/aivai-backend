from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, Enum as SQLEnum, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base_class import Base, TimestampMixin
from app.models.enums import AiAgentType

if TYPE_CHECKING:
    from app.models.ai_session import AiSession
    from app.models.ai_subscription import AiSubscription
    from app.models.user import User


class AiSearchTask(Base, TimestampMixin):
    """Structured search criteria created by an AI agent for background monitoring."""

    __tablename__ = "ai_search_tasks"
    __table_args__ = (
        Index("ix_ai_search_tasks_user_agent_active", "user_id", "agent_type", "is_active"),
        Index(
            "ix_ai_search_tasks_criteria_gin",
            "criteria_json",
            postgresql_using="gin",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_type: Mapped[AiAgentType] = mapped_column(
        SQLEnum(AiAgentType, name="ai_agent_type_enum", create_type=False),
        nullable=False,
        index=True,
    )
    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("ai_subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[int] = mapped_column(
        ForeignKey("ai_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    criteria_json: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        server_default="{}",
    )
    category_ids: Mapped[list[int]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        server_default="[]",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship("User")
    subscription: Mapped[AiSubscription] = relationship("AiSubscription")
    session: Mapped[AiSession] = relationship("AiSession")
