from decimal import Decimal
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_listing_service, get_promotion_service
from app.core.constants import MAX_LIMIT
from app.core.rate_limit import LISTING_CREATE_LIMITER
from app.models.enums import Currency, ListingStatus
from app.models.category_enums import VehicleExecution
from app.models.job_create_intent import VALID_JOB_CREATE_INTENTS
from app.repositories.category_repository import CategoryRepository
from app.schemas.listing import (
    ListingCreate,
    ListingFeedPage,
    ListingRead,
    ListingStatusUpdate,
    ListingUpdate,
    PromotionActivate,
    PromotionStopRead,
)
from app.schemas.user import UserRead
from app.services.listing_service import ListingService
from app.services.promotion_service import PromotionService
from app.services.vehicle_execution import parse_execution

router = APIRouter()

# Mobile «Продажа авто» canonical slug (Phase 1 transport canonicalization).
_CAR_SALE_SLUGS = ("transport-car-sale",)


async def _enforce_listing_create_rate_limit(
    user: UserRead = Depends(get_current_user),
) -> None:
    await LISTING_CREATE_LIMITER.hit(f"listing_create:{user.id}")


async def _resolve_category_ids(
    *,
    category_id: int | None,
    category_slug: str | None,
    session: AsyncSession,
) -> list[int] | None:
    if category_id is not None:
        return [category_id]
    if not category_slug:
        return None
    categories = CategoryRepository(session)
    slug = category_slug.strip()
    slugs = list(_CAR_SALE_SLUGS) if slug in _CAR_SALE_SLUGS else [slug]
    ids: list[int] = []
    for s in slugs:
        row = await categories.get_by_slug(s)
        if row is not None:
            ids.append(row.id)
    return ids or None


