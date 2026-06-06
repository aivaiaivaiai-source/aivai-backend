from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import Chat
from app.models.listing import Listing
from app.models.message import Message
from app.repositories.base import BaseRepository


class ChatRepository(BaseRepository[Chat]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Chat)

    async def get_by_id_loaded(self, entity_id: int) -> Chat | None:
        stmt = (
            select(Chat)
            .where(Chat.id == entity_id)
            .options(
                selectinload(Chat.listing).selectinload(Listing.images),
                selectinload(Chat.listing).selectinload(Listing.category),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_listing_and_participants(
        self,
        *,
        listing_id: int,
        buyer_id: int,
        seller_id: int,
    ) -> Chat | None:
        stmt = select(Chat).where(
            Chat.listing_id == listing_id,
            Chat.buyer_id == buyer_id,
            Chat.seller_id == seller_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create_chat(
        self,
        *,
        listing_id: int,
        buyer_id: int,
        seller_id: int,
    ) -> tuple[Chat, bool]:
        """Return (chat, created). Uses one lookup; caller commits the unit of work."""
        existing = await self.find_by_listing_and_participants(
            listing_id=listing_id,
            buyer_id=buyer_id,
            seller_id=seller_id,
        )
        if existing is not None:
            return existing, False
        chat = Chat(
            listing_id=listing_id,
            buyer_id=buyer_id,
            seller_id=seller_id,
        )
        created = await self.create(chat)
        return created, True

    async def list_user_chats(self, user_id: int) -> list[tuple[Chat, int]]:
        sort_ts = func.coalesce(Chat.last_message_at, Chat.created_at)
        unread_sq = (
            select(func.count(Message.id))
            .where(
                Message.chat_id == Chat.id,
                Message.sender_id != user_id,
                Message.read_at.is_(None),
            )
            .scalar_subquery()
        )
        stmt = (
            select(Chat, unread_sq)
            .where(or_(Chat.buyer_id == user_id, Chat.seller_id == user_id))
            .options(
                selectinload(Chat.listing).selectinload(Listing.images),
                selectinload(Chat.listing).selectinload(Listing.category),
            )
            .order_by(sort_ts.desc())
        )
        result = await self._session.execute(stmt)
        return [(chat, int(unread_count)) for chat, unread_count in result.all()]
