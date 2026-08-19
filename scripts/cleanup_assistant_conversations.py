#!/usr/bin/env python3
"""Delete assistant conversations inactive longer than the configured TTL.

Usage (from project root):
    python -m scripts.cleanup_assistant_conversations
    python -m scripts.cleanup_assistant_conversations --ttl-days 7
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import get_settings
from app.db.session import async_session_maker
from app.services.assistant_conversation_cleanup_service import (
    cleanup_inactive_assistant_conversations,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _run(ttl_days: int) -> int:
    settings = get_settings()
    async with async_session_maker() as session:
        result = await cleanup_inactive_assistant_conversations(
            session,
            ttl_days,
            batch_size=settings.ASSISTANT_CONVERSATION_CLEANUP_BATCH_SIZE,
            max_batches=settings.ASSISTANT_CONVERSATION_CLEANUP_MAX_BATCHES,
            batch_pause_seconds=max(0, settings.ASSISTANT_CONVERSATION_CLEANUP_BATCH_PAUSE_MS)
            / 1000.0,
            use_advisory_lock=True,
        )
    logger.info(
        "assistant_conversation_cleanup finished deleted=%d batches=%d skipped_lock=%s "
        "ttl_days=%d cutoff=%s",
        result.deleted_count,
        result.batch_count,
        result.skipped_lock,
        result.ttl_days,
        result.cutoff.isoformat(),
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(
        description="Delete assistant conversations inactive longer than TTL days",
    )
    parser.add_argument(
        "--ttl-days",
        type=int,
        default=settings.ASSISTANT_CONVERSATION_TTL_DAYS,
        help=(
            "Delete conversations with last_activity_at older than this many days "
            f"(default: {settings.ASSISTANT_CONVERSATION_TTL_DAYS})"
        ),
    )
    args = parser.parse_args(argv)

    if args.ttl_days < 0:
        parser.error("--ttl-days must be non-negative")

    return asyncio.run(_run(args.ttl_days))


if __name__ == "__main__":
    raise SystemExit(main())
