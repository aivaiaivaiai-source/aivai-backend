from __future__ import annotations

from sqlalchemy import Integer, Numeric, String, and_, cast, func, literal, or_, select
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
        """Return saved searches matched in SQL + JSONB; caller applies ``q`` in Python."""
        if listing.owner_id is None:
            return []

        qp = SavedSearch.query_params
        cid = qp["category_id"].astext
        cur = qp["currency"].astext
        min_raw = qp["min_price"].astext
        max_raw = qp["max_price"].astext

        def json_text_unset_or_empty(col):  # type: ignore[no-untyped-def]
            return or_(
                col.is_(None),
                func.trim(func.coalesce(col, "")) == "",
            )

        category_ok = or_(
            json_text_unset_or_empty(cid),
            cast(cid, Integer) == literal(listing.category_id, type_=Integer),
        )
        currency_ok = or_(
            json_text_unset_or_empty(cur),
            cur == literal(listing.currency.value, type_=String()),
        )

        price_lit = literal(listing.price, type_=Numeric(12, 2))
        min_ok = or_(
            json_text_unset_or_empty(min_raw),
            price_lit >= cast(min_raw, Numeric(12, 2)),
        )
        max_ok = or_(
            json_text_unset_or_empty(max_raw),
            price_lit <= cast(max_raw, Numeric(12, 2)),
        )

        stmt = (
            select(SavedSearch)
            .where(SavedSearch.is_active.is_(True))
            .where(SavedSearch.user_id != literal(listing.owner_id, type_=Integer))
            .where(and_(category_ok, currency_ok, min_ok, max_ok))
            .order_by(SavedSearch.id.asc())
        )
        result = await self._session.execute(stmt)
        rows = list(result.scalars().all())

        matched: list[SavedSearch] = []
        for ss in rows:
            params = ss.query_params if isinstance(ss.query_params, dict) else {}
            raw_q = params.get("q")
            if raw_q is None:
                matched.append(ss)
                continue
            needle = str(raw_q).strip().lower()
            if not needle:
                matched.append(ss)
                continue
            title_l = listing.title.lower()
            desc = (listing.description or "").lower()
            if needle in title_l or needle in desc:
                matched.append(ss)
        return matched
