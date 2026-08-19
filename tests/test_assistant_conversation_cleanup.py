from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.assistant_conversation_cleanup_service import (
    cleanup_inactive_assistant_conversations,
)


@pytest.mark.asyncio
async def test_cleanup_rejects_negative_ttl() -> None:
    session = AsyncMock()
    with pytest.raises(ValueError, match="ttl_days"):
        await cleanup_inactive_assistant_conversations(
            session,
            -1,
            use_advisory_lock=False,
        )


@pytest.mark.asyncio
async def test_cleanup_batches_until_short_batch(monkeypatch: pytest.MonkeyPatch) -> None:
    now = datetime(2026, 8, 15, 12, 0, tzinfo=UTC)
    cutoff = now - timedelta(days=7)
    batch_sizes = [2, 2, 1]
    calls: list[int] = []

    class _Repo:
        def __init__(self, session) -> None:
            self._session = session

        async def delete_inactive_before_batch(self, before: datetime, *, limit: int) -> int:
            assert before == cutoff
            assert limit == 2
            n = batch_sizes[len(calls)]
            calls.append(n)
            return n

    monkeypatch.setattr(
        "app.services.assistant_conversation_cleanup_service.AssistantConversationRepository",
        _Repo,
    )

    session = AsyncMock()
    session.commit = AsyncMock()
    sleeps: list[float] = []

    async def _sleep(seconds: float) -> None:
        sleeps.append(seconds)

    result = await cleanup_inactive_assistant_conversations(
        session,
        7,
        now=now,
        batch_size=2,
        max_batches=10,
        batch_pause_seconds=0.01,
        use_advisory_lock=False,
        sleep=_sleep,
    )

    assert result.deleted_count == 5
    assert result.batch_count == 3
    assert result.skipped_lock is False
    assert calls == [2, 2, 1]
    assert sleeps == [0.01, 0.01]
    assert session.commit.await_count == 3


@pytest.mark.asyncio
async def test_cleanup_skips_when_lock_held(monkeypatch: pytest.MonkeyPatch) -> None:
    session = AsyncMock()
    session.commit = AsyncMock()

    async def _no_lock(session, *, lock_key: int) -> bool:
        return False

    monkeypatch.setattr(
        "app.services.assistant_conversation_cleanup_service.try_acquire_cleanup_lock",
        _no_lock,
    )

    result = await cleanup_inactive_assistant_conversations(
        session,
        7,
        now=datetime(2026, 8, 15, 12, 0, tzinfo=UTC),
        use_advisory_lock=True,
    )

    assert result.skipped_lock is True
    assert result.deleted_count == 0
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_cleanup_acquires_and_releases_lock(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []

    class _Repo:
        def __init__(self, session) -> None:
            self._session = session

        async def delete_inactive_before_batch(self, before: datetime, *, limit: int) -> int:
            events.append("delete")
            return 0

    async def _lock(session, *, lock_key: int) -> bool:
        events.append(f"lock:{lock_key}")
        return True

    async def _unlock(session, *, lock_key: int) -> None:
        events.append(f"unlock:{lock_key}")

    monkeypatch.setattr(
        "app.services.assistant_conversation_cleanup_service.AssistantConversationRepository",
        _Repo,
    )
    monkeypatch.setattr(
        "app.services.assistant_conversation_cleanup_service.try_acquire_cleanup_lock",
        _lock,
    )
    monkeypatch.setattr(
        "app.services.assistant_conversation_cleanup_service.release_cleanup_lock",
        _unlock,
    )

    session = AsyncMock()
    session.commit = AsyncMock()
    result = await cleanup_inactive_assistant_conversations(
        session,
        7,
        now=datetime(2026, 8, 15, 12, 0, tzinfo=UTC),
        batch_size=100,
        use_advisory_lock=True,
        lock_key=42,
        batch_pause_seconds=0,
    )

    assert result.deleted_count == 0
    assert events == ["lock:42", "delete", "unlock:42"]
    assert session.commit.await_count == 2  # batch + unlock


@pytest.mark.asyncio
async def test_repo_delete_inactive_before_batch_uses_limit() -> None:
    from app.repositories.assistant_conversation_repository import AssistantConversationRepository

    cutoff = datetime(2026, 8, 8, 12, 0, tzinfo=UTC)
    execute_result = SimpleNamespace(rowcount=5)
    session = AsyncMock()
    session.execute = AsyncMock(return_value=execute_result)
    session.flush = AsyncMock()

    repo = AssistantConversationRepository(session)
    deleted = await repo.delete_inactive_before_batch(cutoff, limit=100)

    assert deleted == 5
    stmt = session.execute.await_args.args[0]
    sql = str(stmt)
    assert "assistant_conversations" in sql
    assert "last_activity_at" in sql


def test_config_defaults() -> None:
    from app.core.config import Settings

    assert Settings.model_fields["ASSISTANT_CONVERSATION_TTL_DAYS"].default == 7
    assert Settings.model_fields["ASSISTANT_CONVERSATION_CLEANUP_ENABLED"].default is True
    assert Settings.model_fields["ASSISTANT_CONVERSATION_CLEANUP_INTERVAL_HOURS"].default == 24
    assert Settings.model_fields["ASSISTANT_CONVERSATION_CLEANUP_BATCH_SIZE"].default == 2000
    assert Settings.model_fields["ASSISTANT_CONVERSATION_CLEANUP_MAX_BATCHES"].default == 500
    assert Settings.model_fields["ASSISTANT_CONVERSATION_CLEANUP_BATCH_PAUSE_MS"].default == 50


@pytest.mark.asyncio
async def test_cleanup_loop_skips_when_disabled() -> None:
    from app.services.assistant_conversation_cleanup_worker import (
        assistant_conversation_cleanup_loop,
    )

    settings = SimpleNamespace(
        ASSISTANT_CONVERSATION_CLEANUP_ENABLED=False,
        ASSISTANT_CONVERSATION_TTL_DAYS=7,
        ASSISTANT_CONVERSATION_CLEANUP_INTERVAL_HOURS=24,
        ASSISTANT_CONVERSATION_CLEANUP_BATCH_SIZE=2000,
        ASSISTANT_CONVERSATION_CLEANUP_MAX_BATCHES=500,
    )
    stop = asyncio.Event()
    await assistant_conversation_cleanup_loop(settings=settings, stop_event=stop)


@pytest.mark.asyncio
async def test_cleanup_loop_runs_once_then_stops(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import assistant_conversation_cleanup_worker as worker

    calls = {"n": 0}
    stop = asyncio.Event()

    async def _once(*, settings=None) -> int:
        calls["n"] += 1
        stop.set()
        return 1

    monkeypatch.setattr(worker, "run_assistant_conversation_cleanup_once", _once)

    settings = SimpleNamespace(
        ASSISTANT_CONVERSATION_CLEANUP_ENABLED=True,
        ASSISTANT_CONVERSATION_TTL_DAYS=7,
        ASSISTANT_CONVERSATION_CLEANUP_INTERVAL_HOURS=24,
        ASSISTANT_CONVERSATION_CLEANUP_BATCH_SIZE=2000,
        ASSISTANT_CONVERSATION_CLEANUP_MAX_BATCHES=500,
    )
    await worker.assistant_conversation_cleanup_loop(
        settings=settings,
        stop_event=stop,
        interval_seconds=60,
    )
    assert calls["n"] == 1
