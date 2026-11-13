"""Ready Business V2 Package B — Search SoT + Create↔Search parity."""
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
from app.models.user import User
from app.schemas.user import UserRead
from app.seeds.ready_business_v2 import (
    READY_BUSINESS_KIND_KEY,
    READY_BUSINESS_KIND_LABEL,
    READY_BUSINESS_POSTER_KEY,
    READY_BUSINESS_POSTER_LABEL,
    READY_BUSINESS_POSTER_OPTIONS,
    READY_BUSINESS_PREMISES_KEY,
    READY_BUSINESS_PREMISES_LABEL,
    READY_BUSINESS_V2_CANONICAL_SLUGS,
    READY_BUSINESS_V2_EXPECTED_L2_COUNT,
    READY_BUSINESS_V2_RETIRED_SLUGS,
    READY_BUSINESS_V2_SEARCH_ALLOWLIST,
    READY_BUSINESS_V2_SEARCH_EAV_KEYS,
    READY_BUSINESS_V2_SEARCH_POLICY,
    build_ready_business_v2_core_fields,
    build_ready_business_v2_search_filters,
    ready_business_v2_all_search_kind_audit,
    ready_business_v2_assert_package_a_contracts,
    ready_business_v2_assert_package_b_contracts,
    ready_business_v2_kind_count,
)

_REPR = {
    "shops": "ready-business-magaziny-i-torgovye-tochki",
    "online": "ready-business-onlayn-magaziny",
    "franchise": "ready-business-franshizy",
    "auto": "ready-business-avtomoyki-avtouslugi-i-sto",
    "production": "ready-business-proizvodstvo-i-tseha",
}


def test_package_a_still_locked() -> None:
    ready_business_v2_assert_package_a_contracts()
    assert READY_BUSINESS_V2_EXPECTED_L2_COUNT == 16
    assert ready_business_v2_kind_count() == 70
    cores = build_ready_business_v2_core_fields()
    assert len(cores) == 16
    for slug, fields in cores.items():
        keys = {r[0] for r in fields}
        assert READY_BUSINESS_KIND_KEY in keys
        assert READY_BUSINESS_POSTER_KEY in keys
        assert "condition" not in keys
        assert "seller_type" not in keys


def test_package_b_contracts() -> None:
    ready_business_v2_assert_package_b_contracts()
    assert READY_BUSINESS_V2_SEARCH_POLICY == "SIMPLE"
    assert READY_BUSINESS_KIND_KEY in READY_BUSINESS_V2_SEARCH_EAV_KEYS
    assert READY_BUSINESS_POSTER_KEY in READY_BUSINESS_V2_SEARCH_EAV_KEYS
    assert "geo" in READY_BUSINESS_V2_SEARCH_ALLOWLIST


def test_search_filters_cover_16_l2_and_premises_matrix() -> None:
    filters = build_ready_business_v2_search_filters()
    assert set(filters) == READY_BUSINESS_V2_CANONICAL_SLUGS
    assert len(filters) == 16
    for slug, rows in filters.items():
        keys = [r[0] for r in rows]
        assert READY_BUSINESS_KIND_KEY in keys
        assert READY_BUSINESS_POSTER_KEY in keys
        assert "condition" not in keys
        assert "revenue" not in keys
        assert "seller_type" not in keys
        assert "price" not in keys
        assert "negotiable" not in keys
        cores = {r[0] for r in build_ready_business_v2_core_fields()[slug]}
        if READY_BUSINESS_PREMISES_KEY in cores:
            assert READY_BUSINESS_PREMISES_KEY in keys, slug
        else:
            assert READY_BUSINESS_PREMISES_KEY not in keys, slug


def test_all_70_search_audit() -> None:
    audit = ready_business_v2_all_search_kind_audit()
    assert len(audit) == 70
    yes = sum(1 for r in audit if r["search_premises"] == "YES")
    no = sum(1 for r in audit if r["search_premises"] == "NO")
    assert yes == 62
    assert no == 8
    for row in audit:
        assert row["search_ready_business_kind"] == "YES"
        assert row["search_poster"] == "YES"
        assert row["search_condition"] == "NO"
        assert row["search_revenue"] == "NO"
        assert row["search_profit"] == "NO"
        assert row["retired_resurrected"] is False
        assert row["ownership"] in ("READY_BUSINESS", "FRANCHISE")


