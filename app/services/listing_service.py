from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AppException,
    EntityNotFoundError,
    OwnershipError,
    TransactionFailedError,
)
from app.core.pagination import clamp_limit
from app.core.promotion_policy import read_fields as promotion_read_fields
from app.core.config import get_settings
from app.models.enums import Currency, ListingStatus
from app.models.listing import Listing
from app.models.media import Media
from app.models.category_enums import VehicleExecution
from app.models.category_selection_enums import CategorySelectionSource
from app.models.listing_category_resolver_feedback import CategoryResolverFeedbackOutcome
from app.repositories.category_repository import CategoryRepository
from app.repositories.category_resolver_repository import CategoryResolverRepository
from app.repositories.category_resolver_feedback_repository import (
    CategoryResolverFeedbackRepository,
)
from app.repositories.listing_repository import ListingRepository
from app.schemas.listing import (
    ListingCreate,
    ListingFeedPage,
    ListingFacetOptionCount,
    ListingRead,
    ListingStatusUpdate,
    ListingUpdate,
    serialize_listing_fields,
)
from app.services.listing_field_value_service import ListingFieldValueService
from app.services.listing_vehicle_execution import apply_listing_vehicle_execution
from app.services.notification_service import NotificationService
from app.services.ai_search_service import AiSearchService
from app.models.image_moderation_enums import MediaModerationStatus
from app.services.photo_requirement_policy import (
    PLACEHOLDER_MEDIA_URL,
    PUBLISH_BLOCKED_NO_PHOTO,
    can_publish_active,
    count_real_photos,
    validate_images_for_active_publish,
)
from app.services.vehicle_execution import detect_execution_from_text, text_mentions_execution_sensitive_subject
from app.services import fx_service


