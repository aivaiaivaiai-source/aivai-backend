from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import Settings
from app.media_queue.errors import PermanentMediaJobError, RetryableMediaJobError
from app.media_queue.job_service import MediaJobService, retry_backoff_seconds
from app.media_queue.namespace import media_jobs_stream, media_queue_prefix
from app.media_queue.processor import MediaProcessorOutcome, NoOpMediaProcessor
from app.media_queue.streams import xadd_job
from app.models.media_enums import MediaLifecycleStatus
from app.models.media_job import build_media_job_idempotency_key
from app.models.media_job_enums import MediaJobStatus, MediaOutboxStatus
from app.services.media_lifecycle import lifecycle_after_upload
from app.models.image_moderation_enums import MediaModerationStatus


def test_idempotency_key_includes_pipeline_version() -> None:
    k1 = build_media_job_idempotency_key(5, "v1")
    k2 = build_media_job_idempotency_key(5, "v2")
    assert k1 != k2
    assert k1 == "media:5:pipeline:v1"


def test_namespace_isolated_from_ai_agents() -> None:
    settings = Settings(MEDIA_QUEUE_NAMESPACE="aivai:media")
    assert media_queue_prefix(settings) == "aivai:media"
    assert media_jobs_stream(settings).startswith("aivai:media:")
    assert not media_jobs_stream(settings).startswith("ai:")


def test_lifecycle_async_upload_queued_not_ready() -> None:
    assert (
        lifecycle_after_upload(
            MediaModerationStatus.approved,
            async_pipeline_enabled=True,
        )
        == MediaLifecycleStatus.queued
    )
    assert (
        lifecycle_after_upload(
            MediaModerationStatus.approved,
            async_pipeline_enabled=False,
        )
        == MediaLifecycleStatus.ready
    )


def test_retry_backoff_from_settings() -> None:
    s = Settings(MEDIA_JOB_RETRY_BACKOFF_SECONDS="15,60,300")
    assert retry_backoff_seconds(s, 1) == 15
    assert retry_backoff_seconds(s, 2) == 60
    assert retry_backoff_seconds(s, 99) == 300


@pytest.mark.asyncio
async def test_redis_payload_minimal_job_id_only() -> None:
    client = AsyncMock()
    client.xadd = AsyncMock(return_value="1-0")
    settings = Settings(MEDIA_QUEUE_NAMESPACE="aivai:media")
    await xadd_job(client, settings, 42)
    args, kwargs = client.xadd.call_args
    assert args[1] == {"job_id": "42"}
    assert "media_id" not in args[1]
    assert "path" not in args[1]


@pytest.mark.asyncio
async def test_enqueue_creates_job_and_outbox_once() -> None:
    session = MagicMock()
    settings = Settings()
    jobs_repo = MagicMock()
    jobs_repo.get_by_idempotency_key = AsyncMock(return_value=None)
    created_job = SimpleNamespace(id=7, media_id=3, status=MediaJobStatus.queued)
    jobs_repo.create = AsyncMock(return_value=created_job)
    outbox_repo = MagicMock()
    outbox_repo.create_enqueue_event = AsyncMock(return_value=SimpleNamespace(id=1))

    svc = MediaJobService(session, settings)
    svc._jobs = jobs_repo
    svc._outbox = outbox_repo

    job = await svc.enqueue_for_media(3, pipeline_version="v1")
    assert job.id == 7
    outbox_repo.create_enqueue_event.assert_awaited_once_with(7, suffix="enqueue")

    jobs_repo.get_by_idempotency_key = AsyncMock(return_value=created_job)
    again = await svc.enqueue_for_media(3, pipeline_version="v1")
    assert again.id == 7