def test_search_filters_idempotent() -> None:
    a = build_ready_business_v2_search_filters()
    b = build_ready_business_v2_search_filters()
    assert a.keys() == b.keys()
    for slug in a:
        assert [r[0] for r in a[slug]] == [r[0] for r in b[slug]]


@pytest.mark.asyncio
async def test_live_search_filters_match_builder(client) -> None:
    expected = build_ready_business_v2_search_filters()
    async with async_session_maker() as session:
        for slug in sorted(READY_BUSINESS_V2_RETIRED_SLUGS):
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

        for slug in sorted(READY_BUSINESS_V2_CANONICAL_SLUGS):
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

    for slug in _REPR.values():
        async with async_session_maker() as session:
            cat = (
                await session.execute(select(Category).where(Category.slug == slug))
            ).scalar_one()
            cat_id = int(cat.id)
        resp = await client.get(f"/api/v1/categories/intelligence/{cat_id}")
        assert resp.status_code == 200, slug
        body = resp.json()
        keys = {f["filter_key"] for f in body.get("filters") or []}
        assert READY_BUSINESS_KIND_KEY in keys
        assert READY_BUSINESS_POSTER_KEY in keys
        assert "condition" not in keys
        assert "seller_type" not in keys
        kind_f = next(
            f for f in body["filters"] if f["filter_key"] == READY_BUSINESS_KIND_KEY
        )
        assert kind_f["label"] == READY_BUSINESS_KIND_LABEL
        poster_f = next(
            f for f in body["filters"] if f["filter_key"] == READY_BUSINESS_POSTER_KEY
        )
        assert poster_f["label"] == READY_BUSINESS_POSTER_LABEL
        if slug in (_REPR["online"], _REPR["franchise"]):
            assert READY_BUSINESS_PREMISES_KEY not in keys
        else:
            assert READY_BUSINESS_PREMISES_KEY in keys
            prem = next(
                f for f in body["filters"] if f["filter_key"] == READY_BUSINESS_PREMISES_KEY
            )
            assert prem["label"] == READY_BUSINESS_PREMISES_LABEL


