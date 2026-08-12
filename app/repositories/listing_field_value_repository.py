from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing_field_value import ListingFieldValue
from app.repositories.base import BaseRepository


class ListingFieldValueRepository(BaseRepository[ListingFieldValue]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ListingFieldValue)

    async def list_by_listing_id(self, listing_id: int) -> list[ListingFieldValue]:
        stmt = (
            select(ListingFieldValue)
            .where(ListingFieldValue.listing_id == listing_id)
            .order_by(ListingFieldValue.field_key)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def replace_for_listing(
        self,
        listing_id: int,
        rows: list[ListingFieldValue],
    ) -> list[ListingFieldValue]:
        await self._session.execute(
            delete(ListingFieldValue).where(ListingFieldValue.listing_id == listing_id)
        )
        for row in rows:
            row.listing_id = listing_id
            self._session.add(row)
        await self._session.flush()
        return await self.list_by_listing_id(listing_id)
