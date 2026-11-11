"""Food/Agri V2 Package B — Search SoT + Create↔Search parity."""
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
from app.seeds.food_agri_v2 import (
    FOOD_AGRI_CREATE_FORBIDDEN,
    FOOD_AGRI_KIND_KEY,
    FOOD_AGRI_PRICE_BASIS_FIELD_KEY,
    FOOD_AGRI_SELLER_CHOICES,
    FOOD_AGRI_SELLER_KEY,
    FOOD_AGRI_V2_CANONICAL_SLUGS,
    FOOD_AGRI_V2_EXPECTED_KIND_COUNT,
    FOOD_AGRI_V2_EXPECTED_L2_COUNT,
    FOOD_AGRI_V2_RETIRED_SLUGS,
    FOOD_AGRI_V2_SEARCH_ALLOWLIST,
    FOOD_AGRI_V2_SEARCH_EAV_KEYS,
    FOOD_AGRI_V2_SEARCH_EXCLUDE,
    build_food_agri_v2_core_fields,
    build_food_agri_v2_search_filters,
    food_agri_v2_all_search_kind_audit,
    food_agri_v2_assert_contracts,
    food_agri_v2_section_kinds,
)

# Independent approved expectations (not derived from builder alone).
_INDEPENDENT_SELLER = ("Частное лицо", "Фермер", "Магазин", "Другой")
_FORBIDDEN_SEARCH = frozenset(
    {
        "price",
        "price_basis",
        "negotiable",
        "contact_methods",
        "condition",
        "quantity",
        "weight",
        "volume",
        "brand",
        "origin",
        "producer",
        "organic",
        "eco",
        "expiry",
        "freshness",
        "wholesale",
        "packaging",
    }
)
_REPR_SLUGS = (
    "food-agri-ovoschi-i-frukty",
    "food-agri-myaso-i-myasnaya-produktsiya",
    "food-agri-molochnaya-produktsiya",
    "food-agri-napitki",
    "food-agri-zerno-i-zernovye-kultury",
    "food-agri-gotovaya-eda-i-kulinariya",
    "food-agri-prochie-produkty-i-selhoztovary",
)


def _options_for(filters: list, key: str) -> list[dict]:
    for row in filters:
        if row[0] != key:
            continue
        cfg = row[4] or {}
        return list(cfg.get("options") or cfg.get("choices") or [])
    return []


def test_food_package_a_contracts_still_locked() -> None:
    food_agri_v2_assert_contracts()
    assert len(FOOD_AGRI_V2_CANONICAL_SLUGS) == FOOD_AGRI_V2_EXPECTED_L2_COUNT == 23
    assert FOOD_AGRI_V2_EXPECTED_KIND_COUNT == 158


def test_food_search_filters_cover_all_canonical_l2() -> None:
    filters = build_food_agri_v2_search_filters()
    assert set(filters) == FOOD_AGRI_V2_CANONICAL_SLUGS
    assert len(filters) == 23


def test_food_search_eav_keys_are_short_allowlist() -> None:
    assert FOOD_AGRI_V2_SEARCH_EAV_KEYS <= FOOD_AGRI_V2_SEARCH_ALLOWLIST
    assert FOOD_AGRI_KIND_KEY in FOOD_AGRI_V2_SEARCH_EAV_KEYS
    assert FOOD_AGRI_SELLER_KEY in FOOD_AGRI_V2_SEARCH_EAV_KEYS
    assert FOOD_AGRI_PRICE_BASIS_FIELD_KEY not in FOOD_AGRI_V2_SEARCH_EAV_KEYS
    assert "price" not in FOOD_AGRI_V2_SEARCH_EAV_KEYS
    assert "region" not in FOOD_AGRI_V2_SEARCH_EAV_KEYS


