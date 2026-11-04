"""Global: user-facing Search has_photo filter removed; API capability kept."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.db.session import async_session_maker
from app.main import app as fastapi_app
from app.seeds.bicycle_sale_v2 import BICYCLE_SEARCH_FILTERS_BY_SLUG
from app.seeds.bus_sale_v2 import BUS_SEARCH_FILTERS_BY_SLUG
from app.seeds.car_sale_v2 import CAR_SALE_SEARCH_FILTERS
from app.seeds.electric_sale_v2 import ELECTRIC_SEARCH_FILTERS_BY_SLUG
from app.seeds.moto_sale_v2 import MOTO_SEARCH_FILTERS_BY_SLUG
from app.seeds.cargo_sale_v2 import CARGO_SEARCH_FILTERS_BY_SLUG
from app.seeds.special_sale_v2 import SPECIAL_SEARCH_FILTERS_BY_SLUG
from app.services.listing_service import ListingService


async def _assert_all() -> None:
    async with async_session_maker() as session:
        rows = (
            await session.execute(
                text(
                    """
                    SELECT cat.slug, f.filter_key, f.label
                    FROM category_filters f
                    JOIN categories cat ON cat.id = f.category_id
                    WHERE f.filter_key = 'has_photo'
                       OR lower(f.label) LIKE '%с фото%'
                    ORDER BY cat.slug
                    """
                )
            )
        ).mappings().all()
        assert rows == [], f"user-facing photo filters still present: {rows}"

    bundles = [
        [row[0] for row in CAR_SALE_SEARCH_FILTERS],
        *[
            [row[0] for row in rows]
            for rows in MOTO_SEARCH_FILTERS_BY_SLUG.values()
        ],
        *[
            [row[0] for row in rows]
            for rows in ELECTRIC_SEARCH_FILTERS_BY_SLUG.values()
        ],
        *[
            [row[0] for row in rows]
            for rows in BICYCLE_SEARCH_FILTERS_BY_SLUG.values()
        ],
        *[
            [row[0] for row in rows]
            for rows in BUS_SEARCH_FILTERS_BY_SLUG.values()
        ],
        *[
            [row[0] for row in rows]
            for rows in SPECIAL_SEARCH_FILTERS_BY_SLUG.values()
        ],
        *[
            [row[0] for row in rows]
            for rows in CARGO_SEARCH_FILTERS_BY_SLUG.values()
        ],
    ]
    for keys in bundles:
        assert "has_photo" not in keys
        assert keys, "empty filter schema"

    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://test",
    ) as client:
        r = await client.get(
            "/api/v1/listings",
            params={"has_photo": "true", "limit": 5},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert "items" in body and "total" in body

        r2 = await client.get(
            "/api/v1/listings",
            params={"attrs": '{"has_photo":"true"}', "limit": 5},
        )
        assert r2.status_code == 200, r2.text

    listings = AsyncMock()
    listings.count_listings = AsyncMock(return_value=0)
    listings.search_listings = AsyncMock(return_value=[])
    svc = ListingService(
        session=AsyncMock(),
        listing_repository=listings,
        category_repository=AsyncMock(),
        notification_service=AsyncMock(),
    )
    await svc.get_feed(has_photo=True)
    kwargs = listings.count_listings.await_args.kwargs
    assert kwargs["has_photo"] is True


def test_search_has_photo_filter_removed_globally() -> None:
    """Single asyncio.run — avoids Windows asyncpg dispose across tests."""
    asyncio.run(_assert_all())
