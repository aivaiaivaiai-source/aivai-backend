"""Direct-to-storage upload orchestration (Stage 5)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import AppException, EntityNotFoundError, OwnershipError, TransactionFailedError
from app.core.rate_limit import MEDIA_UPLOAD_INITIATE_LIMITER
from app.media_upload import metrics
from app.models.image_moderation_enums import MediaModerationStatus
from app.models.media import Media
from app.models.media_enums import MediaLifecycleStatus
from app.repositories.listing_repository import ListingRepository
from app.repositories.media_repository import MediaRepository
from app.schemas.direct_upload import (
    DirectUploadAuthorization,
    DirectUploadCompleteResponse,
    DirectUploadInitiateRequest,
    DirectUploadInitiateResponse,
)
from app.schemas.media import MediaRead
from app.services.media_delivery_service import MediaDeliveryService
from app.services.media_lifecycle import LEGACY_SYNC_PIPELINE_VERSION, lifecycle_after_upload
from app.services.storage_service import StorageService
from app.storage.keys import listing_original_key

logger = logging.getLogger(__name__)


class _OrderSlotIdempotentHit(Exception):
    def __init__(self, media: Media) -> None:
        self.media = media
        super().__init__()


_PENDING_URL = "/media/.pending"
_MAX_IMAGES_PER_LISTING = 9


class DirectUploadService:
    def __init__(
        self,
        session: AsyncSession,
        media_repository: MediaRepository,
        listing_repository: ListingRepository,
        storage: StorageService,
        *,
        settings: Settings | None = None,
        moderation_pipeline=None,
        focus_bbox_service=None,
    ) -> None:
        self._session = session
        self._media = media_repository
        self._listings = listing_repository
        self._storage = storage
        self._settings = settings or get_settings()
        self._moderation_pipeline = moderation_pipeline
        self._focus_bbox_service = focus_bbox_service
        self._delivery = MediaDeliveryService(self._settings)

    @staticmethod
    def _ensure_owner(listing, user_id: int) -> None:
        if listing.owner_id is None or listing.owner_id != user_id:
            raise OwnershipError("You cannot modify another user's listing.")

    def _ensure_enabled(self) -> None:
        if not self._settings.MEDIA_DIRECT_UPLOAD_ENABLED:
            raise AppException("Direct upload is not enabled.", status_code=404)

    @staticmethod
    def _is_reclaimable_uploading(media: Media, *, now: datetime) -> bool:
        return (
            media.lifecycle_status == MediaLifecycleStatus.uploading
            and media.upload_expires_at is not None
            and media.upload_expires_at < now
        )

    async def _resolve_order_slot(
        self,
        existing: list[Media],
        *,
        body: DirectUploadInitiateRequest,
        now: datetime,
    ) -> int:
        if body.order is None:
            return max((m.order for m in existing), default=-1) + 1

        order = body.order
        for media in list(existing):
            if media.order != order:
                continue
            if str(media.client_upload_id) == str(body.client_upload_id):
                metrics.incr("upload_initiate_idempotent_total")
                raise _OrderSlotIdempotentHit(media)
            if self._is_reclaimable_uploading(media, now=now):
                await self._media.delete(media)
                existing.remove(media)
                continue
            raise AppException(
                "Photo order slot already reserved for this listing.",
                status_code=409,
            )
        return order

    async def initiate(
        self,
        listing_id: int,
        *,
        actor_user_id: int,
        body: DirectUploadInitiateRequest,
    ) -> DirectUploadInitiateResponse:
        self._ensure_enabled()
        await MEDIA_UPLOAD_INITIATE_LIMITER.hit(f"media-upload:{actor_user_id}")

        listing = await self._listings.get_by_id(listing_id)
        if listing is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)
        self._ensure_owner(listing, actor_user_id)

        self._storage.validate_declared_upload(body.content_type, body.content_length)

        incomplete = await self._media.count_incomplete_uploads_for_owner(actor_user_id)
        if incomplete >= self._settings.MEDIA_MAX_INCOMPLETE_UPLOADS_PER_USER:
            raise AppException(
                "Too many incomplete uploads. Complete or wait for expiration.",
                status_code=429,
            )

        hit = await self._media.get_by_listing_and_client_upload_id(
            listing_id,
            body.client_upload_id,
        )
        if hit is not None:
            if body.content_sha256 and hit.content_sha256 and hit.content_sha256 != body.content_sha256:
                raise AppException(
                    "client_upload_id already used with different content.",
                    status_code=409,
                )
            metrics.incr("upload_initiate_idempotent_total")
            return await self._build_initiate_response(hit, body)

        existing = await self._media.list_by_listing(listing_id)
        if len(existing) >= _MAX_IMAGES_PER_LISTING:
            raise AppException(
                f"A listing may have at most {_MAX_IMAGES_PER_LISTING} images.",
                status_code=400,
            )

        now = datetime.now(UTC)
        try:
            order = await self._resolve_order_slot(existing, body=body, now=now)
        except _OrderSlotIdempotentHit as exc:
            return await self._build_initiate_response(exc.media, body)

        listing = await self._listings.get_by_id(listing_id, for_update=True)
        if listing is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)
        self._ensure_owner(listing, actor_user_id)

        hit = await self._media.get_by_listing_and_client_upload_id(
            listing_id,
            body.client_upload_id,
        )
        if hit is not None:
            if body.content_sha256 and hit.content_sha256 and hit.content_sha256 != body.content_sha256:
                raise AppException(
                    "client_upload_id already used with different content.",
                    status_code=409,
                )
            metrics.incr("upload_initiate_idempotent_total")
            return await self._build_initiate_response(hit, body)

        existing = await self._media.list_by_listing(listing_id)
        if len(existing) >= _MAX_IMAGES_PER_LISTING:
            raise AppException(
                f"A listing may have at most {_MAX_IMAGES_PER_LISTING} images.",
                status_code=400,
            )

        try:
            order = await self._resolve_order_slot(existing, body=body, now=now)
        except _OrderSlotIdempotentHit as exc:
            return await self._build_initiate_response(exc.media, body)

        ext = self._storage.ext_from_content_type(body.content_type)
        expires = now + timedelta(seconds=self._settings.MEDIA_UPLOAD_RESERVATION_TTL_SECONDS)

        row = Media(
            url=_PENDING_URL,
            listing_id=listing_id,
            order=order,
            moderation_status=MediaModerationStatus.pending,
            lifecycle_status=MediaLifecycleStatus.uploading,
            client_upload_id=body.client_upload_id,
            content_sha256=body.content_sha256,
            declared_content_type=body.content_type,
            declared_content_length=body.content_length,
            upload_expires_at=expires,
            pipeline_version=self._settings.MEDIA_ASYNC_PIPELINE_VERSION,
        )
        created = await self._media.create(row)
        storage_key = listing_original_key(listing_id, created.id, ext)
        await self._media.update(
            created.id,
            original_storage_key=storage_key,
        )
        refreshed = await self._media.get_by_id(created.id) or created
        await self._session.commit()

        metrics.incr("upload_initiated_total")
        return await self._build_initiate_response(refreshed, body)

    async def _build_initiate_response(
        self,
        media: Media,
        body: DirectUploadInitiateRequest,
    ) -> DirectUploadInitiateResponse:
        if media.lifecycle_status != MediaLifecycleStatus.uploading:
            raise AppException(
                "Upload reservation is no longer active.",
                status_code=409,
            )
        if media.upload_expires_at and media.upload_expires_at < datetime.now(UTC):
            raise AppException("Upload reservation expired.", status_code=410)

        key = media.original_storage_key
        if not key:
            raise AppException("Upload reservation is invalid.", status_code=500)

        presigned = self._storage.presign_put(
            key,
            listing_id=media.listing_id,
            media_id=media.id,
            content_type=body.content_type,
            content_length=body.content_length,
        )
        return DirectUploadInitiateResponse(
            media_id=media.id,
            client_upload_id=body.client_upload_id,
            status=media.lifecycle_status,
            upload=DirectUploadAuthorization(
                method=presigned.method,
                url=presigned.url,
                headers=presigned.headers,
                expires_at=presigned.expires_at,
            ),
        )

    async def put_upload_bytes(
        self,
        listing_id: int,
        media_id: int,
        *,
        actor_user_id: int,
        content: bytes,
        content_type: str,
    ) -> None:
        """Local-dev fallback: authorized PUT to reserved object key."""
        self._ensure_enabled()
        media = await self._media.get_by_id_for_update(media_id)
        if media is None or media.listing_id != listing_id:
            raise EntityNotFoundError("Media", entity_id=media_id)
        listing = await self._listings.get_by_id(listing_id)
        if listing is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)
        self._ensure_owner(listing, actor_user_id)
        if media.lifecycle_status != MediaLifecycleStatus.uploading:
            raise AppException("Upload reservation is not active.", status_code=409)
        if media.upload_expires_at and media.upload_expires_at < datetime.now(UTC):
            raise AppException("Upload reservation expired.", status_code=410)
        ext = self._storage.validate_image(content, content_type)
        expected_key = listing_original_key(listing_id, media_id, ext)
        if media.original_storage_key != expected_key:
            raise AppException("Storage key mismatch.", status_code=409)
        self._storage.put_bytes(expected_key, content, content_type=content_type)
        await self._session.commit()

    async def complete(
        self,
        listing_id: int,
        media_id: int,
        *,
        actor_user_id: int,
    ) -> DirectUploadCompleteResponse:
        self._ensure_enabled()
        media = await self._media.get_by_id_for_update(media_id)
        if media is None or media.listing_id != listing_id:
            raise EntityNotFoundError("Media", entity_id=media_id)

        listing = await self._listings.get_by_id(listing_id)
        if listing is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)
        self._ensure_owner(listing, actor_user_id)

        if media.lifecycle_status in (
            MediaLifecycleStatus.queued,
            MediaLifecycleStatus.processing,
            MediaLifecycleStatus.ready,
        ):
            metrics.incr("upload_complete_idempotent_total")
            await self._session.commit()
            return DirectUploadCompleteResponse(
                media_id=media.id,
                status=media.lifecycle_status,
                queued=media.lifecycle_status
                in (MediaLifecycleStatus.queued, MediaLifecycleStatus.processing),
            )

        if media.lifecycle_status != MediaLifecycleStatus.uploading:
            raise AppException(
                f"Cannot complete upload in status {media.lifecycle_status.value}.",
                status_code=409,
            )

        if media.upload_expires_at and media.upload_expires_at < datetime.now(UTC):
            metrics.incr("upload_complete_expired_total")
            raise AppException("Upload reservation expired.", status_code=410)

        key = media.original_storage_key
        if not key:
            raise AppException("Missing storage key.", status_code=500)

        head = self._storage.head_object(key)
        if head is None:
            metrics.incr("upload_complete_missing_blob_total")
            raise AppException("Uploaded object not found.", status_code=400)

        if media.declared_content_length and head.content_length != media.declared_content_length:
            metrics.incr("upload_complete_size_mismatch_total")
            raise AppException("Uploaded object size mismatch.", status_code=400)

        if head.content_length <= 0 or head.content_length > 5 * 1024 * 1024:
            raise AppException("Uploaded object size invalid.", status_code=400)

        if media.declared_content_type and head.content_type:
            if head.content_type.split(";")[0].strip().lower() != media.declared_content_type.lower():
                metrics.incr("upload_complete_type_mismatch_total")
                raise AppException("Uploaded object content type mismatch.", status_code=400)

        now = datetime.now(UTC)
        media.upload_completed_at = now
        async_enabled = self._settings.MEDIA_ASYNC_PIPELINE_ENABLED
        category_known = listing.category_id is not None

        if async_enabled:
            media.lifecycle_status = MediaLifecycleStatus.queued
            media.moderation_status = MediaModerationStatus.pending
            media.pipeline_version = self._settings.MEDIA_ASYNC_PIPELINE_VERSION
            media.url = _PENDING_URL
            await self._session.flush()
            # Category-aware Media Engine waits until category is confirmed.
            if category_known:
                from app.media_queue.job_service import MediaJobService

                await MediaJobService(self._session, self._settings).enqueue_for_media(
                    media.id,
                    pipeline_version=self._settings.MEDIA_ASYNC_PIPELINE_VERSION,
                    category_id=listing.category_id,
                )
            else:
                from app.services.media_classification_service import (
                    maybe_enqueue_classification_after_upload,
                )

                await maybe_enqueue_classification_after_upload(
                    self._session,
                    listing.id,
                    settings=self._settings,
                )
            from app.services.visual_evidence_service import (
                maybe_enqueue_visual_evidence_after_upload,
            )

            await maybe_enqueue_visual_evidence_after_upload(
                self._session,
                listing.id,
                settings=self._settings,
            )
            await self._session.commit()
            if category_known:
                await self._best_effort_dispatch_outbox()
            metrics.incr("upload_completed_total")
            return DirectUploadCompleteResponse(
                media_id=media.id,
                status=MediaLifecycleStatus.queued,
                queued=category_known,
            )

        if not category_known:
            # Sync path without category: keep original stored, defer engine/AUTO.
            delivery = self._delivery
            original_url = delivery.original_url(key, fallback=self._storage.public_url(key))
            media.url = original_url or self._storage.public_url(key)
            media.original_url = original_url
            media.display_url = media.url
            media.lifecycle_status = MediaLifecycleStatus.queued
            media.moderation_status = MediaModerationStatus.pending
            media.pipeline_version = self._settings.MEDIA_ASYNC_PIPELINE_VERSION
            from app.services.media_classification_service import (
                maybe_enqueue_classification_after_upload,
            )

            await maybe_enqueue_classification_after_upload(
                self._session,
                listing.id,
                settings=self._settings,
            )
            from app.services.visual_evidence_service import (
                maybe_enqueue_visual_evidence_after_upload,
            )

            await maybe_enqueue_visual_evidence_after_upload(
                self._session,
                listing.id,
                settings=self._settings,
            )
            await self._session.commit()
            metrics.incr("upload_completed_total")
            return DirectUploadCompleteResponse(
                media_id=media.id,
                status=MediaLifecycleStatus.queued,
                queued=False,
            )

        pipeline = self._moderation_pipeline
        if pipeline is None:
            raise AppException("Image moderation pipeline is not configured.", status_code=503)

        content = self._storage.backend.get(key)
        content_type = media.declared_content_type or "image/jpeg"
        outcome = await pipeline.process_existing_media(
            media,
            content=content,
            content_type=content_type,
            source_name=None,
        )
        lifecycle = lifecycle_after_upload(outcome.moderation_status, async_pipeline_enabled=False)
        delivery = self._delivery
        original_url = delivery.original_url(key, fallback=self._storage.public_url(key))
        media.url = original_url or self._storage.public_url(key)
        media.original_url = original_url
        media.display_url = media.url
        media.lifecycle_status = lifecycle
        media.processed_at = now
        media.pipeline_version = LEGACY_SYNC_PIPELINE_VERSION
        media.moderation_status = outcome.moderation_status
        media.moderation_reason = outcome.moderation_reason
        media.moderated_at = outcome.moderated_at

        if self._focus_bbox_service is not None and lifecycle == MediaLifecycleStatus.ready:
            await self._focus_bbox_service.maybe_detect_and_persist(
                listing=listing,
                media=media,
                content=content,
                content_type=content_type,
            )

        await self._session.commit()
        metrics.incr("upload_completed_total")
        return DirectUploadCompleteResponse(
            media_id=media.id,
            status=lifecycle,
            queued=False,
        )

    async def _best_effort_dispatch_outbox(self) -> None:
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
                await dispatch_pending_outbox(session, client, self._settings)
        except Exception:
            logger.warning("best_effort_outbox_dispatch_failed", exc_info=True)
