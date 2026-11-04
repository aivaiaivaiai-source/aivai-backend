"""Persistence for Category Resolver shadow results."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing_category_resolver import ListingCategoryResolverResult


class CategoryResolverRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_idempotency_key(self, key: str) -> ListingCategoryResolverResult | None:
        stmt = select(ListingCategoryResolverResult).where(
            ListingCategoryResolverResult.idempotency_key == key
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_latest_for_listing(self, listing_id: int) -> ListingCategoryResolverResult | None:
        stmt = (
            select(ListingCategoryResolverResult)
            .where(ListingCategoryResolverResult.listing_id == listing_id)
            .order_by(ListingCategoryResolverResult.id.desc())
            .limit(1)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def create(self, row: ListingCategoryResolverResult) -> ListingCategoryResolverResult:
        self._session.add(row)
        await self._session.flush()
        return row

    async def save(self, row: ListingCategoryResolverResult) -> ListingCategoryResolverResult:
        await self._session.flush()
        return row
