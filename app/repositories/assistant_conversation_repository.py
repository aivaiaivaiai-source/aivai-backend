from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete, select
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

    async def delete_inactive_before(self, cutoff: datetime) -> int:
        """Hard-delete all conversations with last_activity_at older than cutoff."""
        stmt = delete(AssistantConversation).where(
            AssistantConversation.last_activity_at < cutoff,
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return int(result.rowcount or 0)

    async def delete_inactive_before_batch(self, cutoff: datetime, *, limit: int) -> int:
        """Hard-delete up to ``limit`` inactive conversations (messages cascade)."""
        if limit < 1:
            raise ValueError("limit must be >= 1")
        ids_stmt = (
            select(AssistantConversation.id)
            .where(AssistantConversation.last_activity_at < cutoff)
            .order_by(AssistantConversation.id)
            .limit(limit)
        )
        stmt = delete(AssistantConversation).where(AssistantConversation.id.in_(ids_stmt))
        result = await self._session.execute(stmt)
        await self._session.flush()
        return int(result.rowcount or 0)
