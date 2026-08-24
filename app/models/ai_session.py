from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin
from app.models.ai_enums import AiAgentType

if TYPE_CHECKING:
    from app.models.ai_message import AiMessage


class AiSession(Base, TimestampMixin):
    __tablename__ = "ai_sessions"
    __table_args__ = (
        UniqueConstraint("user_id", "agent_type", name="uq_ai_sessions_user_agent"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_type: Mapped[AiAgentType] = mapped_column(
        SQLEnum(AiAgentType, name="ai_agent_type_enum"),
        nullable=False,
        index=True,
    )
    subscription_id: Mapped[int | None] = mapped_column(
        ForeignKey("ai_subscriptions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    last_read_message_id: Mapped[int | None] = mapped_column(nullable=True)

    messages: Mapped[list["AiMessage"]] = relationship(
        "AiMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="AiMessage.id",
    )
