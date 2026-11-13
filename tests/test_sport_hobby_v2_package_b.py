"""Sport / Hobby V2 Package B — Search SoT + Create↔Search parity."""
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
from app.seeds.sport_v2 import (
    SPORT_CONDITION_KEY,
    SPORT_KIND_KEY,
    SPORT_KIND_LABEL,
    SPORT_SELLER_KEY,
    SPORT_SELLER_LABEL,
    SPORT_V2_CANONICAL_SLUGS,
    SPORT_V2_EXPECTED_L2_COUNT,
    SPORT_V2_RETIRED_SLUGS,
    SPORT_V2_SEARCH_ALLOWLIST,
    SPORT_V2_SEARCH_EAV_KEYS,
    SPORT_V2_SEARCH_POLICY,
    build_sport_v2_core_fields,
    build_sport_v2_search_filters,
    sport_v2_all_search_kind_audit,
    sport_v2_assert_package_a_contracts,
    sport_v2_assert_package_b_contracts,
    sport_v2_condition_matrix,
    sport_v2_kind_count,
)

_REPR = {
    "sport": "sports-hobby-sportivnye-tovary",
    "nutrition": "sports-hobby-sportivnoe-pitanie",
    "fishing": "sports-hobby-ohota-i-rybalka",
    "music": "sports-hobby-muzykalnye-instrumenty",
    "horse": "sports-hobby-konnyy-sport-i-verhovaya-ezda",
    "collect": "sports-hobby-kollektsionirovanie",
}

_INDEPENDENT_NO = frozenset(
    {
        "Протеин",
        "Гейнеры",
        "Креатин",
        "Аминокислоты",
        "Изотоники",
        "Спортивные батончики",
        "Другое спортивное питание",
        "Блёсны и приманки",
        "Бисер",
        "Валяние",
        "Мыловарение",
    }
)


def test_package_a_still_locked() -> None:
    sport_v2_assert_package_a_contracts()
    assert SPORT_V2_EXPECTED_L2_COUNT == 13
    assert sport_v2_kind_count() == 96
    assert sport_v2_condition_matrix() == {"YES": 85, "NO": 11}
    cores = build_sport_v2_core_fields()
    assert len(cores) == 13


def test_package_b_contracts() -> None:
    sport_v2_assert_package_b_contracts()
    assert SPORT_V2_SEARCH_POLICY == "SIMPLE"
    assert SPORT_KIND_KEY in SPORT_V2_SEARCH_EAV_KEYS
    assert SPORT_SELLER_KEY in SPORT_V2_SEARCH_EAV_KEYS
    assert "geo" in SPORT_V2_SEARCH_ALLOWLIST
    assert "size" not in SPORT_V2_SEARCH_ALLOWLIST


def test_search_filters_cover_13_l2_and_condition_matrix() -> None:
    filters = build_sport_v2_search_filters()
    assert set(filters) == SPORT_V2_CANONICAL_SLUGS
    assert len(filters) == 13
    for slug, rows in filters.items():
        keys = [r[0] for r in rows]
        assert SPORT_KIND_KEY in keys
        assert SPORT_SELLER_KEY in keys
        assert "price" not in keys
        assert "size" not in keys
        assert "brand" not in keys
        cores = {r[0] for r in build_sport_v2_core_fields()[slug]}
        if SPORT_CONDITION_KEY in cores:
            assert SPORT_CONDITION_KEY in keys, slug
        else:
            assert SPORT_CONDITION_KEY not in keys, slug
            assert slug == "sports-hobby-sportivnoe-pitanie"


def test_all_96_search_audit_independent() -> None:
    audit = sport_v2_all_search_kind_audit()
    assert len(audit) == 96
    yes = sum(1 for r in audit if r["search_condition"] == "YES")
    no = sum(1 for r in audit if r["search_condition"] == "NO")
    assert yes == 85
    assert no == 11
    for row in audit:
        expected = "NO" if row["kind"] in _INDEPENDENT_NO else "YES"
        assert row["search_condition"] == expected, row["kind"]
        assert row["search_sport_kind"] == "YES"
        assert row["search_seller"] == "YES"
        assert row["search_size"] == "NO"
        assert row["search_brand"] == "NO"
        assert row["search_tech"] == "NO"
        assert row["search_rental"] == "NO"
        assert row["retired_resurrected"] is False
        assert row["platform_owner"] == "SPORT_HOBBY"
    assert "Охотничьи ножи" not in {r["kind"] for r in audit}
    assert "Юрты" not in {r["kind"] for r in audit}


