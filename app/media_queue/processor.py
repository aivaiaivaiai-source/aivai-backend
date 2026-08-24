"""Stage 3/4 media processor interface."""

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media import Media
from app.models.media_job import MediaJob

logger = logging.getLogger(__name__)


class MediaProcessorOutcome(str, enum.Enum):
    ready = "ready"
    rejected = "rejected"
    review = "review"
    processing = "processing"


@dataclass(frozen=True)
class MediaProcessorResult:
    outcome: MediaProcessorOutcome = MediaProcessorOutcome.ready


class NoOpMediaProcessor:
    """
    Stage 3 infrastructure stub — validates linkage only.
    Does NOT generate variants or set lifecycle ready.
    """

    async def process(
        self,
        session: AsyncSession,
        *,
        job: MediaJob,
        media: Media,
    ) -> MediaProcessorResult:
        del session
        if media.id != job.media_id:
            raise ValueError("media/job mismatch")
        if not media.original_storage_key:
            raise ValueError("missing original_storage_key")
        logger.info(
            "noop_media_processor media_id=%s job_id=%s key=%s",
            media.id,
            job.id,
            media.original_storage_key,
        )
        return MediaProcessorResult(outcome=MediaProcessorOutcome.processing)