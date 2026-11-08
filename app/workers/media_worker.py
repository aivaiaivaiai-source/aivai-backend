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

# Process-local readiness: True after publish-critical pipeline models are loaded.
_WORKER_MODELS_READY = False
# Visual Evidence / SigLIP — separate from media-job readiness.
_VE_MODELS_READY = False


def media_worker_models_ready() -> bool:
    return _WORKER_MODELS_READY


def media_worker_ve_models_ready() -> bool:
    return _VE_MODELS_READY


def _consumer_name(settings: Settings) -> str:
    explicit = (settings.MEDIA_WORKER_CONSUMER_NAME or "").strip()
    if explicit:
        return explicit
    return f"media-worker-{os.getpid()}"


async def preload_media_pipeline_models(settings: Settings) -> None:
    """
    Load models required for publish-critical media jobs (variants / AUTO focus).

    Visual Evidence (SigLIP2) is NOT on this path — it runs on the idle loop and
    must not block claiming media jobs after a cold worker start.
    """
    loop = asyncio.get_running_loop()

    if settings.FOCUS_BBOX_ENABLED and (settings.FOCUS_BBOX_MODEL_ID or "").strip():
        from app.media_engine.engine import _get_detector

        logger.info(
            "media_worker_preload_focus_bbox model=%s",
            settings.FOCUS_BBOX_MODEL_ID,
        )
        await loop.run_in_executor(
            None,
            lambda: _get_detector(
                settings.FOCUS_BBOX_MODEL_ID,
                settings.FOCUS_BBOX_MIN_CONFIDENCE,
                settings.MEDIA_DETECTOR_INFERENCE_MAX_EDGE,
            ),
        )


async def preload_visual_evidence_models(settings: Settings) -> None:
    """Background warm-up for SigLIP2 — does not gate media job readiness."""
    global _VE_MODELS_READY
    if not settings.MEDIA_VISUAL_EVIDENCE_ENABLED:
        _VE_MODELS_READY = True
        return
    if settings.MEDIA_VISUAL_EVIDENCE_USE_STUB:
        _VE_MODELS_READY = True
        return
    loop = asyncio.get_running_loop()
    from app.visual_evidence.siglip2_runtime import get_siglip2_runtime

    logger.info("media_worker_preload_siglip2_bg")
    try:
        runtime = get_siglip2_runtime()
        await loop.run_in_executor(None, runtime.prepare)
        _VE_MODELS_READY = True
        logger.info("media_worker_siglip2_ready=1")
    except Exception:
        logger.exception("media_worker_siglip2_preload_failed")
        # Allow idle VE loop to retry lazily; do not block media jobs.
        _VE_MODELS_READY = True


async def preload_media_worker_models(settings: Settings) -> None:
    """
    Publish-critical preload + mark worker ready for media jobs.

    Kept as the public test entrypoint; SigLIP is intentionally deferred.
    """
    global _WORKER_MODELS_READY
    await preload_media_pipeline_models(settings)
    _WORKER_MODELS_READY = True
    logger.info("media_worker_models_ready=1")


async def media_worker_loop(*, stop_event: asyncio.Event) -> None:
    global _WORKER_MODELS_READY
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
        _WORKER_MODELS_READY = True
        await stop_event.wait()
        return

    client = await init_redis()
    if client is None or not redis_available():
        logger.error("media_worker cannot start — Redis unavailable")
        await stop_event.wait()
        return

    await ensure_consumer_group(client, settings)

    # READY = can claim media jobs (pipeline models). VE warms in background.
    try:
        await preload_media_worker_models(settings)
    except Exception:
        logger.exception("media_worker_model_preload_failed — continuing with lazy load")
        _WORKER_MODELS_READY = True

    ve_task: asyncio.Task[Any] | None = None
    if settings.MEDIA_VISUAL_EVIDENCE_ENABLED and not settings.MEDIA_VISUAL_EVIDENCE_USE_STUB:
        ve_task = asyncio.create_task(preload_visual_evidence_models(settings))

    current_job_task: asyncio.Task[Any] | None = None

    while not stop_event.is_set():
        try:
            # Publish-critical path first: outbox → claim media jobs.
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

            if messages:
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
                continue

            # Secondary AI loops only when idle AND heavy VE models are ready.
            # Running SigLIP/classification before preload finishes starves media jobs.
            if ve_task is not None and not ve_task.done() and not _VE_MODELS_READY:
                await asyncio.sleep(0.05)
                continue

            async with async_session_maker() as session:
                if settings.MEDIA_AI_CLASSIFICATION_ENABLED:
                    from app.services.media_classification_service import (
                        MediaClassificationService,
                    )

                    clf = MediaClassificationService(session, settings)
                    try:
                        await asyncio.wait_for(
                            clf.process_available(limit=2, worker_id=worker_id),
                            timeout=30.0,
                        )
                    except TimeoutError:
                        logger.warning("media_classification_slice_timeout")
                if settings.MEDIA_VISUAL_EVIDENCE_ENABLED and _VE_MODELS_READY:
                    from app.services.visual_evidence_service import VisualEvidenceService

                    ve = VisualEvidenceService(session, settings)
                    try:
                        await asyncio.wait_for(
                            ve.process_available(limit=2, worker_id=worker_id),
                            timeout=float(
                                max(30, settings.MEDIA_VISUAL_EVIDENCE_TIMEOUT_SECONDS)
                            ),
                        )
                    except TimeoutError:
                        logger.warning("media_visual_evidence_slice_timeout")
                await session.commit()
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
    if ve_task is not None and not ve_task.done():
        ve_task.cancel()
        try:
            await ve_task
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
