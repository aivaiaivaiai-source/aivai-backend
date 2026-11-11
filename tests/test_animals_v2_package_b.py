"""Animals V2 Package B — Search SoT + Create↔Search parity."""
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
from app.seeds.animals_v2 import (
    ANIMALS_CONDITION_CHOICES,
    ANIMALS_CONDITION_KEY,
    ANIMALS_CREATE_FORBIDDEN,
    ANIMALS_GENDER_CHOICES,
    ANIMALS_GENDER_KEY,
    ANIMALS_KIND_KEY,
    ANIMALS_SELLER_CHOICES,
    ANIMALS_SELLER_KEY,
    ANIMALS_V2_CANONICAL_SLUGS,
    ANIMALS_V2_CONDITION_APPROVED_KINDS,
    ANIMALS_V2_EXPECTED_L2_COUNT,
    ANIMALS_V2_RETIRED_SLUGS,
    ANIMALS_V2_SEARCH_ALLOWLIST,
    ANIMALS_V2_SEARCH_EAV_KEYS,
    ANIMALS_V2_SEARCH_EXCLUDE,
    ANIMALS_V2_SEX_APPROVED_KINDS,
    ANIMALS_VET_SERVICES_SLUG,
    animals_v2_all_search_kind_audit,
    animals_v2_assert_package_a_contracts,
    animals_v2_kind_count,
    animals_v2_section_kinds,
    build_animals_v2_core_fields,
    build_animals_v2_search_filters,
)

# Independent approved expectations (Package A locked — not derived from builder).
_INDEPENDENT_SELLER = (
    "Частное лицо",
    "Хозяйство",
    "Питомник",
    "Магазин",
    "Другой",
)
_INDEPENDENT_SEX = ("Самец", "Самка")
_INDEPENDENT_CONDITION = ("Новое", "Б/у")
_INDEPENDENT_SEX_YES = frozenset(ANIMALS_V2_SEX_APPROVED_KINDS)
_INDEPENDENT_CONDITION_YES = frozenset(ANIMALS_V2_CONDITION_APPROVED_KINDS)
_FORBIDDEN_SEARCH = frozenset(
    {
        "price",
        "price_basis",
        "negotiable",
        "contact_methods",
        "age",
        "breed",
        "порода",
        "weight",
        "color",
        "documents",
        "vaccination_status",
        "quantity",
        "unit",
        "feed_unit",
    }
)
_REPR_SLUGS = (
    "animals-sobaki",
    "animals-ovtsy-barany-i-kozy",
    "animals-seno-korma-i-kormovye-dobavki",
    "animals-tovary-aksessuary-dlya-zhivotnyh",
    "animals-vetapteka-i-veterinarnye-tovary",
    "animals-ryby-i-akvariumistika",
    "animals-prochie-zhivotnye",
)


def _options_for(filters: list, key: str) -> list[dict]:
    for row in filters:
        if row[0] != key:
            continue
        cfg = row[4] or {}
        return list(cfg.get("options") or cfg.get("choices") or [])
    return []


def _depends_values(filters: list, key: str) -> set[str] | None:
    for row in filters:
        if row[0] != key:
            continue
        cfg = row[4] or {}
        dep = cfg.get("depends_on")
        if not dep:
            return None
        return {str(v) for v in (dep.get("values") or [])}
    return set()


def test_animals_package_a_still_locked() -> None:
    animals_v2_assert_package_a_contracts()
    assert len(ANIMALS_V2_CANONICAL_SLUGS) == ANIMALS_V2_EXPECTED_L2_COUNT == 15
    assert ANIMALS_VET_SERVICES_SLUG in ANIMALS_V2_RETIRED_SLUGS
    assert ANIMALS_VET_SERVICES_SLUG not in ANIMALS_V2_CANONICAL_SLUGS


def test_animals_search_filters_cover_all_canonical_l2() -> None:
    filters = build_animals_v2_search_filters()
    assert set(filters) == ANIMALS_V2_CANONICAL_SLUGS
    assert len(filters) == 15


