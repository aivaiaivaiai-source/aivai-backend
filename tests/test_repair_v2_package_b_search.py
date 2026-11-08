# -*- coding: utf-8 -*-
"""Repair V2 Package B — Search filters, facets, Create↔Search parity."""
from __future__ import annotations

import json
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.db.session import async_session_maker, engine
from app.models.category import Category
from app.models.category_enums import CategoryFilterType
from app.models.category_filter import CategoryFilter
from app.models.enums import Currency, ListingStatus
from app.models.listing import Listing
from app.models.listing_field_value import ListingFieldValue
from app.models.user import User
from app.seeds.repair_v2 import (
    REPAIR_V2_CANONICAL_SLUGS,
    REPAIR_V2_RETIRED_SLUGS,
    build_repair_v2_core_fields,
    build_repair_v2_search_filters,
)


def test_repair_v2_search_filters_shape() -> None:
    filters = build_repair_v2_search_filters()
    assert set(filters) == REPAIR_V2_CANONICAL_SLUGS
    core = build_repair_v2_core_fields()
    for slug in REPAIR_V2_CANONICAL_SLUGS:
        keys = [f[0] for f in filters[slug]]
        assert keys[0] == "repair_kind"
        assert "price" not in keys
        assert "negotiable" not in keys
        assert "contact_methods" not in keys
        by_key = {f[0]: f for f in filters[slug]}
        assert by_key["repair_kind"][1] == "Вид товара"
        assert by_key["repair_kind"][2] == CategoryFilterType.multi_select
        assert "seller_type" in by_key
        # Create↔Search: every search key exists in Create core (except none).
        core_keys = {f[0] for f in core[slug]}
        for key in keys:
            assert key in core_keys, (slug, key)
        # Kind options match Create catalog.
        create_kinds = {
            c["value"] for c in core[slug][0][5]["choices"]
        }
        search_kinds = {
            o["value"] for o in by_key["repair_kind"][4]["options"]
        }
        assert search_kinds == create_kinds

    lumber = {f[0]: f for f in filters["repair-construction-pilomaterialy"]}
    moisture = lumber["moisture"][4]
    assert moisture["depends_on"]["field"] == "repair_kind"
    assert "Доска" in moisture["depends_on"]["values"]


@pytest.mark.asyncio
async def test_repair_v2_search_filters_in_db_and_intelligence(client) -> None:
    await engine.dispose()
    expected = build_repair_v2_search_filters()
    async with async_session_maker() as session:
        for slug in (
            "repair-construction-santehnika-i-vodosnabzhenie",
            "repair-construction-lakokrasochnye-materialy",
            "repair-construction-pilomaterialy",
            "repair-construction-kirpichi-i-stroitelnye-bloki",
        ):
            cat = (
                await session.execute(select(Category).where(Category.slug == slug))
            ).scalar_one()
            rows = (
                await session.execute(
                    select(CategoryFilter)
                    .where(CategoryFilter.category_id == cat.id)
                    .order_by(CategoryFilter.sort_order)
                )
            ).scalars().all()
            assert [r.filter_key for r in rows] == [f[0] for f in expected[slug]]
            assert "price" not in {r.filter_key for r in rows}

        for slug in sorted(REPAIR_V2_RETIRED_SLUGS):
            row = (
                await session.execute(select(Category).where(Category.slug == slug))
            ).scalar_one_or_none()
            if row is None:
                continue
            assert row.is_active is False

        # All 28 leaves: intelligence filters non-empty, repair_kind present.
        for slug in sorted(REPAIR_V2_CANONICAL_SLUGS):
            cat = (
                await session.execute(select(Category).where(Category.slug == slug))
            ).scalar_one()
            assert cat.is_active is True
            rows = (
                await session.execute(
                    select(CategoryFilter).where(CategoryFilter.category_id == cat.id)
                )
            ).scalars().all()
            assert rows, slug
            assert rows[0].filter_key == "repair_kind"
            cfg = rows[0].config or {}
            opts = cfg.get("options") or cfg.get("choices") or []
            assert opts, slug

    async with async_session_maker() as session:
        cat = (
            await session.execute(
                select(Category).where(
                    Category.slug == "repair-construction-pilomaterialy"
                )
            )
        ).scalar_one()
        cat_id = cat.id
    resp = await client.get(f"/api/v1/categories/intelligence/{cat_id}")
    assert resp.status_code == 200
    body = resp.json()
    fkeys = [f["filter_key"] for f in body["filters"]]
    assert fkeys[0] == "repair_kind"
    assert body["filters"][0]["label"] == "Вид товара"
    assert "moisture" in fkeys
    assert "price" not in fkeys
    assert any(f["label"] == "Цена" for f in body["core_fields"])


