"""AiVai Media Engine — production processor replacing NoOp (Stage 4)."""

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.media_engine import metrics as engine_metrics
from app.media_engine.decode import content_type_from_key, decode_image_safe
from app.media_engine.enhance import enhance_image
from app.media_engine.router import MediaPipelineKind, route_pipeline
from app.media_engine.storage_ops import delete_pipeline_variants, put_variants
from app.media_engine.variants import encode_all_variants
from app.media_queue.errors import PermanentMediaJobError, RetryableMediaJobError
from app.media_queue.processor import MediaProcessorOutcome, MediaProcessorResult
from app.models.image_moderation_enums import ImageModerationVerdict, MediaModerationStatus
from app.models.media import Media
from app.models.media_enums import MediaLifecycleStatus
from app.models.media_job import MediaJob
from app.repositories.listing_repository import ListingRepository
from app.schemas.image_moderation import ImageClassificationInput, ImageModerationOutcome
from app.services.focus_bbox_detection import FocusBBoxResult
from app.services.focus_bbox_detector import (
    FocusBBoxDetector,
    NullFocusBBoxDetector,
    RtDetrFocusBBoxDetector,
)
from app.services.image_moderation_service import ImageModerationService
from app.services.image_policy_classifier import ImagePolicyClassifier, StubImagePolicyClassifier
from app.services.media_delivery_service import MediaDeliveryService
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="media-engine")


@lru_cache
def _get_detector(model_id: str, min_confidence: float, inference_max_edge: int) -> FocusBBoxDetector:
    if not model_id:
        return NullFocusBBoxDetector()
    return RtDetrFocusBBoxDetector(
        model_id,
        min_confidence=min_confidence,
        inference_max_edge=inference_max_edge,
    )


def build_media_engine(
    settings: Settings | None = None,
    *,
    classifier: ImagePolicyClassifier | None = None,
    detector: FocusBBoxDetector | None = None,
) -> AiVaiMediaEngine:
    cfg = settings or get_settings()
    if detector is None and cfg.FOCUS_BBOX_ENABLED:
        detector = _get_detector(
            cfg.FOCUS_BBOX_MODEL_ID,
            cfg.FOCUS_BBOX_MIN_CONFIDENCE,
            cfg.MEDIA_DETECTOR_INFERENCE_MAX_EDGE,
        )
    return AiVaiMediaEngine(
        cfg,
        classifier=classifier or StubImagePolicyClassifier(),
        detector=detector or NullFocusBBoxDetector(),
    )


