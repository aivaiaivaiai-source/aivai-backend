from __future__ import annotations

from sqlalchemy import case, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media import Media
from app.repositories.base import BaseRepository


class MediaRepository(BaseRepository[Media]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Media)

    async def get_by_ids(self, media_ids: list[int]) -> list[Media]:
        if not media_ids:
            return []
        stmt = (
            select(Media)
            .where(Media.id.in_(tuple(set(media_ids))))
            .order_by(Media.id)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_listing(self, listing_id: int) -> list[Media]:
        stmt = (
            select(Media)
            .where(Media.listing_id == listing_id)
            .order_by(Media.order, Media.id)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_order(self, listing_id: int, ordered_image_ids: list[int]) -> None:
        id_mapping = {mid: pos for pos, mid in enumerate(ordered_image_ids)}
        stmt = (
            update(Media)
            .where(
                Media.listing_id == listing_id,
                Media.id.in_(ordered_image_ids),
            )
            .values(
                order=case(id_mapping, value=Media.id, else_=Media.order),
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()
