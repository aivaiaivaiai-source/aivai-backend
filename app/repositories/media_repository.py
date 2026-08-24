from __future__ import annotations

from uuid import UUID

from sqlalchemy import case, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media import Media
from app.models.media_enums import MediaLifecycleStatus
from app.repositories.base import BaseRepository


class MediaRepository(BaseRepository[Media]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Media)

    async def get_by_listing_and_client_upload_id(
        self,
        listing_id: int,
        client_upload_id: UUID,
    ) -> Media | None:
        stmt = select(Media).where(
            Media.listing_id == listing_id,
            Media.client_upload_id == client_upload_id,
            Media.chat_id.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_for_update(self, media_id: int) -> Media | None:
        stmt = select(Media).where(Media.id == media_id).with_for_update()
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_incomplete_uploads_for_owner(self, owner_id: int) -> int:
        from app.models.listing import Listing

        stmt = (
            select(Media.id)
            .join(Listing, Media.listing_id == Listing.id)
            .where(
                Listing.owner_id == owner_id,
                Media.lifecycle_status == MediaLifecycleStatus.uploading,
                Media.chat_id.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return len(result.scalars().all())
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
            .where(Media.listing_id == listing_id, Media.chat_id.is_(None))
            .order_by(Media.order, Media.id)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_chat(self, chat_id: int) -> list[Media]:
        stmt = (
            select(Media)
            .where(Media.chat_id == chat_id)
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
