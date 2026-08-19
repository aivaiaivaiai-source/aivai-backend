from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import ListingStatus
from app.models.favorite import Favorite
from app.models.listing import Listing
from app.repositories.base import BaseRepository


class FavoriteRepository(BaseRepository[Favorite]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Favorite)

    async def get_for_user(self, user_id: int, listing_id: int) -> Favorite | None:
        stmt = select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.listing_id == listing_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_listings_for_user(
        self,
        user_id: int,
        *,
        limit: int,
        offset: int,
    ) -> list[Listing]:
        stmt = (
            select(Listing)
            .join(Favorite, Favorite.listing_id == Listing.id)
            .where(
                Favorite.user_id == user_id,
                Listing.status == ListingStatus.active,
            )
            .options(
                selectinload(Listing.images),
                selectinload(Listing.category),
                selectinload(Listing.field_values),
            )
            .order_by(Favorite.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().unique().all())

    async def count_listings_for_user(self, user_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(Favorite)
            .join(Listing, Listing.id == Favorite.listing_id)
            .where(
                Favorite.user_id == user_id,
                Listing.status == ListingStatus.active,
            )
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())
