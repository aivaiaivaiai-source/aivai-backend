"""Background workers for AI search assistants.

1) Match worker — drains Redis/memory queue and emits chat matches.
2) Maintenance — expires stale subscriptions and deactivates their tasks.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime

from sqlalchemy import select, update

from app.core import ai_agent_metrics as metrics
from app.core.config import Settings, get_settings
from app.db.session import async_session_maker
from app.models.ai_enums import AiSubscriptionStatus
from app.models.ai_search_task import AiSearchTask
from app.models.ai_subscription import AiSubscription
from app.repositories.ai_agent_repository import AiAgentRepository
from app.repositories.ai_search_task_repository import AiSearchTaskRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.listing_repository import ListingRepository
from app.repositories.notification_repository import NotificationRepository
from app.services.ai_match_queue import dequeue_listing_for_ai_match
from app.services.ai_search_service import AiSearchService

logger = logging.getLogger(__name__)


async def _process_listing_match(listing_id: int) -> None:
    started = time.perf_counter()
    async with async_session_maker() as session:
        listings = ListingRepository(session)
        listing = await listings.get_by_id(listing_id)
        if listing is None:
            return
        search = AiSearchService(
            session,
            CategoryRepository(session),
            AiSearchTaskRepository(session, listings),
            AiAgentRepository(session),
            NotificationRepository(session),
        )
        await search.emit_matches_for_listing(listing)
        await session.commit()
    metrics.observe_match_latency_ms((time.perf_counter() - started) * 1000)
    metrics.incr("match_ok_total")


async def expire_stale_ai_subscriptions() -> int:
    """Mark expired active subscriptions and stop their monitoring tasks."""
    now = datetime.now(UTC)
    async with async_session_maker() as session:
        stmt = (
            select(AiSubscription.id)
            .where(
                AiSubscription.status == AiSubscriptionStatus.active,
                AiSubscription.expires_at <= now,
            )
            .limit(500)
        )
        result = await session.execute(stmt)
        ids = list(result.scalars().all())
        if not ids:
            return 0

        await session.execute(
            update(AiSubscription)
            .where(AiSubscription.id.in_(ids))
            .values(status=AiSubscriptionStatus.expired)
        )
        await session.execute(
            update(AiSearchTask)
            .where(
                AiSearchTask.subscription_id.in_(ids),
                AiSearchTask.is_active.is_(True),
            )
            .values(is_active=False)
        )
        await session.commit()
        metrics.incr("expired_subscriptions_total", len(ids))
        return len(ids)


async def ai_match_worker_loop(
    *,
    stop_event: asyncio.Event | None = None,
) -> None:
    stop = stop_event or asyncio.Event()
    logger.info("ai_match_worker started")

    while not stop.is_set():
        try:
            listing_id = await dequeue_listing_for_ai_match(timeout=1.0)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("ai_match_worker dequeue failed")
            await asyncio.sleep(0.5)
            continue

        if listing_id is None:
            continue

        try:
            await _process_listing_match(listing_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            metrics.incr("match_error_total")
            logger.exception("ai_match_worker failed listing_id=%s", listing_id)

    logger.info("ai_match_worker stopped")


async def ai_maintenance_loop(
    *,
    settings: Settings | None = None,
    stop_event: asyncio.Event | None = None,
    interval_seconds: float | None = None,
) -> None:
    cfg = settings or get_settings()
    seconds = interval_seconds if interval_seconds is not None else float(
        getattr(cfg, "AI_AGENT_MAINTENANCE_INTERVAL_SECONDS", 300)
    )
    seconds = max(30.0, seconds)
    stop = stop_event or asyncio.Event()
    logger.info("ai_maintenance_loop started interval_seconds=%s", seconds)

    while not stop.is_set():
        try:
            n = await expire_stale_ai_subscriptions()
            if n:
                logger.info("ai_maintenance expired_subscriptions=%d", n)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("ai_maintenance_loop failed")

        try:
            await asyncio.wait_for(stop.wait(), timeout=seconds)
            break
        except TimeoutError:
            continue

    logger.info("ai_maintenance_loop stopped")
