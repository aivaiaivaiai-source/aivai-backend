from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import (
    AppException,
    EntityNotFoundError,
    OwnershipError,
    TransactionFailedError,
)
from app.models.image_moderation_enums import MediaModerationStatus
from app.models.listing import Listing
from app.models.media import Media
from app.models.media_enums import MediaLifecycleStatus
from app.repositories.listing_repository import ListingRepository
from app.repositories.media_repository import MediaRepository
from app.schemas.media import MediaRead, MediaReorderRequest
from app.services.focus_bbox_service import FocusBBoxService
from app.services.image_moderation_pipeline import ImageModerationPipeline
from app.services.media_lifecycle import (
    LEGACY_SYNC_PIPELINE_VERSION,
    lifecycle_after_upload,
)
from app.services.storage_service import StorageService
from app.storage.keys import listing_original_key

logger = logging.getLogger(__name__)

_MAX_IMAGES_PER_LISTING = 9
# Temporary placeholder until blob put succeeds (never committed as final URL).
_PENDING_URL = "/media/.pending"


@dataclass(frozen=True)
class ListingMediaUploadItem:
    content: bytes
    content_type: str
    source_name: str | None = None
    client_upload_id: UUID | None = None


class MediaService:
    def __init__(
        self,
        session: AsyncSession,
        media_repository: MediaRepository,
        listing_repository: ListingRepository,
        storage: StorageService,
        *,
        moderation_pipeline: ImageModerationPipeline | None = None,
        focus_bbox_service: FocusBBoxService | None = None,
    ) -> None:
        self._session = session
        self._media = media_repository
        self._listings = listing_repository
        self._storage = storage
        self._moderation_pipeline = moderation_pipeline
        self._focus_bbox_service = focus_bbox_service

    @staticmethod
    def _ensure_owner(listing: Listing, user_id: int) -> None:
        if listing.owner_id is None or listing.owner_id != user_id:
            raise OwnershipError("You cannot modify another user's listing.")

    @staticmethod
    def _content_sha256(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def _normalize_items(
        payloads: list[
            tuple[bytes, str]
            | tuple[bytes, str, str | None]
            | tuple[bytes, str, str | None, str | None]
            | ListingMediaUploadItem
        ],
    ) -> list[ListingMediaUploadItem]:
        items: list[ListingMediaUploadItem] = []
        for entry in payloads:
            if isinstance(entry, ListingMediaUploadItem):
                items.append(entry)
                continue
            if len(entry) == 2:
                content, content_type = entry  # type: ignore[misc]
                items.append(
                    ListingMediaUploadItem(content=content, content_type=content_type),
                )
            elif len(entry) == 3:
                content, content_type, source_name = entry  # type: ignore[misc]
                items.append(
                    ListingMediaUploadItem(
                        content=content,
                        content_type=content_type,
                        source_name=source_name,
                    ),
                )
            else:
                content, content_type, source_name, raw_client_id = entry  # type: ignore[misc]
                client_upload_id = None
                if raw_client_id:
                    try:
                        client_upload_id = UUID(str(raw_client_id))
                    except ValueError as exc:
                        raise AppException(
                            "client_upload_id must be a valid UUID.",
                            status_code=400,
                        ) from exc
                items.append(
                    ListingMediaUploadItem(
                        content=content,
                        content_type=content_type,
                        source_name=source_name,
                        client_upload_id=client_upload_id,
                    ),
                )
        return items

    async def add_images(
        self,
        listing_id: int,
        *,
        actor_user_id: int,
        payloads: list[
            tuple[bytes, str]
            | tuple[bytes, str, str | None]
            | tuple[bytes, str, str | None, str | None]
            | ListingMediaUploadItem
        ],
    ) -> list[MediaRead]:
        if not payloads:
            raise AppException("At least one file is required.", status_code=400)

        listing = await self._listings.get_by_id(listing_id)
        if listing is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)
        self._ensure_owner(listing, actor_user_id)

        items = self._normalize_items(payloads)
        seen_client_ids: set[UUID] = set()
        for item in items:
            if item.client_upload_id is None:
                continue
            if item.client_upload_id in seen_client_ids:
                raise AppException(
                    "Duplicate client_upload_id in the same request.",
                    status_code=400,
                )
            seen_client_ids.add(item.client_upload_id)

        existing = await self._media.list_by_listing(listing_id)
        idempotent_hits: list[Media] = []
        new_items: list[ListingMediaUploadItem] = []
        for item in items:
            if item.client_upload_id is None:
                new_items.append(item)
                continue
            hit = await self._media.get_by_listing_and_client_upload_id(
                listing_id,
                item.client_upload_id,
            )
            if hit is not None:
                content_hash = self._content_sha256(item.content)
                if hit.content_sha256 and hit.content_sha256 != content_hash:
                    raise AppException(
                        "client_upload_id already used with different content.",
                        status_code=409,
                    )
                idempotent_hits.append(hit)
            else:
                new_items.append(item)

        if len(existing) + len(new_items) > _MAX_IMAGES_PER_LISTING:
            raise AppException(
                f"A listing may have at most {_MAX_IMAGES_PER_LISTING} images.",
                status_code=400,
            )

        next_order_base = max((m.order for m in existing), default=-1) + 1
        pipeline = self._moderation_pipeline
        if pipeline is None:
            raise AppException("Image moderation pipeline is not configured.", status_code=503)

        put_keys: list[str] = []
        settings = get_settings()
        async_enabled = settings.MEDIA_ASYNC_PIPELINE_ENABLED
        pipeline_version = (
            settings.MEDIA_ASYNC_PIPELINE_VERSION
            if async_enabled
            else LEGACY_SYNC_PIPELINE_VERSION
        )
        try:
            created_rows: list[Media] = list(idempotent_hits)
            for idx, item in enumerate(new_items):
                content = item.content
                content_type = item.content_type
                source_name = item.source_name
                content_hash = self._content_sha256(content)
                ext = self._storage.validate_image(content, content_type)

                # 1) Reserve media_id (no blob yet) — storage key is server-derived.
                row = Media(
                    url=_PENDING_URL,
                    listing_id=listing_id,
                    order=next_order_base + idx,
                    moderation_status=MediaModerationStatus.pending,
                    lifecycle_status=MediaLifecycleStatus.uploading,
                    client_upload_id=item.client_upload_id,
                    content_sha256=content_hash,
                    pipeline_version=pipeline_version,
                )
                created = await self._media.create(row)
                storage_key = listing_original_key(listing_id, created.id, ext)

                # 2) Put immutable original at deterministic key.
                try:
                    public_url = self._storage.put_bytes(
                        storage_key,
                        content,
                        content_type=content_type,
                    )
                    put_keys.append(storage_key)
                except Exception:
                    await self._media.delete(created.id)
                    raise

                refreshed = await self._media.update(
                    created.id,
                    url=public_url,
                    original_url=public_url,
                    display_url=public_url,
                    original_storage_key=storage_key,
                )
                if refreshed is None:
                    # DB update failed after put → orphan blob; clean up.
                    self._storage.delete_key(storage_key)
                    put_keys = [k for k in put_keys if k != storage_key]
                    logger.error(
                        "media_db_update_failed_after_put media_id=%s key=%s",
                        created.id,
                        storage_key,
                    )
                    raise TransactionFailedError(
                        "Failed to persist media metadata after storage put.",
                    )

                if async_enabled and not created.is_placeholder:
                    lifecycle = MediaLifecycleStatus.queued
                    refreshed = await self._media.update(
                        created.id,
                        lifecycle_status=lifecycle,
                        pipeline_version=settings.MEDIA_ASYNC_PIPELINE_VERSION,
                        moderation_status=MediaModerationStatus.pending,
                    )
                    if refreshed is None:
                        refreshed = await self._media.get_by_id(created.id)
                else:
                    outcome = await pipeline.process_existing_media(
                        refreshed,
                        content=content,
                        content_type=content_type,
                        source_name=source_name,
                    )
                    lifecycle = lifecycle_after_upload(
                        outcome.moderation_status,
                        async_pipeline_enabled=False,
                    )
                    refreshed = await self._media.update(
                        created.id,
                        lifecycle_status=lifecycle,
                        processed_at=outcome.moderated_at,
                        pipeline_version=pipeline_version,
                        moderation_status=outcome.moderation_status,
                        moderation_reason=outcome.moderation_reason,
                        moderated_at=outcome.moderated_at,
                    )
                    if refreshed is None:
                        refreshed = await self._media.get_by_id(created.id)

                    if (
                        refreshed is not None
                        and self._focus_bbox_service is not None
                        and listing.category_id is not None
                    ):
                        await self._focus_bbox_service.maybe_detect_and_persist(
                            listing=listing,
                            media=refreshed,
                            content=content,
                            content_type=content_type,
                        )
                        refreshed = await self._media.get_by_id(created.id) or refreshed

                if (
                    refreshed is not None
                    and async_enabled
                    and lifecycle == MediaLifecycleStatus.queued
                    and listing.category_id is not None
                ):
                    from app.media_queue.job_service import MediaJobService

                    await MediaJobService(self._session, settings).enqueue_for_media(
                        refreshed.id,
                        pipeline_version=settings.MEDIA_ASYNC_PIPELINE_VERSION,
                        category_id=listing.category_id,
                    )

                if refreshed is not None:
                    created_rows.append(refreshed)

            await self._session.commit()

            if async_enabled and listing.category_id is not None:
                await self._best_effort_dispatch_outbox(settings)

            return [MediaRead.model_validate(m) for m in created_rows]
        except AppException:
            await self._session.rollback()
            for key in put_keys:
                try:
                    self._storage.delete_key(key)
                except Exception:
                    logger.warning("orphan_cleanup_failed key=%s", key)
            raise
        except Exception as exc:
            await self._session.rollback()
            for key in put_keys:
                try:
                    self._storage.delete_key(key)
                except Exception:
                    logger.warning("orphan_cleanup_failed key=%s", key)
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

        storage_key = media.original_storage_key
        variant_keys = [
            getattr(media, "display_storage_key", None),
            getattr(media, "feed_storage_key", None),
            getattr(media, "thumb_storage_key", None),
        ]
        stored_url = media.url
        try:
            await self._media.delete(image_id)
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to delete image; transaction rolled back.",
            ) from exc

        from app.services.media_storage_cleanup_service import MediaStorageCleanupService

        cleanup = MediaStorageCleanupService(
            self._session,
            self._storage,
            get_settings(),
        )
        keys = [k for k in [storage_key, *variant_keys] if k]
        await cleanup.enqueue_keys(keys, media_id=image_id, reason="media_delete")
        await self._session.commit()

        try:
            await cleanup.process_pending(batch_size=len(keys) or 1)
        except Exception:
            logger.warning(
                "media_blob_delete_async_failed media_id=%s key=%s",
                image_id,
                storage_key,
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

    async def _best_effort_dispatch_outbox(self, settings) -> None:
        """Post-commit best-effort outbox dispatch; worker reconciles if Redis down."""
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
                await dispatch_pending_outbox(session, client, settings)
        except Exception:
            logger.warning("best_effort_outbox_dispatch_failed", exc_info=True)
