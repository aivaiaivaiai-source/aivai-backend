from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assistant_message import AssistantMessage
from app.repositories.base import BaseRepository


class AssistantMessageRepository(BaseRepository[AssistantMessage]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AssistantMessage)

    async def list_for_conversation(
        self,
        conversation_id: int,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AssistantMessage]:
        stmt = (
            select(AssistantMessage)
            .where(AssistantMessage.conversation_id == conversation_id)
            .order_by(AssistantMessage.id)
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
