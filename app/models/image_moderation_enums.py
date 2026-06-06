from __future__ import annotations

import enum


class ImageModerationVerdict(str, enum.Enum):
    """Classifier outcome (maps to persisted media moderation_status)."""

    ALLOW = "ALLOW"
    REJECT = "REJECT"
    MODERATION_QUEUE = "MODERATION_QUEUE"


class MediaModerationStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    moderation_queue = "moderation_queue"
