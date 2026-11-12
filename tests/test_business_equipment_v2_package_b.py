"""Business Equipment V2 Package B — Search SoT + Create↔Search parity."""
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
from app.models.category_filter import CategoryFilter
from app.models.listing import Listing
from app.models.user import User
from app.schemas.user import UserRead
from app.seeds.business_equipment_v2 import (
    BUSINESS_CONDITION_KEY,
    BUSINESS_EQUIPMENT_CREATE_FORBIDDEN,
    BUSINESS_EQUIPMENT_SELLER_TARGET,
    BUSINESS_EQUIPMENT_V2_CANONICAL_SLUGS,
    BUSINESS_EQUIPMENT_V2_EXPECTED_L2_COUNT,
    BUSINESS_EQUIPMENT_V2_RETIRED_SLUGS,
    BUSINESS_EQUIPMENT_V2_SEARCH_ALLOWLIST,
    BUSINESS_EQUIPMENT_V2_SEARCH_EAV_KEYS,
    BUSINESS_EQUIPMENT_V2_SEARCH_EXCLUDE,
    BUSINESS_KIND_KEY,
    BUSINESS_SELLER_KEY,
    PLOTTER_KIND,
    STO_COMPRESSOR_KIND,
    build_business_equipment_v2_core_fields,
    build_business_equipment_v2_search_filters,
    business_equipment_v2_all_search_kind_audit,
    business_equipment_v2_assert_package_a_contracts,
    business_equipment_v2_condition_no_kinds,
    business_equipment_v2_condition_yes_kinds,
    business_equipment_v2_section_kinds,
)

_INDEPENDENT_SELLER = ("Частное лицо", "Магазин", "Другой")
_INDEPENDENT_CONDITION = ("Новое", "Б/у")
_INDEPENDENT_CONDITION_YES = frozenset(business_equipment_v2_condition_yes_kinds())
_INDEPENDENT_CONDITION_NO = frozenset(business_equipment_v2_condition_no_kinds())
_FORBIDDEN_SEARCH = frozenset(
    {
        "price",
        "negotiable",
        "contact_methods",
        "brand",
        "model",
        "power",
        "voltage",
        "capacity",
        "year",
        "warranty",
        "currency",
    }
)
_REPR_SLUGS = (
    "business-equipment-torgovoe-oborudovanie",
    "business-equipment-zapchasti-i-komplektuyuschie",
    "business-equipment-poligraficheskoe-oborudovanie",
    "business-equipment-oborudovanie-dlya-avtomoek-i-sto",
)
FORENSIC_LISTING_ID = 2911


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


def test_business_package_a_still_locked() -> None:
    business_equipment_v2_assert_package_a_contracts()
    assert (
        len(BUSINESS_EQUIPMENT_V2_CANONICAL_SLUGS)
        == BUSINESS_EQUIPMENT_V2_EXPECTED_L2_COUNT
        == 20
    )
    assert "business-equipment-cafe" in BUSINESS_EQUIPMENT_V2_RETIRED_SLUGS
    cores = build_business_equipment_v2_core_fields()
    assert len(cores) == 20
    for slug, fields in cores.items():
        keys = {r[0] for r in fields}
        assert BUSINESS_KIND_KEY in keys
        assert "price" in keys
        assert "brand" not in keys


def test_business_search_filters_cover_all_canonical_l2() -> None:
    filters = build_business_equipment_v2_search_filters()
    assert set(filters) == BUSINESS_EQUIPMENT_V2_CANONICAL_SLUGS
    assert len(filters) == 20


def test_business_search_eav_keys_are_short_allowlist() -> None:
    assert BUSINESS_EQUIPMENT_V2_SEARCH_EAV_KEYS <= BUSINESS_EQUIPMENT_V2_SEARCH_ALLOWLIST
    assert BUSINESS_KIND_KEY in BUSINESS_EQUIPMENT_V2_SEARCH_EAV_KEYS
    assert BUSINESS_SELLER_KEY in BUSINESS_EQUIPMENT_V2_SEARCH_EAV_KEYS
    assert BUSINESS_CONDITION_KEY in BUSINESS_EQUIPMENT_V2_SEARCH_EAV_KEYS
    assert "price" not in BUSINESS_EQUIPMENT_V2_SEARCH_EAV_KEYS
    assert "region" not in BUSINESS_EQUIPMENT_V2_SEARCH_EAV_KEYS