def test_food_search_filters_no_forbidden_or_create_only() -> None:
    for slug, rows in build_food_agri_v2_search_filters().items():
        keys = {r[0] for r in rows}
        assert keys == FOOD_AGRI_V2_SEARCH_EAV_KEYS, slug
        assert keys.isdisjoint(_FORBIDDEN_SEARCH), slug
        assert keys.isdisjoint(FOOD_AGRI_V2_SEARCH_EXCLUDE), slug
        assert keys.isdisjoint(FOOD_AGRI_CREATE_FORBIDDEN), slug
        assert FOOD_AGRI_KIND_KEY in keys
        assert FOOD_AGRI_SELLER_KEY in keys


def test_food_search_seller_independent_contract() -> None:
    for slug, rows in build_food_agri_v2_search_filters().items():
        opts = _options_for(rows, FOOD_AGRI_SELLER_KEY)
        labels = tuple(o.get("label") or o.get("value") for o in opts)
        assert labels == _INDEPENDENT_SELLER, slug
        assert labels == FOOD_AGRI_SELLER_CHOICES


def test_food_search_kind_options_match_create_per_l2() -> None:
    cores = build_food_agri_v2_core_fields()
    filters = build_food_agri_v2_search_filters()
    for slug in FOOD_AGRI_V2_CANONICAL_SLUGS:
        create_kinds = {
            c["value"]
            for c in next(r for r in cores[slug] if r[0] == FOOD_AGRI_KIND_KEY)[5][
                "choices"
            ]
        }
        search_kinds = {
            o["value"] for o in _options_for(filters[slug], FOOD_AGRI_KIND_KEY)
        }
        assert search_kinds == create_kinds
        assert len(search_kinds) > 0
        assert set(food_agri_v2_section_kinds(slug)) == create_kinds


def test_food_all_158_search_kind_audit() -> None:
    audit = food_agri_v2_all_search_kind_audit()
    assert len(audit) == FOOD_AGRI_V2_EXPECTED_KIND_COUNT
    for row in audit:
        assert row["search_food_kind"] == "YES"
        assert row["search_seller"] == "YES"
        assert row["search_price_basis"] == "NO"
        assert row["search_condition"] == "NO"
        assert row["search_quantity"] == "NO"
        assert row["retired_resurrected"] is False
        assert FOOD_AGRI_PRICE_BASIS_FIELD_KEY not in row["visible_search_keys"]
        assert "condition" not in row["visible_search_keys"]


def test_food_search_filter_type_multi_select() -> None:
    for slug, rows in build_food_agri_v2_search_filters().items():
        for key, label, ftype, sort, cfg in rows:
            assert ftype == CategoryFilterType.multi_select, (slug, key)
            assert cfg and (cfg.get("options") or cfg.get("choices"))


@pytest.mark.asyncio
async def test_food_search_filters_in_db_and_intelligence(client) -> None:
    await engine.dispose()
    expected = build_food_agri_v2_search_filters()
    async with async_session_maker() as session:
        for slug in sorted(FOOD_AGRI_V2_RETIRED_SLUGS):
            row = (
                await session.execute(select(Category).where(Category.slug == slug))
            ).scalar_one_or_none()
            if row is None:
                continue
            assert row.is_active is False

        for slug in sorted(FOOD_AGRI_V2_CANONICAL_SLUGS):
            cat = (
                await session.execute(select(Category).where(Category.slug == slug))
            ).scalar_one()
            assert cat.is_active is True
            rows = (
                await session.execute(
                    select(CategoryFilter)
                    .where(CategoryFilter.category_id == cat.id)
                    .order_by(CategoryFilter.sort_order)
                )
            ).scalars().all()
            assert [r.filter_key for r in rows] == [f[0] for f in expected[slug]]
            assert FOOD_AGRI_PRICE_BASIS_FIELD_KEY not in {
                r.filter_key for r in rows
            }
            assert "condition" not in {r.filter_key for r in rows}

    async with async_session_maker() as session:
        for slug in _REPR_SLUGS:
            cat = (
                await session.execute(select(Category).where(Category.slug == slug))
            ).scalar_one()
            resp = await client.get(f"/api/v1/categories/intelligence/{cat.id}")
            assert resp.status_code == 200, slug
            body = resp.json()
            keys = {f["filter_key"] for f in body.get("filters") or []}
            assert keys == set(FOOD_AGRI_V2_SEARCH_EAV_KEYS), slug
            seller = next(
                f for f in body["filters"] if f["filter_key"] == FOOD_AGRI_SELLER_KEY
            )
            cfg = seller.get("config") or {}
            opts = (
                seller.get("options")
                or cfg.get("options")
                or cfg.get("choices")
                or []
            )
            labels = [o.get("label") or o.get("value") for o in opts]
            assert tuple(labels) == _INDEPENDENT_SELLER


