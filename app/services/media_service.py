from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AppException,
    EntityNotFoundError,
    OwnershipError,
    TransactionFailedError,
)
from app.models.image_moderation_enums import MediaModerationStatus
from app.models.listing import Listing
from app.models.media import Media
from app.repositories.listing_repository import ListingRepository
from app.repositories.media_repository import MediaRepository
from app.schemas.media import MediaRead, MediaReorderRequest
from app.services.image_moderation_pipeline import ImageModerationPipeline
from app.services.storage_service import StorageService

_MAX_IMAGES_PER_LISTING = 10


class MediaService:
    def __init__(
        self,
        session: AsyncSession,
        media_repository: MediaRepository,
        listing_repository: ListingRepository,
        storage: StorageService,
        *,
        moderation_pipeline: ImageModerationPipeline | None = None,
    ) -> None:
        self._session = session
        self._media = media_repository
        self._listings = listing_repository
        self._storage = storage
        self._moderation_pipeline = moderation_pipeline

    @staticmethod
    def _ensure_owner(listing: Listing, user_id: int) -> None:
        if listing.owner_id is None or listing.owner_id != user_id:
            raise OwnershipError("You cannot modify another user's listing.")

    async def add_images(
        self,
        listing_id: int,
        *,
        actor_user_id: int,
        payloads: list[tuple[bytes, str] | tuple[bytes, str, str | None]],
    ) -> list[MediaRead]:
        if not payloads:
            raise AppException("At least one file is required.", status_code=400)

        listing = await self._listings.get_by_id(listing_id)
        if listing is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)
        self._ensure_owner(listing, actor_user_id)

        existing = await self._media.list_by_listing(listing_id)
        if len(existing) + len(payloads) > _MAX_IMAGES_PER_LISTING:
            raise AppException(
                f"A listing may have at most {_MAX_IMAGES_PER_LISTING} images.",
                status_code=400,
            )

        next_order_base = max((m.order for m in existing), default=-1) + 1
        pipeline = self._moderation_pipeline
        if pipeline is None:
            raise AppException("Image moderation pipeline is not configured.", status_code=503)

        saved_urls: list[str] = []
        try:
            created_rows: list[Media] = []
            for idx, item in enumerate(payloads):
                if len(item) == 3:
                    content, content_type, source_name = item
                else:
                    content, content_type = item  # type: ignore[misc]
                    source_name = None

                url = self._storage.save_image(content, content_type)
                saved_urls.append(url)
                row = Media(
                    url=url,
                    listing_id=listing_id,
                    order=next_order_base + idx,
                    moderation_status=MediaModerationStatus.pending,
                )
                created = await self._media.create(row)
                await pipeline.process_existing_media(
                    created,
                    content=content,
                    content_type=content_type,
                    source_name=source_name,
                )
                refreshed = await self._media.get_by_id(created.id)
                if refreshed is not None:
                    created_rows.append(refreshed)

            await self._session.commit()
            return [MediaRead.model_validate(m) for m in created_rows]
        except AppException:
            await self._session.rollback()
            for u in saved_urls:
                self._storage.delete_file(u)
            raise
        except Exception as exc:
            await self._session.rollback()
            for u in saved_urls:
                self._storage.delete_file(u)
            raise TransactionFailedError(
                "Failed to add images; transaction rolled back.",
            ) from exc

    async def delete_image(self, image_id: int, *, actor_user_id: int) -> None:
        media = await self._media.get_by_id(image_id)
        if media is None:
            raise EntityNotFoundError("Media", entity_id=image_id)

        listing = await self._listings.get_by_id(media.listing_id)
        if listing is None:
            raise EntityNotFoundError("Listing", entity_id=media.listing_id)
        self._ensure_owner(listing, actor_user_id)

        stored_url = media.url
        try:
            await self._media.delete(image_id)
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to delete image; transaction rolled back.",
            ) from exc

        try:
            self._storage.delete_file(stored_url)
        except Exception:
            raise AppException(
                "Image removed from the database but the file could not be deleted.",
                status_code=503,
            )

    async def reorder_images(
        self,
        listing_id: int,
        *,
        actor_user_id: int,
        body: MediaReorderRequest,
    ) -> list[MediaRead]:
        listing = await self._listings.get_by_id(listing_id)
        if listing is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)
        self._ensure_owner(listing, actor_user_id)

        existing = await self._media.list_by_listing(listing_id)
        existing_ids = {m.id for m in existing}
        passed_ids = body.image_ids
        if len(passed_ids) != len(set(passed_ids)):
            raise AppException("Duplicate image_ids are not allowed.", status_code=400)
        if set(passed_ids) != existing_ids:
            raise AppException(
                "image_ids must list every image for this listing exactly once.",
                status_code=400,
            )

        try:
            await self._media.update_order(listing_id, passed_ids)
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to reorder images; transaction rolled back.",
            ) from exc

        refreshed = await self._media.list_by_listing(listing_id)
        id_order = {mid: pos for pos, mid in enumerate(passed_ids)}
        refreshed.sort(key=lambda m: id_order[m.id])
        return [MediaRead.model_validate(m) for m in refreshed]
