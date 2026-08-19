from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import Integer, Numeric, String, and_, cast, func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_search_match import AiSearchMatch
from app.models.ai_search_task import AiSearchTask
from app.models.ai_subscription import AiSubscription
from app.models.enums import AiSubscriptionStatus, ListingStatus
from app.models.listing import Listing
from app.repositories.base import BaseRepository


class AiSearchTaskRepository(BaseRepository[AiSearchTask]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AiSearchTask)

    async def get_active_for_session(
        self, session_id: int,
    ) -> AiSearchTask | None:
        stmt = (
            select(AiSearchTask)
            .where(
                AiSearchTask.session_id == session_id,
                AiSearchTask.is_active.is_(True),
            )
            .order_by(AiSearchTask.id.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def deactivate_for_subscription(self, subscription_id: int) -> None:
        stmt = (
            select(AiSearchTask)
            .where(
                AiSearchTask.subscription_id == subscription_id,
                AiSearchTask.is_active.is_(True),
            )
        )
        result = await self._session.execute(stmt)
        for task in result.scalars().all():
            task.is_active = False

    async def find_matching_for_listing(self, listing: Listing) -> list[AiSearchTask]:
        if listing.owner_id is None or listing.status != ListingStatus.active:
            return []

        stmt = (
            select(AiSearchTask)
            .join(
                AiSubscription,
                AiSearchTask.subscription_id == AiSubscription.id,
            )
            .where(
                AiSearchTask.is_active.is_(True),
                AiSubscription.status == AiSubscriptionStatus.active,
                AiSubscription.expires_at > func.now(),
                AiSearchTask.user_id != literal(listing.owner_id, type_=Integer),
            )
            .order_by(AiSearchTask.id.asc())
        )
        result = await self._session.execute(stmt)
        candidates = list(result.scalars().all())

        matched: list[AiSearchTask] = []
        for task in candidates:
            if task.category_ids and listing.category_id not in task.category_ids:
                continue
            if _listing_matches_criteria(listing, task.criteria_json):
                matched.append(task)
        return matched

    async def match_exists(self, task_id: int, listing_id: int) -> bool:
        stmt = select(AiSearchMatch.id).where(
            AiSearchMatch.task_id == task_id,
            AiSearchMatch.listing_id == listing_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def record_match(self, task_id: int, listing_id: int) -> AiSearchMatch:
        row = AiSearchMatch(task_id=task_id, listing_id=listing_id)
        self._session.add(row)
        await self._session.flush()
        return row


def _listing_matches_criteria(listing: Listing, criteria: dict[str, Any]) -> bool:
    params = criteria if isinstance(criteria, dict) else {}

    raw_q = params.get("q")
    if raw_q is not None:
        needle = str(raw_q).strip().lower()
        if needle:
            title_l = listing.title.lower()
            desc = (listing.description or "").lower()
            if needle not in title_l and needle not in desc:
                # Also try individual tokens for multi-word queries
                tokens = [t for t in needle.split() if len(t) >= 3]
                if tokens and not any(t in title_l or t in desc for t in tokens):
                    return False

    min_price = params.get("min_price")
    max_price = params.get("max_price")
    if min_price is not None:
        try:
            if listing.price < Decimal(str(min_price)):
                return False
        except Exception:
            pass
    if max_price is not None:
        try:
            if listing.price > Decimal(str(max_price)):
                return False
        except Exception:
            pass

    currency = params.get("currency")
    if currency and str(currency) != listing.currency.value:
        return False

    return True