@pytest.mark.asyncio
async def test_food_create_search_parity_and_price_basis_isolation(client) -> None:
    await engine.dispose()
    created_ids: list[int] = []
    try:
        async with async_session_maker() as session:
            owner = (
                await session.execute(select(User).order_by(User.id).limit(1))
            ).scalar_one()
            produce = (
                await session.execute(
                    select(Category).where(
                        Category.slug == "food-agri-ovoschi-i-frukty"
                    )
                )
            ).scalar_one()
            meat = (
                await session.execute(
                    select(Category).where(
                        Category.slug == "food-agri-myaso-i-myasnaya-produktsiya"
                    )
                )
            ).scalar_one()
            dairy = (
                await session.execute(
                    select(Category).where(
                        Category.slug == "food-agri-molochnaya-produktsiya"
                    )
                )
            ).scalar_one()
            drinks = (
                await session.execute(
                    select(Category).where(Category.slug == "food-agri-napitki")
                )
            ).scalar_one()
            grain = (
                await session.execute(
                    select(Category).where(
                        Category.slug == "food-agri-zerno-i-zernovye-kultury"
                    )
                )
            ).scalar_one()
            ready = (
                await session.execute(
                    select(Category).where(
                        Category.slug == "food-agri-gotovaya-eda-i-kulinariya"
                    )
                )
            ).scalar_one()

            produce_kind = food_agri_v2_section_kinds(produce.slug)[0]
            meat_kind = food_agri_v2_section_kinds(meat.slug)[0]
            dairy_kind = food_agri_v2_section_kinds(dairy.slug)[0]
            drinks_kind = food_agri_v2_section_kinds(drinks.slug)[0]
            grain_kind = food_agri_v2_section_kinds(grain.slug)[0]
            ready_kind = food_agri_v2_section_kinds(ready.slug)[0]
            seller_ok = "Фермер"
            seller_other = "Магазин"

            async def _add(
                *,
                category_id: int,
                title: str,
                city: str,
                fields: dict[str, str],
                price: str = "100",
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
                created_ids.append(int(listing.id))
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
                category_id=produce.id,
                title="PKG-B food produce basis-kg",
                city="Бишкек",
                fields={
                    FOOD_AGRI_KIND_KEY: produce_kind,
                    FOOD_AGRI_SELLER_KEY: seller_ok,
                    FOOD_AGRI_PRICE_BASIS_FIELD_KEY: "кг",
                },
            )
            await _add(
                category_id=produce.id,
                title="PKG-B food produce no-basis",
                city="Бишкек",
                fields={
                    FOOD_AGRI_KIND_KEY: produce_kind,
                    FOOD_AGRI_SELLER_KEY: seller_ok,
                },
            )
            await _add(
                category_id=produce.id,
                title="PKG-B food produce wrong-seller",
                city="Бишкек",
                fields={
                    FOOD_AGRI_KIND_KEY: produce_kind,
                    FOOD_AGRI_SELLER_KEY: seller_other,
                },
            )
            await _add(
                category_id=produce.id,
                title="PKG-B food produce osh",
                city="Ош",
                fields={
                    FOOD_AGRI_KIND_KEY: produce_kind,
                    FOOD_AGRI_SELLER_KEY: seller_ok,
                },
            )
            await _add(
                category_id=meat.id,
                title="PKG-B food meat",
                city="Бишкек",
                fields={
                    FOOD_AGRI_KIND_KEY: meat_kind,
                    FOOD_AGRI_SELLER_KEY: seller_ok,
                },
            )
            await _add(
                category_id=dairy.id,
                title="PKG-B food dairy",
                city="Бишкек",
                fields={
                    FOOD_AGRI_KIND_KEY: dairy_kind,
                    FOOD_AGRI_SELLER_KEY: seller_ok,
                },
            )
            await _add(
                category_id=drinks.id,
                title="PKG-B food drinks",
                city="Бишкек",
                fields={
                    FOOD_AGRI_KIND_KEY: drinks_kind,
                    FOOD_AGRI_SELLER_KEY: seller_ok,
                },
            )
            await _add(
                category_id=grain.id,
                title="PKG-B food grain",
                city="Бишкек",
                fields={
                    FOOD_AGRI_KIND_KEY: grain_kind,
                    FOOD_AGRI_SELLER_KEY: seller_ok,
                },
            )
            await _add(
                category_id=ready.id,
                title="PKG-B food ready",
                city="Бишкек",
                fields={
                    FOOD_AGRI_KIND_KEY: ready_kind,
                    FOOD_AGRI_SELLER_KEY: seller_ok,
                },
            )
            await session.commit()
            produce_id = produce.id
            meat_id = meat.id

        # Kind+seller FOUND (includes price_basis=кг and empty basis)
        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": produce_id,
                "attrs": json.dumps(
                    {
                        FOOD_AGRI_KIND_KEY: produce_kind,
                        FOOD_AGRI_SELLER_KEY: seller_ok,
                    }
                ),
                "city": "Бишкек",
                "limit": 40,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        titles = {i["title"] for i in body["items"]}
        assert "PKG-B food produce basis-kg" in titles
        assert "PKG-B food produce no-basis" in titles
        assert "PKG-B food produce wrong-seller" not in titles
        assert "PKG-B food produce osh" not in titles
        assert "PKG-B food meat" not in titles

        # Wrong kind NOT FOUND
        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": produce_id,
                "attrs": json.dumps({FOOD_AGRI_KIND_KEY: meat_kind}),
                "limit": 40,
            },
        )
        assert resp.status_code == 200
        titles = {i["title"] for i in resp.json()["items"]}
        assert "PKG-B food produce basis-kg" not in titles

        # Meat FOUND in meat L2
        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": meat_id,
                "attrs": json.dumps({FOOD_AGRI_KIND_KEY: meat_kind}),
                "limit": 40,
            },
        )
        assert resp.status_code == 200
        titles = {i["title"] for i in resp.json()["items"]}
        assert "PKG-B food meat" in titles

        # Facet self-exclusion: select kind, still see kind distribution
        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": produce_id,
                "attrs": json.dumps({FOOD_AGRI_KIND_KEY: produce_kind}),
                "facets": f"{FOOD_AGRI_KIND_KEY},{FOOD_AGRI_SELLER_KEY}",
                "limit": 1,
            },
        )
        assert resp.status_code == 200
        facets = resp.json().get("facets") or {}
        kind_facet = {
            str(i["value"]): int(i["count"])
            for i in facets.get(FOOD_AGRI_KIND_KEY) or []
        }
        seller_facet = {
            str(i["value"]): int(i["count"])
            for i in facets.get(FOOD_AGRI_SELLER_KEY) or []
        }
        assert kind_facet.get(produce_kind, 0) >= 2
        assert seller_facet.get(seller_ok, 0) >= 1
        assert seller_facet.get(seller_other, 0) >= 1

        # price_basis must not be required for Search
        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": produce_id,
                "attrs": json.dumps({FOOD_AGRI_KIND_KEY: produce_kind}),
                "limit": 40,
            },
        )
        assert resp.status_code == 200
        titles = {i["title"] for i in resp.json()["items"]}
        assert "PKG-B food produce basis-kg" in titles
        assert "PKG-B food produce no-basis" in titles
    finally:
        if created_ids:
            async with async_session_maker() as session:
                await session.execute(
                    ListingFieldValue.__table__.delete().where(
                        ListingFieldValue.listing_id.in_(created_ids)
                    )
                )
                await session.execute(
                    Listing.__table__.delete().where(Listing.id.in_(created_ids))
                )
                await session.commit()
