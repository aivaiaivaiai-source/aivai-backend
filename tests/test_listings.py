from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.api.deps import get_current_user, get_listing_service
from app.core.exceptions import OwnershipError
from app.main import app as fastapi_app
from app.models.enums import Currency, ListingStatus
from app.schemas.category import CategoryRead
from app.schemas.listing import ListingCreate, ListingRead, ListingUpdate
from app.schemas.user import UserRead


class _RaiseOwnershipSvc:
    async def update_listing(
        self,
        listing_id: int,
        *,
        actor_user_id: int,
        data: ListingUpdate,
    ):
        raise OwnershipError("You cannot modify another user's listing.")


class _CreateListingSvc:
    async def create_listing(self, data: ListingCreate, owner_id: int) -> ListingRead:
        now = datetime.now(UTC)
        category = CategoryRead(
            id=data.category_id,
            name="stub-category",
            slug="stub-category",
            parent_id=None,
        )
        return ListingRead(
            id=1042,
            title=data.title,
            description=data.description,
            price=data.price,
            currency=data.currency,
            status=data.status,
            owner_id=owner_id,
            category_id=data.category_id,
            category=category,
            images=[],
            created_at=now,
            updated_at=now,
        )


@pytest.mark.asyncio
async def test_patch_foreign_listing_returns_unified_errors(client: AsyncClient) -> None:
    now = datetime.now(UTC)

    async def fake_user() -> UserRead:
        return UserRead(
            id=99,
            phone="+79990009999",
            full_name="NotOwner",
            is_active=True,
            balance=Decimal("0"),
            last_login=None,
            created_at=now,
            updated_at=now,
        )

    fastapi_app.dependency_overrides[get_current_user] = fake_user
    fastapi_app.dependency_overrides[get_listing_service] = lambda: _RaiseOwnershipSvc()

    resp = await client.patch("/api/v1/listings/1", json={"title": "Hack"})
    assert resp.status_code == 403
    body = resp.json()
    assert body["code"] == "OWNERSHIP_ERROR"
    assert body["status"] == 403
    assert "cannot modify another" in body["detail"].lower()
    assert isinstance(body["request_id"], str)


@pytest.mark.asyncio
async def test_create_listing_mock_returns_201(client: AsyncClient) -> None:
    now = datetime.now(UTC)

    async def creator_user() -> UserRead:
        return UserRead(
            id=501,
            phone="+70009990099",
            full_name="Poster",
            is_active=True,
            balance=Decimal("0"),
            last_login=None,
            created_at=now,
            updated_at=now,
        )

    fastapi_app.dependency_overrides[get_current_user] = creator_user
    fastapi_app.dependency_overrides[get_listing_service] = lambda: _CreateListingSvc()

    payload = {
        "title": "mock listing",
        "description": None,
        "price": "9.99",
        "category_id": 42,
        "currency": Currency.KGS.value,
        "status": ListingStatus.draft.value,
    }

    resp = await client.post(
        "/api/v1/listings",
        json=payload,
        headers={"Authorization": "Bearer ignored"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] == 1042
    assert body["title"] == "mock listing"
    assert body["owner_id"] == 501
