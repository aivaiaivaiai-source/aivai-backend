from __future__ import annotations

import enum


class MediaLifecycleStatus(str, enum.Enum):
    """Server-side processing lifecycle for listing media (Stage 1 foundation)."""

    uploading = "uploading"
    queued = "queued"
    processing = "processing"
    ready = "ready"
    rejected = "rejected"
    failed = "failed"


# Valid transitions for future workers; Stage 1 only validates explicit sets.
MEDIA_LIFECYCLE_TERMINAL: frozenset[MediaLifecycleStatus] = frozenset(
    {
        MediaLifecycleStatus.ready,
        MediaLifecycleStatus.rejected,
        MediaLifecycleStatus.failed,
    }
)

MEDIA_LIFECYCLE_TRANSITIONS: dict[
    MediaLifecycleStatus,
    frozenset[MediaLifecycleStatus],
] = {
    MediaLifecycleStatus.uploading: frozenset(
        {
            MediaLifecycleStatus.queued,
            MediaLifecycleStatus.ready,
            MediaLifecycleStatus.rejected,
            MediaLifecycleStatus.failed,
        }
    ),
    MediaLifecycleStatus.queued: frozenset(
        {
            MediaLifecycleStatus.processing,
            MediaLifecycleStatus.ready,
            MediaLifecycleStatus.rejected,
            MediaLifecycleStatus.failed,
        }
    ),
    MediaLifecycleStatus.processing: frozenset(
        {
            MediaLifecycleStatus.ready,
            MediaLifecycleStatus.rejected,
            MediaLifecycleStatus.failed,
            # Category change before publish — requeue for new category context.
            MediaLifecycleStatus.queued,
        }
    ),
    MediaLifecycleStatus.ready: frozenset(
        {
            # Category change before publish — requeue without bumping global pipeline version.
            MediaLifecycleStatus.queued,
        }
    ),
    MediaLifecycleStatus.rejected: frozenset(),
    MediaLifecycleStatus.failed: frozenset(),
}
