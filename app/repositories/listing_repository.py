from __future__ import annotations

from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import Currency, ListingStatus
from app.models.listing import Listing
from app.repositories.base import BaseRepository


class ListingRepository(BaseRepository[Listing]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Listing)

    async def get_by_id(self, entity_id: int) -> Listing | None:
        stmt = (
            select(Listing)
            .where(Listing.id == entity_id)
            .options(
                selectinload(Listing.images),
                selectinload(Listing.category),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def search_listings(
        self,
        *,
        category_id: int | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        currency: Currency | None = None,
        status: ListingStatus | None = None,
        q: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Listing]:
        stmt = (
            select(Listing)
            .options(
                selectinload(Listing.images),
                selectinload(Listing.category),
            )
            .order_by(Listing.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if category_id is not None:
            stmt = stmt.where(Listing.category_id == category_id)
        if min_price is not None:
            stmt = stmt.where(Listing.price >= min_price)
        if max_price is not None:
            stmt = stmt.where(Listing.price <= max_price)
        if currency is not None:
            stmt = stmt.where(Listing.currency == currency)
        if status is not None:
            stmt = stmt.where(Listing.status == status)
        if q:
            pattern = f"%{q}%"
            stmt = stmt.where(
                or_(
                    Listing.title.ilike(pattern),
                    Listing.description.ilike(pattern),
                )
            )

        result = await self._session.execute(stmt)
        return list(result.scalars().unique().all())