@router.get("", response_model=ListingFeedPage)
async def get_feed(
    service: ListingService = Depends(get_listing_service),
    session: AsyncSession = Depends(get_db),
    q: str | None = Query(default=None),
    category_id: int | None = Query(default=None),
    category_slug: str | None = Query(default=None),
    category_ids: str | None = Query(
        default=None,
        description="Optional comma-separated category IDs (Package B property counts).",
    ),
    city: str | None = Query(default=None),
    region: str | None = Query(default=None),
    brand: str | None = Query(default=None),
    model: str | None = Query(default=None),
    year_min: int | None = Query(default=None, ge=1900, le=2100),
    year_max: int | None = Query(default=None, ge=1900, le=2100),
    steering: str | None = Query(default=None),
    engine_volume: str | None = Query(default=None),
    fuel: str | None = Query(default=None),
    transmission: str | None = Query(default=None),
    vehicle_execution: str | None = Query(
        default=None,
        description="Filter by listing execution: cargo | passenger",
    ),
    attrs: str | None = Query(
        default=None,
        description=(
            'JSON object of dynamic field filters, e.g. '
            '{"drive":"Полный","engine_volume__min":"2.0","has_photo":"true","sort":"price_asc"}'
        ),
    ),
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    currency: Currency | None = Query(
        default=None,
        description="Legacy alias for price_currency when filtering by min/max.",
    ),
    price_currency: Currency | None = Query(
        default=None,
        description="Currency of min_price/max_price (KGS|USD). Converted via current FX.",
    ),
    has_photo: bool | None = Query(default=None),
    sort: str | None = Query(
        default=None,
        description="newest | price_asc | price_desc",
    ),
    status: ListingStatus | None = Query(
        default=None,
        description=(
            "Public home/search feed. Omitted = active only. "
            "draft is never listed."
        ),
    ),
    job_intent: str | None = Query(
        default=None,
        description="Jobs Search V2: hiring | job_seeking. Optional; ignored when omitted.",
    ),
    facets: str | None = Query(
        default=None,
        description=(
            "Optional comma-separated facet field keys, e.g. "
            "deal_type,rooms,district,_category. "
            "Omitted = no aggregation (backward compatible)."
        ),
    ),
    limit: int = Query(default=20, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
) -> ListingFeedPage:
    if job_intent is not None and job_intent not in VALID_JOB_CREATE_INTENTS:
        raise HTTPException(
            status_code=400,
            detail="job_intent must be hiring or job_seeking",
        )
    resolved_category_ids = await _resolve_category_ids(
        category_id=category_id,
        category_slug=category_slug,
        session=session,
    )
    if category_ids:
        parsed_ids: list[int] = []
        for part in category_ids.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                parsed_ids.append(int(part))
            except ValueError:
                continue
        if parsed_ids:
            resolved_category_ids = parsed_ids
    execution: VehicleExecution | None = parse_execution(vehicle_execution)
    field_attrs: dict[str, str] | None = None
    if attrs:
        try:
            parsed = json.loads(attrs)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            field_attrs = {
                str(k): str(v)
                for k, v in parsed.items()
                if k is not None and v is not None and str(v).strip()
            } or None
    facet_keys: list[str] | None = None
    if facets:
        facet_keys = [
            p.strip()
            for p in facets.split(",")
            if p is not None and str(p).strip()
        ] or None
        # Whitelist-ish: reject empty / overly long keys (no SQL injection path —
        # keys are bound as ORM parameters, never interpolated into SQL).
        if facet_keys is not None:
            cleaned: list[str] = []
            for k in facet_keys:
                if len(k) > 64:
                    continue
                if not all(ch.isalnum() or ch in ("_", "-") for ch in k):
                    continue
                cleaned.append(k)
            facet_keys = cleaned or None
    return await service.get_feed(
        q=q,
        category_id=None if resolved_category_ids else category_id,
        category_ids=resolved_category_ids,
        city=city,
        region=region,
        brand=brand,
        model=model,
        year_min=year_min,
        year_max=year_max,
        steering=steering,
        engine_volume=engine_volume,
        fuel=fuel,
        transmission=transmission,
        vehicle_execution=execution,
        field_attrs=field_attrs,
        min_price=min_price,
        max_price=max_price,
        currency=currency,
        price_currency=price_currency,
        status=status,
        job_intent=job_intent,
        has_photo=has_photo,
        sort=sort,
        facet_keys=facet_keys,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=ListingRead, status_code=201)
async def create_listing(
    body: ListingCreate,
    service: ListingService = Depends(get_listing_service),
    user: UserRead = Depends(get_current_user),
    _: None = Depends(_enforce_listing_create_rate_limit),
) -> ListingRead:
    # Public create is always a draft. Activation (and later moderation)
    # goes through PATCH /listings/{id}/status after photos are uploaded.
    draft = body.model_copy(update={"status": ListingStatus.draft})
    return await service.create_listing(
        draft,
        owner_id=user.id,
        known_fields=draft.fields or None,
    )


@router.get("/mine", response_model=ListingFeedPage)
async def get_my_listings(
    service: ListingService = Depends(get_listing_service),
    user: UserRead = Depends(get_current_user),
    status: ListingStatus | None = Query(
        default=None,
        description="Optional filter. Omitted = active + draft + sold.",
    ),
    limit: int = Query(default=40, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
) -> ListingFeedPage:
    return await service.get_mine(
        owner_id=user.id,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get("/{listing_id}", response_model=ListingRead)
async def read_listing(
    listing_id: int,
    service: ListingService = Depends(get_listing_service),
) -> ListingRead:
    return await service.get_listing(listing_id)


@router.patch("/{listing_id}", response_model=ListingRead)
async def patch_listing(
    listing_id: int,
    body: ListingUpdate,
    service: ListingService = Depends(get_listing_service),
    user: UserRead = Depends(get_current_user),
) -> ListingRead:
    return await service.update_listing(listing_id, actor_user_id=user.id, data=body)


@router.delete("/{listing_id}", status_code=204)
async def delete_listing(
    listing_id: int,
    service: ListingService = Depends(get_listing_service),
    user: UserRead = Depends(get_current_user),
) -> None:
    await service.delete_listing(listing_id, actor_user_id=user.id)


@router.patch("/{listing_id}/status", response_model=ListingRead)
async def patch_listing_status(
    listing_id: int,
    body: ListingStatusUpdate,
    service: ListingService = Depends(get_listing_service),
    user: UserRead = Depends(get_current_user),
) -> ListingRead:
    return await service.change_status(
        listing_id,
        actor_user_id=user.id,
        payload=body,
    )


@router.post("/{listing_id}/promotion", response_model=ListingRead)
async def activate_promotion(
    listing_id: int,
    body: PromotionActivate,
    service: PromotionService = Depends(get_promotion_service),
    user: UserRead = Depends(get_current_user),
) -> ListingRead:
    return await service.activate(
        listing_id,
        actor_user_id=user.id,
        daily_rate=body.daily_rate,
        days=body.days,
    )


@router.post("/{listing_id}/promotion/stop", response_model=PromotionStopRead)
async def stop_promotion(
    listing_id: int,
    service: PromotionService = Depends(get_promotion_service),
    user: UserRead = Depends(get_current_user),
) -> PromotionStopRead:
    return await service.stop(listing_id, actor_user_id=user.id)
