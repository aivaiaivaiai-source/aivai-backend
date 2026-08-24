from __future__ import annotations

from datetime import UTC, datetime

from app.core.exceptions import AppException
from app.models.image_moderation_enums import MediaModerationStatus
from app.models.media_enums import (
    MEDIA_LIFECYCLE_TERMINAL,
    MEDIA_LIFECYCLE_TRANSITIONS,
    MediaLifecycleStatus,
)

# Sync upload path marks legacy rows processed immediately (no worker on Stage 1).
LEGACY_SYNC_PIPELINE_VERSION: str | None = None


def validate_lifecycle_transition(
    current: MediaLifecycleStatus,
    target: MediaLifecycleStatus,
) -> None:
    if current == target:
        return
    allowed = MEDIA_LIFECYCLE_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise AppException(
            f"Invalid media lifecycle transition: {current.value} → {target.value}.",
            status_code=409,
        )


def lifecycle_status_for_moderation(
    moderation_status: MediaModerationStatus,
) -> MediaLifecycleStatus:
    if moderation_status == MediaModerationStatus.rejected:
        return MediaLifecycleStatus.rejected
    return MediaLifecycleStatus.ready


def lifecycle_after_upload(
    moderation_status: MediaModerationStatus,
    *,
    async_pipeline_enabled: bool,
) -> MediaLifecycleStatus:
    if moderation_status == MediaModerationStatus.rejected:
        return MediaLifecycleStatus.rejected
    if async_pipeline_enabled:
        return MediaLifecycleStatus.queued
    return MediaLifecycleStatus.ready


def initial_sync_upload_lifecycle() -> tuple[MediaLifecycleStatus, datetime | None]:
    """Current synchronous upload completes in one request → ready immediately."""
    return MediaLifecycleStatus.ready, datetime.now(UTC)


def is_terminal_lifecycle(status: MediaLifecycleStatus) -> bool:
    return status in MEDIA_LIFECYCLE_TERMINAL
