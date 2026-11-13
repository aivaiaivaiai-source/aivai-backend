"""Beauty & Personal Care V2 Package B — Search SoT + Create↔Search parity."""
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
from app.seeds.beauty_v2 import (
    BEAUTY_CONDITION_KEY,
    BEAUTY_KIND_KEY,
    BEAUTY_KIND_LABEL,
    BEAUTY_SELLER_KEY,
    BEAUTY_SELLER_LABEL,
    BEAUTY_V2_CANONICAL_SLUGS,
    BEAUTY_V2_EXPECTED_L2_COUNT,
    BEAUTY_V2_RETIRED_SLUGS,
    BEAUTY_V2_SEARCH_ALLOWLIST,
    BEAUTY_V2_SEARCH_EAV_KEYS,
    BEAUTY_V2_SEARCH_POLICY,
    build_beauty_v2_core_fields,
    build_beauty_v2_search_filters,
    beauty_v2_all_search_kind_audit,
    beauty_v2_assert_package_a_contracts,
    beauty_v2_assert_package_b_contracts,
    beauty_v2_condition_matrix,
    beauty_v2_kind_count,
)

_REPR = {
    "cosmetics": "beauty-kosmetika",
    "perfume": "beauty-parfyumeriya",
    "hair": "beauty-uhod-za-volosami",
    "tools": "beauty-instrumenty-oborud-e-dlya-krasoty",
    "tattoo": "beauty-tovary-dlya-tatu-i-pirsinga",
    "barber": "beauty-tovary-dlya-barbershopov",
    "other": "beauty-prochee-dlya-krasoty-i-uhoda",
}

_INDEPENDENT_YES = frozenset(
    {
        "Фены",
        "Плойки и выпрямители",
        "Домашние машинки для стрижки",
        "Электробритвы",
        "Эпиляторы",
        "Лампы для маникюра",
        "Аппараты для маникюра",
        "Воскоплавы",
        "Другие персональные устройства для красоты",
        "Машинки для барберов",
        "Ножницы для барберов",
        "Опасные бритвы",
        "Другие товары для барбершопов",
        "Машинки для тату",
        "Другие товары для тату",
        "Парики и шиньоны",
        "Косметические зеркала",
        "Другие товары для красоты",
    }
)


def test_package_a_still_locked() -> None:
    beauty_v2_assert_package_a_contracts()
    assert BEAUTY_V2_EXPECTED_L2_COUNT == 16
    assert beauty_v2_kind_count() == 99
    assert beauty_v2_condition_matrix() == {"YES": 18, "NO": 81}
    cores = build_beauty_v2_core_fields()
    assert len(cores) == 16


def test_package_b_contracts() -> None:
    beauty_v2_assert_package_b_contracts()
    assert BEAUTY_V2_SEARCH_POLICY == "SIMPLE"
    assert BEAUTY_KIND_KEY in BEAUTY_V2_SEARCH_EAV_KEYS
    assert BEAUTY_SELLER_KEY in BEAUTY_V2_SEARCH_EAV_KEYS
    assert "geo" in BEAUTY_V2_SEARCH_ALLOWLIST
    assert "package_state" not in BEAUTY_V2_SEARCH_ALLOWLIST
    assert "beauty_brand" not in BEAUTY_V2_SEARCH_ALLOWLIST
    assert "volume" not in BEAUTY_V2_SEARCH_ALLOWLIST


def test_search_filters_cover_16_l2_and_condition_matrix() -> None:
    filters = build_beauty_v2_search_filters()
    assert set(filters) == BEAUTY_V2_CANONICAL_SLUGS
    assert len(filters) == 16
    for slug, rows in filters.items():
        keys = [r[0] for r in rows]
        assert BEAUTY_KIND_KEY in keys
        assert BEAUTY_SELLER_KEY in keys
        assert "price" not in keys
        assert "package_state" not in keys
        assert "beauty_brand" not in keys
        assert "volume" not in keys
        cores = {r[0] for r in build_beauty_v2_core_fields()[slug]}
        if BEAUTY_CONDITION_KEY in cores:
            assert BEAUTY_CONDITION_KEY in keys, slug
        else:
            assert BEAUTY_CONDITION_KEY not in keys, slug


