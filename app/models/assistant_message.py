from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base_class import Base, TimestampMixin
from app.models.assistant_enums import AssistantMessageRole, AssistantMessageType

if TYPE_CHECKING:
    from app.models.assistant_conversation import AssistantConversation


class AssistantMessage(Base, TimestampMixin):
    __tablename__ = "assistant_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("assistant_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[AssistantMessageRole] = mapped_column(
        SQLEnum(AssistantMessageRole, name="assistant_message_role_enum"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[AssistantMessageType] = mapped_column(
        SQLEnum(AssistantMessageType, name="assistant_message_type_enum"),
        nullable=False,
        default=AssistantMessageType.text,
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
        server_default="{}",
    )

    conversation: Mapped["AssistantConversation"] = relationship(
        "AssistantConversation",
        back_populates="messages",
    )
