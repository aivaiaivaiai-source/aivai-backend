"""Stationery V2 Package B — Search SoT + Create↔Search parity."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select, text

from app.api.deps import get_current_user
from app.db.session import async_session_maker, engine
from app.main import app
from app.models.category import Category
from app.models.category_enums import CategoryFilterType
from app.models.category_filter import CategoryFilter
from app.models.listing import Listing
from app.models.listing_field_value import ListingFieldValue
from app.models.user import User
from app.schemas.user import UserRead
from app.seeds.stationery_v2 import (
    STATIONERY_CONDITION_CHOICES,
    STATIONERY_CONDITION_KEY,
    STATIONERY_CREATE_FORBIDDEN,
    STATIONERY_GRADE_KEY,
    STATIONERY_KIND_KEY,
    STATIONERY_SCHOOL_GRADE_KINDS,
    STATIONERY_SCHOOL_GRADE_OPTIONS,
    STATIONERY_SELLER_KEY,
    STATIONERY_SELLER_TARGET,
    STATIONERY_V2_CANONICAL_SLUGS,
    STATIONERY_V2_EXPECTED_L2_COUNT,
    STATIONERY_V2_RETIRED_SLUGS,
    STATIONERY_V2_SEARCH_ALLOWLIST,
    STATIONERY_V2_SEARCH_EAV_KEYS,
    STATIONERY_V2_SEARCH_EXCLUDE,
    build_stationery_v2_core_fields,
    build_stationery_v2_search_filters,
    stationery_v2_all_search_kind_audit,
    stationery_v2_assert_package_a_contracts,
    stationery_v2_condition_yes_kinds,
    stationery_v2_kind_count,
    stationery_v2_section_kinds,
)

_INDEPENDENT_SELLER = ("Частное лицо", "Магазин", "Другой")
_INDEPENDENT_CONDITION = ("Новое", "Б/у")
_INDEPENDENT_CONDITION_YES = frozenset(stationery_v2_condition_yes_kinds())
_INDEPENDENT_GRADE_YES = frozenset(STATIONERY_SCHOOL_GRADE_KINDS)
_FORBIDDEN_SEARCH = frozenset(
    {
        "price",
        "negotiable",
        "contact_methods",
        "language",
        "author",
        "publisher",
        "isbn",
        "year",
        "brand",
        "color",
        "material",
        "size",
        "paper_format",
        "quantity",
        "item_type",
        "currency",
    }
)
_REPR_SLUGS = (
    "stationery-books-kantselyarskie-tovary",
    "stationery-books-uchebniki-i-uchebnye-posobiya",
    "stationery-books-hudozhestvennaya-literatura",
    "stationery-books-elektronnye-knigi",
    "stationery-books-tovary-dlya-ofisa",
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


def test_stationery_package_a_still_locked() -> None:
    stationery_v2_assert_package_a_contracts()
    assert len(STATIONERY_V2_CANONICAL_SLUGS) == STATIONERY_V2_EXPECTED_L2_COUNT == 15
    assert "books-fiction" in STATIONERY_V2_RETIRED_SLUGS
    assert "books-study" in STATIONERY_V2_RETIRED_SLUGS
    cores = build_stationery_v2_core_fields()
    assert len(cores) == 15
    for slug, fields in cores.items():
        keys = {r[0] for r in fields}
        assert STATIONERY_KIND_KEY in keys
        assert "price" in keys
        assert "language" not in keys


def test_stationery_search_filters_cover_all_canonical_l2() -> None:
    filters = build_stationery_v2_search_filters()
    assert set(filters) == STATIONERY_V2_CANONICAL_SLUGS
    assert len(filters) == 15


def test_stationery_search_eav_keys_are_short_allowlist() -> None:
    assert STATIONERY_V2_SEARCH_EAV_KEYS <= STATIONERY_V2_SEARCH_ALLOWLIST
    assert STATIONERY_KIND_KEY in STATIONERY_V2_SEARCH_EAV_KEYS
    assert STATIONERY_SELLER_KEY in STATIONERY_V2_SEARCH_EAV_KEYS
    assert STATIONERY_CONDITION_KEY in STATIONERY_V2_SEARCH_EAV_KEYS
    assert STATIONERY_GRADE_KEY in STATIONERY_V2_SEARCH_EAV_KEYS
    assert "price" not in STATIONERY_V2_SEARCH_EAV_KEYS
    assert "language" not in STATIONERY_V2_SEARCH_EAV_KEYS
    assert "region" not in STATIONERY_V2_SEARCH_EAV_KEYS


def test_stationery_search_filters_no_forbidden() -> None:
    for slug, rows in build_stationery_v2_search_filters().items():
        keys = {r[0] for r in rows}
        assert keys <= STATIONERY_V2_SEARCH_EAV_KEYS, slug
        assert STATIONERY_KIND_KEY in keys
        assert STATIONERY_SELLER_KEY in keys
        assert keys.isdisjoint(_FORBIDDEN_SEARCH), slug
        assert keys.isdisjoint(STATIONERY_CREATE_FORBIDDEN), slug
        assert keys.isdisjoint(STATIONERY_V2_SEARCH_EXCLUDE & _FORBIDDEN_SEARCH), slug


def test_stationery_search_seller_independent_contract() -> None:
    assert STATIONERY_SELLER_TARGET == _INDEPENDENT_SELLER
    for slug, rows in build_stationery_v2_search_filters().items():
        opts = _options_for(rows, STATIONERY_SELLER_KEY)
        labels = tuple(o.get("label") or o.get("value") for o in opts)
        assert labels == _INDEPENDENT_SELLER, slug


def test_stationery_search_kind_options_match_create_per_l2() -> None:
    cores = build_stationery_v2_core_fields()
    filters = build_stationery_v2_search_filters()
    for slug in STATIONERY_V2_CANONICAL_SLUGS:
        create_kinds = {
            c["value"]
            for c in next(r for r in cores[slug] if r[0] == STATIONERY_KIND_KEY)[5][
                "choices"
            ]
        }
        search_kinds = {
            o["value"] for o in _options_for(filters[slug], STATIONERY_KIND_KEY)
        }
        assert search_kinds == create_kinds
        assert len(search_kinds) > 0
        assert set(stationery_v2_section_kinds(slug)) == create_kinds


def test_stationery_search_condition_depends_on_independent_allowlist() -> None:
    assert STATIONERY_CONDITION_CHOICES == _INDEPENDENT_CONDITION
    assert len(_INDEPENDENT_CONDITION_YES) == 72
    filters = build_stationery_v2_search_filters()
    for slug, rows in filters.items():
        keys = {r[0] for r in rows}
        section_kinds = set(stationery_v2_section_kinds(slug))
        cond_in_section = section_kinds & _INDEPENDENT_CONDITION_YES
        if not cond_in_section:
            assert STATIONERY_CONDITION_KEY not in keys, slug
            continue
        assert STATIONERY_CONDITION_KEY in keys, slug
        opts = _options_for(rows, STATIONERY_CONDITION_KEY)
        labels = tuple(o.get("label") or o.get("value") for o in opts)
        assert labels == _INDEPENDENT_CONDITION, slug
        dep = _depends_values(rows, STATIONERY_CONDITION_KEY)
        if dep is None:
            assert cond_in_section == section_kinds
        else:
            assert dep == cond_in_section


def test_stationery_search_grade_depends_on_independent_allowlist() -> None:
    assert len(_INDEPENDENT_GRADE_YES) == 15
    assert STATIONERY_SCHOOL_GRADE_OPTIONS[0] == "1 класс"
    filters = build_stationery_v2_search_filters()
    for slug, rows in filters.items():
        keys = {r[0] for r in rows}
        section_kinds = set(stationery_v2_section_kinds(slug))
        grade_in_section = section_kinds & _INDEPENDENT_GRADE_YES
        if not grade_in_section:
            assert STATIONERY_GRADE_KEY not in keys, slug
            continue
        assert STATIONERY_GRADE_KEY in keys, slug
        opts = _options_for(rows, STATIONERY_GRADE_KEY)
        labels = tuple(o.get("label") or o.get("value") for o in opts)
        assert labels == STATIONERY_SCHOOL_GRADE_OPTIONS, slug
        dep = _depends_values(rows, STATIONERY_GRADE_KEY)
        assert dep == grade_in_section


def test_stationery_all_kind_search_audit() -> None:
    audit = stationery_v2_all_search_kind_audit()
    assert len(audit) == stationery_v2_kind_count() == 105
    for row in audit:
        assert row["search_stationery_kind"] == "YES"
        assert row["search_seller"] == "YES"
        assert row["search_geo"] == "YES"
        assert row["search_language"] == "NO"
        assert row["search_author"] == "NO"
        assert row["search_price"] == "NO"
        assert row["search_negotiable"] == "NO"
        assert row["search_contacts"] == "NO"
        assert row["retired_resurrected"] is False
        assert row["ownership"] == "stationery"
        expected_cond = (
            "YES" if row["kind"] in _INDEPENDENT_CONDITION_YES else "NO"
        )
        expected_grade = "YES" if row["kind"] in _INDEPENDENT_GRADE_YES else "NO"
        assert row["search_condition"] == expected_cond, row["kind"]
        assert row["search_grade"] == expected_grade, row["kind"]
        if expected_cond == "YES":
            assert STATIONERY_CONDITION_KEY in row["visible_search_keys"]
        else:
            assert STATIONERY_CONDITION_KEY not in row["visible_search_keys"]
        if expected_grade == "YES":
            assert STATIONERY_GRADE_KEY in row["visible_search_keys"]
        else:
            assert STATIONERY_GRADE_KEY not in row["visible_search_keys"]
    by_kind = {r["kind"]: r for r in audit}
    assert by_kind["Школьные дневники"]["search_condition"] == "NO"
    assert by_kind["Школьные рюкзаки"]["search_condition"] == "YES"
    assert by_kind["Школьные рюкзаки"]["search_grade"] == "NO"
    assert by_kind["Алгебра"]["search_grade"] == "YES"
    assert by_kind["Подготовка к ОРТ"]["search_grade"] == "NO"


def test_stationery_search_filter_type_multi_select() -> None:
    for slug, rows in build_stationery_v2_search_filters().items():
        for key, label, ftype, sort, cfg in rows:
            assert ftype == CategoryFilterType.multi_select, (slug, key)
            assert cfg and (cfg.get("options") or cfg.get("choices"))


def test_stationery_search_builder_idempotent() -> None:
    a = build_stationery_v2_search_filters()
    b = build_stationery_v2_search_filters()
    assert json.dumps(a, default=str, ensure_ascii=False) == json.dumps(
        b, default=str, ensure_ascii=False
    )


def test_stationery_no_retired_slugs_in_search_map() -> None:
    filters = build_stationery_v2_search_filters()
    assert set(filters).isdisjoint(STATIONERY_V2_RETIRED_SLUGS)


@pytest.mark.asyncio
async def test_stationery_search_filters_in_db_and_intelligence(client) -> None:
    await engine.dispose()
    expected = build_stationery_v2_search_filters()
    async with async_session_maker() as session:
        for slug in sorted(STATIONERY_V2_RETIRED_SLUGS):
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

        for slug in sorted(STATIONERY_V2_CANONICAL_SLUGS):
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
            assert "language" not in {r.filter_key for r in rows}
            assert "price" not in {r.filter_key for r in rows}

    async with async_session_maker() as session:
        for slug in _REPR_SLUGS:
            cat = (
                await session.execute(select(Category).where(Category.slug == slug))
            ).scalar_one()
            resp = await client.get(f"/api/v1/categories/intelligence/{cat.id}")
            assert resp.status_code == 200, slug
            body = resp.json()
            keys = {f["filter_key"] for f in body.get("filters") or []}
            assert STATIONERY_KIND_KEY in keys
            assert STATIONERY_SELLER_KEY in keys
            assert "language" not in keys and "price" not in keys
            core_keys = {f["field_key"] for f in body.get("core_fields") or []}
            assert STATIONERY_KIND_KEY in core_keys
            assert "price" in core_keys


def _auth_as(user_id: int) -> None:
    now = datetime.now(UTC)

    async def _user() -> UserRead:
        return UserRead(
            id=user_id,
            phone="+79001234567",
            full_name="StationerySearchParity",
            is_active=True,
            balance=Decimal("0"),
            last_login=None,
            created_at=now,
            updated_at=now,
        )

    app.dependency_overrides[get_current_user] = _user


async def _attach_photo(session, listing_id: int) -> None:
    await session.execute(
        text(
            """
            INSERT INTO media (
              listing_id, url, "order", is_placeholder,
              lifecycle_status, moderation_status,
              created_at, updated_at
            ) VALUES (
              :lid, '/media/test/stationery-pb.jpg', 0, false,
              'ready', 'approved', now(), now()
            )
            """
        ),
        {"lid": listing_id},
    )
    await session.commit()


async def _cleanup(session, listing_ids: list[int]) -> None:
    if not listing_ids:
        return
    await session.execute(
        text("DELETE FROM media WHERE listing_id = ANY(:ids)"),
        {"ids": listing_ids},
    )
    await session.execute(
        text("DELETE FROM listing_field_values WHERE listing_id = ANY(:ids)"),
        {"ids": listing_ids},
    )
    await session.execute(
        text("DELETE FROM listings WHERE id = ANY(:ids)"),
        {"ids": listing_ids},
    )
    await session.commit()


async def _create_activate(
    client,
    *,
    owner_id: int,
    category_id: int,
    title: str,
    fields: dict[str, str],
) -> int:
    _auth_as(owner_id)
    created = await client.post(
        "/api/v1/listings",
        json={
            "title": title,
            "description": f"{title} package B parity",
            "price": "1200",
            "currency": "KGS",
            "category_id": category_id,
            "status": "draft",
            "fields": fields,
        },
        headers={"Authorization": "Bearer test"},
    )
    assert created.status_code in (200, 201), created.text
    lid = int(created.json()["id"])
    async with async_session_maker() as session:
        await _attach_photo(session, lid)
    act = await client.patch(
        f"/api/v1/listings/{lid}/status",
        json={"status": "active"},
        headers={"Authorization": "Bearer test"},
    )
    assert act.status_code == 200, act.text
    return lid


@pytest.mark.asyncio
async def test_stationery_create_search_parity_cases_a_e(client) -> None:
    """Real Create API → Search FOUND/NOT FOUND for A–E."""
    await engine.dispose()
    created_ids: list[int] = []
    try:
        async with async_session_maker() as session:
            owner = (
                await session.execute(select(User).order_by(User.id).limit(1))
            ).scalar_one()
            owner_id = int(owner.id)

            async def _cid(slug: str) -> int:
                return int(
                    (
                        await session.execute(
                            select(Category).where(Category.slug == slug)
                        )
                    )
                    .scalar_one()
                    .id
                )

            stationery_id = await _cid("stationery-books-kantselyarskie-tovary")
            fiction_id = await _cid(
                "stationery-books-hudozhestvennaya-literatura"
            )
            textbooks_id = await _cid(
                "stationery-books-uchebniki-i-uchebnye-posobiya"
            )

        # A consumable — no Condition
        lid_a = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=stationery_id,
            title="PKG-B stationery pens A",
            fields={
                STATIONERY_KIND_KEY: "Ручки",
                STATIONERY_SELLER_KEY: "Частное лицо",
                "contact_methods": "Только чат",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
        )
        created_ids.append(lid_a)
        found = await client.get(
            "/api/v1/listings",
            params={
                "category_id": stationery_id,
                "attrs": json.dumps(
                    {
                        STATIONERY_KIND_KEY: "Ручки",
                        STATIONERY_SELLER_KEY: "Частное лицо",
                    },
                    ensure_ascii=False,
                ),
                "city": "Бишкек",
                "limit": 40,
            },
        )
        assert found.status_code == 200
        ids = [int(i["id"]) for i in found.json().get("items") or []]
        assert lid_a in ids

        # B book Condition
        lid_b = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=fiction_id,
            title="PKG-B stationery novel B",
            fields={
                STATIONERY_KIND_KEY: "Романы",
                STATIONERY_SELLER_KEY: "Магазин",
                STATIONERY_CONDITION_KEY: "Б/у",
                "contact_methods": "Только чат",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
        )
        created_ids.append(lid_b)
        hit = await client.get(
            "/api/v1/listings",
            params={
                "category_id": fiction_id,
                "attrs": json.dumps(
                    {
                        STATIONERY_KIND_KEY: "Романы",
                        STATIONERY_CONDITION_KEY: "Б/у",
                    },
                    ensure_ascii=False,
                ),
                "limit": 40,
            },
        )
        miss = await client.get(
            "/api/v1/listings",
            params={
                "category_id": fiction_id,
                "attrs": json.dumps(
                    {
                        STATIONERY_KIND_KEY: "Романы",
                        STATIONERY_CONDITION_KEY: "Новое",
                    },
                    ensure_ascii=False,
                ),
                "limit": 40,
            },
        )
        assert lid_b in [int(i["id"]) for i in hit.json().get("items") or []]
        assert lid_b not in [int(i["id"]) for i in miss.json().get("items") or []]

        # C school textbook Grade
        lid_c = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=textbooks_id,
            title="PKG-B stationery algebra C",
            fields={
                STATIONERY_KIND_KEY: "Алгебра",
                STATIONERY_SELLER_KEY: "Частное лицо",
                STATIONERY_CONDITION_KEY: "Б/у",
                STATIONERY_GRADE_KEY: "7 класс",
                "contact_methods": "Только чат",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
        )
        created_ids.append(lid_c)
        hit = await client.get(
            "/api/v1/listings",
            params={
                "category_id": textbooks_id,
                "attrs": json.dumps(
                    {
                        STATIONERY_KIND_KEY: "Алгебра",
                        STATIONERY_GRADE_KEY: "7 класс",
                    },
                    ensure_ascii=False,
                ),
                "limit": 40,
            },
        )
        miss = await client.get(
            "/api/v1/listings",
            params={
                "category_id": textbooks_id,
                "attrs": json.dumps(
                    {
                        STATIONERY_KIND_KEY: "Алгебра",
                        STATIONERY_GRADE_KEY: "8 класс",
                    },
                    ensure_ascii=False,
                ),
                "limit": 40,
            },
        )
        assert lid_c in [int(i["id"]) for i in hit.json().get("items") or []]
        assert lid_c not in [int(i["id"]) for i in miss.json().get("items") or []]

        # D backpack Condition YES, Grade NO
        lid_d = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=stationery_id,
            title="PKG-B stationery backpack D",
            fields={
                STATIONERY_KIND_KEY: "Школьные рюкзаки",
                STATIONERY_SELLER_KEY: "Другой",
                STATIONERY_CONDITION_KEY: "Новое",
                "contact_methods": "Только чат",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
        )
        created_ids.append(lid_d)
        hit = await client.get(
            "/api/v1/listings",
            params={
                "category_id": stationery_id,
                "attrs": json.dumps(
                    {
                        STATIONERY_KIND_KEY: "Школьные рюкзаки",
                        STATIONERY_CONDITION_KEY: "Новое",
                    },
                    ensure_ascii=False,
                ),
                "limit": 40,
            },
        )
        assert lid_d in [int(i["id"]) for i in hit.json().get("items") or []]
        async with async_session_maker() as session:
            eav = {
                r.field_key: r.value_text
                for r in (
                    await session.execute(
                        select(ListingFieldValue).where(
                            ListingFieldValue.listing_id == lid_d
                        )
                    )
                ).scalars()
            }
        assert STATIONERY_GRADE_KEY not in eav

        # E ORT — no Grade in Search filters for that kind
        textbooks_filters = build_stationery_v2_search_filters()[
            "stationery-books-uchebniki-i-uchebnye-posobiya"
        ]
        grade_dep = _depends_values(textbooks_filters, STATIONERY_GRADE_KEY)
        assert grade_dep is not None
        assert "Подготовка к ОРТ" not in grade_dep
        assert "Вузские учебники" not in grade_dep

        lid_e = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=textbooks_id,
            title="PKG-B stationery ort E",
            fields={
                STATIONERY_KIND_KEY: "Подготовка к ОРТ",
                STATIONERY_SELLER_KEY: "Частное лицо",
                STATIONERY_CONDITION_KEY: "Б/у",
                "contact_methods": "Только чат",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
        )
        created_ids.append(lid_e)
        async with async_session_maker() as session:
            eav = {
                r.field_key: r.value_text
                for r in (
                    await session.execute(
                        select(ListingFieldValue).where(
                            ListingFieldValue.listing_id == lid_e
                        )
                    )
                ).scalars()
            }
        assert STATIONERY_GRADE_KEY not in eav
    finally:
        async with async_session_maker() as session:
            await _cleanup(session, created_ids)
            leftover = (
                await session.execute(
                    select(Listing.id).where(
                        Listing.title.like("PKG-B stationery%")
                    )
                )
            ).scalars().all()
            assert list(leftover) == []