def test_all_99_search_audit_independent() -> None:
    audit = beauty_v2_all_search_kind_audit()
    assert len(audit) == 99
    yes = sum(1 for r in audit if r["search_condition"] == "YES")
    no = sum(1 for r in audit if r["search_condition"] == "NO")
    assert yes == 18
    assert no == 81
    for row in audit:
        expected = "YES" if row["kind"] in _INDEPENDENT_YES else "NO"
        assert row["search_condition"] == expected, row["kind"]
        assert row["search_beauty_kind"] == "YES"
        assert row["search_seller"] == "YES"
        assert row["search_package_state"] == "NO"
        assert row["search_brand"] == "NO"
        assert row["search_volume"] == "NO"
        assert row["search_authenticity"] == "NO"
        assert row["retired_resurrected"] is False
        assert row["platform_owner"] == "BEAUTY"
    assert "Косметички" not in {r["kind"] for r in audit}
    assert "Украшения для пирсинга" not in {r["kind"] for r in audit}


def test_search_filters_idempotent() -> None:
    a = build_beauty_v2_search_filters()
    b = build_beauty_v2_search_filters()
    assert a.keys() == b.keys()
    for slug in a:
        assert [r[0] for r in a[slug]] == [r[0] for r in b[slug]]


@pytest.mark.asyncio
async def test_live_search_filters_match_builder(client) -> None:
    expected = build_beauty_v2_search_filters()
    async with async_session_maker() as session:
        for slug in sorted(BEAUTY_V2_RETIRED_SLUGS):
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

        for slug in sorted(BEAUTY_V2_CANONICAL_SLUGS):
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
        assert BEAUTY_KIND_KEY in keys
        assert BEAUTY_SELLER_KEY in keys
        assert "package_state" not in keys
        assert "beauty_brand" not in keys
        assert "price" not in keys
        kind_f = next(f for f in body["filters"] if f["filter_key"] == BEAUTY_KIND_KEY)
        assert kind_f["label"] == BEAUTY_KIND_LABEL
        seller_f = next(
            f for f in body["filters"] if f["filter_key"] == BEAUTY_SELLER_KEY
        )
        assert seller_f["label"] == BEAUTY_SELLER_LABEL
        if slug in {
            _REPR["cosmetics"],
            _REPR["perfume"],
            _REPR["hair"],
        }:
            assert BEAUTY_CONDITION_KEY not in keys
        else:
            assert BEAUTY_CONDITION_KEY in keys