class ListingService:
    def __init__(
        self,
        session: AsyncSession,
        listing_repository: ListingRepository,
        category_repository: CategoryRepository,
        notification_service: NotificationService,
        field_value_service: ListingFieldValueService | None = None,
        ai_search_service: AiSearchService | None = None,
    ) -> None:
        self._session = session
        self._listings = listing_repository
        self._categories = category_repository
        self._notifications = notification_service
        self._field_values = field_value_service
        self._ai_search = ai_search_service

    @staticmethod
    def _to_read(row: Listing) -> ListingRead:
        read = ListingRead.model_validate(row)
        updates: dict[str, Any] = promotion_read_fields(row, now=datetime.now(UTC))
        raw_fields = row.__dict__.get("field_values")
        if raw_fields:
            updates["fields"] = serialize_listing_fields(raw_fields)
        return read.model_copy(update=updates)

    @staticmethod
    def _ensure_owner(listing: Listing, user_id: int) -> None:
        if listing.owner_id is None or listing.owner_id != user_id:
            raise OwnershipError("You cannot modify another user's listing.")

    @staticmethod
    def _validate_active_publish(
        *,
        category_slug: str | None,
        images: list[Any] | None,
        uses_placeholder: bool,
    ) -> None:
        moderation_block = validate_images_for_active_publish(images)
        if moderation_block:
            raise AppException(moderation_block, status_code=400)
        real_count = count_real_photos(images)
        if can_publish_active(
            category_slug=category_slug,
            real_photo_count=real_count,
            uses_placeholder=uses_placeholder,
            images=images,
        ):
            return
        raise AppException(PUBLISH_BLOCKED_NO_PHOTO, status_code=400)

    @staticmethod
    def _validate_price_contract(
        *,
        category_slug: str | None,
        price: Decimal | None,
        fields: dict[str, Any] | None,
    ) -> None:
        """Services: numeric «Цена от» XOR «По договорённости». Others need price."""
        from app.seeds.services_v2 import SERVICES_NEGOTIATED_VALUE

        slug = (category_slug or "").strip()
        negotiated = (
            str((fields or {}).get("negotiable") or "").strip()
            == SERVICES_NEGOTIATED_VALUE
        )
        has_price = price is not None and Decimal(price) > 0
        if slug.startswith("services-") or slug == "services":
            if has_price or negotiated:
                return
            raise AppException(
                "Укажите «Цена от» или «По договорённости».",
                status_code=400,
            )
        if price is None:
            raise AppException("price is required", status_code=400)

    async def _attach_placeholder_image(self, listing_id: int) -> None:
        from datetime import UTC, datetime

        from app.models.media_enums import MediaLifecycleStatus

        self._session.add(
            Media(
                listing_id=listing_id,
                url=PLACEHOLDER_MEDIA_URL,
                order=0,
                is_placeholder=True,
                lifecycle_status=MediaLifecycleStatus.ready,
                original_url=PLACEHOLDER_MEDIA_URL,
                display_url=PLACEHOLDER_MEDIA_URL,
                moderation_status=MediaModerationStatus.approved,
                moderation_reason=None,
                moderated_at=datetime.now(UTC),
                processed_at=datetime.now(UTC),
            ),
        )
        await self._session.flush()

    async def get_listing(self, listing_id: int) -> ListingRead:
        row = await self._listings.get_by_id(listing_id)
        if row is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)
        return self._to_read(row)

    async def _ensure_publishable_leaf_category(self, category_id: int) -> None:
        """Reject activate/publish on picker-only parents or inactive/retired categories."""
        category = await self._categories.get_by_id(category_id)
        if category is None:
            raise EntityNotFoundError("Category", entity_id=category_id)
        if not category.is_active:
            raise AppException(
                "Категория недоступна для публикации.",
                status_code=400,
            )
        if await self._categories.has_active_children(category_id):
            raise AppException(
                "Выберите конкретную подкатегорию перед публикацией.",
                status_code=400,
            )

    async def create_listing(
        self,
        data: ListingCreate,
        owner_id: int,
        *,
        known_fields: dict[str, Any] | None = None,
    ) -> ListingRead:
        category = None
        category_slug: str | None = None
        if data.category_id is not None:
            category = await self._categories.get_by_id(data.category_id)
            if category is None:
                raise EntityNotFoundError("Category", entity_id=data.category_id)
            category_slug = category.slug
        elif data.status != ListingStatus.draft:
            raise AppException(
                "category_id is required unless listing status is draft.",
                status_code=400,
            )

        uses_placeholder = data.uses_placeholder_image
        # Reject inactive/retired and picker-only parents for any new listing
        # (draft or active). Historical rows on those categories remain readable.
        if data.category_id is not None:
            await self._ensure_publishable_leaf_category(data.category_id)
        if data.status == ListingStatus.active:
            self._validate_active_publish(
                category_slug=category_slug,
                images=None,
                uses_placeholder=uses_placeholder,
            )
            self._validate_price_contract(
                category_slug=category_slug,
                price=data.price,
                fields=data.fields,
            )

        listing = Listing(
            title=data.title,
            description=data.description,
            price=data.price,
            currency=data.currency,
            status=data.status,
            owner_id=owner_id,
            category_id=data.category_id,
            uses_placeholder_image=uses_placeholder,
            vehicle_execution=data.vehicle_execution,
            job_intent=data.job_intent,
        )
        refreshed = await self._listings.create(listing)
        if uses_placeholder and data.status == ListingStatus.active:
            await self._attach_placeholder_image(refreshed.id)
            refreshed = await self._listings.get_by_id(refreshed.id)
            if refreshed is None:
                raise TransactionFailedError("Listing vanished after placeholder attach.")
        payload_fields = known_fields if known_fields is not None else data.fields
        try:
            if (
                payload_fields
                and self._field_values is not None
                and data.category_id is not None
            ):
                await self._field_values.replace_from_known_fields(
                    listing_id=refreshed.id,
                    category_id=data.category_id,
                    known_fields=payload_fields,
                    create_intent=data.job_intent,
                )
            await apply_listing_vehicle_execution(
                self._session,
                refreshed,
                requested=data.vehicle_execution,
                category_slug=category_slug,
                status=data.status,
            )
            if refreshed.status == ListingStatus.active:
                await self._capture_fx_snapshot(refreshed)
                await self._notifications.emit_saved_search_alerts_for_listing(refreshed)
                await self._emit_ai_matches(refreshed)
            await self._session.commit()
        except AppException:
            await self._session.rollback()
            raise
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to create listing; transaction rolled back.",
            ) from exc

        persisted = await self._listings.get_by_id(refreshed.id)
        if persisted is None:
            raise TransactionFailedError("Listing vanished after creation.")
        return self._to_read(persisted)

    async def update_listing(
        self,
        listing_id: int,
        *,
        actor_user_id: int,
        data: ListingUpdate,
    ) -> ListingRead:
        listing = await self._listings.get_by_id(listing_id)
        if listing is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)

        self._ensure_owner(listing, actor_user_id)

        payload = data.model_dump(exclude_unset=True)
        # Client must never supply FX snapshot / normalized — strip if sneaked in.
        payload.pop("exchange_rate_snapshot", None)
        payload.pop("normalized_price_kgs", None)
        known_fields = payload.pop("fields", None)
        requested_execution = payload.pop("vehicle_execution", None)
        execution_in_payload = "vehicle_execution" in data.model_fields_set
        previous_category_id = listing.category_id
        previous_source = listing.category_selection_source
        prev_price = listing.price
        prev_currency = listing.currency
        price_changed = "price" in payload and payload["price"] != prev_price
        currency_changed = (
            "currency" in payload and payload["currency"] != prev_currency
        )
        if "category_id" in payload:
            cat_id = payload["category_id"]
            if cat_id is None:
                if listing.status != ListingStatus.draft:
                    raise AppException(
                        "Cannot clear category_id on a non-draft listing.",
                        status_code=400,
                    )
                payload["category_selection_source"] = None
            else:
                cat = await self._categories.get_by_id(cat_id)
                if cat is None:
                    raise EntityNotFoundError(
                        "Category",
                        entity_id=cat_id,
                    )
                await self._ensure_publishable_leaf_category(cat_id)
                if cat_id != previous_category_id:
                    payload["category_selection_source"] = CategorySelectionSource.manual

        updated = await self._listings.update(listing_id, **payload)
        if updated is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)

        category_id = payload.get("category_id", listing.category_id)
        if (
            known_fields is not None
            and self._field_values is not None
            and category_id is not None
        ):
            await self._field_values.replace_from_known_fields(
                listing_id=listing_id,
                category_id=category_id,
                known_fields=known_fields,
                create_intent=payload.get(
                    "job_intent",
                    updated.job_intent if updated else listing.job_intent,
                ),
            )

        cat_for_exec = None
        if category_id is not None:
            cat_row = await self._categories.get_by_id(category_id)
            cat_for_exec = cat_row.slug if cat_row else None
        exec_requested = (
            requested_execution if execution_in_payload else updated.vehicle_execution
        )
        if known_fields is not None or execution_in_payload or "category_id" in payload:
            await apply_listing_vehicle_execution(
                self._session,
                updated,
                requested=exec_requested,
                category_slug=cat_for_exec,
                status=updated.status,
            )

        category_became_known = (
            previous_category_id is None
            and category_id is not None
        )
        category_changed = (
            previous_category_id is not None
            and category_id is not None
            and previous_category_id != category_id
        )
        if category_became_known:
            from app.services.media_category_processing import (
                enqueue_category_aware_media_for_listing,
            )

            await enqueue_category_aware_media_for_listing(
                self._session,
                listing_id,
            )
        elif category_changed:
            from app.services.media_category_processing import (
                requeue_media_for_category_change,
            )

            await requeue_media_for_category_change(
                self._session,
                listing_id,
                new_category_id=int(category_id),
            )
        elif updated.category_id is not None:
            # Heal A→B→A stuck queued media before publish wait/activate.
            from app.services.media_category_processing import (
                heal_media_lifecycle_for_listing_category,
            )

            await heal_media_lifecycle_for_listing_category(
                self._session,
                listing_id,
            )

        # Currency V2: refresh FX only on explicit price/currency change of active listing.
        if (
            updated.status == ListingStatus.active
            and (price_changed or currency_changed)
        ):
            await self._capture_fx_snapshot(updated)

        try:
            await self._session.commit()
        except AppException:
            await self._session.rollback()
            raise
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to update listing; transaction rolled back.",
            ) from exc

        if category_became_known or category_changed:
            await self._best_effort_dispatch_media_outbox()

        if (
            "category_id" in payload
            and payload.get("category_id") != previous_category_id
            and previous_source == CategorySelectionSource.resolver
        ):
            await self._record_category_correction_feedback(
                listing_id=listing_id,
                previous_category_id=previous_category_id,
                selected_category_id=payload.get("category_id"),
            )

        final = await self._listings.get_by_id(updated.id)
        if final is None:
            raise TransactionFailedError("Listing not found after update.")
        return self._to_read(final)

    async def delete_listing(self, listing_id: int, *, actor_user_id: int) -> None:
        listing = await self._listings.get_by_id(listing_id)
        if listing is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)

        self._ensure_owner(listing, actor_user_id)

        try:
            await self._listings.delete(listing_id)
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to delete listing; transaction rolled back.",
            ) from exc

    async def change_status(
        self,
        listing_id: int,
        *,
        actor_user_id: int,
        payload: ListingStatusUpdate,
    ) -> ListingRead:
        listing = await self._listings.get_by_id(listing_id)
        if listing is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)

        self._ensure_owner(listing, actor_user_id)

        current = listing.status
        target = payload.status
        allowed = {
            (ListingStatus.draft, ListingStatus.active),
            (ListingStatus.active, ListingStatus.draft),  # deactivate
            (ListingStatus.active, ListingStatus.sold),
            (ListingStatus.sold, ListingStatus.active),
            (ListingStatus.sold, ListingStatus.draft),
        }
        if (current, target) not in allowed:
            raise AppException("Invalid status transition", status_code=400)

        if target == ListingStatus.active:
            if listing.category_id is None:
                raise AppException(
                    "category_id is required before publishing.",
                    status_code=400,
                )
            await self._ensure_publishable_leaf_category(listing.category_id)
            category = await self._categories.get_by_id(listing.category_id)
            category_slug = category.slug if category else None
            self._validate_active_publish(
                category_slug=category_slug,
                images=list(listing.images or []),
                uses_placeholder=listing.uses_placeholder_image,
            )
            field_map = serialize_listing_fields(
                list(getattr(listing, "field_values", None) or [])
            )
            self._validate_price_contract(
                category_slug=category_slug,
                price=listing.price,
                fields=field_map,
            )
            from app.services.media_category_processing import (
                enqueue_category_aware_media_for_listing,
            )

            await enqueue_category_aware_media_for_listing(
                self._session,
                listing_id,
            )

        # Currency V2: capture snapshot only on first activation (no snapshot yet).
        # Deactivate→reactivate without price/currency change must NOT refresh.
        # Negotiated Services (price null) may refresh snapshot once; normalized stays null.
        if target == ListingStatus.active and (
            listing.exchange_rate_snapshot is None
            or (listing.price is not None and listing.normalized_price_kgs is None)
        ):
            await self._capture_fx_snapshot(listing)

        updated = await self._listings.update(listing_id, status=payload.status)
        if updated is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)

        try:
            await self._session.commit()
        except AppException:
            await self._session.rollback()
            raise
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to change listing status; transaction rolled back.",
            ) from exc

        await self._best_effort_dispatch_media_outbox()

        final = await self._listings.get_by_id(updated.id)
        if final is None:
            raise TransactionFailedError("Listing not found after status update.")

        if target == ListingStatus.active:
            await self._notifications.emit_saved_search_alerts_for_listing(final)
            await self._emit_ai_matches(final)
            try:
                await self._session.commit()
            except Exception as exc:
                await self._session.rollback()
                raise TransactionFailedError(
                    "Failed to emit listing alerts; transaction rolled back.",
                ) from exc

        return self._to_read(final)

    async def _capture_fx_snapshot(self, listing: Listing) -> None:
        """Require trusted Backend rate; set snapshot + normalized_price_kgs."""
        rate_row = await fx_service.get_current_usd_kgs_rate(self._session)
        fx_service.apply_listing_fx_snapshot(listing, rate=rate_row.rate)
        await self._session.flush()

    @staticmethod
    def _reject_inverted_field_ranges(attrs: dict[str, str]) -> None:
        """Reject generic ``field__min`` > ``field__max`` pairs (area, etc.)."""
        mins: dict[str, Decimal] = {}
        maxs: dict[str, Decimal] = {}
        for key, raw in attrs.items():
            if not key or raw is None:
                continue
            if key.endswith("__min"):
                base = key[: -len("__min")]
                try:
                    mins[base] = Decimal(str(raw).strip().replace(",", "."))
                except Exception:
                    continue
            elif key.endswith("__max"):
                base = key[: -len("__max")]
                try:
                    maxs[base] = Decimal(str(raw).strip().replace(",", "."))
                except Exception:
                    continue
        for base, lo in mins.items():
            hi = maxs.get(base)
            if hi is None:
                continue
            if lo > hi:
                raise AppException(
                    f"{base}__min cannot be greater than {base}__max",
                    status_code=400,
                )

    async def get_feed(
        self,
        *,
        category_id: int | None = None,
        category_ids: list[int] | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        currency: Currency | None = None,
        price_currency: Currency | None = None,
        status: ListingStatus | None = None,
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
        facet_keys: list[str] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> ListingFeedPage:
        limit = clamp_limit(limit, max_limit=100)
        if q is not None:
            q = q.strip() or None
        if city is not None:
            city = city.strip() or None
        if region is not None:
            region = region.strip() or None
        if brand is not None:
            brand = brand.strip() or None
        if model is not None:
            model = model.strip() or None
        if steering is not None:
            steering = steering.strip() or None
        if engine_volume is not None:
            engine_volume = engine_volume.strip() or None
        if fuel is not None:
            fuel = fuel.strip() or None
        if transmission is not None:
            transmission = transmission.strip() or None
        if sort is not None:
            sort = sort.strip().lower() or None

        # General search: "грузовой Sprinter" → filter execution; bare "Sprinter" → both.
        if vehicle_execution is None and q and text_mentions_execution_sensitive_subject(q):
            vehicle_execution = detect_execution_from_text(q)

        if (
            min_price is not None
            and max_price is not None
            and min_price > max_price
        ):
            raise AppException(
                "min_price cannot be greater than max_price",
                status_code=400,
            )
        if (
            year_min is not None
            and year_max is not None
            and year_min > year_max
        ):
            raise AppException(
                "year_min cannot be greater than year_max",
                status_code=400,
            )

        # Rental V2: price range / price sort require rental_price_unit.
        attrs = dict(field_attrs or {})
        self._reject_inverted_field_ranges(attrs)
        rental_unit = (attrs.get("rental_price_unit") or "").strip()
        wants_price = min_price is not None or max_price is not None
        sort_key = (sort or attrs.get("sort") or "").strip().lower()
        wants_price_sort = sort_key in {"price_asc", "price_desc"}
        rental_cat = False
        check_ids = list(category_ids or [])
        if category_id is not None:
            check_ids.append(category_id)
        if check_ids and (wants_price or wants_price_sort):
            from sqlalchemy import select
            from app.models.category import Category

            rows = (
                await self._session.execute(
                    select(Category.slug).where(Category.id.in_(check_ids))
                )
            ).scalars().all()
            rental_cat = any(
                (s or "").startswith("transport-rental-") for s in rows
            )
        if rental_cat and wants_price and not rental_unit:
            raise AppException(
                "Rental price filter requires rental_price_unit",
                status_code=400,
                code="RENTAL_PRICE_UNIT_REQUIRED",
            )
        if rental_cat and wants_price_sort and not rental_unit:
            raise AppException(
                "Rental price sort requires rental_price_unit",
                status_code=400,
                code="RENTAL_PRICE_UNIT_REQUIRED",
            )

        # Currency V2: interpret min/max in price_currency (legacy: currency) → normalized KGS.
        # Do NOT filter by Listing.currency for Search price context.
        filter_price_currency = price_currency or currency or Currency.KGS
        listing_currency_filter: Currency | None = None
        norm_min = min_price
        norm_max = max_price
        if wants_price:
            if filter_price_currency == Currency.USD:
                rate_row = await fx_service.get_current_usd_kgs_rate(self._session)
                rate = fx_service.validate_rate(rate_row.rate)
                if norm_min is not None:
                    norm_min = fx_service.quantize_money(Decimal(str(norm_min)) * rate)
                if norm_max is not None:
                    norm_max = fx_service.quantize_money(Decimal(str(norm_max)) * rate)
            elif filter_price_currency != Currency.KGS:
                raise AppException(
                    f"Unsupported price_currency: {filter_price_currency}",
                    status_code=400,
                )

        # Public GET /listings is a marketplace feed — never list drafts.
        if status == ListingStatus.draft:
            raise AppException(
                "Draft listings are not available in the public feed",
                status_code=400,
                code="INVALID_FEED_STATUS",
            )
        effective_status = status if status is not None else ListingStatus.active
        filter_kwargs = dict(
            category_id=category_id,
            category_ids=category_ids,
            min_price=norm_min,
            max_price=norm_max,
            currency=listing_currency_filter,
            status=effective_status,
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
            sort=sort,
        )
        total = await self._listings.count_listings(**filter_kwargs)
        rows = await self._listings.search_listings(
            **filter_kwargs,
            limit=limit,
            offset=offset,
        )
        facets_out = None
        if facet_keys:
            facet_filter_kwargs = {
                k: v for k, v in filter_kwargs.items() if k != "sort"
            }
            raw = await self._listings.facet_counts(
                facet_keys=facet_keys,
                **facet_filter_kwargs,
            )
            facets_out = {
                k: [
                    ListingFacetOptionCount(value=v, count=c)
                    for v, c in pairs
                ]
                for k, pairs in raw.items()
            }
        return ListingFeedPage(
            items=[self._to_read(x) for x in rows],
            total=total,
            facets=facets_out,
        )

    async def get_mine(
        self,
        *,
        owner_id: int,
        status: ListingStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> ListingFeedPage:
        """Owner cabinet — any status, including drafts."""
        limit = clamp_limit(limit, max_limit=100)
        filter_kwargs: dict = {"owner_id": owner_id}
        if status is not None:
            filter_kwargs["status"] = status
        else:
            filter_kwargs["statuses"] = [
                ListingStatus.active,
                ListingStatus.draft,
                ListingStatus.sold,
            ]
        total = await self._listings.count_listings(**filter_kwargs)
        rows = await self._listings.search_listings(
            **filter_kwargs,
            limit=limit,
            offset=offset,
        )
        return ListingFeedPage(
            items=[self._to_read(x) for x in rows],
            total=total,
        )

    async def _record_category_correction_feedback(
        self,
        *,
        listing_id: int,
        previous_category_id: int | None,
        selected_category_id: int | None,
    ) -> None:
        resolver_repo = CategoryResolverRepository(self._session)
        feedback_repo = CategoryResolverFeedbackRepository(self._session)
        latest = await resolver_repo.get_latest_for_listing(listing_id)
        await feedback_repo.record(
            listing_id=listing_id,
            suggested_category_id=previous_category_id or (
                latest.suggested_category_id if latest else None
            ),
            selected_category_id=selected_category_id,
            outcome=CategoryResolverFeedbackOutcome.corrected,
            resolver_result_id=latest.id if latest else None,
            resolver_version=latest.resolver_version if latest else None,
        )

    async def _emit_ai_matches(self, listing: Listing) -> None:
        """Enqueue match work so publish HTTP path stays fast."""
        if self._ai_search is None:
            return
        from app.services.ai_match_queue import enqueue_listing_for_ai_match

        await enqueue_listing_for_ai_match(listing.id)

    async def _best_effort_dispatch_media_outbox(self) -> None:
        try:
            from app.core.redis import get_redis, redis_available
            from app.db.session import async_session_maker
            from app.media_queue.outbox_dispatcher import dispatch_pending_outbox

            if not redis_available():
                return
            client = get_redis()
            if client is None:
                return
            async with async_session_maker() as session:
                await dispatch_pending_outbox(session, client, get_settings())
                await session.commit()
        except Exception:
            logger = __import__("logging").getLogger(__name__)
            logger.exception("media_outbox_dispatch_failed_after_category")

