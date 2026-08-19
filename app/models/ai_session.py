from __future__ import annotations

from sqlalchemy import Enum as SQLEnum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base, TimestampMixin
from app.models.enums import AiAgentType


class AiSession(Base, TimestampMixin):
    __tablename__ = "ai_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True,
    )
    agent_type: Mapped[AiAgentType] = mapped_column(
        SQLEnum(AiAgentType, name="ai_agent_type_enum", create_type=False),
        nullable=False,
        index=True,
    )
    subscription_id: Mapped[int | None] = mapped_column(
        ForeignKey("ai_subscriptions.id"), nullable=True,
    )
