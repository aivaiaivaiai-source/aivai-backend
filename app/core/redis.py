"""Redis client for AI match queue / realtime pub-sub.

Falls back gracefully when Redis is unreachable (local memory path).
"""

from __future__ import annotations

import logging
from typing import Any

from redis.asyncio import Redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_redis: Redis | None = None
_redis_ok: bool | None = None


async def init_redis() -> Redis | None:
    global _redis, _redis_ok
    settings = get_settings()
    url = (settings.REDIS_URL or "").strip()
    if not url:
        logger.info("redis disabled (REDIS_URL empty)")
        _redis = None
        _redis_ok = False
        return None
    client = Redis.from_url(url, decode_responses=True)
    try:
        await client.ping()
    except Exception:
        logger.exception("redis ping failed url=%s — using in-memory fallback", url)
        await client.aclose()
        _redis = None
        _redis_ok = False
        return None
    _redis = client
    _redis_ok = True
    logger.info("redis connected")
    return client


async def close_redis() -> None:
    global _redis, _redis_ok
    if _redis is not None:
        await _redis.aclose()
    _redis = None
    _redis_ok = False


def get_redis() -> Redis | None:
    return _redis


def redis_available() -> bool:
    return bool(_redis_ok and _redis is not None)


async def redis_publish(channel: str, message: str) -> None:
    client = get_redis()
    if client is None:
        return
    try:
        await client.publish(channel, message)
    except Exception:
        logger.exception("redis_publish failed channel=%s", channel)


async def redis_info() -> dict[str, Any]:
    return {
        "available": redis_available(),
        "url_configured": bool((get_settings().REDIS_URL or "").strip()),
    }
