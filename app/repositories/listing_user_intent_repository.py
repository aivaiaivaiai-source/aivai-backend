"""Persistence for listing user intent."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing_user_intent import ListingUserIntent
from app.models.listing_user_intent_enums import ListingUserIntentStatus


class ListingUserIntentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_listing_id(self, listing_id: int) -> ListingUserIntent | None:
        result = await self._session.execute(
            select(ListingUserIntent).where(ListingUserIntent.listing_id == listing_id),
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        listing_id: int,
        raw_intent_text: str,
        intent_status: ListingUserIntentStatus,
        intent_fingerprint: str,
        intent_version: int,
    ) -> ListingUserIntent:
        row = ListingUserIntent(
            listing_id=listing_id,
            raw_intent_text=raw_intent_text,
            intent_status=intent_status,
            intent_fingerprint=intent_fingerprint,
            intent_version=intent_version,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def save(self, row: ListingUserIntent) -> ListingUserIntent:
        await self._session.flush()
        return row

    async def delete_by_listing_id(self, listing_id: int) -> bool:
        row = await self.get_by_listing_id(listing_id)
        if row is None:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True
