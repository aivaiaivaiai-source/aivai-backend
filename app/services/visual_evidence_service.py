"""Local visual evidence orchestration — durable PG jobs, NOT category assignment."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import AppException, EntityNotFoundError
from app.db.idempotency import insert_or_get_on_unique
from app.media_classification.fingerprint import media_set_fingerprint
from app.models.listing_visual_evidence import (
    ListingVisualEvidence,
    build_visual_evidence_idempotency_key,
)
from app.models.visual_evidence_enums import VisualEvidenceStatus
from app.repositories.listing_repository import ListingRepository
from app.repositories.media_repository import MediaRepository
from app.repositories.visual_evidence_repository import VisualEvidenceRepository
from app.schemas.visual_evidence import VisualConceptObservationRead, VisualEvidenceRead
from app.services.storage_service import StorageService
from app.visual_evidence.siglip2_provider import SigLIP2VisualEvidenceProvider
from app.visual_evidence.stub_provider import StubVisualEvidenceProvider
from app.visual_evidence.types import VisualEvidenceMediaInput

logger = logging.getLogger(__name__)


def build_default_visual_evidence_provider(settings: Settings):
    if settings.MEDIA_VISUAL_EVIDENCE_USE_STUB:
        return StubVisualEvidenceProvider()
    try:
        return SigLIP2VisualEvidenceProvider()
    except Exception:
        logger.warning("visual_evidence_siglip_unavailable_using_stub", exc_info=True)
        return StubVisualEvidenceProvider()


class VisualEvidenceService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings | None = None,
        *,
        provider=None,
    ) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._provider = provider or build_default_visual_evidence_provider(self._settings)
        self._repo = VisualEvidenceRepository(session)
        self._listings = ListingRepository(session)
        self._media = MediaRepository(session)
        self._storage = StorageService(self._settings)

    @property
    def feature_enabled(self) -> bool:
        return bool(self._settings.MEDIA_VISUAL_EVIDENCE_ENABLED)

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
    ) -> ListingVisualEvidence | None:
        if not self.feature_enabled:
            return None

        listing = await self._listings.get_by_id(listing_id)
        if listing is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)
        if actor_user_id is not None and listing.owner_id != actor_user_id:
            raise AppException("Not allowed.", status_code=403)

        fingerprint = await self.current_media_fingerprint(listing_id)
        if fingerprint == media_set_fingerprint([]):
            return None

        model_version = self._provider.model_version
        prompt_version = self._provider.prompt_version
        calibration_version = getattr(self._provider, "calibration_version", None)
        prompt_hash = self._provider.prompt_hash
        key = build_visual_evidence_idempotency_key(
            listing_id,
            fingerprint,
            model_version,
            prompt_version,
            calibration_version,
        )
        existing = await self._repo.get_by_idempotency_key(key)
        if existing is not None:
            return existing

        latest = await self._repo.get_latest_for_listing(listing_id)
        if latest is not None and latest.media_set_fingerprint != fingerprint:
            if latest.status not in (
                VisualEvidenceStatus.stale,
            ):
                latest.status = VisualEvidenceStatus.stale

        now = datetime.now(UTC)
        row = ListingVisualEvidence(
            listing_id=listing_id,
            idempotency_key=key,
            media_set_fingerprint=fingerprint,
            model_version=model_version,
            prompt_version=prompt_version,
            prompt_hash=prompt_hash,
            calibration_version=calibration_version,
            status=VisualEvidenceStatus.pending,
            available_at=now,
        )

        async def _insert() -> ListingVisualEvidence:
            return await self._repo.create(row)

        created = await insert_or_get_on_unique(
            self._session,
            insert=_insert,
            fetch_existing=lambda: self._repo.get_by_idempotency_key(key),
            constraint_names=("uq_listing_visual_evidence_idempotency_key",),
            reused_log=(
                "visual_evidence_idempotency_reused listing_id=%s "
                "idempotency_key=%s"
            ),
            reused_log_args=(listing_id, key),
        )
        if created is row:
            logger.info(
                "visual_evidence_enqueued listing_id=%s id=%s fp_prefix=%s model=%s",
                listing_id,
                created.id,
                fingerprint[:8],
                model_version,
            )
        return created

    async def get_status(
        self,
        listing_id: int,
        *,
        actor_user_id: int,
    ) -> VisualEvidenceRead:
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
            return VisualEvidenceRead(
                id=0,
                listing_id=listing_id,
                status="idle",
                model_version=self._provider.model_version,
                prompt_version=self._provider.prompt_version,
                media_set_fingerprint=fingerprint,
                feature_enabled=self.feature_enabled,
                is_stale_for_current_media=False,
                created_at=datetime.now(UTC),
            )

        stale = row.media_set_fingerprint != fingerprint
        return self._to_read(row, stale=stale)

    async def process_job(self, evidence_id: int) -> ListingVisualEvidence:
        row = await self._repo.get_by_id(evidence_id)
        if row is None:
            raise EntityNotFoundError("ListingVisualEvidence", entity_id=evidence_id)
        if row.status not in (
            VisualEvidenceStatus.pending,
            VisualEvidenceStatus.processing,
        ):
            return row

        now = datetime.now(UTC)
        started = now
        row.status = VisualEvidenceStatus.processing
        row.attempt_count = int(row.attempt_count or 0) + 1
        row.lease_owner = "visual-evidence"
        row.lease_until = now + timedelta(
            seconds=self._settings.MEDIA_VISUAL_EVIDENCE_TIMEOUT_SECONDS
        )
        if row.created_at:
            row.queue_wait_ms = int((now - row.created_at).total_seconds() * 1000)
        await self._session.flush()

        try:
            current_fp = await self.current_media_fingerprint(row.listing_id)
            if current_fp != row.media_set_fingerprint:
                row.status = VisualEvidenceStatus.stale
                row.completed_at = datetime.now(UTC)
                await self._session.flush()
                return row

            media_rows = await self._media.list_by_listing(row.listing_id)
            media_inputs = [
                VisualEvidenceMediaInput(
                    media_id=m.id,
                    order=int(m.order or 0),
                    storage_key=m.original_storage_key or "",
                )
                for m in sorted(media_rows, key=lambda r: (r.order, r.id))
                if not getattr(m, "is_placeholder", False) and m.original_storage_key
            ]

            async def _load_bytes(key: str) -> bytes:
                return await asyncio.to_thread(
                    self._storage.backend.get,
                    key,
                )

            infer_started = datetime.now(UTC)
            output = await self._provider.infer(
                listing_id=row.listing_id,
                media_inputs=media_inputs,
                max_images=self._settings.MEDIA_VISUAL_EVIDENCE_MAX_IMAGES,
                load_image_bytes=_load_bytes,
            )
            infer_ms = int((datetime.now(UTC) - infer_started).total_seconds() * 1000)

            row.inference_ms = infer_ms
            row.processing_ms = int((datetime.now(UTC) - started).total_seconds() * 1000)
            row.images_inspected = int(output.images_inspected)
            row.observations_json = [o.to_json() for o in output.observations]
            row.top_concepts_json = list(output.top_concepts)
            row.notes = output.notes
            row.prompt_hash = self._provider.prompt_hash
            row.calibration_version = getattr(self._provider, "calibration_version", None)
            row.lease_owner = None
            row.lease_until = None
            row.completed_at = datetime.now(UTC)

            if output.no_match or not output.observations:
                row.status = VisualEvidenceStatus.no_match
            else:
                row.status = VisualEvidenceStatus.ready

            await self._session.flush()
            logger.info(
                "visual_evidence_done listing_id=%s id=%s status=%s images=%s ms=%s fp_prefix=%s",
                row.listing_id,
                row.id,
                row.status.value,
                row.images_inspected,
                row.processing_ms,
                row.media_set_fingerprint[:8],
            )
            return row
        except Exception as exc:
            logger.exception("visual_evidence_failed id=%s", evidence_id)
            row.status = VisualEvidenceStatus.failed
            row.last_error_code = type(exc).__name__[:64]
            row.last_error_message = str(exc)[:512]
            row.lease_owner = None
            row.lease_until = None
            row.completed_at = datetime.now(UTC)
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
                seconds=self._settings.MEDIA_VISUAL_EVIDENCE_TIMEOUT_SECONDS
            )
            await self._session.flush()
            await self.process_job(row.id)
            done += 1
        return done

    def _to_read(self, row: ListingVisualEvidence, *, stale: bool) -> VisualEvidenceRead:
        from app.visual_evidence.types import VisualConceptObservation

        observations = [
            VisualConceptObservationRead(
                concept=o.concept,
                score=o.score,
                evidence_media_ids=list(o.evidence_media_ids),
            )
            for o in (
                VisualConceptObservation.from_json(item)
                for item in (row.observations_json or [])
                if isinstance(item, dict)
            )
        ]
        return VisualEvidenceRead(
            id=row.id,
            listing_id=row.listing_id,
            status=row.status.value if hasattr(row.status, "value") else str(row.status),
            model_version=row.model_version,
            prompt_version=row.prompt_version,
            media_set_fingerprint=row.media_set_fingerprint,
            observations=observations,
            top_concepts=list(row.top_concepts_json or []),
            images_inspected=int(row.images_inspected or 0),
            processing_ms=row.processing_ms,
            feature_enabled=self.feature_enabled,
            is_stale_for_current_media=stale,
            created_at=row.created_at,
            completed_at=row.completed_at,
        )


async def maybe_enqueue_visual_evidence_after_upload(
    session: AsyncSession,
    listing_id: int,
    *,
    settings: Settings | None = None,
) -> None:
    """Hook from direct upload complete — no-op when flag off."""
    cfg = settings or get_settings()
    if not cfg.MEDIA_VISUAL_EVIDENCE_ENABLED:
        return
    svc = VisualEvidenceService(session, cfg)
    await svc.ensure_job_for_listing(listing_id)
