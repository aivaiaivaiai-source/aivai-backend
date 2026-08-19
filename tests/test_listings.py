from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.api.deps import get_current_user, get_listing_service
from app.core.exceptions import AppException, OwnershipError
from app.main import app as fastapi_app
from app.models.enums import Currency, ListingStatus
from app.schemas.category import CategoryRead
from app.schemas.listing import ListingCreate, ListingFeedPage, ListingRead, ListingUpdate
from app.schemas.user import UserRead
from app.services.listing_service import ListingService


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
    def __init__(self) -> None:
        self.last_body: ListingCreate | None = None
        self.last_owner_id: int | None = None
        self.last_known_fields: dict | None = None

    async def create_listing(
        self,
        data: ListingCreate,
        owner_id: int,
        *,
        known_fields: dict | None = None,
    ) -> ListingRead:
        self.last_body = data
        self.last_owner_id = owner_id
        self.last_known_fields = known_fields
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
            fields=dict(data.fields),
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
    create_svc = _CreateListingSvc()
    fastapi_app.dependency_overrides[get_listing_service] = lambda: create_svc

    payload = {
        "title": "mock listing",
        "description": None,
        "price": "9.99",
        "category_id": 42,
        "currency": Currency.KGS.value,
        "status": ListingStatus.active.value,
        "fields": {"city": "Бишкек", "year": 2018},
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
    assert body["status"] == ListingStatus.draft.value
    assert body["fields"]["city"] == "Бишкек"
    assert create_svc.last_owner_id == 501
    assert create_svc.last_body is not None
    assert create_svc.last_body.status == ListingStatus.draft
    assert create_svc.last_known_fields == {"city": "Бишкек", "year": 2018}


@pytest.mark.asyncio
async def test_create_listing_rejects_too_many_fields(client: AsyncClient) -> None:
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
        "title": "spam",
        "price": "1",
        "category_id": 1,
        "fields": {f"k{i}": "x" for i in range(41)},
    }
    resp = await client.post(
        "/api/v1/listings",
        json=payload,
        headers={"Authorization": "Bearer ignored"},
    )
    assert resp.status_code == 422


def test_listing_update_does_not_accept_status() -> None:
    updated = ListingUpdate.model_validate({"title": "ok", "status": "active"})
    assert updated.title == "ok"
    assert "status" not in updated.model_dump(exclude_unset=True)


def _sample_listing_read(*, listing_id: int = 7, title: str = "Camry") -> ListingRead:
    now = datetime.now(UTC)
    return ListingRead(
        id=listing_id,
        title=title,
        description=None,
        price=Decimal("1000"),
        currency=Currency.USD,
        status=ListingStatus.active,
        owner_id=1,
        category_id=2,
        category=CategoryRead(
            id=2,
            name="Продажа авто",
            slug="transport-car-sale",
            parent_id=None,
        ),
        images=[],
        fields={"city": "Бишкек"},
        created_at=now,
        updated_at=now,
    )


class _FeedSvc:
    def __init__(self, page: ListingFeedPage) -> None:
        self.page = page
        self.kwargs: dict | None = None

    async def get_feed(self, **kwargs) -> ListingFeedPage:
        self.kwargs = kwargs
        return self.page


@pytest.mark.asyncio
async def test_public_feed_returns_items_and_total(client: AsyncClient) -> None:
    svc = _FeedSvc(ListingFeedPage(items=[_sample_listing_read()], total=1))
    fastapi_app.dependency_overrides[get_listing_service] = lambda: svc

    resp = await client.get("/api/v1/listings", params={"limit": 20})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["title"] == "Camry"
    assert body["items"][0]["status"] == ListingStatus.active.value
    assert svc.kwargs is not None
    assert svc.kwargs["status"] is None


@pytest.mark.asyncio
async def test_public_feed_forwards_fuel_and_transmission(client: AsyncClient) -> None:
    svc = _FeedSvc(ListingFeedPage(items=[], total=0))
    fastapi_app.dependency_overrides[get_listing_service] = lambda: svc

    resp = await client.get(
        "/api/v1/listings",
        params={"fuel": "Бензин", "transmission": "Автомат"},
    )
    assert resp.status_code == 200
    assert svc.kwargs is not None
    assert svc.kwargs["fuel"] == "Бензин"
    assert svc.kwargs["transmission"] == "Автомат"


@pytest.mark.asyncio
async def test_get_feed_passes_fuel_and_transmission() -> None:
    listings = AsyncMock()
    listings.count_listings = AsyncMock(return_value=0)
    listings.search_listings = AsyncMock(return_value=[])
    svc = ListingService(
        session=AsyncMock(),
        listing_repository=listings,
        category_repository=AsyncMock(),
        notification_service=AsyncMock(),
    )
    await svc.get_feed(fuel=" Бензин ", transmission=" Автомат ")
    kwargs = listings.count_listings.await_args.kwargs
    assert kwargs["fuel"] == "Бензин"
    assert kwargs["transmission"] == "Автомат"


@pytest.mark.asyncio
async def test_get_feed_rejects_draft_status() -> None:
    listings = AsyncMock()
    svc = ListingService(
        session=AsyncMock(),
        listing_repository=listings,
        category_repository=AsyncMock(),
        notification_service=AsyncMock(),
    )
    with pytest.raises(AppException) as exc:
        await svc.get_feed(status=ListingStatus.draft)
    assert exc.value.status_code == 400
    assert exc.value.error_code == "INVALID_FEED_STATUS"
    listings.count_listings.assert_not_called()
    listings.search_listings.assert_not_called()


@pytest.mark.asyncio
async def test_change_status_allows_deactivate() -> None:
    listing = type(
        "L",
        (),
        {
            "id": 9,
            "owner_id": 501,
            "status": ListingStatus.active,
            "category_id": 2,
            "images": [],
            "uses_placeholder_image": False,
            "field_values": [],
        },
    )()
    listings = AsyncMock()
    listings.get_by_id = AsyncMock(side_effect=[listing, listing, listing])

    async def _update(_id, **kwargs):
        listing.status = kwargs["status"]
        return listing

    listings.update = AsyncMock(side_effect=_update)
    session = AsyncMock()
    svc = ListingService(
        session=session,
        listing_repository=listings,
        category_repository=AsyncMock(),
        notification_service=AsyncMock(),
    )
    svc._to_read = lambda row: _sample_listing_read(listing_id=row.id)  # type: ignore[method-assign]
    from app.schemas.listing import ListingStatusUpdate

    result = await svc.change_status(
        9,
        actor_user_id=501,
        payload=ListingStatusUpdate(status=ListingStatus.draft),
    )
    assert result.id == 9
    listings.update.assert_awaited()
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_get_feed_rejects_inverted_year_range() -> None:
    listings = AsyncMock()
    svc = ListingService(
        session=AsyncMock(),
        listing_repository=listings,
        category_repository=AsyncMock(),
        notification_service=AsyncMock(),
    )
    with pytest.raises(AppException) as exc:
        await svc.get_feed(year_min=2020, year_max=2010)
    assert exc.value.status_code == 400
    listings.count_listings.assert_not_called()