@pytest.mark.asyncio
async def test_repair_v2_search_parity_facets_geo_isolation(client) -> None:
    await engine.dispose()
    async with async_session_maker() as session:
        owner = (
            await session.execute(select(User).order_by(User.id).limit(1))
        ).scalar_one()
        bricks = (
            await session.execute(
                select(Category).where(
                    Category.slug
                    == "repair-construction-kirpichi-i-stroitelnye-bloki"
                )
            )
        ).scalar_one()
        plumbing = (
            await session.execute(
                select(Category).where(
                    Category.slug
                    == "repair-construction-santehnika-i-vodosnabzhenie"
                )
            )
        ).scalar_one()
        tools = (
            await session.execute(
                select(Category).where(
                    Category.slug == "repair-construction-instrumenty"
                )
            )
        ).scalar_one()
        power = (
            await session.execute(
                select(Category).where(
                    Category.slug == "repair-construction-elektroinstrumenty"
                )
            )
        ).scalar_one()
        services_plumbing = (
            await session.execute(
                select(Category).where(Category.slug == "services-santehnika")
            )
        ).scalar_one_or_none()

        brick_kinds = build_repair_v2_core_fields()[
            "repair-construction-kirpichi-i-stroitelnye-bloki"
        ][0][5]["choices"]
        kind_a = brick_kinds[0]["value"]
        kind_b = brick_kinds[1]["value"]
        seller = next(
            f
            for f in build_repair_v2_core_fields()[
                "repair-construction-kirpichi-i-stroitelnye-bloki"
            ]
            if f[0] == "seller_type"
        )[5]["choices"][0]["value"]
        condition = next(
            f
            for f in build_repair_v2_core_fields()[
                "repair-construction-kirpichi-i-stroitelnye-bloki"
            ]
            if f[0] == "condition"
        )[5]["choices"][0]["value"]

        plumbing_kind = build_repair_v2_core_fields()[
            "repair-construction-santehnika-i-vodosnabzhenie"
        ][0][5]["choices"][0]["value"]
        tool_kind = build_repair_v2_core_fields()[
            "repair-construction-instrumenty"
        ][0][5]["choices"][0]["value"]
        power_kind = build_repair_v2_core_fields()[
            "repair-construction-elektroinstrumenty"
        ][0][5]["choices"][0]["value"]

        created_ids: list[int] = []

        async def _add(
            *,
            category_id: int,
            title: str,
            city: str,
            fields: dict[str, str],
            price: str = "1500",
        ) -> None:
            listing = Listing(
                title=title,
                description=title,
                price=Decimal(price),
                currency=Currency.KGS,
                status=ListingStatus.active,
                owner_id=owner.id,
                category_id=category_id,
            )
            session.add(listing)
            await session.flush()
            created_ids.append(listing.id)
            payload = {
                "city": city,
                "contact_methods": "Только чат",
                **fields,
            }
            for key, value in payload.items():
                session.add(
                    ListingFieldValue(
                        listing_id=listing.id,
                        field_key=key,
                        value_text=value,
                    )
                )

        await _add(
            category_id=bricks.id,
            title="PKG-B brick A1",
            city="Бишкек",
            fields={
                "repair_kind": kind_a,
                "seller_type": seller,
                "condition": condition,
            },
        )
        await _add(
            category_id=bricks.id,
            title="PKG-B brick A2",
            city="Бишкек",
            fields={
                "repair_kind": kind_a,
                "seller_type": seller,
                "condition": condition,
            },
            price="2000",
        )
        await _add(
            category_id=bricks.id,
            title="PKG-B brick B",
            city="Ош",
            fields={
                "repair_kind": kind_b,
                "seller_type": seller,
                "condition": condition,
            },
        )
        await _add(
            category_id=plumbing.id,
            title="PKG-B plumbing goods",
            city="Бишкек",
            fields={"repair_kind": plumbing_kind, "seller_type": seller},
        )
        await _add(
            category_id=tools.id,
            title="PKG-B hand tools",
            city="Бишкек",
            fields={"repair_kind": tool_kind, "seller_type": seller},
        )
        await _add(
            category_id=power.id,
            title="PKG-B power tools",
            city="Бишкек",
            fields={"repair_kind": power_kind, "seller_type": seller},
        )
        if services_plumbing is not None:
            await _add(
                category_id=services_plumbing.id,
                title="PKG-B services plumbing work",
                city="Бишкек",
                fields={
                    "service_kind": "Установка сантехники",
                    "executor": "Частный мастер",
                },
                price="3000",
            )
        await session.commit()
        bricks_id = bricks.id
        plumbing_id = plumbing.id
        tools_id = tools.id
        power_id = power.id
        services_plumbing_id = (
            services_plumbing.id if services_plumbing is not None else None
        )

    try:
        # Kind A FOUND (2), kind B NOT for kind A filter
        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": bricks_id,
                "attrs": json.dumps({"repair_kind": kind_a}),
                "limit": 40,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 2
        titles = {i["title"] for i in body["items"]}
        assert "PKG-B brick A1" in titles
        assert "PKG-B brick B" not in titles

        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": bricks_id,
                "attrs": json.dumps({"repair_kind": kind_b}),
                "limit": 40,
            },
        )
        assert resp.status_code == 200
        titles = {i["title"] for i in resp.json()["items"]}
        assert "PKG-B brick B" in titles
        assert "PKG-B brick A1" not in titles

        # Facet self-exclusion: select kind A, still see A/B distribution
        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": bricks_id,
                "attrs": json.dumps({"repair_kind": kind_a}),
                "facets": "repair_kind",
                "limit": 1,
            },
        )
        assert resp.status_code == 200
        kind_facet = {
            str(i["value"]): int(i["count"])
            for i in (resp.json().get("facets") or {}).get("repair_kind") or []
        }
        assert kind_facet.get(kind_a, 0) >= 2
        assert kind_facet.get(kind_b, 0) >= 1

        # Geo: Bishkek vs Osh
        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": bricks_id,
                "city": "Бишкек",
                "limit": 40,
            },
        )
        assert resp.status_code == 200
        titles = {i["title"] for i in resp.json()["items"]}
        assert "PKG-B brick A1" in titles
        assert "PKG-B brick B" not in titles

        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": bricks_id,
                "city": "Ош",
                "limit": 40,
            },
        )
        assert resp.status_code == 200
        titles = {i["title"] for i in resp.json()["items"]}
        assert "PKG-B brick B" in titles
        assert "PKG-B brick A1" not in titles

        # Plumbing goods leaf does not mix Services plumbing
        resp = await client.get(
            "/api/v1/listings",
            params={"category_id": plumbing_id, "limit": 40},
        )
        assert resp.status_code == 200
        titles = {i["title"] for i in resp.json()["items"]}
        assert "PKG-B plumbing goods" in titles
        assert "PKG-B services plumbing work" not in titles

        # Tools vs power tools isolation
        resp = await client.get(
            "/api/v1/listings",
            params={"category_id": tools_id, "limit": 40},
        )
        titles = {i["title"] for i in resp.json()["items"]}
        assert "PKG-B hand tools" in titles
        assert "PKG-B power tools" not in titles

        resp = await client.get(
            "/api/v1/listings",
            params={"category_id": power_id, "limit": 40},
        )
        titles = {i["title"] for i in resp.json()["items"]}
        assert "PKG-B power tools" in titles
        assert "PKG-B hand tools" not in titles

        if services_plumbing_id is not None:
            resp = await client.get(
                "/api/v1/listings",
                params={"category_id": services_plumbing_id, "limit": 40},
            )
            titles = {i["title"] for i in resp.json()["items"]}
            assert "PKG-B plumbing goods" not in titles
    finally:
        async with async_session_maker() as session:
            for lid in created_ids:
                await session.execute(
                    ListingFieldValue.__table__.delete().where(
                        ListingFieldValue.listing_id == lid
                    )
                )
                await session.execute(
                    Listing.__table__.delete().where(Listing.id == lid)
                )
            await session.commit()
