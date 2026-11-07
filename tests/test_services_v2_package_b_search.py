# -*- coding: utf-8 -*-
"""Services V2 Package B — Search filters, facets, Create↔Search parity."""
from __future__ import annotations

from decimal import Decimal

import json

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
from app.seeds.services_v2 import (
    SERVICES_NEGOTIATED_VALUE,
    SERVICES_V2_CANONICAL_SLUGS,
    SERVICES_V2_RETIRED_SLUGS,
    build_services_v2_core_fields,
    build_services_v2_search_filters,
)


def test_services_v2_search_filters_shape() -> None:
    filters = build_services_v2_search_filters()
    assert set(filters) == SERVICES_V2_CANONICAL_SLUGS
    for slug in SERVICES_V2_CANONICAL_SLUGS:
        keys = [f[0] for f in filters[slug]]
        assert keys[0] == "service_kind"
        assert "executor" in keys
        assert "price" not in keys
        assert "negotiable" not in keys
        assert "contact_methods" not in keys
        assert "service_materials" not in keys
        by_key = {f[0]: f for f in filters[slug]}
        assert by_key["service_kind"][2] == CategoryFilterType.multi_select
        assert by_key["executor"][2] == CategoryFilterType.multi_select
    plumbing = {f[0]: f for f in filters["services-santehnika"]}
    assert "service_object" in plumbing
    assert plumbing["service_object"][2] == CategoryFilterType.multi_select
    cleaning = {f[0]: f for f in filters["services-uborka-i-klining"]}
    kind_opts = {
        o["value"] for o in cleaning["service_kind"][4]["options"]
    }
    assert "Уборка помещений" in kind_opts
    assert "Химчистка одежды и текстиля" in kind_opts
    assert "Дезинфекция" in kind_opts
    realtor = {f[0]: f for f in filters["services-rieltorskie-uslugi"]}
    assert "service_kind" in realtor


