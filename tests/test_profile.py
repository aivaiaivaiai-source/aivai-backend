from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.api.deps import get_current_user, get_review_service, get_user_service
from app.main import app as fastapi_app
from app.schemas.review import ReviewRead
from app.schemas.user import UserRead, UserUpdate


def _user(*, user_id: int = 1, name: str = "Dev") -> UserRead:
    now = datetime.now(UTC)
    return UserRead(
        id=user_id,
        phone="+79001234567",
        full_name=name,
        is_active=True,
        balance=Decimal("1230"),
        city="Бишкек",
        avatar_url=None,
        rating=5,
        reviews_count=2,
        listings_created_count=8,
        last_login=None,
        created_at=now,
        updated_at=now,
    )


class _UserSvc:
    def __init__(self) -> None:
        self.updated: UserUpdate | None = None

    async def get_profile(self, user_id: int) -> UserRead:
        return _user(user_id=user_id)

    async def update_me(self, user_id: int, data: UserUpdate) -> UserRead:
        self.updated = data
        current = _user(user_id=user_id)
        return current.model_copy(
            update={
                "full_name": data.full_name or current.full_name,
                "city": data.city if data.city is not None else current.city,
            }
        )


class _ReviewSvc:
    async def list_for_user(
        self,
        subject_id: int,
        *,
        limit: int,
        offset: int,
    ) -> list[ReviewRead]:
        now = datetime.now(UTC)
        return [
            ReviewRead(
                id=1,
                author_id=2,
                subject_id=subject_id,
                author_name="Айбек",
                rating=5,
                comment="Отлично",
                owner_reply=None,
                created_at=now,
            )
        ]


@pytest.mark.asyncio
async def test_read_me_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_read_me_returns_profile(client: AsyncClient) -> None:
    fastapi_app.dependency_overrides[get_current_user] = lambda: _user()
    fastapi_app.dependency_overrides[get_user_service] = lambda: _UserSvc()
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 200
    body = resp.json()
    assert body["full_name"] == "Dev"
    assert body["city"] == "Бишкек"
    assert body["balance"] == "1230.00" or float(body["balance"]) == 1230
    assert body["reviews_count"] == 2


@pytest.mark.asyncio
async def test_patch_me_forwards_city(client: AsyncClient) -> None:
    svc = _UserSvc()
    fastapi_app.dependency_overrides[get_current_user] = lambda: _user()
    fastapi_app.dependency_overrides[get_user_service] = lambda: svc
    resp = await client.patch("/api/v1/users/me", json={"city": "Ош", "full_name": "Гульжан"})
    assert resp.status_code == 200
    assert svc.updated is not None
    assert svc.updated.city == "Ош"
    assert resp.json()["city"] == "Ош"


@pytest.mark.asyncio
async def test_list_reviews(client: AsyncClient) -> None:
    fastapi_app.dependency_overrides[get_review_service] = lambda: _ReviewSvc()
    resp = await client.get("/api/v1/users/1/reviews")
    assert resp.status_code == 200
    assert resp.json()[0]["author_name"] == "Айбек"
