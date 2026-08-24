"""Redis Streams consumer group for media jobs."""

from __future__ import annotations

import logging
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import ResponseError

from app.core.config import Settings
from app.media_queue import metrics
from app.media_queue.namespace import media_jobs_consumer_group, media_jobs_stream

logger = logging.getLogger(__name__)


async def ensure_consumer_group(client: Redis, settings: Settings) -> None:
    stream = media_jobs_stream(settings)
    group = media_jobs_consumer_group(settings)
    try:
        await client.xgroup_create(stream, group, id="0", mkstream=True)
        logger.info("media_stream_group_created stream=%s group=%s", stream, group)
    except ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise


async def xadd_job(client: Redis, settings: Settings, job_id: int) -> str:
    stream = media_jobs_stream(settings)
    msg_id = await client.xadd(stream, {"job_id": str(job_id)})
    metrics.incr("redis_xadd_total")
    return msg_id


async def xread_jobs(
    client: Redis,
    settings: Settings,
    *,
    consumer_name: str,
    count: int = 1,
    block_ms: int = 5000,
) -> list[tuple[str, str, dict[str, str]]]:
    """Return list of (stream, message_id, fields)."""
    stream = media_jobs_stream(settings)
    group = media_jobs_consumer_group(settings)
    raw = await client.xreadgroup(
        groupname=group,
        consumername=consumer_name,
        streams={stream: ">"},
        count=count,
        block=block_ms,
    )
    out: list[tuple[str, str, dict[str, str]]] = []
    if not raw:
        return out
    for stream_name, messages in raw:
        for msg_id, fields in messages:
            out.append((stream_name, msg_id, fields))
    return out


async def xack_job(
    client: Redis,
    settings: Settings,
    *,
    message_id: str,
) -> None:
    stream = media_jobs_stream(settings)
    group = media_jobs_consumer_group(settings)
    await client.xack(stream, group, message_id)
    metrics.incr("redis_xack_total")


async def stream_length(client: Redis, settings: Settings) -> int:
    stream = media_jobs_stream(settings)
    try:
        return int(await client.xlen(stream))
    except Exception:
        logger.exception("media_stream_length_failed")
        return 0


async def pending_summary(client: Redis, settings: Settings) -> dict[str, Any]:
    stream = media_jobs_stream(settings)
    group = media_jobs_consumer_group(settings)
    try:
        info = await client.xpending(stream, group)
        # (pending_count, min_id, max_id, [(consumer, count), ...])
        return {
            "pending": int(info[0]) if info else 0,
        }
    except Exception:
        return {"pending": 0}
