from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media_classification import MediaClassification
from app.models.media_classification_enums import MediaClassificationStatus
from app.repositories.base import BaseRepository


class MediaClassificationRepository(BaseRepository[MediaClassification]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MediaClassification)

    async def get_by_idempotency_key(self, key: str) -> MediaClassification | None:
        stmt = select(MediaClassification).where(
            MediaClassification.idempotency_key == key
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_for_listing(self, listing_id: int) -> MediaClassification | None:
        stmt = (
            select(MediaClassification)
            .where(MediaClassification.listing_id == listing_id)
            .order_by(MediaClassification.id.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_for_listing_fingerprint(
        self,
        listing_id: int,
        fingerprint: str,
    ) -> MediaClassification | None:
        stmt = (
            select(MediaClassification)
            .where(
                MediaClassification.listing_id == listing_id,
                MediaClassification.media_set_fingerprint == fingerprint,
            )
            .order_by(MediaClassification.id.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_claimable(
        self,
        *,
        now: datetime,
        limit: int,
    ) -> list[MediaClassification]:
        stmt = (
            select(MediaClassification)
            .where(
                MediaClassification.status == MediaClassificationStatus.pending,
                MediaClassification.available_at <= now,
            )
            .order_by(MediaClassification.available_at.asc(), MediaClassification.id.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
