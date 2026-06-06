from __future__ import annotations

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
from app.models.enums import Currency, ListingStatus
from app.models.listing import Listing
from app.models.media import Media
from app.repositories.category_repository import CategoryRepository
from app.repositories.listing_repository import ListingRepository
from app.schemas.listing import ListingCreate, ListingRead, ListingStatusUpdate, ListingUpdate
from app.services.notification_service import NotificationService
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
    ) -> None:
        self._session = session
        self._listings = listing_repository
        self._categories = category_repository
        self._notifications = notification_service

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
        return ListingRead.model_validate(row)

    async def create_listing(self, data: ListingCreate, owner_id: int) -> ListingRead:
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
        try:
            if refreshed.status == ListingStatus.active:
                await self._notifications.emit_saved_search_alerts_for_listing(refreshed)
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to create listing; transaction rolled back.",
            ) from exc

        persisted = await self._listings.get_by_id(refreshed.id)
        if persisted is None:
            raise TransactionFailedError("Listing vanished after creation.")
        return ListingRead.model_validate(persisted)

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
        return ListingRead.model_validate(final)

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
            (ListingStatus.active, ListingStatus.sold),
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
        return ListingRead.model_validate(final)

    async def get_feed(
        self,
        *,
        category_id: int | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        currency: Currency | None = None,
        status: ListingStatus | None = None,
        q: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ListingRead]:
        limit = clamp_limit(limit, max_limit=100)
        if q is not None:
            q = q.strip() or None

        if (
            min_price is not None
            and max_price is not None
            and min_price > max_price
        ):
            raise AppException(
                "min_price cannot be greater than max_price",
                status_code=400,
            )

        rows = await self._listings.search_listings(
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            currency=currency,
            status=status if status is not None else ListingStatus.active,
            q=q,
            limit=limit,
            offset=offset,
        )
        return [ListingRead.model_validate(x) for x in rows]
