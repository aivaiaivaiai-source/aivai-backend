from __future__ import annotations

import enum


class MediaJobStatus(str, enum.Enum):
    queued = "queued"
    leased = "leased"
    succeeded = "succeeded"
    failed = "failed"
    dead = "dead"


class MediaOutboxStatus(str, enum.Enum):
    pending = "pending"
    dispatched = "dispatched"