@pytest.mark.asyncio
async def test_succeeded_job_redelivery_is_noop_and_acks() -> None:
    settings = Settings()
    redis = AsyncMock()
    session = MagicMock()
    job = SimpleNamespace(
        id=1,
        media_id=2,
        status=MediaJobStatus.succeeded,
        attempt_count=1,
        lease_owner=None,
        lease_until=None,
    )
    jobs_repo = MagicMock()
    jobs_repo.get_by_id_for_update = AsyncMock(return_value=job)
    jobs_repo.get_by_id = AsyncMock(return_value=job)

    svc = MediaJobService(session, settings)
    svc._jobs = jobs_repo
    svc._processor = NoOpMediaProcessor()

    with patch("app.media_queue.job_service.xack_job", new_callable=AsyncMock) as ack:
        ok = await svc.process_stream_message(
            redis,
            job_id=1,
            message_id="1-0",
            worker_id="w1",
        )
    assert ok is True
    ack.assert_awaited_once()
    svc._processor.process = AsyncMock()  # type: ignore[method-assign]
    assert not svc._processor.process.called  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_active_lease_blocks_other_worker() -> None:
    settings = Settings()
    redis = AsyncMock()
    session = MagicMock()
    now = datetime.now(UTC)
    job = SimpleNamespace(
        id=1,
        media_id=2,
        status=MediaJobStatus.leased,
        attempt_count=1,
        lease_owner="worker-a",
        lease_until=now + timedelta(minutes=5),
    )
    jobs_repo = MagicMock()
    jobs_repo.get_by_id_for_update = AsyncMock(return_value=job)
    jobs_repo.get_by_id = AsyncMock(return_value=job)
    jobs_repo.claim_job = AsyncMock(return_value=None)

    svc = MediaJobService(session, settings)
    svc._jobs = jobs_repo

    ok = await svc.process_stream_message(
        redis,
        job_id=1,
        message_id="1-0",
        worker_id="worker-b",
    )
    assert ok is False


@pytest.mark.asyncio
async def test_max_attempts_marks_dead_and_media_failed() -> None:
    settings = Settings(MEDIA_JOB_MAX_ATTEMPTS=2)
    redis = AsyncMock()
    session = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    now = datetime.now(UTC)
    job = SimpleNamespace(
        id=1,
        media_id=2,
        status=MediaJobStatus.leased,
        attempt_count=2,
        lease_owner="w1",
        lease_until=now + timedelta(minutes=1),
    )
    media = SimpleNamespace(
        id=2,
        lifecycle_status=MediaLifecycleStatus.processing,
        error_code=None,
        error_message=None,
    )
    jobs_repo = MagicMock()
    jobs_repo.get_by_id_for_update = AsyncMock(return_value=job)
    jobs_repo.claim_job = AsyncMock(return_value=job)
    jobs_repo.get_by_id = AsyncMock(return_value=media)
    media_repo = MagicMock()
    media_repo.get_by_id = AsyncMock(return_value=media)
    outbox_repo = MagicMock()
    outbox_repo.create_enqueue_event = AsyncMock()

    svc = MediaJobService(session, settings)
    svc._jobs = jobs_repo
    svc._media = media_repo
    svc._outbox = outbox_repo
    svc._processor = MagicMock()
    svc._processor.process = AsyncMock(
        side_effect=RetryableMediaJobError("temporary"),
    )

    with patch("app.media_queue.job_service.xack_job", new_callable=AsyncMock):
        await svc.process_stream_message(
            redis,
            job_id=1,
            message_id="1-0",
            worker_id="w1",
        )

    assert job.status == MediaJobStatus.dead
    assert media.lifecycle_status == MediaLifecycleStatus.failed


@pytest.mark.asyncio
async def test_outbox_dispatch_marks_dispatched() -> None:
    from app.media_queue.outbox_dispatcher import dispatch_pending_outbox

    session = MagicMock()
    session.commit = AsyncMock()
    redis = AsyncMock()
    settings = Settings()
    row = SimpleNamespace(id=10, job_id=5)
    repo = MagicMock()
    repo.list_pending = AsyncMock(return_value=[row])
    repo.mark_dispatched = AsyncMock(return_value=True)

    with patch("app.media_queue.outbox_dispatcher.MediaOutboxRepository", return_value=repo):
        with patch("app.media_queue.outbox_dispatcher.xadd_job", new_callable=AsyncMock):
            n = await dispatch_pending_outbox(session, redis, settings)
    assert n == 1
    session.commit.assert_awaited()


