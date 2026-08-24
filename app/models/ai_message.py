from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum as SQLEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base_class import Base, TimestampMixin
from app.models.ai_enums import AiMessageType
from app.models.assistant_enums import AssistantMessageRole

if TYPE_CHECKING:
    from app.models.ai_session import AiSession


class AiMessage(Base, TimestampMixin):
    __tablename__ = "ai_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("ai_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[AssistantMessageRole] = mapped_column(
        SQLEnum(AssistantMessageRole, name="assistant_message_role_enum"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[AiMessageType] = mapped_column(
        SQLEnum(AiMessageType, name="ai_message_type_enum"),
        nullable=False,
        default=AiMessageType.text,
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
        server_default="{}",
    )
    # Idempotency for match retries: unique per session when set.
    dedupe_key: Mapped[str | None] = mapped_column(String(128), nullable=True)

    session: Mapped["AiSession"] = relationship("AiSession", back_populates="messages")
