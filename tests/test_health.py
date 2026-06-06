from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.api.deps import get_health_service


class _FakeHealthSvc:
    async def check(self) -> dict[str, str]:
        return {"status": "ok"}


@pytest.mark.asyncio
async def test_health_ok(client: AsyncClient) -> None:
    from app.main import app as fastapi_app

    fastapi_app.dependency_overrides[get_health_service] = lambda: _FakeHealthSvc()
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_ready_ok(client: AsyncClient) -> None:
    from app.main import app as fastapi_app

    fastapi_app.dependency_overrides[get_health_service] = lambda: _FakeHealthSvc()
    resp = await client.get("/ready")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