@pytest.mark.asyncio
async def test_services_v2_search_filters_in_db_and_intelligence(client) -> None:
    await engine.dispose()
    expected = build_services_v2_search_filters()
    async with async_session_maker() as session:
        for slug in (
            "services-santehnika",
            "services-uborka-i-klining",
            "services-rieltorskie-uslugi",
            "services-kompyutery-i-it-uslugi",
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
            assert "service_materials" not in {r.filter_key for r in rows}
            assert "price" not in {r.filter_key for r in rows}

        for slug in sorted(SERVICES_V2_RETIRED_SLUGS):
            row = (
                await session.execute(select(Category).where(Category.slug == slug))
            ).scalar_one_or_none()
            if row is None:
                continue
            assert row.is_active is False

    async with async_session_maker() as session:
        cat = (
            await session.execute(
                select(Category).where(Category.slug == "services-santehnika")
            )
        ).scalar_one()
        cat_id = cat.id
    resp = await client.get(f"/api/v1/categories/intelligence/{cat_id}")
    assert resp.status_code == 200
    body = resp.json()
    fkeys = [f["filter_key"] for f in body["filters"]]
    assert fkeys[0] == "service_kind"
    assert "executor" in fkeys
    assert "service_object" in fkeys
    assert "price" not in fkeys
    assert "service_materials" not in fkeys
    core_keys = [f["field_key"] for f in body["core_fields"]]
    assert "service_materials" not in core_keys
    assert any(f["label"] == "Цена от" for f in body["core_fields"])


@pytest.mark.asyncio
async def test_services_v2_search_parity_facets_and_negotiated(client) -> None:
    await engine.dispose()
    async with async_session_maker() as session:
        owner = (
            await session.execute(select(User).order_by(User.id).limit(1))
        ).scalar_one()
        plumbing = (
            await session.execute(
                select(Category).where(Category.slug == "services-santehnika")
            )
        ).scalar_one()
        cleaning = (
            await session.execute(
                select(Category).where(Category.slug == "services-uborka-i-klining")
            )
        ).scalar_one()
        realtor = (
            await session.execute(
                select(Category).where(Category.slug == "services-rieltorskie-uslugi")
            )
        ).scalar_one()

        kinds = build_services_v2_core_fields()["services-santehnika"]
        kind_choices = kinds[0][5]["choices"]
        kind_a = kind_choices[0]["value"]
        kind_b = kind_choices[1]["value"] if len(kind_choices) > 1 else kind_a
        executor_choices = next(f for f in kinds if f[0] == "executor")[5]["choices"]
        exec_y = executor_choices[0]["value"]
        exec_other = (
            executor_choices[1]["value"]
            if len(executor_choices) > 1
            else f"{exec_y}-other"
        )
        object_choices = next(f for f in kinds if f[0] == "service_object")[5][
            "choices"
        ]
        obj_a = object_choices[0]["value"]
        obj_b = object_choices[1]["value"]
        obj_c = object_choices[2]["value"] if len(object_choices) > 2 else obj_b

        cleaning_kinds = build_services_v2_search_filters()[
            "services-uborka-i-klining"
        ][0][4]["options"]
        merged_kind = next(
            o["value"]
            for o in cleaning_kinds
            if "Химчистка" in o["value"] or "Дезинфекция" in o["value"]
        )
        realtor_kind = build_services_v2_search_filters()[
            "services-rieltorskie-uslugi"
        ][0][4]["options"][0]["value"]

        created_ids: list[int] = []

        async def _add(
            *,
            category_id: int,
            title: str,
            price: Decimal | None,
            fields: dict[str, str],
        ) -> Listing:
            listing = Listing(
                title=title,
                description=title,
                price=price,
                currency=Currency.KGS,
                status=ListingStatus.active,
                owner_id=owner.id,
                category_id=category_id,
            )
            session.add(listing)
            await session.flush()
            created_ids.append(listing.id)
            for key, value in fields.items():
                session.add(
                    ListingFieldValue(
                        listing_id=listing.id,
                        field_key=key,
                        value_text=value,
                    )
                )
            return listing

        plumbing_id = plumbing.id
        cleaning_id = cleaning.id
        realtor_id = realtor.id

        await _add(
            category_id=plumbing_id,
            title="PKG-B plumbing multi",
            price=Decimal("1000"),
            fields={
                "service_kind": kind_a,
                "executor": exec_y,
                "service_object": f"{obj_a}||{obj_b}",
                "city": "Бишкек",
                "contact_methods": "Только чат",
            },
        )
        await _add(
            category_id=plumbing_id,
            title="PKG-B plumbing negotiated",
            price=None,
            fields={
                "service_kind": kind_a,
                "executor": exec_y,
                "service_object": obj_a,
                "city": "Ош",
                "negotiable": SERVICES_NEGOTIATED_VALUE,
                "contact_methods": "Только чат",
            },
        )
        await _add(
            category_id=cleaning_id,
            title="PKG-B cleaning merged",
            price=Decimal("500"),
            fields={
                "service_kind": merged_kind,
                "executor": build_services_v2_search_filters()[
                    "services-uborka-i-klining"
                ][1][4]["options"][0]["value"],
                "city": "Бишкек",
                "contact_methods": "Только чат",
            },
        )
        await _add(
            category_id=realtor_id,
            title="PKG-B realtor",
            price=Decimal("2000"),
            fields={
                "service_kind": realtor_kind,
                "executor": build_services_v2_search_filters()[
                    "services-rieltorskie-uslugi"
                ][1][4]["options"][0]["value"],
                "city": "Бишкек",
                "contact_methods": "Только чат",
            },
        )
        await session.commit()

    try:
        # Kind A + object A → FOUND
        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": plumbing_id,
                "attrs": json.dumps(
                    {"service_kind": kind_a, "service_object": obj_a}
                ),
                "limit": 40,
                "facets": "service_kind,executor,service_object",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        titles = {i["title"] for i in body["items"]}
        assert "PKG-B plumbing multi" in titles
        assert body["total"] >= 1

        def _facet_map(raw) -> dict[str, int]:
            out: dict[str, int] = {}
            for item in raw or []:
                out[str(item["value"])] = int(item["count"])
            return out

        obj_facet = _facet_map(body["facets"]["service_object"])
        assert obj_facet.get(obj_a, 0) >= 1
        assert obj_facet.get(obj_b, 0) >= 1

        if kind_b != kind_a:
            resp = await client.get(
                "/api/v1/listings",
                params={
                    "category_id": plumbing_id,
                    "attrs": json.dumps({"service_kind": kind_b}),
                    "limit": 40,
                },
            )
            titles = {i["title"] for i in resp.json()["items"]}
            assert "PKG-B plumbing multi" not in titles

        if obj_c not in {obj_a, obj_b}:
            resp = await client.get(
                "/api/v1/listings",
                params={
                    "category_id": plumbing_id,
                    "attrs": json.dumps({"service_object": obj_c}),
                    "limit": 40,
                },
            )
            titles = {i["title"] for i in resp.json()["items"]}
            assert "PKG-B plumbing multi" not in titles

        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": plumbing_id,
                "attrs": json.dumps({"executor": exec_y}),
                "limit": 40,
            },
        )
        titles = {i["title"] for i in resp.json()["items"]}
        assert "PKG-B plumbing multi" in titles

        if exec_other != exec_y:
            resp = await client.get(
                "/api/v1/listings",
                params={
                    "category_id": plumbing_id,
                    "attrs": json.dumps({"executor": exec_other}),
                    "limit": 40,
                },
            )
            titles = {i["title"] for i in resp.json()["items"]}
            assert "PKG-B plumbing multi" not in titles

        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": plumbing_id,
                "city": "Бишкек",
                "limit": 40,
            },
        )
        titles = {i["title"] for i in resp.json()["items"]}
        assert "PKG-B plumbing multi" in titles
        assert "PKG-B plumbing negotiated" not in titles

        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": plumbing_id,
                "city": "Ош",
                "limit": 40,
            },
        )
        titles = {i["title"] for i in resp.json()["items"]}
        assert "PKG-B plumbing negotiated" in titles

        negotiated = next(
            i
            for i in resp.json()["items"]
            if i["title"] == "PKG-B plumbing negotiated"
        )
        assert negotiated.get("price") is None

        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": cleaning_id,
                "attrs": json.dumps({"service_kind": merged_kind}),
                "limit": 40,
            },
        )
        titles = {i["title"] for i in resp.json()["items"]}
        assert "PKG-B cleaning merged" in titles

        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": realtor_id,
                "attrs": json.dumps({"service_kind": realtor_kind}),
                "limit": 40,
            },
        )
        titles = {i["title"] for i in resp.json()["items"]}
        assert "PKG-B realtor" in titles

        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": plumbing_id,
                "attrs": json.dumps(
                    {"service_kind": kind_a, "service_object": obj_a}
                ),
                "facets": "service_object",
                "limit": 1,
            },
        )
        obj_facet = {
            str(i["value"]): int(i["count"])
            for i in resp.json()["facets"]["service_object"]
        }
        assert obj_facet.get(obj_a, 0) >= 1
        assert obj_facet.get(obj_b, 0) >= 1
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