def _auth_as(user_id: int) -> None:
    now = datetime.now(UTC)

    async def _user() -> UserRead:
        return UserRead(
            id=user_id,
            phone="+79001234567",
            full_name="ReadyBusinessSearchParity",
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
              :lid, '/media/test/ready-business-pb.jpg', 0, false,
              'ready', 'approved', now(), now()
            )
            """
        ),
        {"lid": listing_id},
    )
    await session.commit()


async def _cleanup(session, listing_ids: list[int]) -> None:
    ids = [i for i in listing_ids if i]
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
    price: str = "250000",
) -> int:
    _auth_as(owner_id)
    created = await client.post(
        "/api/v1/listings",
        json={
            "title": title,
            "description": f"{title} package B parity",
            "price": price,
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


async def _http_ids(
    client,
    *,
    category_id: int,
    attrs: dict[str, str],
    city: str | None = "Бишкек",
) -> set[int]:
    params: dict = {
        "category_id": category_id,
        "attrs": json.dumps(attrs, ensure_ascii=False),
        "limit": 40,
    }
    if city:
        params["city"] = city
    resp = await client.get("/api/v1/listings", params=params)
    assert resp.status_code == 200, resp.text
    return {int(i["id"]) for i in (resp.json().get("items") or [])}


@pytest.mark.asyncio
async def test_ready_business_create_search_parity_cases_a_e(client) -> None:
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

            shops_id = await _cid(_REPR["shops"])
            online_id = await _cid(_REPR["online"])
            franchise_id = await _cid(_REPR["franchise"])
            auto_id = await _cid(_REPR["auto"])
            production_id = await _cid(_REPR["production"])

        geo = {"region": "Чуйская область", "city": "Бишкек"}

        # A — physical + premises FOUND / wrong premises NOT FOUND
        lid_a = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=shops_id,
            title="PKG-B rb shop A",
            fields={
                READY_BUSINESS_KIND_KEY: "Магазины",
                READY_BUSINESS_POSTER_KEY: "Владелец",
                READY_BUSINESS_PREMISES_KEY: "В аренде",
                "contact_methods": "Чат + телефон",
                "negotiable": "Есть торг",
                **geo,
            },
            price="450000",
        )
        created_ids.append(lid_a)
        found = await _http_ids(
            client,
            category_id=shops_id,
            attrs={
                READY_BUSINESS_KIND_KEY: "Магазины",
                READY_BUSINESS_POSTER_KEY: "Владелец",
                READY_BUSINESS_PREMISES_KEY: "В аренде",
            },
        )
        assert lid_a in found
        miss = await _http_ids(
            client,
            category_id=shops_id,
            attrs={
                READY_BUSINESS_KIND_KEY: "Магазины",
                READY_BUSINESS_PREMISES_KEY: "В собственности",
            },
        )
        assert lid_a not in miss

        # B — online, no premises
        lid_b = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=online_id,
            title="PKG-B rb online B",
            fields={
                READY_BUSINESS_KIND_KEY: "Интернет-магазины",
                READY_BUSINESS_POSTER_KEY: "Представитель",
                "contact_methods": "Только чат",
                **geo,
            },
            price="120000",
        )
        created_ids.append(lid_b)
        found_b = await _http_ids(
            client,
            category_id=online_id,
            attrs={
                READY_BUSINESS_KIND_KEY: "Интернет-магазины",
                READY_BUSINESS_POSTER_KEY: "Представитель",
            },
        )
        assert lid_b in found_b

        # C — franchise
        lid_c = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=franchise_id,
            title="PKG-B rb franchise C",
            fields={
                READY_BUSINESS_KIND_KEY: "Франшиза точки",
                READY_BUSINESS_POSTER_KEY: "Другой",
                "contact_methods": "Чат + Wapp",
                **geo,
            },
            price="80000",
        )
        created_ids.append(lid_c)
        found_c = await _http_ids(
            client,
            category_id=franchise_id,
            attrs={
                READY_BUSINESS_KIND_KEY: "Франшиза точки",
                READY_BUSINESS_POSTER_KEY: "Другой",
            },
        )
        assert lid_c in found_c

        # D — auto business stays Ready Business
        lid_d = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=auto_id,
            title="PKG-B rb auto D",
            fields={
                READY_BUSINESS_KIND_KEY: "Автомойки",
                READY_BUSINESS_POSTER_KEY: "Владелец",
                READY_BUSINESS_PREMISES_KEY: "В собственности",
                "contact_methods": "Только телефон",
                **geo,
            },
            price="900000",
        )
        created_ids.append(lid_d)
        found_d = await _http_ids(
            client,
            category_id=auto_id,
            attrs={READY_BUSINESS_KIND_KEY: "Автомойки"},
        )
        assert lid_d in found_d

        # E — production
        lid_e = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=production_id,
            title="PKG-B rb production E",
            fields={
                READY_BUSINESS_KIND_KEY: "Заводы",
                READY_BUSINESS_POSTER_KEY: "Представитель",
                READY_BUSINESS_PREMISES_KEY: "В аренде",
                "contact_methods": "Чат + Тел. + Wapp",
                **geo,
            },
            price="1500000",
        )
        created_ids.append(lid_e)
        found_e = await _http_ids(
            client,
            category_id=production_id,
            attrs={READY_BUSINESS_KIND_KEY: "Заводы"},
        )
        assert lid_e in found_e

        # Facet self-exclusion smoke on shops
        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": shops_id,
                "attrs": json.dumps(
                    {READY_BUSINESS_KIND_KEY: "Магазины"}, ensure_ascii=False
                ),
                "facets": f"{READY_BUSINESS_KIND_KEY},{READY_BUSINESS_POSTER_KEY},{READY_BUSINESS_PREMISES_KEY}",
                "city": "Бишкек",
                "limit": 1,
            },
        )
        assert resp.status_code == 200, resp.text
        facets = resp.json().get("facets") or {}
        assert READY_BUSINESS_POSTER_KEY in facets
        assert READY_BUSINESS_PREMISES_KEY in facets

        assert list(READY_BUSINESS_POSTER_OPTIONS) == [
            "Владелец",
            "Представитель",
            "Другой",
        ]
    finally:
        async with async_session_maker() as session:
            await _cleanup(session, created_ids)
        async with async_session_maker() as session:
            left = (
                await session.execute(
                    text(
                        """
                        SELECT count(*) FROM listings l
                        JOIN categories c ON c.id = l.category_id
                        WHERE c.slug LIKE 'ready-business-%'
                          AND l.title LIKE 'PKG-B rb%'
                        """
                    )
                )
            ).scalar_one()
            assert int(left or 0) == 0