def test_animals_search_eav_keys_are_short_allowlist() -> None:
    assert ANIMALS_V2_SEARCH_EAV_KEYS <= ANIMALS_V2_SEARCH_ALLOWLIST
    assert ANIMALS_KIND_KEY in ANIMALS_V2_SEARCH_EAV_KEYS
    assert ANIMALS_SELLER_KEY in ANIMALS_V2_SEARCH_EAV_KEYS
    assert ANIMALS_GENDER_KEY in ANIMALS_V2_SEARCH_EAV_KEYS
    assert ANIMALS_CONDITION_KEY in ANIMALS_V2_SEARCH_EAV_KEYS
    assert "price" not in ANIMALS_V2_SEARCH_EAV_KEYS
    assert "age" not in ANIMALS_V2_SEARCH_EAV_KEYS
    assert "breed" not in ANIMALS_V2_SEARCH_EAV_KEYS
    assert "region" not in ANIMALS_V2_SEARCH_EAV_KEYS


def test_animals_search_filters_no_forbidden_or_create_only() -> None:
    for slug, rows in build_animals_v2_search_filters().items():
        keys = {r[0] for r in rows}
        assert keys <= ANIMALS_V2_SEARCH_EAV_KEYS, slug
        assert ANIMALS_KIND_KEY in keys
        assert ANIMALS_SELLER_KEY in keys
        assert keys.isdisjoint(_FORBIDDEN_SEARCH), slug
        assert keys.isdisjoint(ANIMALS_V2_SEARCH_EXCLUDE & _FORBIDDEN_SEARCH), slug
        assert keys.isdisjoint(ANIMALS_CREATE_FORBIDDEN), slug
        assert "age" not in keys and "breed" not in keys


def test_animals_search_seller_independent_contract() -> None:
    assert ANIMALS_SELLER_CHOICES == _INDEPENDENT_SELLER
    for slug, rows in build_animals_v2_search_filters().items():
        opts = _options_for(rows, ANIMALS_SELLER_KEY)
        labels = tuple(o.get("label") or o.get("value") for o in opts)
        assert labels == _INDEPENDENT_SELLER, slug


def test_animals_search_kind_options_match_create_per_l2() -> None:
    cores = build_animals_v2_core_fields()
    filters = build_animals_v2_search_filters()
    for slug in ANIMALS_V2_CANONICAL_SLUGS:
        create_kinds = {
            c["value"]
            for c in next(r for r in cores[slug] if r[0] == ANIMALS_KIND_KEY)[5][
                "choices"
            ]
        }
        search_kinds = {
            o["value"] for o in _options_for(filters[slug], ANIMALS_KIND_KEY)
        }
        assert search_kinds == create_kinds
        assert len(search_kinds) > 0
        assert set(animals_v2_section_kinds(slug)) == create_kinds


def test_animals_search_sex_depends_on_independent_allowlist() -> None:
    assert ANIMALS_GENDER_CHOICES == _INDEPENDENT_SEX
    filters = build_animals_v2_search_filters()
    for slug, rows in filters.items():
        keys = {r[0] for r in rows}
        section_kinds = set(animals_v2_section_kinds(slug))
        sex_in_section = section_kinds & _INDEPENDENT_SEX_YES
        if not sex_in_section:
            assert ANIMALS_GENDER_KEY not in keys, slug
            continue
        assert ANIMALS_GENDER_KEY in keys, slug
        opts = _options_for(rows, ANIMALS_GENDER_KEY)
        labels = tuple(o.get("label") or o.get("value") for o in opts)
        assert labels == _INDEPENDENT_SEX, slug
        dep = _depends_values(rows, ANIMALS_GENDER_KEY)
        if dep is None:
            assert sex_in_section == section_kinds
        else:
            assert dep == sex_in_section


def test_animals_search_condition_depends_on_independent_allowlist() -> None:
    assert ANIMALS_CONDITION_CHOICES == _INDEPENDENT_CONDITION
    filters = build_animals_v2_search_filters()
    for slug, rows in filters.items():
        keys = {r[0] for r in rows}
        section_kinds = set(animals_v2_section_kinds(slug))
        cond_in_section = section_kinds & _INDEPENDENT_CONDITION_YES
        if not cond_in_section:
            assert ANIMALS_CONDITION_KEY not in keys, slug
            continue
        assert ANIMALS_CONDITION_KEY in keys, slug
        opts = _options_for(rows, ANIMALS_CONDITION_KEY)
        labels = tuple(o.get("label") or o.get("value") for o in opts)
        assert labels == _INDEPENDENT_CONDITION, slug
        dep = _depends_values(rows, ANIMALS_CONDITION_KEY)
        if dep is None:
            assert cond_in_section == section_kinds
        else:
            assert dep == cond_in_section


