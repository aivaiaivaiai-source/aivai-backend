from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.api.deps import get_current_user, get_favorite_service
from app.core.exceptions import EntityNotFoundError
from app.main import app as fastapi_app
from app.models.enums import Currency, ListingStatus
from app.schemas.category import CategoryRead
from app.schemas.favorite import FavoriteToggleRead
from app.schemas.listing import ListingFeedPage, ListingRead
from app.schemas.user import UserRead
from app.services.favorite_service import FavoriteService


def _listing_read() -> ListingRead:
    now = datetime.now(UTC)
    return ListingRead(
        id=16,
        title="Camry",
        description=None,
        price=Decimal("1000"),
        currency=Currency.KGS,
        status=ListingStatus.active,
        owner_id=2,
        category_id=2,
        category=CategoryRead(
            id=2,
            name="Продажа авто",
            slug="transport-car-sale",
            parent_id=None,
        ),
        images=[],
        fields={},
        created_at=now,
        updated_at=now,
    )


async def _user() -> UserRead:
    now = datetime.now(UTC)
    return UserRead(
        id=1,
        phone="+79001234567",
        full_name="Dev",
        is_active=True,
        balance=Decimal("0"),
        last_login=None,
        created_at=now,
        updated_at=now,
    )


class _FavSvc:
    def __init__(self) -> None:
        self.toggle_id: int | None = None

    async def list_for_user(
        self,
        user_id: int,
        *,
        limit: int,
        offset: int,
    ) -> ListingFeedPage:
        return ListingFeedPage(items=[_listing_read()], total=1)

    async def toggle(self, user_id: int, listing_id: int) -> FavoriteToggleRead:
        self.toggle_id = listing_id
        return FavoriteToggleRead(listing_id=listing_id, favorited=True)


@pytest.mark.asyncio
async def test_list_favorites_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/favorites")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_favorites_returns_page(client: AsyncClient) -> None:
    fastapi_app.dependency_overrides[get_current_user] = _user
    fastapi_app.dependency_overrides[get_favorite_service] = lambda: _FavSvc()
    resp = await client.get("/api/v1/favorites")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == 16


@pytest.mark.asyncio
async def test_toggle_favorite_forwards_listing_id(client: AsyncClient) -> None:
    svc = _FavSvc()
    fastapi_app.dependency_overrides[get_current_user] = _user
    fastapi_app.dependency_overrides[get_favorite_service] = lambda: svc
    resp = await client.post("/api/v1/favorites/16/toggle")
    assert resp.status_code == 200
    assert resp.json()["favorited"] is True
    assert svc.toggle_id == 16


@pytest.mark.asyncio
async def test_toggle_missing_listing_raises() -> None:
    listings = AsyncMock()
    listings.get_by_id = AsyncMock(return_value=None)
    svc = FavoriteService(
        session=AsyncMock(),
        favorite_repository=AsyncMock(),
        listing_repository=listings,
        listing_service=AsyncMock(),
    )
    with pytest.raises(EntityNotFoundError):
        await svc.toggle(1, 99)
