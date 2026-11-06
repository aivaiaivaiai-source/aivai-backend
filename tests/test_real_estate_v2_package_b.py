# -*- coding: utf-8 -*-
"""Real Estate V2 Package B — area schema + Search/facets + identity."""
from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from decimal import Decimal

from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.api.deps import get_current_user
from app.api.v1.endpoints.listings import _enforce_listing_create_rate_limit
from app.db.session import async_session_maker
from app.main import app
from app.schemas.user import UserRead
from app.seeds.real_estate_v2 import (
    APARTMENTS_ID,
    APARTMENTS_SLUG,
    COMMERCIAL_ID,
    GARAGES_ID,
    HOUSES_ID,
    LAND_ID,
    PARKING_SLUG,
    ROOMS_ID,
)


def _auth_user(user_id: int = 1) -> None:
    now = datetime.now(UTC)

    async def _user() -> UserRead:
        return UserRead(
            id=user_id,
            phone="+79001234567",
            full_name="RealEstateV2PkgB",
            is_active=True,
            balance=Decimal("0"),
            last_login=None,
            created_at=now,
            updated_at=now,
        )

    app.dependency_overrides[get_current_user] = _user

    async def _no_rate() -> None:
        return None

    app.dependency_overrides[_enforce_listing_create_rate_limit] = _no_rate


async def _slug_id(session, slug: str) -> int:
    return int(
        (
            await session.execute(
                text("SELECT id FROM categories WHERE slug = :s"),
                {"s": slug},
            )
        ).scalar_one()
    )


async def _force_active(
    listing_id: int,
    *,
    normalized_kgs: str,
    currency: str = "USD",
) -> None:
    """Bypass photo publish gate for Search fixture listings."""
    async with async_session_maker() as session:
        await session.execute(
            text(
                """
                UPDATE listings
                SET status = 'active',
                    normalized_price_kgs = CAST(:nk AS numeric),
                    currency = CAST(:cur AS currency_enum),
                    updated_at = now()
                WHERE id = :id
                """
            ),
            {"id": listing_id, "nk": normalized_kgs, "cur": currency},
        )
        await session.commit()


async def _create_draft(client: AsyncClient, payload: dict) -> int:
    resp = await client.post("/api/v1/listings", json=payload)
    assert resp.status_code in {200, 201}, resp.text
    return int(resp.json()["id"])


