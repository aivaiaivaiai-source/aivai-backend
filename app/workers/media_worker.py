"""Media Platform worker — separate process from FastAPI."""

from __future__ import annotations

import asyncio
import logging
import os
import signal
from typing import Any

from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.core.redis import close_redis, init_redis, redis_available
from app.db.session import async_session_maker
from app.media_queue import metrics
from app.media_engine import build_media_engine
from app.media_queue.job_service import MediaJobService, run_outbox_and_reconcile
from app.media_queue.streams import ensure_consumer_group, stream_length, xread_jobs

logger = logging.getLogger(__name__)


def _consumer_name(settings: Settings) -> str:
    explicit = (settings.MEDIA_WORKER_CONSUMER_NAME or "").strip()
    if explicit:
        return explicit
    return f"media-worker-{os.getpid()}"


async def media_worker_loop(*, stop_event: asyncio.Event) -> None:
    settings = get_settings()
    worker_id = _consumer_name(settings)
    logger.info(
        "media_worker_started worker_id=%s async_pipeline=%s namespace=%s",
        worker_id,
        settings.MEDIA_ASYNC_PIPELINE_ENABLED,
        settings.MEDIA_QUEUE_NAMESPACE,
    )

    if not settings.MEDIA_ASYNC_PIPELINE_ENABLED:
        logger.warning("media_worker idle — MEDIA_ASYNC_PIPELINE_ENABLED=false")
        await stop_event.wait()
        return

    client = await init_redis()
    if client is None or not redis_available():
        logger.error("media_worker cannot start — Redis unavailable")
        await stop_event.wait()
        return

    await ensure_consumer_group(client, settings)
    current_job_task: asyncio.Task[Any] | None = None

    while not stop_event.is_set():
        try:
            async with async_session_maker() as session:
                await run_outbox_and_reconcile(session, client, settings)
                from app.services.media_storage_cleanup_service import (
                    MediaStorageCleanupService,
                )
                from app.services.storage_service import StorageService

                cleanup = MediaStorageCleanupService(
                    session,
                    StorageService(settings),
                    settings,
                )
                await cleanup.expire_abandoned_uploads()
                await cleanup.process_pending()
                if settings.MEDIA_AI_CLASSIFICATION_ENABLED:
                    from app.services.media_classification_service import (
                        MediaClassificationService,
                    )

                    clf = MediaClassificationService(session, settings)
                    await clf.process_available(limit=2, worker_id=worker_id)
                if settings.MEDIA_VISUAL_EVIDENCE_ENABLED:
                    from app.services.visual_evidence_service import VisualEvidenceService

                    ve = VisualEvidenceService(session, settings)
                    await ve.process_available(limit=2, worker_id=worker_id)
                await session.commit()
                depth = await stream_length(client, settings)
                metrics.set_gauge("queue_depth", depth)

            messages = await xread_jobs(
                client,
                settings,
                consumer_name=worker_id,
                count=1,
                block_ms=min(settings.MEDIA_WORKER_BLOCK_MS, 1000),
            )
            if not messages:
                continue

            for _stream, msg_id, fields in messages:
                if stop_event.is_set():
                    break
                raw_job_id = fields.get("job_id")
                if not raw_job_id:
                    logger.warning("media_stream_missing_job_id msg_id=%s", msg_id)
                    from app.media_queue.streams import xack_job

                    await xack_job(client, settings, message_id=msg_id)
                    continue
                job_id = int(raw_job_id)

                async def _run(job_id: int = job_id, msg_id: str = msg_id) -> None:
                    async with async_session_maker() as session:
                        processor = build_media_engine(settings)
                        svc = MediaJobService(session, settings, processor=processor)
                        await svc.process_stream_message(
                            client,
                            job_id=job_id,
                            message_id=msg_id,
                            worker_id=worker_id,
                        )

                current_job_task = asyncio.create_task(_run())
                try:
                    await asyncio.wait_for(
                        current_job_task,
                        timeout=settings.MEDIA_JOB_PROCESSING_TIMEOUT_SECONDS,
                    )
                except TimeoutError:
                    logger.error("media_job_timeout job_id=%s", job_id)
                    current_job_task.cancel()
                    metrics.incr("jobs_timeout_total")
                finally:
                    current_job_task = None
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("media_worker_loop_error")
            await asyncio.sleep(1.0)

    if current_job_task is not None and not current_job_task.done():
        current_job_task.cancel()
        try:
            await current_job_task
        except asyncio.CancelledError:
            pass

    await close_redis()
    logger.info("media_worker_stopped worker_id=%s", worker_id)


async def _async_main() -> None:
    configure_logging()
    stop = asyncio.Event()

    def _handle_sig(*_args: object) -> None:
        logger.info("media_worker_sigterm")
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_sig)
        except NotImplementedError:
            signal.signal(sig, lambda *_: stop.set())

    await media_worker_loop(stop_event=stop)


def main() -> None:
    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
