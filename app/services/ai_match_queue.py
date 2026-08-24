"""AI listing-match job queue with Redis + in-memory fallback and dedup.

Enqueue is idempotent per ``listing_id`` while the id is still pending.
"""

from __future__ import annotations

import asyncio
import logging

from app.core import ai_agent_metrics as metrics
from app.core.redis import get_redis, redis_available

logger = logging.getLogger(__name__)

_QUEUE_KEY = "ai:match:queue"
_PENDING_KEY = "ai:match:pending"

_memory_queue: asyncio.Queue[int] | None = None
_memory_pending: set[int] = set()
_memory_lock = asyncio.Lock()
_MAX_MEMORY = 5000


def _mem_queue() -> asyncio.Queue[int]:
    global _memory_queue
    if _memory_queue is None:
        _memory_queue = asyncio.Queue(maxsize=_MAX_MEMORY)
    return _memory_queue


async def enqueue_listing_for_ai_match(listing_id: int) -> bool:
    """Return True if newly enqueued, False if deduped / dropped."""
    if redis_available():
        return await _enqueue_redis(listing_id)
    return await _enqueue_memory(listing_id)


async def dequeue_listing_for_ai_match(*, timeout: float = 1.0) -> int | None:
    if redis_available():
        return await _dequeue_redis(timeout=timeout)
    return await _dequeue_memory(timeout=timeout)


async def queue_depth() -> int:
    client = get_redis()
    if client is not None and redis_available():
        try:
            return int(await client.llen(_QUEUE_KEY))
        except Exception:
            logger.exception("queue_depth redis failed")
    q = _mem_queue()
    return q.qsize()


async def _enqueue_redis(listing_id: int) -> bool:
    client = get_redis()
    assert client is not None
    try:
        added = await client.sadd(_PENDING_KEY, listing_id)
        if not added:
            metrics.incr("enqueue_deduped")
            return False
        await client.rpush(_QUEUE_KEY, listing_id)
        metrics.incr("enqueue_total")
        return True
    except Exception:
        logger.exception("enqueue redis failed listing_id=%s — memory fallback", listing_id)
        return await _enqueue_memory(listing_id)


async def _dequeue_redis(*, timeout: float) -> int | None:
    client = get_redis()
    assert client is not None
    try:
        item = await client.blpop(_QUEUE_KEY, timeout=max(1, int(timeout)))
        if not item:
            return None
        listing_id = int(item[1])
        await client.srem(_PENDING_KEY, listing_id)
        metrics.incr("dequeue_total")
        return listing_id
    except Exception:
        logger.exception("dequeue redis failed")
        return None


async def _enqueue_memory(listing_id: int) -> bool:
    async with _memory_lock:
        if listing_id in _memory_pending:
            metrics.incr("enqueue_deduped")
            return False
        q = _mem_queue()
        if q.full():
            logger.warning("ai_match_queue_full listing_id=%s size=%s", listing_id, q.qsize())
            return False
        _memory_pending.add(listing_id)
        q.put_nowait(listing_id)
        metrics.incr("enqueue_total")
        return True


async def _dequeue_memory(*, timeout: float) -> int | None:
    q = _mem_queue()
    try:
        listing_id = await asyncio.wait_for(q.get(), timeout=timeout)
    except TimeoutError:
        return None
    async with _memory_lock:
        _memory_pending.discard(listing_id)
    metrics.incr("dequeue_total")
    return listing_id
