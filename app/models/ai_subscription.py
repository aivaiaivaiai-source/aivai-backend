from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum as SQLEnum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base, TimestampMixin
from app.models.enums import AiAgentType, AiSubscriptionStatus


class AiSubscription(Base, TimestampMixin):
    __tablename__ = "ai_subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True,
    )
    agent_type: Mapped[AiAgentType] = mapped_column(
        SQLEnum(AiAgentType, name="ai_agent_type_enum"),
        nullable=False,
        index=True,
    )
    status: Mapped[AiSubscriptionStatus] = mapped_column(
        SQLEnum(AiSubscriptionStatus, name="ai_subscription_status_enum"),
        nullable=False,
        server_default=AiSubscriptionStatus.active.value,
    )
    price_som: Mapped[int] = mapped_column(Integer, nullable=False)
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True,
    )
    messages_today: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0",
    )
    messages_today_reset: Mapped[date | None] = mapped_column(
        Date, nullable=True,
    )
