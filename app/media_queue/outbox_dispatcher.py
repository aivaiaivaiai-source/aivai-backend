"""Transactional outbox → Redis Streams dispatcher."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.media_queue import metrics
from app.media_queue.streams import xadd_job
from app.repositories.media_outbox_repository import MediaOutboxRepository

logger = logging.getLogger(__name__)


async def dispatch_pending_outbox(
    session: AsyncSession,
    redis: Redis,
    settings: Settings,
    *,
    batch_size: int | None = None,
) -> int:
    """
    Deliver pending outbox rows to Redis Streams.
    Idempotent: duplicate XADD is safe — job claim/processing is idempotent.
    """
    limit = batch_size or settings.MEDIA_OUTBOX_DISPATCH_BATCH
    repo = MediaOutboxRepository(session)
    pending = await repo.list_pending(limit=limit)
    dispatched = 0
    for row in pending:
        try:
            await xadd_job(redis, settings, row.job_id)
        except Exception:
            logger.exception("outbox_xadd_failed job_id=%s outbox_id=%s", row.job_id, row.id)
            metrics.incr("outbox_dispatch_failed")
            continue
        if await repo.mark_dispatched(row.id, now=datetime.now(UTC)):
            dispatched += 1
            metrics.incr("outbox_dispatched_total")
    if dispatched:
        await session.commit()
    return dispatched
