from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import Numeric, and_, cast, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_agent_policy import MAX_MATCHES_PER_LISTING
from app.core.ai_search_criteria import (
    BRAND_ALIASES,
    MODEL_ALIASES,
    AiSearchCriteria,
    engine_volumes_match,
    models_match,
    normalize_brand,
)
from app.models.ai_enums import AiAgentType
from app.models.ai_search_match import AiSearchMatch
from app.models.ai_search_task import AiSearchTask
from app.models.enums import ListingStatus
from app.models.listing import Listing
from app.models.listing_field_value import ListingFieldValue
from app.repositories.base import BaseRepository
from app.repositories.listing_repository import ListingRepository


class AiSearchTaskRepository(BaseRepository[AiSearchTask]):
    def __init__(
        self,
        session: AsyncSession,
        listings: ListingRepository,
    ) -> None:
        super().__init__(session, AiSearchTask)
        self._listings = listings

    async def deactivate_for_subscription(self, subscription_id: int) -> None:
        stmt = select(AiSearchTask).where(
            AiSearchTask.subscription_id == subscription_id,
            AiSearchTask.is_active.is_(True),
        )
        result = await self._session.execute(stmt)
        for task in result.scalars():
            task.is_active = False

    async def upsert_task(
        self,
        *,
        user_id: int,
        agent_type: AiAgentType,
        subscription_id: int,
        session_id: int,
        criteria: dict[str, Any],
        category_ids: list[int],
        source_text: str,
    ) -> AiSearchTask:
        normalized = AiSearchCriteria.from_dict(criteria).to_dict()
        stmt = (
            select(AiSearchTask)
            .where(
                AiSearchTask.user_id == user_id,
                AiSearchTask.agent_type == agent_type,
                AiSearchTask.is_active.is_(True),
            )
            .order_by(AiSearchTask.id.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        task = result.scalar_one_or_none()
        if task is None:
            task = AiSearchTask(
                user_id=user_id,
                agent_type=agent_type,
                subscription_id=subscription_id,
                session_id=session_id,
                criteria_json=normalized,
                category_ids=category_ids,
                source_text=source_text,
                is_active=True,
            )
            self._session.add(task)
        else:
            task.criteria_json = normalized
            task.category_ids = category_ids
            task.source_text = source_text
            task.subscription_id = subscription_id
            task.session_id = session_id
        await self._session.flush()
        return task

    async def search_listings(
        self,
        criteria: dict[str, Any],
        category_ids: list[int],
        *,
        limit: int = 5,
    ) -> list[Listing]:
        c = AiSearchCriteria.from_dict(criteria)
        return await self._listings.search_listings(
            category_ids=category_ids or None,
            min_price=_dec(c.min_price),
            max_price=_dec(c.max_price),
            city=c.city,
            brand=c.brand,
            model=c.model,
            year_min=c.year_min,
            year_max=c.year_max,
            steering=c.steering,
            engine_volume=c.engine_volume,
            q=c.q,
            status=ListingStatus.active,
            limit=limit,
            offset=0,
        )

    async def list_active_tasks_for_listing(self, listing: Listing) -> list[AiSearchTask]:
        """SQL-narrow candidates (category/price/owner/dedup), then Python field checks."""
        if listing.category_id is None:
            return []

        cat_filter = or_(
            AiSearchTask.category_ids.contains([listing.category_id]),
            AiSearchTask.category_ids == [],
        )

        max_price_expr = AiSearchTask.criteria_json.op("->>")("max_price")
        min_price_expr = AiSearchTask.criteria_json.op("->>")("min_price")
        price_filters = []
        if listing.price is not None:
            price_filters.append(
                or_(
                    max_price_expr.is_(None),
                    max_price_expr == "",
                    cast(max_price_expr, Numeric) >= listing.price,
                )
            )
            price_filters.append(
                or_(
                    min_price_expr.is_(None),
                    min_price_expr == "",
                    cast(min_price_expr, Numeric) <= listing.price,
                )
            )

        owner_filter = True
        if listing.owner_id is not None:
            owner_filter = AiSearchTask.user_id != listing.owner_id

        stmt = (
            select(AiSearchTask)
            .outerjoin(
                AiSearchMatch,
                and_(
                    AiSearchMatch.task_id == AiSearchTask.id,
                    AiSearchMatch.listing_id == listing.id,
                ),
            )
            .where(AiSearchTask.is_active.is_(True))
            .where(cat_filter)
            .where(owner_filter)
            .where(AiSearchMatch.id.is_(None))
            .order_by(AiSearchTask.id.desc())
            .limit(500)
        )
        for pf in price_filters:
            stmt = stmt.where(pf)

        result = await self._session.execute(stmt)
        candidates = list(result.scalars().unique().all())

        out: list[AiSearchTask] = []
        for task in candidates:
            if self._listing_matches_criteria(listing, task):
                out.append(task)
            if len(out) >= MAX_MATCHES_PER_LISTING:
                break
        return out

    async def record_match(self, task_id: int, listing_id: int) -> AiSearchMatch | None:
        match = AiSearchMatch(task_id=task_id, listing_id=listing_id)
        try:
            async with self._session.begin_nested():
                self._session.add(match)
                await self._session.flush()
        except IntegrityError:
            return None
        return match

    def _listing_matches_criteria(self, listing: Listing, task: AiSearchTask) -> bool:
        if listing.status != ListingStatus.active:
            return False
        if task.category_ids and listing.category_id not in task.category_ids:
            return False
        if listing.owner_id is not None and listing.owner_id == task.user_id:
            return False

        criteria = AiSearchCriteria.from_dict(task.criteria_json)
        fields = _field_map(listing)

        city = fields.get("city")
        if criteria.city and city:
            if criteria.city.lower() not in str(city).lower():
                return False
        if criteria.min_price is not None and listing.price is not None:
            if listing.price < Decimal(criteria.min_price):
                return False
        if criteria.max_price is not None and listing.price is not None:
            if listing.price > Decimal(criteria.max_price):
                return False

        q = (criteria.q or "").strip().lower()
        if q:
            hay = f"{listing.title} {listing.description or ''}".lower()
            tokens = [t for t in q.replace(",", " ").split() if len(t) >= 3][:5]
            # Drop tokens that are already covered by structured filters.
            skip = {
                *(criteria.city or "").lower().split(),
                *(criteria.brand or "").split(),
                *(criteria.model or "").replace("-", " ").split(),
                str(criteria.min_price or ""),
                str(criteria.max_price or ""),
                str(criteria.year_min or ""),
                str(criteria.year_max or ""),
                str(criteria.engine_volume or ""),
                "л",
                "литр",
                "литра",
                "литров",
                "ищу",
                "хочу",
                "авто",
            }
            if criteria.brand:
                skip.update(
                    alias
                    for alias, canon in BRAND_ALIASES.items()
                    if canon == criteria.brand
                )
            if criteria.model:
                skip.update(
                    alias
                    for alias, canon in MODEL_ALIASES.items()
                    if canon == criteria.model
                )
            tokens = [t for t in tokens if t not in skip and not t.isdigit()]
            if tokens and not any(t in hay for t in tokens):
                return False

        if criteria.brand:
            actual = normalize_brand(fields.get("brand"))
            if not actual or (
                criteria.brand not in actual and actual not in criteria.brand
            ):
                return False
        if criteria.model:
            if not models_match(criteria.model, fields.get("model")):
                return False
        if criteria.engine_volume:
            volume = fields.get("engine_volume")
            if not engine_volumes_match(criteria.engine_volume, volume):
                return False

        steering_actual = fields.get("steering_side") or fields.get("steering")
        if criteria.steering and steering_actual:
            side = str(steering_actual).lower()
            if criteria.steering == "left" and not (
                "лев" in side or "left" in side
            ):
                return False
            if criteria.steering == "right" and not (
                "прав" in side or "right" in side
            ):
                return False

        year_val = _int(fields.get("year"))
        if criteria.year_min is not None and year_val is not None and year_val < criteria.year_min:
            return False
        if criteria.year_max is not None and year_val is not None and year_val > criteria.year_max:
            return False
        return True


def _field_map(listing: Listing) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for fv in listing.field_values or []:
        if not isinstance(fv, ListingFieldValue):
            continue
        if fv.value_text is not None:
            out[fv.field_key] = fv.value_text
        elif fv.value_int is not None:
            out[fv.field_key] = fv.value_int
        elif fv.value_decimal is not None:
            out[fv.field_key] = fv.value_decimal
        elif fv.ref_brand is not None:
            out[fv.field_key] = fv.ref_brand.name
        elif fv.ref_model is not None:
            out[fv.field_key] = fv.ref_model.name
    return out


def _dec(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
