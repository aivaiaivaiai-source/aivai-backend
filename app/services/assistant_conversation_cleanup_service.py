from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.assistant_conversation_repository import AssistantConversationRepository

logger = logging.getLogger(__name__)

DEFAULT_ASSISTANT_CONVERSATION_TTL_DAYS = 7

# Stable Postgres advisory-lock key (session-level). Only one cleaner runs cluster-wide.
ASSISTANT_CONVERSATION_CLEANUP_LOCK_KEY = 872_451_003


@dataclass(frozen=True)
class AssistantConversationCleanupResult:
    deleted_count: int
    ttl_days: int
    cutoff: datetime
    batch_count: int = 0
    skipped_lock: bool = False


async def try_acquire_cleanup_lock(session: AsyncSession, *, lock_key: int) -> bool:
    result = await session.execute(
        text("SELECT pg_try_advisory_lock(:key)"),
        {"key": lock_key},
    )
    return bool(result.scalar())


async def release_cleanup_lock(session: AsyncSession, *, lock_key: int) -> None:
    await session.execute(
        text("SELECT pg_advisory_unlock(:key)"),
        {"key": lock_key},
    )


async def cleanup_inactive_assistant_conversations(
    session: AsyncSession,
    ttl_days: int,
    *,
    now: datetime | None = None,
    batch_size: int = 2000,
    max_batches: int = 500,
    batch_pause_seconds: float = 0.05,
    use_advisory_lock: bool = True,
    lock_key: int = ASSISTANT_CONVERSATION_CLEANUP_LOCK_KEY,
    sleep=None,
) -> AssistantConversationCleanupResult:
    """Delete inactive assistant conversations in batches.

    Uses a Postgres advisory lock so only one API replica / script cleans at a time.
    Commits after each batch to keep transactions short under load.
    """
    if ttl_days < 0:
        raise ValueError("ttl_days must be non-negative")
    if batch_size < 1:
        raise ValueError("batch_size must be >= 1")
    if max_batches < 1:
        raise ValueError("max_batches must be >= 1")

    moment = now or datetime.now(UTC)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    cutoff = moment - timedelta(days=ttl_days)

    if use_advisory_lock:
        locked = await try_acquire_cleanup_lock(session, lock_key=lock_key)
        if not locked:
            logger.info(
                "assistant_conversation_cleanup skipped reason=lock_held lock_key=%s",
                lock_key,
            )
            return AssistantConversationCleanupResult(
                deleted_count=0,
                ttl_days=ttl_days,
                cutoff=cutoff,
                skipped_lock=True,
            )

    sleeper = sleep
    if sleeper is None:
        import asyncio

        sleeper = asyncio.sleep

    repo = AssistantConversationRepository(session)
    total_deleted = 0
    batches = 0

    try:
        while batches < max_batches:
            deleted = await repo.delete_inactive_before_batch(cutoff, limit=batch_size)
            await session.commit()
            batches += 1
            total_deleted += deleted
            if deleted < batch_size:
                break
            if batch_pause_seconds > 0:
                await sleeper(batch_pause_seconds)
    finally:
        if use_advisory_lock:
            try:
                await release_cleanup_lock(session, lock_key=lock_key)
                await session.commit()
            except Exception:
                logger.exception(
                    "assistant_conversation_cleanup unlock_failed lock_key=%s",
                    lock_key,
                )

    result = AssistantConversationCleanupResult(
        deleted_count=total_deleted,
        ttl_days=ttl_days,
        cutoff=cutoff,
        batch_count=batches,
    )
    logger.info(
        "assistant_conversation_cleanup deleted=%d batches=%d ttl_days=%d cutoff=%s",
        result.deleted_count,
        result.batch_count,
        result.ttl_days,
        result.cutoff.isoformat(),
    )
    return result