async def _run_all() -> None:
    _auth_user(1)
    created_ids: list[int] = []
    parking_id: int

    async with async_session_maker() as session:
        # Area schema on apartments.
        apt_area = (
            await session.execute(
                text(
                    """
                    SELECT field_type, is_required, options
                    FROM category_core_fields
                    WHERE category_id = :cid AND field_key = 'area'
                    """
                ),
                {"cid": APARTMENTS_ID},
            )
        ).one()
        assert apt_area[0] == "decimal"
        assert bool(apt_area[1]) is True
        opts = apt_area[2] or {}
        assert opts.get("unit") == "m2"

        rooms_area = (
            await session.execute(
                text(
                    """
                    SELECT is_required, options
                    FROM category_core_fields
                    WHERE category_id = :cid AND field_key = 'area'
                    """
                ),
                {"cid": ROOMS_ID},
            )
        ).one()
        assert bool(rooms_area[0]) is False
        depends = ((rooms_area[1] or {}).get("depends_on") or {}).get("values") or []
        assert "rent" in depends
        assert "rent_bed" not in depends

        land_area = (
            await session.execute(
                text(
                    """
                    SELECT count(*) FROM category_core_fields
                    WHERE category_id = :cid AND field_key = 'area'
                    """
                ),
                {"cid": LAND_ID},
            )
        ).scalar_one()
        assert int(land_area) == 0
        parking_id = await _slug_id(session, PARKING_SLUG)

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            fixtures = [
                (
                    {
                        "title": "PkgB Apt sell 72",
                        "description": "b",
                        "price": 80000,
                        "currency": "USD",
                        "category_id": APARTMENTS_ID,
                        "fields": {
                            "deal_type": "sell",
                            "rooms": "2",
                            "area": "72",
                            "subtype": "secondary",
                            "district": "sverdlovsky",
                            "seller_type": "owner",
                            "renovation": "euro",
                            "city": "Р‘РёС€РєРµРє",
                            "negotiable": "yes",
                            "contact_methods": "Только телефон",
                        },
                    },
                    "6960000",
                    "USD",
                    True,
                ),
                (
                    {
                        "title": "PkgB Apt rent 55",
                        "description": "b",
                        "price": 35000,
                        "currency": "KGS",
                        "category_id": APARTMENTS_ID,
                        "fields": {
                            "deal_type": "rent",
                            "rooms": "1",
                            "area": "55",
                            "subtype": "long_term",
                            "district": "oktyabrsky",
                            "seller_type": "owner",
                            "city": "Р‘РёС€РєРµРє",
                            "negotiable": "no",
                            "contact_methods": "Только телефон",
                        },
                    },
                    "35000",
                    "KGS",
                    True,
                ),
                (
                    {
                        "title": "PkgB Apt buy",
                        "description": "b",
                        "price": 50000,
                        "currency": "USD",
                        "category_id": APARTMENTS_ID,
                        "fields": {
                            "deal_type": "buy",
                            "rooms": "3",
                            "area": "90",
                            "city": "РћС€",
                            "seller_type": "buyer",
                            "negotiable": "yes",
                            "contact_methods": "Только телефон",
                        },
                    },
                    "4350000",
                    "USD",
                    True,
                ),
                (
                    {
                        "title": "PkgB Apt want_rent",
                        "description": "b",
                        "price": 25000,
                        "currency": "KGS",
                        "category_id": APARTMENTS_ID,
                        "fields": {
                            "deal_type": "want_rent",
                            "rooms": "2",
                            "area": "60",
                            "city": "Р‘РёС€РєРµРє",
                            "seller_type": "renter",
                            "negotiable": "yes",
                            "contact_methods": "Только телефон",
                        },
                    },
                    "25000",
                    "KGS",
                    True,
                ),
                (
                    {
                        "title": "PkgB House 160",
                        "description": "b",
                        "price": 120000,
                        "currency": "USD",
                        "category_id": HOUSES_ID,
                        "fields": {
                            "deal_type": "sell",
                            "area": "160",
                            "rooms": "4",
                            "city": "Р‘РёС€РєРµРє",
                            "seller_type": "owner",
                            "negotiable": "yes",
                            "contact_methods": "Только телефон",
                        },
                    },
                    "10440000",
                    "USD",
                    True,
                ),
                (
                    {
                        "title": "PkgB Room rent",
                        "description": "b",
                        "price": 8000,
                        "currency": "KGS",
                        "category_id": ROOMS_ID,
                        "fields": {
                            "deal_type": "rent",
                            "area": "18",
                            "city": "Р‘РёС€РєРµРє",
                            "seller_type": "owner",
                            "negotiable": "yes",
                            "contact_methods": "Только телефон",
                        },
                    },
                    "8000",
                    "KGS",
                    True,
                ),
                (
                    {
                        "title": "PkgB Land sell",
                        "description": "b",
                        "price": 30000,
                        "currency": "USD",
                        "category_id": LAND_ID,
                        "fields": {
                            "deal_type": "sell",
                            "plot_area": "8",
                            "city": "Р‘РёС€РєРµРє",
                            "seller_type": "owner",
                            "negotiable": "yes",
                            "contact_methods": "Только телефон",
                        },
                    },
                    "2610000",
                    "USD",
                    True,
                ),
                (
                    {
                        "title": "PkgB Commercial office",
                        "description": "b",
                        "price": 1500,
                        "currency": "USD",
                        "category_id": COMMERCIAL_ID,
                        "fields": {
                            "deal_type": "rent",
                            "commercial_direction": "office_coworking",
                            "area": "120",
                            "city": "Р‘РёС€РєРµРє",
                            "seller_type": "owner",
                            "negotiable": "yes",
                            "contact_methods": "Только телефон",
                        },
                    },
                    "130500",
                    "USD",
                    True,
                ),
                (
                    {
                        "title": "PkgB Garage",
                        "description": "b",
                        "price": 5000,
                        "currency": "USD",
                        "category_id": GARAGES_ID,
                        "fields": {
                            "deal_type": "sell",
                            "city": "Р‘РёС€РєРµРє",
                            "seller_type": "owner",
                            "negotiable": "yes",
                            "contact_methods": "Только телефон",
                        },
                    },
                    "435000",
                    "USD",
                    True,
                ),
                (
                    {
                        "title": "PkgB Parking",
                        "description": "b",
                        "price": 2000,
                        "currency": "USD",
                        "category_id": parking_id,
                        "fields": {
                            "deal_type": "sell",
                            "city": "Р‘РёС€РєРµРє",
                            "seller_type": "owner",
                            "negotiable": "yes",
                            "contact_methods": "Только телефон",
                        },
                    },
                    "174000",
                    "USD",
                    True,
                ),
                (
                    {
                        "title": "PkgB Draft apt",
                        "description": "b",
                        "price": 1,
                        "currency": "USD",
                        "category_id": APARTMENTS_ID,
                        "fields": {
                            "deal_type": "sell",
                            "area": "40",
                            "city": "Р‘РёС€РєРµРє",
                            "seller_type": "owner",
                            "negotiable": "yes",
                            "contact_methods": "Только телефон",
                        },
                    },
                    "87",
                    "USD",
                    False,
                ),
                (
                    {
                        "title": "PkgB Apt sell KGS",
                        "description": "b",
                        "price": 5000000,
                        "currency": "KGS",
                        "category_id": APARTMENTS_ID,
                        "fields": {
                            "deal_type": "sell",
                            "rooms": "2",
                            "area": "70",
                            "district": "sverdlovsky",
                            "city": "Р‘РёС€РєРµРє",
                            "seller_type": "owner",
                            "negotiable": "yes",
                            "contact_methods": "Только телефон",
                        },
                    },
                    "5000000",
                    "KGS",
                    True,
                ),
            ]

            for payload, nk, cur, activate in fixtures:
                lid = await _create_draft(client, payload)
                created_ids.append(lid)
                if activate:
                    await _force_active(lid, normalized_kgs=nk, currency=cur)

            # Mark one as sold (non-searchable)
            sold = await _create_draft(
                client,
                {
                    "title": "PkgB Sold apt",
                    "description": "b",
                    "price": 1,
                    "currency": "USD",
                    "category_id": APARTMENTS_ID,
                    "fields": {
                        "deal_type": "sell",
                        "area": "40",
                        "city": "Р‘РёС€РєРµРє",
                        "seller_type": "owner",
                        "negotiable": "yes",
                        "contact_methods": "Только телефон",
                    },
                },
            )
            created_ids.append(sold)
            async with async_session_maker() as session:
                await session.execute(
                    text(
                        "UPDATE listings SET status='sold', updated_at=now() WHERE id=:id"
                    ),
                    {"id": sold},
                )
                await session.commit()

            # Property category facets
            ids = ",".join(
                str(i)
                for i in (
                    APARTMENTS_ID,
                    HOUSES_ID,
                    ROOMS_ID,
                    LAND_ID,
                    COMMERCIAL_ID,
                    GARAGES_ID,
                    parking_id,
                )
            )
            r = await client.get(
                "/api/v1/listings",
                params={"category_ids": ids, "facets": "_category", "limit": 1},
            )
            assert r.status_code == 200, r.text
            facets = {x["value"]: x["count"] for x in r.json()["facets"]["_category"]}
            assert facets[str(APARTMENTS_ID)] >= 4
            assert facets[str(HOUSES_ID)] >= 1
            assert facets[str(GARAGES_ID)] >= 1
            assert facets[str(parking_id)] >= 1

            r = await client.get(
                "/api/v1/listings",
                params={
                    "category_id": APARTMENTS_ID,
                    "attrs": json.dumps({"deal_type": "sell", "rooms": "2"}),
                    "facets": "deal_type,rooms",
                    "limit": 1,
                },
            )
            assert r.status_code == 200, r.text
            deals = {x["value"]: x["count"] for x in r.json()["facets"]["deal_type"]}
            rooms = {x["value"]: x["count"] for x in r.json()["facets"]["rooms"]}
            assert deals.get("sell", 0) >= 1
            assert rooms.get("2", 0) >= 1

            found = await client.get(
                "/api/v1/listings",
                params={
                    "category_id": APARTMENTS_ID,
                    "attrs": json.dumps(
                        {
                            "deal_type": "sell",
                            "area__min": "60",
                            "area__max": "80",
                        }
                    ),
                    "limit": 40,
                },
            )
            assert found.status_code == 200
            titles = [i["title"] for i in found.json()["items"]]
            assert any("72" in t for t in titles)

            missed = await client.get(
                "/api/v1/listings",
                params={
                    "category_id": APARTMENTS_ID,
                    "attrs": json.dumps(
                        {
                            "deal_type": "sell",
                            "area__min": "80",
                            "area__max": "100",
                        }
                    ),
                    "limit": 40,
                },
            )
            assert missed.status_code == 200
            titles2 = [i["title"] for i in missed.json()["items"]]
            assert not any("72" in t for t in titles2)

            items = (
                await client.get(
                    "/api/v1/listings",
                    params={
                        "category_id": APARTMENTS_ID,
                        "attrs": json.dumps({"deal_type": "sell"}),
                        "limit": 50,
                    },
                )
            ).json()["items"]
            assert all(i["title"] != "PkgB Draft apt" for i in items)
            assert all(i["title"] != "PkgB Sold apt" for i in items)

            r = await client.get(
                "/api/v1/listings",
                params={
                    "category_id": COMMERCIAL_ID,
                    "attrs": json.dumps({"deal_type": "rent"}),
                    "facets": "commercial_direction",
                    "limit": 1,
                },
            )
            assert r.status_code == 200
            dirs = {
                x["value"]: x["count"]
                for x in r.json()["facets"]["commercial_direction"]
            }
            assert dirs.get("office_coworking", 0) >= 1

            # Geo / floor / district facets are whitelist-safe field keys.
            r = await client.get(
                "/api/v1/listings",
                params={
                    "category_id": APARTMENTS_ID,
                    "facets": "city,region,district,floor,subtype",
                    "limit": 1,
                },
            )
            assert r.status_code == 200
            assert "city" in (r.json().get("facets") or {})
            assert "district" in (r.json().get("facets") or {})
            assert "subtype" in (r.json().get("facets") or {})

            r = await client.get(
                "/api/v1/listings",
                params={"category_id": APARTMENTS_ID, "limit": 5},
            )
            assert r.status_code == 200
            assert r.json().get("facets") is None

            a = (
                await client.get(
                    "/api/v1/listings",
                    params={
                        "category_id": APARTMENTS_ID,
                        "sort": "newest",
                        "limit": 1,
                    },
                )
            ).json()["total"]
            b = (
                await client.get(
                    "/api/v1/listings",
                    params={
                        "category_id": APARTMENTS_ID,
                        "sort": "price_asc",
                        "limit": 1,
                    },
                )
            ).json()["total"]
            assert a == b

            g = (
                await client.get(
                    "/api/v1/listings",
                    params={"category_id": GARAGES_ID, "limit": 10},
                )
            ).json()
            p = (
                await client.get(
                    "/api/v1/listings",
                    params={"category_id": parking_id, "limit": 10},
                )
            ).json()
            assert g["total"] >= 1
            assert p["total"] >= 1

            # Intelligence still returns area for apartments
            intel = await client.get(
                f"/api/v1/categories/intelligence/{APARTMENTS_ID}"
            )
            assert intel.status_code == 200
            keys = {
                f.get("field_key") or f.get("key")
                for f in (intel.json().get("core_fields") or [])
            }
            assert "area" in keys
            assert APARTMENTS_SLUG.startswith("real-estate")
    finally:
        async with async_session_maker() as session:
            if created_ids:
                await session.execute(
                    text(
                        "DELETE FROM listing_field_values WHERE listing_id = ANY(:ids)"
                    ),
                    {"ids": created_ids},
                )
                await session.execute(
                    text("DELETE FROM listings WHERE id = ANY(:ids)"),
                    {"ids": created_ids},
                )
                await session.commit()
        app.dependency_overrides.clear()


def test_real_estate_v2_package_b() -> None:
    asyncio.run(_run_all())
