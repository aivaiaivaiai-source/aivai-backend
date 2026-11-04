from __future__ import annotations

from decimal import Decimal

from sqlalchemy import and_, case, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import Currency, ListingStatus
from app.models.category_enums import VehicleExecution
from app.models.image_moderation_enums import MediaModerationStatus
from app.models.listing import Listing
from app.models.listing_field_value import ListingFieldValue
from app.models.media import Media
from app.models.media_enums import MediaLifecycleStatus
from app.models.vehicle import VehicleBrand, VehicleModel
from app.repositories.base import BaseRepository

_SORT_NEWEST = "newest"
_SORT_PRICE_ASC = "price_asc"
_SORT_PRICE_DESC = "price_desc"


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
                selectinload(Listing.field_values).selectinload(
                    ListingFieldValue.ref_brand
                ),
                selectinload(Listing.field_values).selectinload(
                    ListingFieldValue.ref_model
                ),
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
        vehicle_execution: VehicleExecution | None = None,
        field_attrs: dict[str, str] | None = None,
        job_intent: str | None = None,
        region: str | None = None,
        has_photo: bool | None = None,
    ):
        attrs = dict(field_attrs or {})
        sort_raw = (attrs.pop("sort", None) or "").strip().lower() or None
        # Consume sort from attrs; ordering applied by caller via sort_key.
        _ = sort_raw
        if has_photo is None and "has_photo" in attrs:
            raw_photo = str(attrs.pop("has_photo")).strip().lower()
            if raw_photo in {"1", "true", "yes", "да"}:
                has_photo = True
            elif raw_photo in {"0", "false", "no", "нет"}:
                has_photo = False
        if region is None:
            region = (attrs.pop("region", None) or "").strip() or None
        # Prefer attrs multi-select over legacy single query params when present.
        drive = (attrs.pop("drive", None) or "").strip() or None
        condition = (attrs.pop("condition", None) or "").strip() or None
        needs_investment = (attrs.pop("needs_investment", None) or "").strip() or None
        seller_type = (attrs.pop("seller_type", None) or "").strip() or None
        steering_side = (attrs.pop("steering_side", None) or "").strip() or None

        if category_ids:
            stmt = stmt.where(Listing.category_id.in_(category_ids))
        elif category_id is not None:
            stmt = stmt.where(Listing.category_id == category_id)
        if job_intent is not None:
            # Explicit intent only — NULL legacy rows excluded from both modes.
            stmt = stmt.where(Listing.job_intent == job_intent)
        # Currency V2: price filters compare normalized KGS (caller converts thresholds).
        if min_price is not None:
            stmt = stmt.where(Listing.normalized_price_kgs >= min_price)
        if max_price is not None:
            stmt = stmt.where(Listing.normalized_price_kgs <= max_price)
        # `currency` is reserved for exact listing-currency filter (rare).
        # Search price context uses price_currency → converted thresholds upstream.
        if currency is not None:
            stmt = stmt.where(Listing.currency == currency)
        if owner_id is not None:
            stmt = stmt.where(Listing.owner_id == owner_id)
        if statuses:
            stmt = stmt.where(Listing.status.in_(statuses))
        elif status is not None:
            stmt = stmt.where(Listing.status == status)
        if vehicle_execution is not None:
            stmt = stmt.where(Listing.vehicle_execution == vehicle_execution)
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
        if region:
            region_pat = f"%{region.strip()}%"
            stmt = stmt.where(
                exists(
                    select(ListingFieldValue.id).where(
                        ListingFieldValue.listing_id == Listing.id,
                        ListingFieldValue.field_key == "region",
                        ListingFieldValue.value_text.ilike(region_pat),
                    )
                )
            )
        if has_photo is True:
            stmt = stmt.where(
                exists(
                    select(Media.id).where(
                        Media.listing_id == Listing.id,
                        Media.is_placeholder.is_(False),
                        Media.lifecycle_status == MediaLifecycleStatus.ready,
                        Media.moderation_status == MediaModerationStatus.approved,
                    )
                )
            )
        if has_photo is False:
            stmt = stmt.where(
                ~exists(
                    select(Media.id).where(
                        Media.listing_id == Listing.id,
                        Media.is_placeholder.is_(False),
                        Media.lifecycle_status == MediaLifecycleStatus.ready,
                        Media.moderation_status == MediaModerationStatus.approved,
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
                        ListingFieldValue.field_key.in_(
                            ("brand", "vehicle_brand")
                        ),
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
                        ListingFieldValue.field_key.in_(
                            ("model", "vehicle_model")
                        ),
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
        steer_raw = steering_side or steering
        if steer_raw:
            parts = [p.strip() for p in steer_raw.split("||") if p.strip()]
            if len(parts) == 1:
                side = parts[0].lower()
                if "прав" in side:
                    steer_pat = "%прав%"
                elif "лев" in side:
                    steer_pat = "%лев%"
                else:
                    steer_pat = f"%{parts[0]}%"
                stmt = stmt.where(
                    exists(
                        select(ListingFieldValue.id).where(
                            ListingFieldValue.listing_id == Listing.id,
                            ListingFieldValue.field_key == "steering_side",
                            ListingFieldValue.value_text.ilike(steer_pat),
                        )
                    )
                )
            elif len(parts) > 1:
                stmt = self._filter_option_any(stmt, "steering_side", parts)

        # Legacy single engine_volume string ignored when numeric range attrs present.
        has_engine_range = any(
            k.startswith("engine_volume__") for k in attrs
        )
        if engine_volume and not has_engine_range:
            # Only accept numeric exact liters for Create↔Search parity.
            try:
                vol = Decimal(str(engine_volume).strip().replace(",", "."))
            except Exception:
                vol = None
            if vol is not None:
                stmt = stmt.where(
                    exists(
                        select(ListingFieldValue.id).where(
                            ListingFieldValue.listing_id == Listing.id,
                            ListingFieldValue.field_key == "engine_volume",
                            ListingFieldValue.value_decimal == vol,
                        )
                    )
                )
        stmt = self._filter_option_csv(stmt, "fuel", fuel)
        stmt = self._filter_option_csv(stmt, "transmission", transmission)
        if drive:
            stmt = self._filter_option_csv(stmt, "drive", drive)
        if condition:
            stmt = self._filter_option_csv(stmt, "condition", condition)
        if needs_investment:
            stmt = self._filter_option_csv(stmt, "needs_investment", needs_investment)
        if seller_type:
            stmt = self._filter_option_csv(stmt, "seller_type", seller_type)

        for raw_key, raw_val in attrs.items():
            key = (raw_key or "").strip()
            val = (str(raw_val) if raw_val is not None else "").strip()
            if not key or not val:
                continue
            if key.endswith("__min") or key.endswith("__max"):
                base, side = key.rsplit("__", 1)
                try:
                    num = Decimal(val.replace(",", "."))
                except Exception:
                    continue
                conds = [
                    ListingFieldValue.listing_id == Listing.id,
                    ListingFieldValue.field_key == base,
                ]
                if side == "min":
                    conds.append(
                        or_(
                            ListingFieldValue.value_decimal >= num,
                            ListingFieldValue.value_int >= int(num),
                        )
                    )
                else:
                    conds.append(
                        or_(
                            ListingFieldValue.value_decimal <= num,
                            ListingFieldValue.value_int <= int(num),
                        )
                    )
                stmt = stmt.where(
                    exists(select(ListingFieldValue.id).where(*conds))
                )
                continue
            # Vehicle compatibility stored as brand/model field types (ref IDs).
            if key in ("vehicle_brand", "brand"):
                brand_key = val
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
                            ListingFieldValue.field_key.in_(
                                ("brand", "vehicle_brand")
                            ),
                            or_(
                                VehicleBrand.name.ilike(brand_key),
                                VehicleBrand.slug == brand_slug,
                            ),
                        )
                    )
                )
                continue
            if key in ("vehicle_model", "model"):
                model_key = val
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
                            ListingFieldValue.field_key.in_(
                                ("model", "vehicle_model")
                            ),
                            or_(
                                VehicleModel.name.ilike(model_key),
                                VehicleModel.slug == model_slug,
                            ),
                        )
                    )
                )
                continue
            # OEM / part number: casefold + strip spaces for matching.
            if key in ("part_number", "oem_number"):
                from app.seeds.auto_parts_v2 import normalize_part_number

                needle = normalize_part_number(val)
                if not needle:
                    continue
                # Mirror normalize_part_number in SQL: lower + drop spaces/hyphens.
                normalized_col = func.replace(
                    func.replace(
                        func.lower(ListingFieldValue.value_text), " ", ""
                    ),
                    "-",
                    "",
                )
                stmt = stmt.where(
                    exists(
                        select(ListingFieldValue.id).where(
                            ListingFieldValue.listing_id == Listing.id,
                            ListingFieldValue.field_key.in_(
                                ("part_number", "oem_number")
                            ),
                            or_(
                                ListingFieldValue.value_text.ilike(val),
                                normalized_col == needle,
                            ),
                        )
                    )
                )
                continue
            parts = [part.strip() for part in val.split("||") if part.strip()]
            if not parts:
                continue
            stmt = self._filter_option_any(stmt, key, parts)
        return stmt

    @staticmethod
    def _filter_option_csv(stmt, field_key: str, raw: str | None):
        if not raw:
            return stmt
        parts = [p.strip() for p in raw.split("||") if p.strip()]
        if not parts:
            return stmt
        return ListingRepository._filter_option_any(stmt, field_key, parts)

    @staticmethod
    def _filter_option_any(stmt, field_key: str, parts: list[str]):
        """Match single-value fields OR multi-select ``a||b`` token overlap.

        Search ``passenger`` must find listing ``passenger||cargo``.
        Token boundaries use ``||`` so ``car`` does not match ``cargo``.
        Within one filter key, parts are OR'd (ANY).
        """
        sep = "||"
        clauses = []
        for part in parts:
            # Pad stored value so first/last tokens have boundaries.
            padded = func.concat(sep, ListingFieldValue.value_text, sep)
            token = f"{sep}{part}{sep}"
            clauses.append(
                or_(
                    ListingFieldValue.value_text == part,
                    ListingFieldValue.value_text.ilike(part),
                    padded.like(f"%{token}%"),
                    func.lower(padded).like(func.lower(f"%{token}%")),
                )
            )
        match = or_(*clauses)
        return stmt.where(
            exists(
                select(ListingFieldValue.id).where(
                    ListingFieldValue.listing_id == Listing.id,
                    ListingFieldValue.field_key == field_key,
                    match,
                )
            )
        )

    @staticmethod
    def _order_clause(sort: str | None):
        promo = ListingRepository._effective_promotion_tier().desc()
        key = (sort or _SORT_NEWEST).strip().lower()
        # Currency V2: sort by Backend-owned normalized KGS (snapshot-based).
        if key == _SORT_PRICE_ASC:
            return (
                promo,
                Listing.normalized_price_kgs.asc().nulls_last(),
                Listing.created_at.desc(),
            )
        if key == _SORT_PRICE_DESC:
            return (
                promo,
                Listing.normalized_price_kgs.desc().nulls_last(),
                Listing.created_at.desc(),
            )
        return promo, Listing.created_at.desc()

    @staticmethod
    def _extract_sort(field_attrs: dict[str, str] | None) -> str | None:
        if not field_attrs:
            return None
        raw = field_attrs.get("sort")
        if raw is None:
            return None
        return str(raw).strip().lower() or None

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
        vehicle_execution: VehicleExecution | None = None,
        field_attrs: dict[str, str] | None = None,
        job_intent: str | None = None,
        region: str | None = None,
        has_photo: bool | None = None,
        sort: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Listing]:
        effective_sort = sort or self._extract_sort(field_attrs)
        stmt = (
            select(Listing)
            .options(
                selectinload(Listing.images),
                selectinload(Listing.category),
                selectinload(Listing.field_values).selectinload(
                    ListingFieldValue.ref_brand
                ),
                selectinload(Listing.field_values).selectinload(
                    ListingFieldValue.ref_model
                ),
            )
            .order_by(*self._order_clause(effective_sort))
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
            job_intent=job_intent,
            vehicle_execution=vehicle_execution,
            field_attrs=field_attrs,
            region=region,
            has_photo=has_photo,
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
        vehicle_execution: VehicleExecution | None = None,
        field_attrs: dict[str, str] | None = None,
        job_intent: str | None = None,
        region: str | None = None,
        has_photo: bool | None = None,
        sort: str | None = None,
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
            vehicle_execution=vehicle_execution,
            field_attrs=field_attrs,
            job_intent=job_intent,
            region=region,
            has_photo=has_photo,
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def count_by_owner(self, owner_id: int) -> int:
        stmt = select(func.count(Listing.id)).where(Listing.owner_id == owner_id)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())