class AiVaiMediaEngine:
    """Server-side media pipeline: decode → moderate → detect → enhance → variants."""

    def __init__(
        self,
        settings: Settings,
        *,
        classifier: ImagePolicyClassifier,
        detector: FocusBBoxDetector,
    ) -> None:
        self._settings = settings
        self._moderation = ImageModerationService(classifier=classifier)
        self._detector = detector

    async def process(
        self,
        session: AsyncSession,
        *,
        job: MediaJob,
        media: Media,
    ) -> MediaProcessorResult:
        if media.id != job.media_id:
            raise PermanentMediaJobError("media/job mismatch", error_code="JOB_MISMATCH")
        if not media.original_storage_key:
            raise PermanentMediaJobError(
                "missing original_storage_key",
                error_code="ORIGINAL_KEY_MISSING",
            )

        storage = StorageService(self._settings)
        listing_repo = ListingRepository(session)
        listing = await listing_repo.get_by_id(media.listing_id)
        category_slug = listing.category.slug if listing and listing.category else None

        pipeline_version = (job.pipeline_version or self._settings.MEDIA_PIPELINE_VERSION).strip()

        with engine_metrics.timed("engine_total_ms"):
            try:
                raw_bytes = storage.backend.get(media.original_storage_key)
            except KeyError as exc:
                raise PermanentMediaJobError(
                    "original blob missing",
                    error_code="ORIGINAL_MISSING",
                ) from exc

            engine_metrics.add_bytes("original_bytes_total", len(raw_bytes))
            content_type = content_type_from_key(media.original_storage_key)

            with engine_metrics.timed("decode_ms"):
                decoded = decode_image_safe(
                    raw_bytes,
                    content_type=content_type,
                    settings=self._settings,
                )

            with engine_metrics.timed("moderation_ms"):
                mod_outcome = await self._run_moderation(media, raw_bytes, content_type)

            media.moderation_status = mod_outcome.moderation_status
            media.moderation_reason = mod_outcome.moderation_reason
            media.moderated_at = mod_outcome.moderated_at

            if mod_outcome.verdict == ImageModerationVerdict.REJECT:
                engine_metrics.incr("engine_rejected_total")
                media.lifecycle_status = MediaLifecycleStatus.rejected
                media.pipeline_version = pipeline_version
                return MediaProcessorResult(outcome=MediaProcessorOutcome.rejected)

            if mod_outcome.verdict == ImageModerationVerdict.MODERATION_QUEUE:
                engine_metrics.incr("engine_review_total")
                media.lifecycle_status = MediaLifecycleStatus.processing
                media.pipeline_version = pipeline_version
                return MediaProcessorResult(outcome=MediaProcessorOutcome.review)

            pipeline_kind = route_pipeline(category_slug)
            focus: FocusBBoxResult | None = None
            if pipeline_kind == MediaPipelineKind.AUTO:
                with engine_metrics.timed("detection_ms"):
                    focus = await self._run_detection(decoded.image)
                if focus is None:
                    engine_metrics.incr("detector_miss_total")
                else:
                    engine_metrics.incr("detector_hit_total")

            with engine_metrics.timed("enhance_ms"):
                enhanced = enhance_image(decoded.image, self._settings)

            with engine_metrics.timed("encode_ms"):
                variant_outputs = encode_all_variants(
                    enhanced,
                    focus=focus,
                    settings=self._settings,
                )

            with engine_metrics.timed("storage_ms"):
                for vo in variant_outputs:
                    engine_metrics.add_bytes(
                        f"variant_{vo.name}_bytes_total",
                        len(vo.content),
                    )
                stored = put_variants(
                    storage,
                    listing_id=media.listing_id,
                    media_id=media.id,
                    pipeline_version=pipeline_version,
                    variants=variant_outputs,
                )

            by_name = {v.name: v for v in stored}
            required = ("display", "feed", "thumb")
            missing = [n for n in required if n not in by_name]
            if missing:
                delete_pipeline_variants(
                    storage,
                    listing_id=media.listing_id,
                    media_id=media.id,
                    pipeline_version=pipeline_version,
                )
                raise RetryableMediaJobError(
                    f"variant storage incomplete: {missing}",
                )

            display = by_name["display"]
            feed = by_name["feed"]
            thumb = by_name["thumb"]

            if not all(storage.exists_key(v.key) for v in (display, feed, thumb)):
                delete_pipeline_variants(
                    storage,
                    listing_id=media.listing_id,
                    media_id=media.id,
                    pipeline_version=pipeline_version,
                )
                raise RetryableMediaJobError("variant blob verification failed")

            delivery = MediaDeliveryService(self._settings)

            media.display_storage_key = display.key
            media.feed_storage_key = feed.key
            media.thumb_storage_key = thumb.key
            media.original_url = delivery.original_url(
                media.original_storage_key,
                fallback=storage.public_url(media.original_storage_key),
            )
            media.display_url = delivery.public_variant_url(display.key) or display.url
            media.feed_url = delivery.public_variant_url(feed.key) or feed.url
            media.thumb_url = delivery.public_variant_url(thumb.key) or thumb.url
            media.url = media.display_url or display.url
            media.pipeline_version = pipeline_version
            media.processed_at = datetime.now(UTC)
            media.lifecycle_status = MediaLifecycleStatus.ready
            media.error_code = None
            media.error_message = None

            if focus is not None:
                media.focus_bbox_left = focus.left
                media.focus_bbox_top = focus.top
                media.focus_bbox_width = focus.width
                media.focus_bbox_height = focus.height
                media.focus_confidence = focus.confidence

            engine_metrics.incr("engine_ready_total")
            logger.info(
                "media_engine_ready media_id=%s job_id=%s pipeline=%s kind=%s",
                media.id,
                job.id,
                pipeline_version,
                pipeline_kind.value,
            )
            return MediaProcessorResult(outcome=MediaProcessorOutcome.ready)

    async def _run_moderation(
        self,
        media: Media,
        content: bytes,
        content_type: str,
    ) -> ImageModerationOutcome:
        payload = ImageClassificationInput(
            content=content,
            content_type=content_type,
            source_name=None,
            listing_id=media.listing_id,
        )
        try:
            outcome = await self._moderation.run_classification(payload)
        except Exception as exc:
            engine_metrics.incr("moderation_unavailable_total")
            raise RetryableMediaJobError(
                "moderation engine unavailable",
            ) from exc
        outcome.media_id = media.id
        return outcome

    async def _run_detection(self, image) -> FocusBBoxResult | None:
        timeout = self._settings.MEDIA_DETECTOR_TIMEOUT_SECONDS

        def _detect():
            return self._detector.detect_image(image)

        if not hasattr(self._detector, "detect_image"):
            return None

        loop = asyncio.get_running_loop()
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(_executor, _detect),
                timeout=timeout,
            )
        except TimeoutError as exc:
            engine_metrics.incr("detector_timeout_total")
            raise RetryableMediaJobError("detector timeout") from exc
        except Exception as exc:
            logger.exception("detector_runtime_error media_detection")
            engine_metrics.incr("detector_error_total")
            return None
