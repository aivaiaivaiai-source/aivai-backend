from __future__ import annotations

from decimal import Decimal

from sqlalchemy import and_, case, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import Currency, ListingStatus
from app.models.listing import Listing
from app.models.listing_field_value import ListingFieldValue
from app.models.vehicle import VehicleBrand, VehicleModel
from app.repositories.base import BaseRepository


class ListingRepository(BaseRepository[Listing]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Listing)

    async def get_by_id(self, entity_id: int, *, for_update: bool = False) -> Listing | None:
        stmt = (
            select(Listing)
            .where(Listing.id == entity_id)
            .options(
                selectinload(Listing.images),
                selectinload(Listing.category),
                selectinload(Listing.field_values),
            )
        )
        if for_update:
            stmt = stmt.with_for_update()
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _effective_promotion_tier():
        """Query-time rank: expired windows count as free (tier 0)."""
        return case(
            (
                and_(
                    Listing.is_promoted.is_(True),
                    Listing.promotion_ends_at.is_not(None),
                    Listing.promotion_ends_at > func.now(),
                ),
                Listing.promotion_tier,
            ),
            else_=0,
        )

    def _apply_search_filters(
        self,
        stmt,
        *,
        category_id: int | None = None,
        category_ids: list[int] | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        currency: Currency | None = None,
        status: ListingStatus | None = None,
        statuses: list[ListingStatus] | None = None,
        owner_id: int | None = None,
        q: str | None = None,
        city: str | None = None,
        brand: str | None = None,
        model: str | None = None,
        year_min: int | None = None,
        year_max: int | None = None,
        steering: str | None = None,
        engine_volume: str | None = None,
        fuel: str | None = None,
        transmission: str | None = None,
    ):
        if category_ids:
            stmt = stmt.where(Listing.category_id.in_(category_ids))
        elif category_id is not None:
            stmt = stmt.where(Listing.category_id == category_id)
        if min_price is not None:
            stmt = stmt.where(Listing.price >= min_price)
        if max_price is not None:
            stmt = stmt.where(Listing.price <= max_price)
        if currency is not None:
            stmt = stmt.where(Listing.currency == currency)
        if owner_id is not None:
            stmt = stmt.where(Listing.owner_id == owner_id)
        if statuses:
            stmt = stmt.where(Listing.status.in_(statuses))
        elif status is not None:
            stmt = stmt.where(Listing.status == status)
        if q:
            pattern = f"%{q}%"
            stmt = stmt.where(
                or_(
                    Listing.title.ilike(pattern),
                    Listing.description.ilike(pattern),
                )
            )
        if city:
            city_pat = f"%{city.strip()}%"
            stmt = stmt.where(
                exists(
                    select(ListingFieldValue.id).where(
                        ListingFieldValue.listing_id == Listing.id,
                        ListingFieldValue.field_key == "city",
                        ListingFieldValue.value_text.ilike(city_pat),
                    )
                )
            )
        if brand:
            brand_key = brand.strip()
            brand_slug = brand_key.lower().replace(" ", "-")
            stmt = stmt.where(
                exists(
                    select(ListingFieldValue.id)
                    .join(
                        VehicleBrand,
                        ListingFieldValue.ref_brand_id == VehicleBrand.id,
                    )
                    .where(
                        ListingFieldValue.listing_id == Listing.id,
                        ListingFieldValue.field_key == "brand",
                        or_(
                            VehicleBrand.name.ilike(brand_key),
                            VehicleBrand.slug == brand_slug,
                        ),
                    )
                )
            )
        if model:
            model_key = model.strip()
            model_slug = model_key.lower().replace(" ", "-")
            stmt = stmt.where(
                exists(
                    select(ListingFieldValue.id)
                    .join(
                        VehicleModel,
                        ListingFieldValue.ref_model_id == VehicleModel.id,
                    )
                    .where(
                        ListingFieldValue.listing_id == Listing.id,
                        ListingFieldValue.field_key == "model",
                        or_(
                            VehicleModel.name.ilike(model_key),
                            VehicleModel.slug == model_slug,
                        ),
                    )
                )
            )
        if year_min is not None or year_max is not None:
            year_conds = [
                ListingFieldValue.listing_id == Listing.id,
                ListingFieldValue.field_key == "year",
            ]
            if year_min is not None:
                year_conds.append(ListingFieldValue.value_int >= year_min)
            if year_max is not None:
                year_conds.append(ListingFieldValue.value_int <= year_max)
            stmt = stmt.where(exists(select(ListingFieldValue.id).where(*year_conds)))
        if steering:
            side = steering.strip().lower()
            if "прав" in side:
                steer_pat = "%прав%"
            elif "лев" in side:
                steer_pat = "%лев%"
            else:
                steer_pat = f"%{steering.strip()}%"
            stmt = stmt.where(
                exists(
                    select(ListingFieldValue.id).where(
                        ListingFieldValue.listing_id == Listing.id,
                        ListingFieldValue.field_key == "steering_side",
                        ListingFieldValue.value_text.ilike(steer_pat),
                    )
                )
            )
        stmt = self._filter_text_field(stmt, "engine_volume", engine_volume)
        stmt = self._filter_text_field(stmt, "fuel", fuel)
        stmt = self._filter_text_field(stmt, "transmission", transmission)
        return stmt

    @staticmethod
    def _filter_text_field(stmt, field_key: str, raw: str | None):
        if not raw:
            return stmt
        value = raw.strip()
        if not value:
            return stmt
        return stmt.where(
            exists(
                select(ListingFieldValue.id).where(
                    ListingFieldValue.listing_id == Listing.id,
                    ListingFieldValue.field_key == field_key,
                    ListingFieldValue.value_text.ilike(value),
                )
            )
        )

    async def search_listings(
        self,
        *,
        category_id: int | None = None,
        category_ids: list[int] | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        currency: Currency | None = None,
        status: ListingStatus | None = None,
        statuses: list[ListingStatus] | None = None,
        owner_id: int | None = None,
        q: str | None = None,
        city: str | None = None,
        brand: str | None = None,
        model: str | None = None,
        year_min: int | None = None,
        year_max: int | None = None,
        steering: str | None = None,
        engine_volume: str | None = None,
        fuel: str | None = None,
        transmission: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Listing]:
        stmt = (
            select(Listing)
            .options(
                selectinload(Listing.images),
                selectinload(Listing.category),
                selectinload(Listing.field_values),
            )
            .order_by(
                ListingRepository._effective_promotion_tier().desc(),
                Listing.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        stmt = self._apply_search_filters(
            stmt,
            category_id=category_id,
            category_ids=category_ids,
            min_price=min_price,
            max_price=max_price,
            currency=currency,
            status=status,
            statuses=statuses,
            owner_id=owner_id,
            q=q,
            city=city,
            brand=brand,
            model=model,
            year_min=year_min,
            year_max=year_max,
            steering=steering,
            engine_volume=engine_volume,
            fuel=fuel,
            transmission=transmission,
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().unique().all())

    async def count_listings(
        self,
        *,
        category_id: int | None = None,
        category_ids: list[int] | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        currency: Currency | None = None,
        status: ListingStatus | None = None,
        statuses: list[ListingStatus] | None = None,
        owner_id: int | None = None,
        q: str | None = None,
        city: str | None = None,
        brand: str | None = None,
        model: str | None = None,
        year_min: int | None = None,
        year_max: int | None = None,
        steering: str | None = None,
        engine_volume: str | None = None,
        fuel: str | None = None,
        transmission: str | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(Listing)
        stmt = self._apply_search_filters(
            stmt,
            category_id=category_id,
            category_ids=category_ids,
            min_price=min_price,
            max_price=max_price,
            currency=currency,
            status=status,
            statuses=statuses,
            owner_id=owner_id,
            q=q,
            city=city,
            brand=brand,
            model=model,
            year_min=year_min,
            year_max=year_max,
            steering=steering,
            engine_volume=engine_volume,
            fuel=fuel,
            transmission=transmission,
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def count_by_owner(self, owner_id: int) -> int:
        stmt = select(func.count(Listing.id)).where(Listing.owner_id == owner_id)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())
