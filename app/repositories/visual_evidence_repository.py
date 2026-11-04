from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing_visual_evidence import ListingVisualEvidence
from app.models.visual_evidence_enums import VisualEvidenceStatus
from app.repositories.base import BaseRepository


class VisualEvidenceRepository(BaseRepository[ListingVisualEvidence]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ListingVisualEvidence)

    async def get_by_idempotency_key(self, key: str) -> ListingVisualEvidence | None:
        stmt = select(ListingVisualEvidence).where(
            ListingVisualEvidence.idempotency_key == key
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_latest_for_listing(self, listing_id: int) -> ListingVisualEvidence | None:
        stmt = (
            select(ListingVisualEvidence)
            .where(ListingVisualEvidence.listing_id == listing_id)
            .order_by(ListingVisualEvidence.id.desc())
            .limit(1)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_for_listing_fingerprint(
        self,
        listing_id: int,
        fingerprint: str,
    ) -> ListingVisualEvidence | None:
        stmt = (
            select(ListingVisualEvidence)
            .where(
                ListingVisualEvidence.listing_id == listing_id,
                ListingVisualEvidence.media_set_fingerprint == fingerprint,
            )
            .order_by(ListingVisualEvidence.id.desc())
            .limit(1)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_claimable(
        self,
        *,
        now: datetime,
        limit: int,
    ) -> list[ListingVisualEvidence]:
        stmt = (
            select(ListingVisualEvidence)
            .where(
                ListingVisualEvidence.status == VisualEvidenceStatus.pending,
                ListingVisualEvidence.available_at <= now,
            )
            .order_by(ListingVisualEvidence.available_at.asc(), ListingVisualEvidence.id.asc())
            .limit(limit)
        )
        return list((await self._session.execute(stmt)).scalars().all())
