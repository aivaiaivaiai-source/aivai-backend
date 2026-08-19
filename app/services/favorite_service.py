from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundError, TransactionFailedError
from app.core.pagination import clamp_limit
from app.models.enums import ListingStatus
from app.models.favorite import Favorite
from app.repositories.favorite_repository import FavoriteRepository
from app.repositories.listing_repository import ListingRepository
from app.schemas.favorite import FavoriteToggleRead
from app.schemas.listing import ListingFeedPage
from app.services.listing_service import ListingService


class FavoriteService:
    def __init__(
        self,
        session: AsyncSession,
        favorite_repository: FavoriteRepository,
        listing_repository: ListingRepository,
        listing_service: ListingService,
    ) -> None:
        self._session = session
        self._favorites = favorite_repository
        self._listings = listing_repository
        self._listing_service = listing_service

    async def list_for_user(
        self,
        user_id: int,
        *,
        limit: int = 40,
        offset: int = 0,
    ) -> ListingFeedPage:
        limit = clamp_limit(limit, max_limit=100)
        total = await self._favorites.count_listings_for_user(user_id)
        rows = await self._favorites.list_listings_for_user(
            user_id,
            limit=limit,
            offset=offset,
        )
        return ListingFeedPage(
            items=[self._listing_service._to_read(row) for row in rows],
            total=total,
        )

    async def toggle(self, user_id: int, listing_id: int) -> FavoriteToggleRead:
        listing = await self._listings.get_by_id(listing_id)
        if listing is None or listing.status != ListingStatus.active:
            raise EntityNotFoundError("Listing", entity_id=listing_id)

        existing = await self._favorites.get_for_user(user_id, listing_id)
        if existing is not None:
            await self._favorites.delete(existing)
            try:
                await self._session.commit()
            except Exception as exc:
                await self._session.rollback()
                raise TransactionFailedError(
                    "Failed to remove favorite; transaction rolled back.",
                ) from exc
            return FavoriteToggleRead(listing_id=listing_id, favorited=False)

        await self._favorites.create(
            Favorite(user_id=user_id, listing_id=listing_id)
        )
        try:
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            return FavoriteToggleRead(listing_id=listing_id, favorited=True)
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to add favorite; transaction rolled back.",
            ) from exc
        return FavoriteToggleRead(listing_id=listing_id, favorited=True)
