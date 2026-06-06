from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.api.deps import get_auth_service
from app.schemas.auth import TokenResponse


class _QuickAuthSvc:
    async def login_by_phone(self, phone: str | None, full_name: str) -> TokenResponse:
        del phone, full_name
        return TokenResponse(access_token="access-test", refresh_token="refresh-test")


@pytest.mark.asyncio
async def test_login_mocked_return_tokens(client: AsyncClient) -> None:
    from app.main import app as fastapi_app

    fastapi_app.dependency_overrides[get_auth_service] = lambda: _QuickAuthSvc()
    resp = await client.post(
        "/api/v1/auth/login",
        json={"phone": "+70000000000", "full_name": "Tester"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"] == "access-test"
    assert data["refresh_token"] == "refresh-test"
    assert data.get("token_type") == "bearer"


@pytest.mark.asyncio
async def test_login_rate_limit_by_ip(client: AsyncClient) -> None:
    from app.main import app as fastapi_app

    fastapi_app.dependency_overrides[get_auth_service] = lambda: _QuickAuthSvc()
    body = {"phone": "+70000000001", "full_name": "Flooder"}
    for _ in range(5):
        r = await client.post("/api/v1/auth/login", json=body)
        assert r.status_code == 200
    blocked = await client.post("/api/v1/auth/login", json=body)
    assert blocked.status_code == 429
    err = blocked.json()
    assert err["code"] == "RATE_LIMIT_EXCEEDED"
    assert err["status"] == 429
    assert "request_id" in err
