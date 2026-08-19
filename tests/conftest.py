from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.logging import configure_logging
from app.core.rate_limit import AUTH_IP_LIMITER, LISTING_CREATE_LIMITER
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def _configure_test_logging() -> None:
    configure_logging()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture(autouse=True)
def _clear_dependency_overrides() -> None:
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
async def _reset_auth_rate_limits() -> AsyncGenerator[None, None]:
    await AUTH_IP_LIMITER.reset()
    await LISTING_CREATE_LIMITER.reset()
    yield
    await AUTH_IP_LIMITER.reset()
    await LISTING_CREATE_LIMITER.reset()
