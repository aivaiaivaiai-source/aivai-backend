from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assistant_conversation import AssistantConversation
from app.models.assistant_enums import AssistantConversationStatus
from app.repositories.base import BaseRepository


class AssistantConversationRepository(BaseRepository[AssistantConversation]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AssistantConversation)

    async def get_for_user(self, conversation_id: int, user_id: int) -> AssistantConversation | None:
        stmt = select(AssistantConversation).where(
            AssistantConversation.id == conversation_id,
            AssistantConversation.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_messages(
        self,
        conversation_id: int,
        user_id: int,
        *,
        message_limit: int = 50,
    ) -> AssistantConversation | None:
        stmt = (
            select(AssistantConversation)
            .where(
                AssistantConversation.id == conversation_id,
                AssistantConversation.user_id == user_id,
            )
            .options(selectinload(AssistantConversation.messages))
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is not None and len(row.messages) > message_limit:
            row.messages = row.messages[-message_limit:]
        return row

    async def touch_activity(self, conversation_id: int) -> None:
        await self.update(
            conversation_id,
            last_activity_at=datetime.now(UTC),
        )

    async def close(self, conversation_id: int) -> AssistantConversation | None:
        return await self.update(
            conversation_id,
            status=AssistantConversationStatus.closed,
            last_activity_at=datetime.now(UTC),
        )
