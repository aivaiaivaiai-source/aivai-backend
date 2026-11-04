"""Media classification orchestration — durable PG jobs, catalog-bound results."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import AppException, EntityNotFoundError
from app.db.idempotency import insert_or_get_on_unique
from app.media_classification import metrics as clf_metrics
from app.media_classification.dev_classifier import DevelopmentDeterministicClassifier
from app.media_classification.fingerprint import media_set_fingerprint
from app.media_classification.protocol import MediaCategoryClassifier
from app.media_classification.types import (
    AllowedCategory,
    CategoryCandidate,
    ClassificationMediaInput,
)
from app.models.media_classification import (
    MediaClassification,
    build_classification_idempotency_key,
)
from app.models.media_classification_enums import (
    MediaClassificationConfidenceBand,
    MediaClassificationStatus,
)
from app.models.media_enums import MediaLifecycleStatus
from app.repositories.category_repository import CategoryRepository
from app.repositories.listing_repository import ListingRepository
from app.repositories.media_classification_repository import MediaClassificationRepository
from app.repositories.media_repository import MediaRepository
from app.schemas.media_classification import (
    MediaClassificationCandidateRead,
    MediaClassificationConfirmResponse,
    MediaClassificationRead,
)

logger = logging.getLogger(__name__)


def build_default_classifier(settings: Settings) -> MediaCategoryClassifier:
    return DevelopmentDeterministicClassifier(
        version=settings.MEDIA_CLASSIFIER_VERSION,
    )


def confidence_band_for(
    top: float | None,
    *,
    high: float,
    medium: float,
) -> MediaClassificationConfidenceBand:
    if top is None:
        return MediaClassificationConfidenceBand.none
    if top >= high:
        return MediaClassificationConfidenceBand.high
    if top >= medium:
        return MediaClassificationConfidenceBand.medium
    if top > 0:
        return MediaClassificationConfidenceBand.low
    return MediaClassificationConfidenceBand.none


class MediaClassificationService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings | None = None,
        *,
        classifier: MediaCategoryClassifier | None = None,
    ) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._classifier = classifier or build_default_classifier(self._settings)
        self._repo = MediaClassificationRepository(session)
        self._listings = ListingRepository(session)
        self._media = MediaRepository(session)
        self._categories = CategoryRepository(session)

    @property
    def feature_enabled(self) -> bool:
        return bool(self._settings.MEDIA_AI_CLASSIFICATION_ENABLED)

    async def current_media_fingerprint(self, listing_id: int) -> str:
        rows = await self._media.list_by_listing(listing_id)
        ids = [
            m.id
            for m in sorted(rows, key=lambda r: (r.order, r.id))
            if not getattr(m, "is_placeholder", False) and m.original_storage_key
        ]
        return media_set_fingerprint(ids)

    async def ensure_job_for_listing(
        self,
        listing_id: int,
        *,
        actor_user_id: int | None = None,
    ) -> MediaClassification | None:
        """Create pending classification for current media set (idempotent)."""
        if not self.feature_enabled:
            return None

        listing = await self._listings.get_by_id(listing_id)
        if listing is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)
        if actor_user_id is not None and listing.owner_id != actor_user_id:
            raise AppException("Not allowed.", status_code=403)
        if listing.category_id is not None:
            # Category already known — skip AI classification.
            return None

        fingerprint = await self.current_media_fingerprint(listing_id)
        if fingerprint == media_set_fingerprint([]):
            return None

        version = self._classifier.version
        key = build_classification_idempotency_key(listing_id, fingerprint, version)
        existing = await self._repo.get_by_idempotency_key(key)
        if existing is not None:
            if existing.status == MediaClassificationStatus.stale:
                return existing
            return existing

        # Mark older non-terminal results for this listing as stale.
        latest = await self._repo.get_latest_for_listing(listing_id)
        if latest is not None and latest.media_set_fingerprint != fingerprint:
            if latest.status not in (
                MediaClassificationStatus.confirmed,
                MediaClassificationStatus.stale,
            ):
                latest.status = MediaClassificationStatus.stale

        now = datetime.now(UTC)
        row = MediaClassification(
            listing_id=listing_id,
            idempotency_key=key,
            media_set_fingerprint=fingerprint,
            classifier_version=version,
            status=MediaClassificationStatus.pending,
            available_at=now,
        )

        async def _insert() -> MediaClassification:
            return await self._repo.create(row)

        created = await insert_or_get_on_unique(
            self._session,
            insert=_insert,
            fetch_existing=lambda: self._repo.get_by_idempotency_key(key),
            constraint_names=("uq_media_classifications_idempotency_key",),
            reused_log=(
                "media_classification_idempotency_reused listing_id=%s "
                "idempotency_key=%s"
            ),
            reused_log_args=(listing_id, key),
        )
        if created is row:
            clf_metrics.incr("jobs_created")
            logger.info(
                "media_classification_enqueued listing_id=%s id=%s fp=%s",
                listing_id,
                created.id,
                fingerprint,
            )
        return created

    async def get_status(
        self,
        listing_id: int,
        *,
        actor_user_id: int,
    ) -> MediaClassificationRead:
        listing = await self._listings.get_by_id(listing_id)
        if listing is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)
        if listing.owner_id != actor_user_id:
            raise AppException("Not allowed.", status_code=403)

        fingerprint = await self.current_media_fingerprint(listing_id)
        row = await self._repo.get_for_listing_fingerprint(listing_id, fingerprint)
        if row is None:
            row = await self._repo.get_latest_for_listing(listing_id)

        if row is None:
            return MediaClassificationRead(
                id=0,
                listing_id=listing_id,
                status="idle",
                classifier_version=self._classifier.version,
                media_set_fingerprint=fingerprint,
                confidence_band="none",
                feature_enabled=self.feature_enabled,
                is_stale_for_current_media=False,
                created_at=datetime.now(UTC),
            )

        stale = row.media_set_fingerprint != fingerprint
        return self._to_read(row, stale=stale)

    async def process_job(self, classification_id: int) -> MediaClassification:
        row = await self._repo.get_by_id(classification_id)
        if row is None:
            raise EntityNotFoundError("MediaClassification", entity_id=classification_id)
        if row.status not in (
            MediaClassificationStatus.pending,
            MediaClassificationStatus.running,
        ):
            return row

        now = datetime.now(UTC)
        started = now
        row.status = MediaClassificationStatus.running
        row.attempt_count = int(row.attempt_count or 0) + 1
        row.lease_owner = "classifier"
        row.lease_until = now + timedelta(seconds=self._settings.MEDIA_CLASSIFICATION_TIMEOUT_SECONDS)
        if row.created_at:
            row.queue_wait_ms = int((now - row.created_at).total_seconds() * 1000)
        await self._session.flush()

        try:
            listing = await self._listings.get_by_id(row.listing_id)
            if listing is None:
                raise AppException("Listing missing", status_code=404)

            current_fp = await self.current_media_fingerprint(row.listing_id)
            if current_fp != row.media_set_fingerprint:
                row.status = MediaClassificationStatus.stale
                row.completed_at = datetime.now(UTC)
                clf_metrics.incr("jobs_stale")
                await self._session.flush()
                return row

            media_rows = await self._media.list_by_listing(row.listing_id)
            media_inputs = [
                ClassificationMediaInput(
                    media_id=m.id,
                    order=int(m.order or 0),
                    storage_key=m.original_storage_key or "",
                    content_hint=None,
                )
                for m in sorted(media_rows, key=lambda r: (r.order, r.id))
                if not getattr(m, "is_placeholder", False) and m.original_storage_key
            ]

            allowed = await self._load_allowed_categories()
            infer_started = datetime.now(UTC)
            output = await self._classifier.classify(
                listing_id=row.listing_id,
                media_inputs=media_inputs,
                allowed_categories=allowed,
                max_images=self._settings.MEDIA_CLASSIFICATION_MAX_IMAGES,
                high_confidence_threshold=self._settings.MEDIA_CLASSIFICATION_HIGH_CONFIDENCE,
                medium_confidence_threshold=self._settings.MEDIA_CLASSIFICATION_MEDIUM_CONFIDENCE,
            )
            infer_ms = int((datetime.now(UTC) - infer_started).total_seconds() * 1000)

            # Security: drop any candidate not in allowed catalog.
            allowed_ids = {c.category_id for c in allowed}
            filtered = [
                c for c in output.candidates if c.category_id in allowed_ids
            ]
            filtered.sort(key=lambda c: c.confidence, reverse=True)

            row.inference_ms = infer_ms
            row.total_ms = int((datetime.now(UTC) - started).total_seconds() * 1000)
            row.images_inspected = int(output.images_inspected)
            row.evidence_media_ids = list(output.evidence_media_ids)
            row.candidates_json = [c.to_json() for c in filtered]
            row.notes = output.notes
            row.suggested_attributes_json = output.suggested_attributes
            row.lease_owner = None
            row.lease_until = None
            row.completed_at = datetime.now(UTC)

            if output.no_match or not filtered:
                row.status = MediaClassificationStatus.no_match
                row.confidence_band = MediaClassificationConfidenceBand.none
                row.top_confidence = None
                row.predicted_category_id = None
                clf_metrics.incr("jobs_no_match")
            else:
                top = filtered[0]
                row.status = MediaClassificationStatus.succeeded
                row.top_confidence = float(top.confidence)
                row.predicted_category_id = top.category_id
                row.confidence_band = confidence_band_for(
                    top.confidence,
                    high=self._settings.MEDIA_CLASSIFICATION_HIGH_CONFIDENCE,
                    medium=self._settings.MEDIA_CLASSIFICATION_MEDIUM_CONFIDENCE,
                )
                clf_metrics.incr("jobs_succeeded")
                clf_metrics.incr(f"confidence_{row.confidence_band.value}")

            clf_metrics.incr("images_inspected", row.images_inspected)
            await self._session.flush()
            return row
        except Exception as exc:
            logger.exception("media_classification_failed id=%s", classification_id)
            row.status = MediaClassificationStatus.failed
            row.last_error_code = type(exc).__name__[:64]
            row.last_error_message = str(exc)[:512]
            row.lease_owner = None
            row.lease_until = None
            row.completed_at = datetime.now(UTC)
            clf_metrics.incr("jobs_failed")
            await self._session.flush()
            return row

    async def process_available(self, *, limit: int = 2, worker_id: str = "worker") -> int:
        if not self.feature_enabled:
            return 0
        now = datetime.now(UTC)
        rows = await self._repo.list_claimable(now=now, limit=limit)
        done = 0
        for row in rows:
            row.lease_owner = worker_id
            row.lease_until = now + timedelta(
                seconds=self._settings.MEDIA_CLASSIFICATION_TIMEOUT_SECONDS
            )
            await self._session.flush()
            await self.process_job(row.id)
            done += 1
        return done

    async def confirm_category(
        self,
        listing_id: int,
        *,
        actor_user_id: int,
        category_id: int,
        classification_id: int | None = None,
    ) -> MediaClassificationConfirmResponse:
        listing = await self._listings.get_by_id(listing_id)
        if listing is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)
        if listing.owner_id != actor_user_id:
            raise AppException("Not allowed.", status_code=403)

        cat = await self._categories.get_by_id(category_id)
        if cat is None or not cat.is_active:
            raise EntityNotFoundError("Category", entity_id=category_id)

        fingerprint = await self.current_media_fingerprint(listing_id)
        row: MediaClassification | None = None
        if classification_id is not None:
            row = await self._repo.get_by_id(classification_id)
            if row is None or row.listing_id != listing_id:
                raise EntityNotFoundError("MediaClassification", entity_id=classification_id)
            if row.media_set_fingerprint != fingerprint:
                raise AppException(
                    "Classification result is stale for current photos.",
                    status_code=409,
                )
            if row.status == MediaClassificationStatus.stale:
                raise AppException(
                    "Classification result is stale.",
                    status_code=409,
                )

        previous_category_id = listing.category_id
        listing.category_id = category_id
        await self._session.flush()

        user_overridden = False
        if row is not None:
            predicted = row.predicted_category_id
            user_overridden = predicted is not None and predicted != category_id
            row.selected_category_id = category_id
            row.user_overridden = user_overridden
            row.status = MediaClassificationStatus.confirmed
            if user_overridden:
                clf_metrics.incr("user_overridden")
            else:
                clf_metrics.incr("user_accepted")

        from app.services.media_category_processing import (
            enqueue_category_aware_media_for_listing,
            requeue_media_for_category_change,
        )

        jobs = 0
        if previous_category_id is None:
            jobs = await enqueue_category_aware_media_for_listing(
                self._session,
                listing_id,
                settings=self._settings,
            )
        elif previous_category_id != category_id:
            jobs = await requeue_media_for_category_change(
                self._session,
                listing_id,
                new_category_id=category_id,
                settings=self._settings,
            )

        await self._session.commit()

        # Best-effort outbox after commit (worker reconciles if Redis down).
        try:
            from app.core.redis import get_redis, redis_available
            from app.db.session import async_session_maker
            from app.media_queue.outbox_dispatcher import dispatch_pending_outbox

            client = get_redis()
            if client is not None and redis_available():
                async with async_session_maker() as session:
                    await dispatch_pending_outbox(session, client, self._settings)
                    await session.commit()
        except Exception:
            logger.warning("classification_confirm_outbox_best_effort_failed", exc_info=True)

        return MediaClassificationConfirmResponse(
            listing_id=listing_id,
            category_id=category_id,
            classification_id=row.id if row else None,
            media_jobs_enqueued=jobs,
            user_overridden=user_overridden,
        )

    async def _load_allowed_categories(self) -> list[AllowedCategory]:
        rows = await self._categories.get_all_active()
        by_id = {c.id: c for c in rows}
        out: list[AllowedCategory] = []
        for c in rows:
            path_parts: list[str] = [c.name]
            parent_id = c.parent_id
            guard = 0
            while parent_id is not None and guard < 8:
                parent = by_id.get(parent_id)
                if parent is None:
                    break
                path_parts.append(parent.name)
                parent_id = parent.parent_id
                guard += 1
            path_parts.reverse()
            out.append(
                AllowedCategory(
                    category_id=c.id,
                    slug=c.slug,
                    name=c.name,
                    parent_id=c.parent_id,
                    hierarchy_path=" → ".join(path_parts),
                )
            )
        return out

    def _to_read(self, row: MediaClassification, *, stale: bool) -> MediaClassificationRead:
        candidates = [
            MediaClassificationCandidateRead(**CategoryCandidate.from_json(c).to_json())
            for c in (row.candidates_json or [])
            if isinstance(c, dict)
        ]
        return MediaClassificationRead(
            id=row.id,
            listing_id=row.listing_id,
            status=row.status.value if hasattr(row.status, "value") else str(row.status),
            classifier_version=row.classifier_version,
            media_set_fingerprint=row.media_set_fingerprint,
            confidence_band=(
                row.confidence_band.value
                if hasattr(row.confidence_band, "value")
                else str(row.confidence_band)
            ),
            top_confidence=row.top_confidence,
            candidates=candidates,
            evidence_media_ids=list(row.evidence_media_ids or []),
            images_inspected=int(row.images_inspected or 0),
            selected_category_id=row.selected_category_id,
            predicted_category_id=row.predicted_category_id,
            user_overridden=bool(row.user_overridden),
            feature_enabled=self.feature_enabled,
            is_stale_for_current_media=stale,
            created_at=row.created_at,
            completed_at=row.completed_at,
            notes=row.notes,
            suggested_attributes=row.suggested_attributes_json,
        )


async def maybe_enqueue_classification_after_upload(
    session: AsyncSession,
    listing_id: int,
    *,
    settings: Settings | None = None,
) -> None:
    """Hook from direct upload complete — no-op when flag off or category known."""
    cfg = settings or get_settings()
    if not cfg.MEDIA_AI_CLASSIFICATION_ENABLED:
        return
    svc = MediaClassificationService(session, cfg)
    listing = await ListingRepository(session).get_by_id(listing_id)
    if listing is None or listing.category_id is not None:
        return
    await svc.ensure_job_for_listing(listing_id)
