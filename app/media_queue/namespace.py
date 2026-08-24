"""Media Platform Redis Streams namespace (isolated from AI agents)."""

from __future__ import annotations

from app.core.config import Settings


def media_queue_prefix(settings: Settings) -> str:
    raw = (settings.MEDIA_QUEUE_NAMESPACE or "aivai:media").strip().rstrip(":")
    return raw or "aivai:media"


def media_jobs_stream(settings: Settings) -> str:
    return f"{media_queue_prefix(settings)}:jobs:stream"


def media_jobs_consumer_group(settings: Settings) -> str:
    return f"{media_queue_prefix(settings)}:workers"


def media_worker_metrics_key(settings: Settings) -> str:
    return f"{media_queue_prefix(settings)}:metrics"