def test_feature_flag_default_false() -> None:
    s = Settings()
    assert s.MEDIA_ASYNC_PIPELINE_ENABLED is False


def _job_row(**overrides: object) -> SimpleNamespace:
    now = datetime.now(UTC)
    defaults = dict(
        id=1,
        media_id=2,
        status=MediaJobStatus.queued,
        attempt_count=0,
        lease_owner=None,
        lease_until=None,
        available_at=now,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _media_row(**overrides: object) -> SimpleNamespace:
    defaults = dict(
        id=2,
        lifecycle_status=MediaLifecycleStatus.queued,
        original_storage_key="media/1/2/original.jpg",
        error_code=None,
        error_message=None,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


@pytest.mark.asyncio
async def test_expired_lease_allows_reclaim() -> None:
    settings = Settings()
    redis = AsyncMock()
    session = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    now = datetime.now(UTC)
    job = _job_row(
        status=MediaJobStatus.leased,
        lease_owner="worker-a",
        lease_until=now - timedelta(seconds=30),
        attempt_count=1,
    )
    claimed = _job_row(
        status=MediaJobStatus.leased,
        lease_owner="worker-b",
        attempt_count=2,
    )
    media = _media_row(lifecycle_status=MediaLifecycleStatus.queued)
    jobs_repo = MagicMock()
    jobs_repo.get_by_id_for_update = AsyncMock(return_value=job)
    jobs_repo.claim_job = AsyncMock(return_value=claimed)
    jobs_repo.get_by_id = AsyncMock(return_value=media)
    media_repo = MagicMock()
    media_repo.get_by_id = AsyncMock(return_value=media)

    svc = MediaJobService(session, settings)
    svc._jobs = jobs_repo
    svc._media = media_repo

    with patch("app.media_queue.job_service.xack_job", new_callable=AsyncMock):
        ok = await svc.process_stream_message(
            redis,
            job_id=1,
            message_id="1-0",
            worker_id="worker-b",
        )
    assert ok is True
    jobs_repo.claim_job.assert_awaited_once()


@pytest.mark.asyncio
async def test_claim_race_only_one_worker_wins() -> None:
    settings = Settings()
    redis = AsyncMock()
    session = MagicMock()
    now = datetime.now(UTC)
    job = _job_row(status=MediaJobStatus.queued, available_at=now)
    jobs_repo = MagicMock()
    jobs_repo.get_by_id_for_update = AsyncMock(return_value=job)
    jobs_repo.claim_job = AsyncMock(side_effect=[None, None])
    jobs_repo.get_by_id = AsyncMock(return_value=job)

    svc = MediaJobService(session, settings)
    svc._jobs = jobs_repo

    ok_a = await svc.process_stream_message(
        redis, job_id=1, message_id="1-0", worker_id="a",
    )
    ok_b = await svc.process_stream_message(
        redis, job_id=1, message_id="2-0", worker_id="b",
    )
    assert ok_a is False
    assert ok_b is False


@pytest.mark.asyncio
async def test_retryable_failure_schedules_backoff_and_outbox() -> None:
    settings = Settings(MEDIA_JOB_MAX_ATTEMPTS=5)
    redis = AsyncMock()
    session = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    now = datetime.now(UTC)
    job = _job_row(
        status=MediaJobStatus.leased,
        lease_owner="w1",
        lease_until=now + timedelta(minutes=1),
        attempt_count=1,
    )
    media = _media_row(lifecycle_status=MediaLifecycleStatus.queued)
    jobs_repo = MagicMock()
    jobs_repo.get_by_id_for_update = AsyncMock(return_value=job)
    jobs_repo.claim_job = AsyncMock(return_value=job)
    media_repo = MagicMock()
    media_repo.get_by_id = AsyncMock(return_value=media)
    outbox_repo = MagicMock()
    outbox_repo.create_enqueue_event = AsyncMock()

    svc = MediaJobService(session, settings)
    svc._jobs = jobs_repo
    svc._media = media_repo
    svc._outbox = outbox_repo
    svc._processor = MagicMock()
    svc._processor.process = AsyncMock(
        side_effect=RetryableMediaJobError("temporary"),
    )

    with patch("app.media_queue.job_service.xack_job", new_callable=AsyncMock):
        await svc.process_stream_message(
            redis, job_id=1, message_id="1-0", worker_id="w1",
        )

    assert job.status == MediaJobStatus.failed
    assert job.available_at > now
    outbox_repo.create_enqueue_event.assert_awaited_once()


@pytest.mark.asyncio
async def test_permanent_failure_marks_dead_without_retry_outbox() -> None:
    settings = Settings(MEDIA_JOB_MAX_ATTEMPTS=5)
    redis = AsyncMock()
    session = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    now = datetime.now(UTC)
    job = _job_row(
        status=MediaJobStatus.leased,
        lease_owner="w1",
        lease_until=now + timedelta(minutes=1),
        attempt_count=1,
    )
    media = _media_row()
    jobs_repo = MagicMock()
    jobs_repo.get_by_id_for_update = AsyncMock(return_value=job)
    jobs_repo.claim_job = AsyncMock(return_value=job)
    media_repo = MagicMock()
    media_repo.get_by_id = AsyncMock(return_value=media)
    outbox_repo = MagicMock()
    outbox_repo.create_enqueue_event = AsyncMock()

    svc = MediaJobService(session, settings)
    svc._jobs = jobs_repo
    svc._media = media_repo
    svc._outbox = outbox_repo
    svc._processor = MagicMock()
    svc._processor.process = AsyncMock(
        side_effect=PermanentMediaJobError("corrupt", error_code="CORRUPT"),
    )

    with patch("app.media_queue.job_service.xack_job", new_callable=AsyncMock):
        await svc.process_stream_message(
            redis, job_id=1, message_id="1-0", worker_id="w1",
        )

    assert job.status == MediaJobStatus.dead
    assert media.lifecycle_status == MediaLifecycleStatus.failed
    outbox_repo.create_enqueue_event.assert_not_awaited()


@pytest.mark.asyncio
async def test_noop_success_keeps_media_processing_not_ready() -> None:
    settings = Settings()
    redis = AsyncMock()
    session = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    now = datetime.now(UTC)
    job = _job_row(
        status=MediaJobStatus.queued,
        available_at=now,
    )
    media = _media_row(lifecycle_status=MediaLifecycleStatus.queued)
    jobs_repo = MagicMock()
    jobs_repo.get_by_id_for_update = AsyncMock(return_value=job)
    jobs_repo.claim_job = AsyncMock(return_value=job)
    media_repo = MagicMock()
    media_repo.get_by_id = AsyncMock(return_value=media)

    svc = MediaJobService(session, settings)
    svc._jobs = jobs_repo
    svc._media = media_repo

    with patch("app.media_queue.job_service.xack_job", new_callable=AsyncMock):
        ok = await svc.process_stream_message(
            redis, job_id=1, message_id="1-0", worker_id="w1",
        )

    assert ok is True
    assert job.status == MediaJobStatus.succeeded
    assert media.lifecycle_status == MediaLifecycleStatus.processing
    assert media.lifecycle_status != MediaLifecycleStatus.ready


@pytest.mark.asyncio
async def test_outbox_redis_unavailable_stays_pending() -> None:
    from app.media_queue.outbox_dispatcher import dispatch_pending_outbox

    session = MagicMock()
    session.commit = AsyncMock()
    redis = AsyncMock()
    settings = Settings()
    row = SimpleNamespace(id=10, job_id=5)
    repo = MagicMock()
    repo.list_pending = AsyncMock(return_value=[row])
    repo.mark_dispatched = AsyncMock(return_value=True)

    with patch("app.media_queue.outbox_dispatcher.MediaOutboxRepository", return_value=repo):
        with patch(
            "app.media_queue.outbox_dispatcher.xadd_job",
            new_callable=AsyncMock,
            side_effect=ConnectionError("redis down"),
        ):
            n = await dispatch_pending_outbox(session, redis, settings)

    assert n == 0
    repo.mark_dispatched.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_duplicate_outbox_dispatch_idempotent() -> None:
    from app.media_queue.outbox_dispatcher import dispatch_pending_outbox

    session = MagicMock()
    session.commit = AsyncMock()
    redis = AsyncMock()
    settings = Settings()
    row = SimpleNamespace(id=10, job_id=5)
    repo = MagicMock()
    repo.list_pending = AsyncMock(return_value=[row])
    repo.mark_dispatched = AsyncMock(return_value=False)

    with patch("app.media_queue.outbox_dispatcher.MediaOutboxRepository", return_value=repo):
        with patch("app.media_queue.outbox_dispatcher.xadd_job", new_callable=AsyncMock):
            n = await dispatch_pending_outbox(session, redis, settings)

    assert n == 0


@pytest.mark.asyncio
async def test_reconcile_creates_outbox_for_queued_jobs_without_pending() -> None:
    session = MagicMock()
    settings = Settings()
    job = SimpleNamespace(id=3, status=MediaJobStatus.queued, attempt_count=0)
    jobs_repo = MagicMock()
    jobs_repo.list_redispatchable = AsyncMock(return_value=[job])
    outbox_repo = MagicMock()
    outbox_repo.has_pending_for_job = AsyncMock(return_value=False)
    outbox_repo.create_enqueue_event = AsyncMock()

    svc = MediaJobService(session, settings)
    svc._jobs = jobs_repo
    svc._outbox = outbox_repo

    created = await svc.reconcile_undispatched_jobs()
    assert created == 1
    outbox_repo.create_enqueue_event.assert_awaited_once_with(
        3, suffix="reconcile-a0",
    )


@pytest.mark.asyncio
async def test_worker_respects_stop_event_when_pipeline_disabled() -> None:
    from app.workers.media_worker import media_worker_loop

    stop = asyncio.Event()
    settings = Settings(MEDIA_ASYNC_PIPELINE_ENABLED=False)

    async def _set_stop() -> None:
        await asyncio.sleep(0.05)
        stop.set()

    with patch("app.workers.media_worker.get_settings", return_value=settings):
        task = asyncio.create_task(_set_stop())
        await media_worker_loop(stop_event=stop)
        await task


@pytest.mark.asyncio
async def test_client_upload_id_different_content_rejected() -> None:
    """Immutable original: same client_upload_id + different hash → 409."""
    from app.core.exceptions import AppException
    from tests.test_media_foundation import _media_row, _service_with_mocks
    from uuid import uuid4

    existing_id = uuid4()
    hit = _media_row(client_upload_id=existing_id, media_id=42)
    hit.content_sha256 = "aa" * 32
    svc, repo_media, _, storage, pipeline = _service_with_mocks()
    repo_media.get_by_listing_and_client_upload_id = AsyncMock(return_value=hit)

    with pytest.raises(AppException, match="different content"):
        await svc.add_images(
            1,
            actor_user_id=2,
            payloads=[
                (
                    b"\xff\xd8\xff" + b"\x00" * 16,
                    "image/jpeg",
                    "a.jpg",
                    str(existing_id),
                ),
            ],
        )
    storage.put_bytes.assert_not_called()
    pipeline.process_existing_media.assert_not_awaited()


def test_outbox_dedupe_key_unique_per_suffix() -> None:
    from app.models.media_outbox import outbox_dedupe_key

    assert outbox_dedupe_key(1, suffix="enqueue") != outbox_dedupe_key(
        1, suffix="retry-a1",
    )