def test_business_search_filters_no_forbidden() -> None:
    for slug, rows in build_business_equipment_v2_search_filters().items():
        keys = {r[0] for r in rows}
        assert keys <= BUSINESS_EQUIPMENT_V2_SEARCH_EAV_KEYS, slug
        assert BUSINESS_KIND_KEY in keys
        assert BUSINESS_SELLER_KEY in keys
        assert keys.isdisjoint(_FORBIDDEN_SEARCH), slug
        assert keys.isdisjoint(BUSINESS_EQUIPMENT_CREATE_FORBIDDEN), slug


def test_business_search_seller_independent_contract() -> None:
    assert BUSINESS_EQUIPMENT_SELLER_TARGET == _INDEPENDENT_SELLER
    for slug, rows in build_business_equipment_v2_search_filters().items():
        opts = _options_for(rows, BUSINESS_SELLER_KEY)
        labels = tuple(o.get("label") or o.get("value") for o in opts)
        assert labels == _INDEPENDENT_SELLER, slug


def test_business_search_kind_options_match_create_per_l2() -> None:
    cores = build_business_equipment_v2_core_fields()
    filters = build_business_equipment_v2_search_filters()
    for slug in BUSINESS_EQUIPMENT_V2_CANONICAL_SLUGS:
        create_kinds = {
            c["value"]
            for c in next(r for r in cores[slug] if r[0] == BUSINESS_KIND_KEY)[5][
                "choices"
            ]
        }
        search_kinds = {
            o["value"] for o in _options_for(filters[slug], BUSINESS_KIND_KEY)
        }
        assert search_kinds == create_kinds
        assert len(search_kinds) > 0
        assert set(business_equipment_v2_section_kinds(slug)) == create_kinds


def test_business_search_condition_depends_on_independent_allowlist() -> None:
    assert len(_INDEPENDENT_CONDITION_YES) == 172
    assert len(_INDEPENDENT_CONDITION_NO) == 4
    assert _INDEPENDENT_CONDITION_NO == {
        "Ценникодержатели",
        "Крючки для торгового оборудования",
        "Подставки для украшений",
        "Иглы промышленные",
    }
    filters = build_business_equipment_v2_search_filters()
    for slug, rows in filters.items():
        keys = {r[0] for r in rows}
        section_kinds = set(business_equipment_v2_section_kinds(slug))
        cond_in_section = section_kinds & _INDEPENDENT_CONDITION_YES
        if not cond_in_section:
            assert BUSINESS_CONDITION_KEY not in keys, slug
            continue
        assert BUSINESS_CONDITION_KEY in keys, slug
        opts = _options_for(rows, BUSINESS_CONDITION_KEY)
        labels = tuple(o.get("label") or o.get("value") for o in opts)
        assert labels == _INDEPENDENT_CONDITION, slug
        dep = _depends_values(rows, BUSINESS_CONDITION_KEY)
        if dep is None:
            assert cond_in_section == section_kinds
        else:
            assert dep == cond_in_section
            assert dep.isdisjoint(_INDEPENDENT_CONDITION_NO)


def test_business_all_176_search_audit() -> None:
    rows = business_equipment_v2_all_search_kind_audit()
    assert len(rows) == 176
    for row in rows:
        assert row["search_business_kind"] == "YES"
        assert row["search_seller"] == "YES"
        assert row["search_geo"] == "YES"
        assert row["search_brand"] == "NO"
        assert row["search_model"] == "NO"
        assert row["search_price"] == "NO"
        assert row["retired_resurrected"] is False
        if row["kind"] in _INDEPENDENT_CONDITION_NO:
            assert row["search_condition"] == "NO"
            assert BUSINESS_CONDITION_KEY not in row["visible_search_keys"]
        else:
            assert row["search_condition"] == "YES"
            assert BUSINESS_CONDITION_KEY in row["visible_search_keys"]
        assert row["ownership"] == "BUSINESS_EQUIPMENT"


def test_business_search_builder_idempotent() -> None:
    a = build_business_equipment_v2_search_filters()
    b = build_business_equipment_v2_search_filters()
    assert json.dumps(a, default=str, ensure_ascii=False) == json.dumps(
        b, default=str, ensure_ascii=False
    )


def test_business_no_retired_slugs_in_search_map() -> None:
    filters = build_business_equipment_v2_search_filters()
    assert set(filters).isdisjoint(BUSINESS_EQUIPMENT_V2_RETIRED_SLUGS)