def test_animals_all_kind_search_audit() -> None:
    audit = animals_v2_all_search_kind_audit()
    assert len(audit) == animals_v2_kind_count()
    for row in audit:
        assert row["search_animals_kind"] == "YES"
        assert row["search_seller"] == "YES"
        assert row["search_geo"] == "YES"
        assert row["search_age"] == "NO"
        assert row["search_breed"] == "NO"
        assert row["search_weight"] == "NO"
        assert row["search_color"] == "NO"
        assert row["search_documents"] == "NO"
        assert row["search_vaccination"] == "NO"
        assert row["search_price"] == "NO"
        assert row["search_price_basis"] == "NO"
        assert row["search_negotiable"] == "NO"
        assert row["search_contacts"] == "NO"
        assert row["retired_resurrected"] is False
        assert row["ownership"] == "animals"
        expected_sex = "YES" if row["kind"] in _INDEPENDENT_SEX_YES else "NO"
        expected_cond = (
            "YES" if row["kind"] in _INDEPENDENT_CONDITION_YES else "NO"
        )
        assert row["search_sex"] == expected_sex, row["kind"]
        assert row["search_condition"] == expected_cond, row["kind"]
        assert ANIMALS_KIND_KEY in row["visible_search_keys"]
        assert ANIMALS_SELLER_KEY in row["visible_search_keys"]
        if expected_sex == "YES":
            assert ANIMALS_GENDER_KEY in row["visible_search_keys"]
        else:
            assert ANIMALS_GENDER_KEY not in row["visible_search_keys"]
        if expected_cond == "YES":
            assert ANIMALS_CONDITION_KEY in row["visible_search_keys"]
        else:
            assert ANIMALS_CONDITION_KEY not in row["visible_search_keys"]


def test_animals_search_filter_type_multi_select() -> None:
    for slug, rows in build_animals_v2_search_filters().items():
        for key, label, ftype, sort, cfg in rows:
            assert ftype == CategoryFilterType.multi_select, (slug, key)
            assert cfg and (cfg.get("options") or cfg.get("choices"))


def test_animals_no_honey_or_saddle_in_search_kinds() -> None:
    banned = {"Мёд", "Соты", "Яйца", "Сёдла", "Молоко"}
    for slug, rows in build_animals_v2_search_filters().items():
        kinds = {o["value"] for o in _options_for(rows, ANIMALS_KIND_KEY)}
        assert kinds.isdisjoint(banned), slug


