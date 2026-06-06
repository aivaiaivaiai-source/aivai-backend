from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.message import Message
from app.models.message_attachment import MessageAttachment
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Message)

    async def list_by_chat(self, chat_id: int, *, limit: int, offset: int) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .options(selectinload(Message.attachments).selectinload(MessageAttachment.media))
            .order_by(Message.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        rows = list(result.scalars().unique().all())
        rows.reverse()
        return rows

    async def mark_as_read_from_others(self, chat_id: int, reader_user_id: int) -> None:
        """Incoming messages only (sender != reader); only rows still unread."""
        stmt = (
            update(Message)
            .where(
                Message.chat_id == chat_id,
                Message.sender_id != reader_user_id,
                Message.read_at.is_(None),
            )
            .values(read_at=datetime.now(UTC))
            .execution_options(synchronize_session=False)
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def count_unread_from_others(self, chat_id: int, reader_user_id: int) -> int:
        stmt = select(func.count(Message.id)).where(
            Message.chat_id == chat_id,
            Message.sender_id != reader_user_id,
            Message.read_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def get_by_id_with_attachments(self, message_id: int) -> Message | None:
        stmt = (
            select(Message)
            .where(Message.id == message_id)
            .options(selectinload(Message.attachments).selectinload(MessageAttachment.media))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_attachments(self, *, message_id: int, media_ids: list[int]) -> None:
        for mid in media_ids:
            self._session.add(MessageAttachment(message_id=message_id, media_id=mid))
        await self._session.flush()
