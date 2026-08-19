from __future__ import annotations

from sqlalchemy import Enum as SQLEnum, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base, TimestampMixin
from app.models.assistant_enums import AssistantMessageRole
from app.models.enums import AiMessageType


class AiMessage(Base, TimestampMixin):
    __tablename__ = "ai_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("ai_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[AssistantMessageRole] = mapped_column(
        SQLEnum(AssistantMessageRole, name="assistant_message_role_enum", create_type=False),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[AiMessageType] = mapped_column(
        SQLEnum(AiMessageType, name="ai_message_type_enum"),
        nullable=False,
        server_default=AiMessageType.text.value,
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSON, nullable=False, server_default="{}",
    )