@pytest.mark.asyncio
async def test_animals_search_filters_in_db_and_intelligence(client) -> None:
    await engine.dispose()
    expected = build_animals_v2_search_filters()
    async with async_session_maker() as session:
        for slug in sorted(ANIMALS_V2_RETIRED_SLUGS):
            row = (
                await session.execute(select(Category).where(Category.slug == slug))
            ).scalar_one_or_none()
            if row is None:
                continue
            assert row.is_active is False
            leftover = (
                await session.execute(
                    select(CategoryFilter).where(CategoryFilter.category_id == row.id)
                )
            ).scalars().all()
            assert leftover == [], slug

        for slug in sorted(ANIMALS_V2_CANONICAL_SLUGS):
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
            assert "age" not in {r.filter_key for r in rows}
            assert "breed" not in {r.filter_key for r in rows}

    async with async_session_maker() as session:
        for slug in _REPR_SLUGS:
            cat = (
                await session.execute(select(Category).where(Category.slug == slug))
            ).scalar_one()
            resp = await client.get(f"/api/v1/categories/intelligence/{cat.id}")
            assert resp.status_code == 200, slug
            body = resp.json()
            keys = {f["filter_key"] for f in body.get("filters") or []}
            assert ANIMALS_KIND_KEY in keys
            assert ANIMALS_SELLER_KEY in keys
            assert "age" not in keys and "breed" not in keys
            seller = next(
                f for f in body["filters"] if f["filter_key"] == ANIMALS_SELLER_KEY
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
            # Create cores still present (Package A).
            core_keys = {f["field_key"] for f in body.get("core_fields") or []}
            assert ANIMALS_KIND_KEY in core_keys
            assert "price" in core_keys
            assert "age" not in core_keys and "breed" not in core_keys


@pytest.mark.asyncio
async def test_animals_search_engine_semantic_classes_orm_fixtures(client) -> None:
    """SEARCH_ENGINE_TEST — ORM-injected EAV (not Create↔Search product parity).

    Proves Backend Search filtering semantics for Animals classes A–G.
    Does NOT cross Flutter/production Create persistence boundary.
    """
    await engine.dispose()
    created_ids: list[int] = []
    try:
        async with async_session_maker() as session:
            owner = (
                await session.execute(select(User).order_by(User.id).limit(1))
            ).scalar_one()

            async def _cat(slug: str) -> Category:
                return (
                    await session.execute(select(Category).where(Category.slug == slug))
                ).scalar_one()

            dogs = await _cat("animals-sobaki")
            sheep = await _cat("animals-ovtsy-barany-i-kozy")
            feed = await _cat("animals-seno-korma-i-kormovye-dobavki")
            accessories = await _cat("animals-tovary-aksessuary-dlya-zhivotnyh")
            vet = await _cat("animals-vetapteka-i-veterinarnye-tovary")
            cattle = await _cat("animals-korovy-byki-i-telyata")
            fish = await _cat("animals-ryby-i-akvariumistika")

            async def _add(
                *,
                category_id: int,
                title: str,
                city: str,
                fields: dict[str, str],
                description: str | None = None,
            ) -> None:
                listing = Listing(
                    title=title,
                    description=description or title,
                    price=Decimal("1000"),
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

            # A. Dog — Sex YES
            await _add(
                category_id=dogs.id,
                title="PKG-B animals dog male",
                city="Бишкек",
                description="Хаски, 2 года",
                fields={
                    ANIMALS_KIND_KEY: "Собаки",
                    ANIMALS_SELLER_KEY: "Частное лицо",
                    ANIMALS_GENDER_KEY: "Самец",
                },
            )
            await _add(
                category_id=dogs.id,
                title="PKG-B animals dog female",
                city="Бишкек",
                fields={
                    ANIMALS_KIND_KEY: "Собаки",
                    ANIMALS_SELLER_KEY: "Частное лицо",
                    ANIMALS_GENDER_KEY: "Самка",
                },
            )
            # B. Sex-encoded livestock — NO Sex filter usage
            await _add(
                category_id=sheep.id,
                title="PKG-B animals rams",
                city="Бишкек",
                fields={
                    ANIMALS_KIND_KEY: "Бараны",
                    ANIMALS_SELLER_KEY: "Хозяйство",
                },
            )
            # C. Feed — NO Condition
            await _add(
                category_id=feed.id,
                title="PKG-B animals hay",
                city="Бишкек",
                fields={
                    ANIMALS_KIND_KEY: "Сено",
                    ANIMALS_SELLER_KEY: "Хозяйство",
                },
            )
            # D. Durable accessory — Condition YES
            await _add(
                category_id=accessories.id,
                title="PKG-B animals collar new",
                city="Бишкек",
                fields={
                    ANIMALS_KIND_KEY: "Ошейники",
                    ANIMALS_SELLER_KEY: "Магазин",
                    ANIMALS_CONDITION_KEY: "Новое",
                },
            )
            await _add(
                category_id=accessories.id,
                title="PKG-B animals collar used",
                city="Бишкек",
                fields={
                    ANIMALS_KIND_KEY: "Ошейники",
                    ANIMALS_SELLER_KEY: "Магазин",
                    ANIMALS_CONDITION_KEY: "Б/у",
                },
            )
            # E. Vet consumable — NO Condition
            await _add(
                category_id=vet.id,
                title="PKG-B animals vitamins",
                city="Бишкек",
                fields={
                    ANIMALS_KIND_KEY: "Витамины для животных",
                    ANIMALS_SELLER_KEY: "Магазин",
                },
            )
            # F. Ordinary live livestock — seller + geo
            await _add(
                category_id=cattle.id,
                title="PKG-B animals cows bishkek",
                city="Бишкек",
                fields={
                    ANIMALS_KIND_KEY: "Коровы",
                    ANIMALS_SELLER_KEY: "Хозяйство",
                },
            )
            await _add(
                category_id=cattle.id,
                title="PKG-B animals cows osh",
                city="Ош",
                fields={
                    ANIMALS_KIND_KEY: "Коровы",
                    ANIMALS_SELLER_KEY: "Хозяйство",
                },
            )
            # G. Aquarium durable — Condition YES
            await _add(
                category_id=fish.id,
                title="PKG-B animals aquarium new",
                city="Бишкек",
                fields={
                    ANIMALS_KIND_KEY: "Аквариумы",
                    ANIMALS_SELLER_KEY: "Магазин",
                    ANIMALS_CONDITION_KEY: "Новое",
                },
            )
            await session.commit()
            dogs_id = dogs.id
            sheep_id = sheep.id
            feed_id = feed.id
            accessories_id = accessories.id
            vet_id = vet.id
            cattle_id = cattle.id
            fish_id = fish.id

        # A. Sex filter FOUND / NOT FOUND
        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": dogs_id,
                "attrs": json.dumps(
                    {
                        ANIMALS_KIND_KEY: "Собаки",
                        ANIMALS_GENDER_KEY: "Самец",
                    }
                ),
                "city": "Бишкек",
                "limit": 40,
            },
        )
        assert resp.status_code == 200
        titles = {i["title"] for i in resp.json()["items"]}
        assert "PKG-B animals dog male" in titles
        assert "PKG-B animals dog female" not in titles

        # Breed/Age in description must not block kind/seller/geo find
        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": dogs_id,
                "attrs": json.dumps(
                    {
                        ANIMALS_KIND_KEY: "Собаки",
                        ANIMALS_SELLER_KEY: "Частное лицо",
                    }
                ),
                "city": "Бишкек",
                "limit": 40,
            },
        )
        assert resp.status_code == 200
        titles = {i["title"] for i in resp.json()["items"]}
        assert "PKG-B animals dog male" in titles

        # B. Sex-encoded kind FOUND without gender
        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": sheep_id,
                "attrs": json.dumps({ANIMALS_KIND_KEY: "Бараны"}),
                "limit": 40,
            },
        )
        assert resp.status_code == 200
        titles = {i["title"] for i in resp.json()["items"]}
        assert "PKG-B animals rams" in titles

        # C. Feed FOUND; wrong condition attr must not be required
        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": feed_id,
                "attrs": json.dumps({ANIMALS_KIND_KEY: "Сено"}),
                "limit": 40,
            },
        )
        assert resp.status_code == 200
        titles = {i["title"] for i in resp.json()["items"]}
        assert "PKG-B animals hay" in titles

        # D. Condition FOUND / NOT FOUND
        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": accessories_id,
                "attrs": json.dumps(
                    {
                        ANIMALS_KIND_KEY: "Ошейники",
                        ANIMALS_CONDITION_KEY: "Новое",
                    }
                ),
                "limit": 40,
            },
        )
        assert resp.status_code == 200
        titles = {i["title"] for i in resp.json()["items"]}
        assert "PKG-B animals collar new" in titles
        assert "PKG-B animals collar used" not in titles

        # E. Vet consumable FOUND without condition
        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": vet_id,
                "attrs": json.dumps(
                    {ANIMALS_KIND_KEY: "Витамины для животных"}
                ),
                "limit": 40,
            },
        )
        assert resp.status_code == 200
        titles = {i["title"] for i in resp.json()["items"]}
        assert "PKG-B animals vitamins" in titles

        # F. Geo + seller
        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": cattle_id,
                "attrs": json.dumps(
                    {
                        ANIMALS_KIND_KEY: "Коровы",
                        ANIMALS_SELLER_KEY: "Хозяйство",
                    }
                ),
                "city": "Бишкек",
                "limit": 40,
            },
        )
        assert resp.status_code == 200
        titles = {i["title"] for i in resp.json()["items"]}
        assert "PKG-B animals cows bishkek" in titles
        assert "PKG-B animals cows osh" not in titles

        # G. Aquarium durable condition
        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": fish_id,
                "attrs": json.dumps(
                    {
                        ANIMALS_KIND_KEY: "Аквариумы",
                        ANIMALS_CONDITION_KEY: "Новое",
                    }
                ),
                "limit": 40,
            },
        )
        assert resp.status_code == 200
        titles = {i["title"] for i in resp.json()["items"]}
        assert "PKG-B animals aquarium new" in titles

        # Facet self-exclusion on dogs kind
        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": dogs_id,
                "attrs": json.dumps({ANIMALS_KIND_KEY: "Собаки"}),
                "facets": (
                    f"{ANIMALS_KIND_KEY},{ANIMALS_GENDER_KEY},"
                    f"{ANIMALS_SELLER_KEY}"
                ),
                "limit": 1,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 2
        facets = body.get("facets") or {}
        kind_facet = {
            str(i["value"]): int(i["count"])
            for i in facets.get(ANIMALS_KIND_KEY) or []
        }
        gender_facet = {
            str(i["value"]): int(i["count"])
            for i in facets.get(ANIMALS_GENDER_KEY) or []
        }
        assert kind_facet.get("Собаки", 0) >= 2
        assert gender_facet.get("Самец", 0) >= 1
        assert gender_facet.get("Самка", 0) >= 1
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