@pytest.mark.asyncio
async def test_business_search_filters_in_db_and_intelligence(client) -> None:
    await engine.dispose()
    expected = build_business_equipment_v2_search_filters()
    async with async_session_maker() as session:
        for slug in sorted(BUSINESS_EQUIPMENT_V2_RETIRED_SLUGS):
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

        for slug in sorted(BUSINESS_EQUIPMENT_V2_CANONICAL_SLUGS):
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
            assert "brand" not in {r.filter_key for r in rows}
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
            assert BUSINESS_KIND_KEY in keys
            assert BUSINESS_SELLER_KEY in keys
            assert "brand" not in keys and "price" not in keys
            core_keys = {f["field_key"] for f in body.get("core_fields") or []}
            assert BUSINESS_KIND_KEY in core_keys
            assert "price" in core_keys


def _auth_as(user_id: int) -> None:
    now = datetime.now(UTC)

    async def _user() -> UserRead:
        return UserRead(
            id=user_id,
            phone="+79001234567",
            full_name="BusinessSearchParity",
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
              :lid, '/media/test/business-pb.jpg', 0, false,
              'ready', 'approved', now(), now()
            )
            """
        ),
        {"lid": listing_id},
    )
    await session.commit()


async def _cleanup(session, listing_ids: list[int]) -> None:
    ids = [i for i in listing_ids if i != FORENSIC_LISTING_ID]
    if not ids:
        return
    await session.execute(
        text("DELETE FROM media WHERE listing_id = ANY(:ids)"),
        {"ids": ids},
    )
    await session.execute(
        text("DELETE FROM listing_field_values WHERE listing_id = ANY(:ids)"),
        {"ids": ids},
    )
    await session.execute(
        text("DELETE FROM listings WHERE id = ANY(:ids)"),
        {"ids": ids},
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
            "price": "15000",
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
async def test_business_create_search_parity_cases_a_d_and_2911(client) -> None:
    """Real Create API → Search FOUND/NOT FOUND + forensic 2911 boundary."""
    await engine.dispose()
    created_ids: list[int] = []
    forensic_existed = False
    forensic_eav_before: dict[str, str] = {}
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

            trade_id = await _cid("business-equipment-torgovoe-oborudovanie")
            parts_id = await _cid(
                "business-equipment-zapchasti-i-komplektuyuschie"
            )
            print_id = await _cid(
                "business-equipment-poligraficheskoe-oborudovanie"
            )
            sto_id = await _cid(
                "business-equipment-oborudovanie-dlya-avtomoek-i-sto"
            )
            forensic = (
                await session.execute(
                    select(Listing).where(Listing.id == FORENSIC_LISTING_ID)
                )
            ).scalar_one_or_none()
            forensic_existed = forensic is not None
            if forensic_existed:
                eav_rows = (
                    await session.execute(
                        text(
                            """
                            SELECT field_key, value_text
                            FROM listing_field_values
                            WHERE listing_id = :lid
                            """
                        ),
                        {"lid": FORENSIC_LISTING_ID},
                    )
                ).all()
                forensic_eav_before = {
                    r[0]: (r[1] or "") for r in eav_rows
                }

        # A durable — Condition YES
        lid_a = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=trade_id,
            title="PKG-B be vitrina A",
            fields={
                BUSINESS_KIND_KEY: "Торговые витрины",
                BUSINESS_SELLER_KEY: "Частное лицо",
                BUSINESS_CONDITION_KEY: "Б/у",
                "contact_methods": "Только чат",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
        )
        created_ids.append(lid_a)
        found = await client.get(
            "/api/v1/listings",
            params={
                "category_id": trade_id,
                "attrs": json.dumps(
                    {
                        BUSINESS_KIND_KEY: "Торговые витрины",
                        BUSINESS_CONDITION_KEY: "Б/у",
                        BUSINESS_SELLER_KEY: "Частное лицо",
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
        miss = await client.get(
            "/api/v1/listings",
            params={
                "category_id": trade_id,
                "attrs": json.dumps(
                    {
                        BUSINESS_KIND_KEY: "Торговые витрины",
                        BUSINESS_CONDITION_KEY: "Новое",
                    },
                    ensure_ascii=False,
                ),
                "limit": 40,
            },
        )
        assert miss.status_code == 200
        miss_ids = [int(i["id"]) for i in miss.json().get("items") or []]
        assert lid_a not in miss_ids

        # B Condition NO — needles
        lid_b = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=parts_id,
            title="PKG-B be needles B",
            fields={
                BUSINESS_KIND_KEY: "Иглы промышленные",
                BUSINESS_SELLER_KEY: "Магазин",
                "contact_methods": "Только чат",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
        )
        created_ids.append(lid_b)
        hit_b = await client.get(
            "/api/v1/listings",
            params={
                "category_id": parts_id,
                "attrs": json.dumps(
                    {
                        BUSINESS_KIND_KEY: "Иглы промышленные",
                        BUSINESS_SELLER_KEY: "Магазин",
                    },
                    ensure_ascii=False,
                ),
                "city": "Бишкек",
                "limit": 40,
            },
        )
        assert hit_b.status_code == 200
        assert lid_b in [int(i["id"]) for i in hit_b.json().get("items") or []]
        parts_filters = build_business_equipment_v2_search_filters()[
            "business-equipment-zapchasti-i-komplektuyuschie"
        ]
        dep = _depends_values(parts_filters, BUSINESS_CONDITION_KEY)
        assert dep is not None
        assert "Иглы промышленные" not in dep

        # C Electronics boundary — plotters
        lid_c = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=print_id,
            title="PKG-B be plotter C",
            fields={
                BUSINESS_KIND_KEY: PLOTTER_KIND,
                BUSINESS_SELLER_KEY: "Другой",
                BUSINESS_CONDITION_KEY: "Новое",
                "contact_methods": "Чат + телефон",
                "region": "Ошская область",
                "city": "Ош",
            },
        )
        created_ids.append(lid_c)
        hit_c = await client.get(
            "/api/v1/listings",
            params={
                "category_id": print_id,
                "attrs": json.dumps(
                    {BUSINESS_KIND_KEY: PLOTTER_KIND},
                    ensure_ascii=False,
                ),
                "limit": 40,
            },
        )
        assert hit_c.status_code == 200
        assert lid_c in [int(i["id"]) for i in hit_c.json().get("items") or []]

        # D Repair boundary — STO compressor
        lid_d = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=sto_id,
            title="PKG-B be sto compressor D",
            fields={
                BUSINESS_KIND_KEY: STO_COMPRESSOR_KIND,
                BUSINESS_SELLER_KEY: "Частное лицо",
                BUSINESS_CONDITION_KEY: "Б/у",
                "contact_methods": "Только телефон",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
        )
        created_ids.append(lid_d)
        hit_d = await client.get(
            "/api/v1/listings",
            params={
                "category_id": sto_id,
                "attrs": json.dumps(
                    {BUSINESS_KIND_KEY: STO_COMPRESSOR_KIND},
                    ensure_ascii=False,
                ),
                "limit": 40,
            },
        )
        assert hit_d.status_code == 200
        assert lid_d in [int(i["id"]) for i in hit_d.json().get("items") or []]

        # Facets self-exclusion smoke on trade
        facets = await client.get(
            "/api/v1/listings",
            params={
                "category_id": trade_id,
                "attrs": json.dumps(
                    {BUSINESS_KIND_KEY: "Торговые витрины"},
                    ensure_ascii=False,
                ),
                "facets": f"{BUSINESS_KIND_KEY},{BUSINESS_SELLER_KEY},{BUSINESS_CONDITION_KEY}",
                "limit": 1,
            },
        )
        assert facets.status_code == 200
        body = facets.json()
        assert "total" in body
        assert isinstance(body.get("facets"), dict)

        # 2911: category-only may find; business_kind filter excludes
        if forensic_existed:
            cat_only = await client.get(
                "/api/v1/listings",
                params={"category_id": trade_id, "limit": 100},
            )
            assert cat_only.status_code == 200
            # May or may not be in trade L2 depending on membership — if present, OK
            filtered = await client.get(
                "/api/v1/listings",
                params={
                    "category_id": trade_id,
                    "attrs": json.dumps(
                        {BUSINESS_KIND_KEY: "Торговые витрины"},
                        ensure_ascii=False,
                    ),
                    "limit": 100,
                },
            )
            assert filtered.status_code == 200
            filtered_ids = [
                int(i["id"]) for i in filtered.json().get("items") or []
            ]
            assert FORENSIC_LISTING_ID not in filtered_ids
            async with async_session_maker() as session:
                eav_rows = (
                    await session.execute(
                        text(
                            """
                            SELECT field_key, value_text
                            FROM listing_field_values
                            WHERE listing_id = :lid
                            """
                        ),
                        {"lid": FORENSIC_LISTING_ID},
                    )
                ).all()
                eav_now = {r[0]: (r[1] or "") for r in eav_rows}
            assert eav_now == forensic_eav_before
            assert BUSINESS_KIND_KEY not in eav_now
    finally:
        async with async_session_maker() as session:
            await _cleanup(session, created_ids)
            leftover = (
                await session.execute(
                    select(Listing.id).where(Listing.id.in_(created_ids or [0]))
                )
            ).scalars().all()
            assert list(leftover) == []
            if forensic_existed:
                still = (
                    await session.execute(
                        select(Listing.id).where(Listing.id == FORENSIC_LISTING_ID)
                    )
                ).scalar_one_or_none()
                assert still == FORENSIC_LISTING_ID
