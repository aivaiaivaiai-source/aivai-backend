from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.core.config import Settings, get_settings
from app.services.category_snapshot import (
    CategoryIntelligenceSnapshot,
    CategorySnapshotProvider,
    reset_process_snapshot_cache,
)


@pytest.fixture(autouse=True)
def _clear_process_snapshot_cache() -> None:
    reset_process_snapshot_cache()
    get_settings.cache_clear()
    yield
    reset_process_snapshot_cache()
    get_settings.cache_clear()


def _provider() -> CategorySnapshotProvider:
    return CategorySnapshotProvider(
        AsyncMock(),
        AsyncMock(),
        AsyncMock(),
        AsyncMock(),
        AsyncMock(),
    )


def _snapshot_marker(marker: str) -> CategoryIntelligenceSnapshot:
    snap = CategoryIntelligenceSnapshot()
    snap.root_category_slugs = [marker]
    return snap


@pytest.mark.asyncio
async def test_first_call_loads_from_db() -> None:
    provider = _provider()
    load_mock = AsyncMock(return_value=_snapshot_marker("first"))
    with patch.object(CategorySnapshotProvider, "_load", load_mock):
        result = await provider.get()
    assert result.root_category_slugs == ["first"]
    load_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_second_call_within_ttl_skips_db() -> None:
    provider_a = _provider()
    provider_b = _provider()
    load_mock = AsyncMock(return_value=_snapshot_marker("cached"))
    with patch.object(CategorySnapshotProvider, "_load", load_mock):
        await provider_a.get()
        await provider_b.get()
    load_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_after_ttl_reloads_snapshot() -> None:
    provider = _provider()
    load_mock = AsyncMock(
        side_effect=[
            _snapshot_marker("v1"),
            _snapshot_marker("v2"),
        ]
    )
    times = iter([100.0, 100.0, 100.0, 200.0, 200.0, 200.0])
    with (
        patch.object(CategorySnapshotProvider, "_load", load_mock),
        patch("app.services.category_snapshot.time.monotonic", side_effect=lambda: next(times)),
        patch(
            "app.services.category_snapshot.get_settings",
            return_value=Settings(CATEGORY_SNAPSHOT_TTL_SECONDS=60),
        ),
    ):
        first = await provider.get()
        second = await provider.get()
    assert first.root_category_slugs == ["v1"]
    assert second.root_category_slugs == ["v2"]
    assert load_mock.await_count == 2


@pytest.mark.asyncio
async def test_concurrent_calls_trigger_single_reload() -> None:
    provider_a = _provider()
    provider_b = _provider()
    load_count = 0
    gate = asyncio.Event()

    async def slow_load(self: CategorySnapshotProvider) -> CategoryIntelligenceSnapshot:
        nonlocal load_count
        load_count += 1
        await gate.wait()
        return _snapshot_marker("shared")

    gate.set()
    with patch.object(CategorySnapshotProvider, "_load", slow_load):
        await asyncio.gather(provider_a.get(), provider_b.get())
    assert load_count == 1


@pytest.mark.asyncio
async def test_invalidate_forces_reload() -> None:
    provider = _provider()
    load_mock = AsyncMock(
        side_effect=[
            _snapshot_marker("before"),
            _snapshot_marker("after"),
        ]
    )
    with patch.object(CategorySnapshotProvider, "_load", load_mock):
        first = await provider.get()
        provider.invalidate()
        second = await provider.get()
    assert first.root_category_slugs == ["before"]
    assert second.root_category_slugs == ["after"]
    assert load_mock.await_count == 2


@pytest.mark.asyncio
async def test_db_error_with_stale_snapshot_returns_stale() -> None:
    provider = _provider()
    load_mock = AsyncMock(
        side_effect=[
            _snapshot_marker("stale"),
            RuntimeError("db unavailable"),
        ]
    )
    times = iter([100.0, 100.0, 100.0, 200.0, 200.0, 200.0])
    with (
        patch.object(CategorySnapshotProvider, "_load", load_mock),
        patch("app.services.category_snapshot.time.monotonic", side_effect=lambda: next(times)),
        patch(
            "app.services.category_snapshot.get_settings",
            return_value=Settings(CATEGORY_SNAPSHOT_TTL_SECONDS=60),
        ),
    ):
        first = await provider.get()
        second = await provider.get()
    assert first.root_category_slugs == ["stale"]
    assert second.root_category_slugs == ["stale"]
    assert load_mock.await_count == 2


@pytest.mark.asyncio
async def test_db_error_without_snapshot_raises() -> None:
    provider = _provider()
    load_mock = AsyncMock(side_effect=RuntimeError("db unavailable"))
    with patch.object(CategorySnapshotProvider, "_load", load_mock):
        with pytest.raises(RuntimeError, match="db unavailable"):
            await provider.get()
    load_mock.assert_awaited_once()
