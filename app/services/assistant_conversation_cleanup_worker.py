from __future__ import annotations

import asyncio
import logging

from app.core.config import Settings, get_settings
from app.db.session import async_session_maker
from app.services.assistant_conversation_cleanup_service import (
    cleanup_inactive_assistant_conversations,
)

logger = logging.getLogger(__name__)


async def run_assistant_conversation_cleanup_once(
    *,
    settings: Settings | None = None,
) -> int:
    cfg = settings or get_settings()
    async with async_session_maker() as session:
        result = await cleanup_inactive_assistant_conversations(
            session,
            cfg.ASSISTANT_CONVERSATION_TTL_DAYS,
            batch_size=cfg.ASSISTANT_CONVERSATION_CLEANUP_BATCH_SIZE,
            max_batches=cfg.ASSISTANT_CONVERSATION_CLEANUP_MAX_BATCHES,
            batch_pause_seconds=max(0, cfg.ASSISTANT_CONVERSATION_CLEANUP_BATCH_PAUSE_MS) / 1000.0,
            use_advisory_lock=True,
        )
        if result.skipped_lock:
            logger.info("assistant_conversation_cleanup auto_run skipped_lock=true")
            return 0
        return result.deleted_count


async def assistant_conversation_cleanup_loop(
    *,
    settings: Settings | None = None,
    stop_event: asyncio.Event | None = None,
    interval_seconds: float | None = None,
) -> None:
    """Periodically delete inactive assistant conversations while the API is running."""
    cfg = settings or get_settings()
    if not cfg.ASSISTANT_CONVERSATION_CLEANUP_ENABLED:
        logger.info("assistant_conversation_cleanup disabled")
        return

    if interval_seconds is None:
        seconds = max(60.0, float(cfg.ASSISTANT_CONVERSATION_CLEANUP_INTERVAL_HOURS) * 3600.0)
    else:
        seconds = max(0.01, float(interval_seconds))
    stop = stop_event or asyncio.Event()

    logger.info(
        "assistant_conversation_cleanup loop started ttl_days=%d interval_seconds=%s "
        "batch_size=%d max_batches=%d",
        cfg.ASSISTANT_CONVERSATION_TTL_DAYS,
        seconds,
        cfg.ASSISTANT_CONVERSATION_CLEANUP_BATCH_SIZE,
        cfg.ASSISTANT_CONVERSATION_CLEANUP_MAX_BATCHES,
    )

    while not stop.is_set():
        try:
            deleted = await run_assistant_conversation_cleanup_once(settings=cfg)
            logger.info("assistant_conversation_cleanup auto_run deleted=%d", deleted)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("assistant_conversation_cleanup auto_run failed")

        try:
            await asyncio.wait_for(stop.wait(), timeout=seconds)
            break
        except TimeoutError:
            continue

    logger.info("assistant_conversation_cleanup loop stopped")