def test_search_filters_idempotent() -> None:
    a = build_sport_v2_search_filters()
    b = build_sport_v2_search_filters()
    assert a.keys() == b.keys()
    for slug in a:
        assert [r[0] for r in a[slug]] == [r[0] for r in b[slug]]


@pytest.mark.asyncio
async def test_live_search_filters_match_builder(client) -> None:
    expected = build_sport_v2_search_filters()
    async with async_session_maker() as session:
        for slug in sorted(SPORT_V2_RETIRED_SLUGS):
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

        for slug in sorted(SPORT_V2_CANONICAL_SLUGS):
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
        assert SPORT_KIND_KEY in keys
        assert SPORT_SELLER_KEY in keys
        assert "size" not in keys
        assert "price" not in keys
        kind_f = next(f for f in body["filters"] if f["filter_key"] == SPORT_KIND_KEY)
        assert kind_f["label"] == SPORT_KIND_LABEL
        seller_f = next(
            f for f in body["filters"] if f["filter_key"] == SPORT_SELLER_KEY
        )
        assert seller_f["label"] == SPORT_SELLER_LABEL
        if slug == _REPR["nutrition"]:
            assert SPORT_CONDITION_KEY not in keys
        else:
            assert SPORT_CONDITION_KEY in keys


def _auth_as(user_id: int) -> None:
    now = datetime.now(UTC)

    async def _user() -> UserRead:
        return UserRead(
            id=user_id,
            phone="+79001234567",
            full_name="SportSearchParity",
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
              :lid, '/media/test/sport-hobby-pb.jpg', 0, false,
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
    price: str = "5000",
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
async def test_sport_hobby_create_search_parity_cases_a_g(client) -> None:
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

            sport_id = await _cid(_REPR["sport"])
            nutrition_id = await _cid(_REPR["nutrition"])
            fishing_id = await _cid(_REPR["fishing"])
            music_id = await _cid(_REPR["music"])
            horse_id = await _cid(_REPR["horse"])
            collect_id = await _cid(_REPR["collect"])

        geo = {"region": "Чуйская область", "city": "Бишкек"}

        # A — durable + Condition FOUND / wrong Condition NOT FOUND
        lid_a = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=sport_id,
            title="PKG-B sport durable A",
            fields={
                SPORT_KIND_KEY: "Лыжи",
                SPORT_SELLER_KEY: "Частное лицо",
                SPORT_CONDITION_KEY: "Новое",
                "contact_methods": "Чат + телефон",
                "negotiable": "Есть торг",
                **geo,
            },
            price="12000",
        )
        created_ids.append(lid_a)
        found = await _http_ids(
            client,
            category_id=sport_id,
            attrs={
                SPORT_KIND_KEY: "Лыжи",
                SPORT_SELLER_KEY: "Частное лицо",
                SPORT_CONDITION_KEY: "Новое",
            },
        )
        assert lid_a in found
        miss = await _http_ids(
            client,
            category_id=sport_id,
            attrs={
                SPORT_KIND_KEY: "Лыжи",
                SPORT_CONDITION_KEY: "Б/у",
            },
        )
        assert lid_a not in miss

        # B — nutrition NO Condition
        lid_b = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=nutrition_id,
            title="PKG-B sport nutrition B",
            fields={
                SPORT_KIND_KEY: "Протеин",
                SPORT_SELLER_KEY: "Магазин",
                "contact_methods": "Только чат",
                **geo,
            },
            price="3500",
        )
        created_ids.append(lid_b)
        found_b = await _http_ids(
            client,
            category_id=nutrition_id,
            attrs={
                SPORT_KIND_KEY: "Протеин",
                SPORT_SELLER_KEY: "Магазин",
            },
        )
        assert lid_b in found_b

        # C — fishing durable
        lid_c = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=fishing_id,
            title="PKG-B sport fishing C",
            fields={
                SPORT_KIND_KEY: "Удочки",
                SPORT_SELLER_KEY: "Частное лицо",
                SPORT_CONDITION_KEY: "Б/у",
                "contact_methods": "Чат + Wapp",
                **geo,
            },
            price="4500",
        )
        created_ids.append(lid_c)
        assert lid_c in await _http_ids(
            client,
            category_id=fishing_id,
            attrs={SPORT_KIND_KEY: "Удочки", SPORT_CONDITION_KEY: "Б/у"},
        )

        # D — echo sounder Sport/Fishing
        lid_d = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=fishing_id,
            title="PKG-B sport echo D",
            fields={
                SPORT_KIND_KEY: "Эхолоты",
                SPORT_SELLER_KEY: "Магазин",
                SPORT_CONDITION_KEY: "Новое",
                "contact_methods": "Только телефон",
                **geo,
            },
            price="18000",
        )
        created_ids.append(lid_d)
        assert lid_d in await _http_ids(
            client,
            category_id=fishing_id,
            attrs={SPORT_KIND_KEY: "Эхолоты", SPORT_SELLER_KEY: "Магазин"},
        )

        # E — synthesizer Sport/Hobby
        lid_e = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=music_id,
            title="PKG-B sport synth E",
            fields={
                SPORT_KIND_KEY: "Синтезаторы",
                SPORT_SELLER_KEY: "Другой",
                SPORT_CONDITION_KEY: "Б/у",
                "contact_methods": "Чат + Тел. + Wapp",
                **geo,
            },
            price="25000",
        )
        created_ids.append(lid_e)
        assert lid_e in await _http_ids(
            client,
            category_id=music_id,
            attrs={SPORT_KIND_KEY: "Синтезаторы"},
        )

        # F — horse gear
        lid_f = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=horse_id,
            title="PKG-B sport horse F",
            fields={
                SPORT_KIND_KEY: "Сёдла",
                SPORT_SELLER_KEY: "Частное лицо",
                SPORT_CONDITION_KEY: "Новое",
                "contact_methods": "Чат + телефон",
                **geo,
            },
            price="15000",
        )
        created_ids.append(lid_f)
        assert lid_f in await _http_ids(
            client,
            category_id=horse_id,
            attrs={SPORT_KIND_KEY: "Сёдла"},
        )

        # G — collectible
        lid_g = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=collect_id,
            title="PKG-B sport collect G",
            fields={
                SPORT_KIND_KEY: "Монеты",
                SPORT_SELLER_KEY: "Магазин",
                SPORT_CONDITION_KEY: "Б/у",
                "contact_methods": "Только чат",
                **geo,
            },
            price="2000",
        )
        created_ids.append(lid_g)
        assert lid_g in await _http_ids(
            client,
            category_id=collect_id,
            attrs={SPORT_KIND_KEY: "Монеты", SPORT_SELLER_KEY: "Магазин"},
        )

        # Facets + total + self-exclusion smoke (durable A)
        facets_resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": sport_id,
                "attrs": json.dumps(
                    {SPORT_KIND_KEY: "Лыжи", SPORT_CONDITION_KEY: "Новое"},
                    ensure_ascii=False,
                ),
                "city": "Бишкек",
                "facets": f"{SPORT_KIND_KEY},{SPORT_SELLER_KEY},{SPORT_CONDITION_KEY}",
                "limit": 1,
            },
        )
        assert facets_resp.status_code == 200, facets_resp.text
        facets_body = facets_resp.json()
        assert isinstance(facets_body.get("total"), int)
        assert facets_body["total"] >= 1
        assert isinstance(facets_body.get("facets"), dict)

        # Strict missing-EAV: strip sport_kind → listing excluded from kind filter
        async with async_session_maker() as session:
            await session.execute(
                text(
                    """
                    DELETE FROM listing_field_values
                    WHERE listing_id = :lid AND field_key = :key
                    """
                ),
                {"lid": lid_a, "key": SPORT_KIND_KEY},
            )
            await session.commit()
        stripped = await _http_ids(
            client,
            category_id=sport_id,
            attrs={SPORT_KIND_KEY: "Лыжи"},
        )
        assert lid_a not in stripped

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
                        WHERE c.slug LIKE 'sports-hobby-%'
                          AND l.title LIKE 'PKG-B sport%'
                        """
                    )
                )
            ).scalar_one()
            assert int(left or 0) == 0