def _auth_as(user_id: int) -> None:
    now = datetime.now(UTC)

    async def _user() -> UserRead:
        return UserRead(
            id=user_id,
            phone="+79001234567",
            full_name="BeautySearchParity",
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
              :lid, '/media/test/beauty-pb.jpg', 0, false,
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
    price: str = "1500",
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
async def test_beauty_create_search_parity_cases_a_g(client) -> None:
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

            cosmetics_id = await _cid(_REPR["cosmetics"])
            perfume_id = await _cid(_REPR["perfume"])
            hair_id = await _cid(_REPR["hair"])
            tools_id = await _cid(_REPR["tools"])
            tattoo_id = await _cid(_REPR["tattoo"])
            barber_id = await _cid(_REPR["barber"])
            other_id = await _cid(_REPR["other"])

        geo = {"region": "Чуйская область", "city": "Бишкек"}

        # A — cosmetic consumable: no Condition
        lid_a = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=cosmetics_id,
            title="PKG-B beauty cosmetic A",
            fields={
                BEAUTY_KIND_KEY: "Тональные средства",
                BEAUTY_SELLER_KEY: "Частное лицо",
                "contact_methods": "Чат + телефон",
                "negotiable": "Есть торг",
                **geo,
            },
        )
        created_ids.append(lid_a)
        found = await _http_ids(
            client,
            category_id=cosmetics_id,
            attrs={
                BEAUTY_KIND_KEY: "Тональные средства",
                BEAUTY_SELLER_KEY: "Частное лицо",
            },
        )
        assert lid_a in found
        # Condition must not be required for discovery
        found_no_cond = await _http_ids(
            client,
            category_id=cosmetics_id,
            attrs={BEAUTY_KIND_KEY: "Тональные средства"},
        )
        assert lid_a in found_no_cond

        # B — perfume
        lid_b = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=perfume_id,
            title="PKG-B beauty perfume B",
            fields={
                BEAUTY_KIND_KEY: "Духи",
                BEAUTY_SELLER_KEY: "Магазин",
                "contact_methods": "Только чат",
                **geo,
            },
        )
        created_ids.append(lid_b)
        assert lid_b in await _http_ids(
            client,
            category_id=perfume_id,
            attrs={BEAUTY_KIND_KEY: "Духи", BEAUTY_SELLER_KEY: "Магазин"},
        )

        # C — hair care
        lid_c = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=hair_id,
            title="PKG-B beauty hair C",
            fields={
                BEAUTY_KIND_KEY: "Шампуни",
                BEAUTY_SELLER_KEY: "Другой",
                "contact_methods": "Чат + Wapp",
                **geo,
            },
        )
        created_ids.append(lid_c)
        assert lid_c in await _http_ids(
            client,
            category_id=hair_id,
            attrs={BEAUTY_KIND_KEY: "Шампуни"},
        )

        # D — durable device Condition isolation
        lid_d = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=tools_id,
            title="PKG-B beauty dryer D",
            fields={
                BEAUTY_KIND_KEY: "Фены",
                BEAUTY_SELLER_KEY: "Частное лицо",
                BEAUTY_CONDITION_KEY: "Новое",
                "contact_methods": "Чат + телефон",
                **geo,
            },
            price="4500",
        )
        created_ids.append(lid_d)
        found_new = await _http_ids(
            client,
            category_id=tools_id,
            attrs={
                BEAUTY_KIND_KEY: "Фены",
                BEAUTY_CONDITION_KEY: "Новое",
            },
        )
        assert lid_d in found_new
        found_used = await _http_ids(
            client,
            category_id=tools_id,
            attrs={
                BEAUTY_KIND_KEY: "Фены",
                BEAUTY_CONDITION_KEY: "Б/у",
            },
        )
        assert lid_d not in found_used

        # E — manicure lamp
        lid_e = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=tools_id,
            title="PKG-B beauty lamp E",
            fields={
                BEAUTY_KIND_KEY: "Лампы для маникюра",
                BEAUTY_SELLER_KEY: "Магазин",
                BEAUTY_CONDITION_KEY: "Б/у",
                "contact_methods": "Только телефон",
                **geo,
            },
            price="2800",
        )
        created_ids.append(lid_e)
        assert lid_e in await _http_ids(
            client,
            category_id=tools_id,
            attrs={
                BEAUTY_KIND_KEY: "Лампы для маникюра",
                BEAUTY_CONDITION_KEY: "Б/у",
            },
        )

        # F — tattoo / barber tools
        lid_f = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=tattoo_id,
            title="PKG-B beauty tattoo F",
            fields={
                BEAUTY_KIND_KEY: "Машинки для тату",
                BEAUTY_SELLER_KEY: "Частное лицо",
                BEAUTY_CONDITION_KEY: "Новое",
                "contact_methods": "Чат + Тел. + Wapp",
                **geo,
            },
            price="15000",
        )
        created_ids.append(lid_f)
        assert lid_f in await _http_ids(
            client,
            category_id=tattoo_id,
            attrs={BEAUTY_KIND_KEY: "Машинки для тату"},
        )
        lid_f2 = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=barber_id,
            title="PKG-B beauty barber F2",
            fields={
                BEAUTY_KIND_KEY: "Машинки для барберов",
                BEAUTY_SELLER_KEY: "Магазин",
                BEAUTY_CONDITION_KEY: "Б/у",
                "contact_methods": "Только чат",
                **geo,
            },
            price="9000",
        )
        created_ids.append(lid_f2)
        assert lid_f2 in await _http_ids(
            client,
            category_id=barber_id,
            attrs={BEAUTY_KIND_KEY: "Машинки для барберов"},
        )

        # G — wig
        lid_g = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=other_id,
            title="PKG-B beauty wig G",
            fields={
                BEAUTY_KIND_KEY: "Парики и шиньоны",
                BEAUTY_SELLER_KEY: "Магазин",
                BEAUTY_CONDITION_KEY: "Новое",
                "contact_methods": "Чат + телефон",
                **geo,
            },
            price="5000",
        )
        created_ids.append(lid_g)
        assert lid_g in await _http_ids(
            client,
            category_id=other_id,
            attrs={BEAUTY_KIND_KEY: "Парики и шиньоны"},
        )

        # Facet self-exclusion smoke via search total
        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": tools_id,
                "attrs": json.dumps(
                    {BEAUTY_KIND_KEY: "Фены"}, ensure_ascii=False
                ),
                "city": "Бишкек",
                "limit": 1,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "total" in body
        assert int(body["total"]) >= 1

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
                        WHERE c.slug LIKE 'beauty%'
                          AND l.title LIKE 'PKG-B beauty%'
                        """
                    )
                )
            ).scalar_one()
            assert int(left or 0) == 0
