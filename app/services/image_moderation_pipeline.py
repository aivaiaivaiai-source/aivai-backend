from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.image_moderation_enums import ImageModerationVerdict, MediaModerationStatus
from app.models.media import Media
from app.repositories.media_repository import MediaRepository
from app.schemas.image_moderation import ImageClassificationInput, ImageModerationOutcome
from app.services.image_moderation_service import (
    ImageModerationService,
    build_moderation_reason,
    verdict_to_status,
)
from app.services.image_policy_classifier import ImagePolicyClassifier, StubImagePolicyClassifier
from app.services.storage_service import StorageService


class ImageModerationPipeline:
    """
    Upload → persist pending media → classify → apply status → optional file cleanup.

    Placeholder images skip classification and are auto-approved.
    """

    def __init__(
        self,
        session: AsyncSession,
        media_repository: MediaRepository,
        storage: StorageService,
        *,
        moderation_service: ImageModerationService | None = None,
        classifier: ImagePolicyClassifier | None = None,
    ) -> None:
        self._session = session
        self._media = media_repository
        self._storage = storage
        self._moderation = moderation_service or ImageModerationService(
            classifier=classifier or StubImagePolicyClassifier(),
        )

    async def apply_placeholder_approval(self, media_id: int) -> ImageModerationOutcome:
        now = datetime.now(UTC)
        updated = await self._media.update(
            media_id,
            moderation_status=MediaModerationStatus.approved,
            moderation_reason=None,
            moderated_at=now,
        )
        if updated is None:
            raise ValueError(f"Media {media_id} not found for placeholder approval")
        return ImageModerationOutcome(
            media_id=media_id,
            verdict=ImageModerationVerdict.ALLOW,
            moderation_status=MediaModerationStatus.approved,
            moderation_reason=None,
            moderated_at=now,
            blocked_from_listing=False,
        )

    async def process_existing_media(
        self,
        media: Media,
        *,
        content: bytes,
        content_type: str,
        source_name: str | None = None,
    ) -> ImageModerationOutcome:
        if media.is_placeholder:
            return await self.apply_placeholder_approval(media.id)

        payload = ImageClassificationInput(
            content=content,
            content_type=content_type,
            source_name=source_name,
            listing_id=media.listing_id,
        )
        result = await self._moderation._classifier.classify(payload)
        status = verdict_to_status(result.verdict)
        reason = build_moderation_reason(result.reason_code, result.reason_detail)
        now = datetime.now(UTC)

        updated = await self._media.update(
            media.id,
            moderation_status=status,
            moderation_reason=reason,
            moderated_at=now,
        )
        if updated is None:
            raise ValueError(f"Media {media.id} missing after moderation update")

        if result.verdict == ImageModerationVerdict.REJECT:
            try:
                self._storage.delete_file(media.url)
            except Exception:
                pass

        return ImageModerationOutcome(
            media_id=media.id,
            verdict=result.verdict,
            moderation_status=status,
            moderation_reason=reason,
            moderated_at=now,
            blocked_from_listing=result.verdict == ImageModerationVerdict.REJECT,
        )


def build_image_moderation_pipeline(
    session: AsyncSession,
    media_repository: MediaRepository,
    storage: StorageService,
    *,
    classifier: ImagePolicyClassifier | None = None,
) -> ImageModerationPipeline:
    return ImageModerationPipeline(
        session,
        media_repository,
        storage,
        classifier=classifier,
    )
