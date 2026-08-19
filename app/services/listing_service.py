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
from app.models.enums import Currency, ListingStatus
from app.models.listing import Listing
from app.models.media import Media
from app.repositories.category_repository import CategoryRepository
from app.repositories.listing_repository import ListingRepository
from app.schemas.listing import (
    ListingCreate,
    ListingFeedPage,
    ListingRead,
    ListingStatusUpdate,
    ListingUpdate,
    serialize_listing_fields,
)
from app.services.listing_field_value_service import ListingFieldValueService
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

    async def _attach_placeholder_image(self, listing_id: int) -> None:
        from datetime import UTC, datetime

        self._session.add(
            Media(
                listing_id=listing_id,
                url=PLACEHOLDER_MEDIA_URL,
                order=0,
                is_placeholder=True,
                moderation_status=MediaModerationStatus.approved,
                moderation_reason=None,
                moderated_at=datetime.now(UTC),
            ),
        )
        await self._session.flush()

    async def get_listing(self, listing_id: int) -> ListingRead:
        row = await self._listings.get_by_id(listing_id)
        if row is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)
        return self._to_read(row)

    async def create_listing(
        self,
        data: ListingCreate,
        owner_id: int,
        *,
        known_fields: dict[str, Any] | None = None,
    ) -> ListingRead:
        category = await self._categories.get_by_id(data.category_id)
        if category is None:
            raise EntityNotFoundError("Category", entity_id=data.category_id)

        category_slug = category.slug
        uses_placeholder = data.uses_placeholder_image
        if data.status == ListingStatus.active:
            self._validate_active_publish(
                category_slug=category_slug,
                images=None,
                uses_placeholder=uses_placeholder,
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
        )
        refreshed = await self._listings.create(listing)
        if uses_placeholder and data.status == ListingStatus.active:
            await self._attach_placeholder_image(refreshed.id)
            refreshed = await self._listings.get_by_id(refreshed.id)
            if refreshed is None:
                raise TransactionFailedError("Listing vanished after placeholder attach.")
        payload_fields = known_fields if known_fields is not None else data.fields
        try:
            if payload_fields and self._field_values is not None:
                await self._field_values.replace_from_known_fields(
                    listing_id=refreshed.id,
                    category_id=data.category_id,
                    known_fields=payload_fields,
                )
            if refreshed.status == ListingStatus.active:
                await self._notifications.emit_saved_search_alerts_for_listing(refreshed)
                if self._ai_search is not None:
                    await self._ai_search.emit_matches_for_listing(refreshed)
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
        if "category_id" in payload:
            cat = await self._categories.get_by_id(payload["category_id"])
            if cat is None:
                raise EntityNotFoundError(
                    "Category",
                    entity_id=payload["category_id"],
                )

        updated = await self._listings.update(listing_id, **payload)
        if updated is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)

        try:
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to update listing; transaction rolled back.",
            ) from exc

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
            category = await self._categories.get_by_id(listing.category_id)
            category_slug = category.slug if category else None
            self._validate_active_publish(
                category_slug=category_slug,
                images=list(listing.images or []),
                uses_placeholder=listing.uses_placeholder_image,
            )

        updated = await self._listings.update(listing_id, status=payload.status)
        if updated is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)

        try:
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to change listing status; transaction rolled back.",
            ) from exc

        final = await self._listings.get_by_id(updated.id)
        if final is None:
            raise TransactionFailedError("Listing not found after status update.")

        if target == ListingStatus.active:
            await self._notifications.emit_saved_search_alerts_for_listing(final)
            if self._ai_search is not None:
                await self._ai_search.emit_matches_for_listing(final)
            try:
                await self._session.commit()
            except Exception as exc:
                await self._session.rollback()
                raise TransactionFailedError(
                    "Failed to emit listing alerts; transaction rolled back.",
                ) from exc

        return self._to_read(final)

    async def get_feed(
        self,
        *,
        category_id: int | None = None,
        category_ids: list[int] | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        currency: Currency | None = None,
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
        limit: int = 20,
        offset: int = 0,
    ) -> ListingFeedPage:
        limit = clamp_limit(limit, max_limit=100)
        if q is not None:
            q = q.strip() or None
        if city is not None:
            city = city.strip() or None
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
            min_price=min_price,
            max_price=max_price,
            currency=currency,
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
        )
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
