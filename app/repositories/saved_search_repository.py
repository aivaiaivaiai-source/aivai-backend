from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing import Listing
from app.models.saved_search import SavedSearch
from app.repositories.base import BaseRepository


class SavedSearchRepository(BaseRepository[SavedSearch]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SavedSearch)

    async def list_for_user(
        self,
        user_id: int,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SavedSearch]:
        stmt = (
            select(SavedSearch)
            .where(SavedSearch.user_id == user_id)
            .order_by(SavedSearch.id.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_for_user(self, search_id: int, user_id: int) -> SavedSearch | None:
        stmt = select(SavedSearch).where(
            SavedSearch.id == search_id,
            SavedSearch.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_matching_for_listing(self, listing: Listing) -> list[SavedSearch]:
        """Match active saved searches to a listing (Python filter — dialect-safe)."""
        if listing.owner_id is None:
            return []

        stmt = (
            select(SavedSearch)
            .where(SavedSearch.is_active.is_(True))
            .where(SavedSearch.user_id != listing.owner_id)
            .order_by(SavedSearch.id.asc())
            .limit(500)
        )
        result = await self._session.execute(stmt)
        rows = list(result.scalars().all())

        matched: list[SavedSearch] = []
        for ss in rows:
            params = ss.query_params if isinstance(ss.query_params, dict) else {}
            if not _matches_params(listing, params):
                continue
            matched.append(ss)
        return matched


def _matches_params(listing: Listing, params: dict) -> bool:
    raw_cat = params.get("category_id")
    if raw_cat not in (None, ""):
        try:
            if int(raw_cat) != listing.category_id:
                return False
        except (TypeError, ValueError):
            return False

    raw_cur = params.get("currency")
    if raw_cur not in (None, ""):
        if str(raw_cur).upper() != listing.currency.value.upper():
            return False

    if listing.price is not None:
        min_raw = params.get("min_price")
        max_raw = params.get("max_price")
        try:
            if min_raw not in (None, "") and listing.price < Decimal(str(min_raw)):
                return False
            if max_raw not in (None, "") and listing.price > Decimal(str(max_raw)):
                return False
        except Exception:
            return False

    raw_q = params.get("q")
    if raw_q is None:
        return True
    needle = str(raw_q).strip().lower()
    if not needle:
        return True
    title_l = listing.title.lower()
    desc = (listing.description or "").lower()
    return needle in title_l or needle in desc
