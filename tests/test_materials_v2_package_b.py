"""Materials V2 Package B — Search SoT + Create↔Search parity."""
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
from app.seeds.materials_v2 import (
    FOOD_TARA_GAP_STATUS,
    MATERIALS_CREATE_FORBIDDEN,
    MATERIALS_KIND_KEY,
    MATERIALS_KIND_LABEL,
    MATERIALS_PRICE_BASIS_KEY,
    MATERIALS_SELLER_KEY,
    MATERIALS_SELLER_TARGET,
    MATERIALS_V2_CANONICAL_SLUGS,
    MATERIALS_V2_EXPECTED_L2_COUNT,
    MATERIALS_V2_RETIRED_SLUGS,
    MATERIALS_V2_SEARCH_ALLOWLIST,
    MATERIALS_V2_SEARCH_EAV_KEYS,
    MATERIALS_V2_SEARCH_EXCLUDE,
    MATERIALS_V2_SEARCH_POLICY,
    MATERIALS_V2_SECTION_KINDS,
    MATERIALS_V2_SECTION_SLUGS,
    build_materials_v2_core_fields,
    build_materials_v2_search_filters,
    materials_v2_all_search_kind_audit,
    materials_v2_assert_package_a_contracts,
    materials_v2_assert_package_b_contracts,
    materials_v2_kind_count,
)

_INDEPENDENT_SELLER = ("Частное лицо", "Магазин", "Другой")
_FORBIDDEN_SEARCH = frozenset(
    {
        "price",
        "negotiable",
        "contact_methods",
        MATERIALS_PRICE_BASIS_KEY,
        "condition",
        "currency",
        "quantity",
        "moq",
        "wholesale_price",
        "brand",
        "model",
        "grade",
        "weight",
        "color",
    }
)
_REPR_SLUGS = (
    "materials-tkani-i-tekstilnoe-syre",
    "materials-metally-metallicheskoe-syre",
    "materials-upakovochnye-materialy",
    "materials-pischevoe-syre-i-ingredienty",
    "materials-prochee-syre-dlya-proizvodstva",
)


def _options_for(filters: list, key: str) -> list[dict]:
    for row in filters:
        if row[0] != key:
            continue
        cfg = row[4] or {}
        return list(cfg.get("options") or cfg.get("choices") or [])
    return []


def test_materials_package_a_still_locked() -> None:
    materials_v2_assert_package_a_contracts()
    assert MATERIALS_V2_EXPECTED_L2_COUNT == 18
    assert materials_v2_kind_count() == 117
    assert FOOD_TARA_GAP_STATUS == "STILL_OPEN"
    cores = build_materials_v2_core_fields()
    assert len(cores) == 18
    for slug, fields in cores.items():
        keys = {r[0] for r in fields}
        assert MATERIALS_KIND_KEY in keys
        assert MATERIALS_PRICE_BASIS_KEY in keys
        assert "condition" not in keys
        assert "price" in keys


def test_materials_package_b_contracts() -> None:
    materials_v2_assert_package_b_contracts()
    assert MATERIALS_V2_SEARCH_POLICY == "SIMPLE"


def test_materials_search_filters_cover_all_canonical_l2() -> None:
    filters = build_materials_v2_search_filters()
    assert set(filters) == MATERIALS_V2_CANONICAL_SLUGS
    assert len(filters) == 18


def test_materials_search_eav_keys_are_short_allowlist() -> None:
    assert MATERIALS_V2_SEARCH_EAV_KEYS <= MATERIALS_V2_SEARCH_ALLOWLIST
    assert MATERIALS_KIND_KEY in MATERIALS_V2_SEARCH_EAV_KEYS
    assert MATERIALS_SELLER_KEY in MATERIALS_V2_SEARCH_EAV_KEYS
    assert MATERIALS_PRICE_BASIS_KEY not in MATERIALS_V2_SEARCH_EAV_KEYS
    assert "condition" not in MATERIALS_V2_SEARCH_EAV_KEYS
    assert "geo" in MATERIALS_V2_SEARCH_ALLOWLIST
    assert "region" not in MATERIALS_V2_SEARCH_EAV_KEYS


def test_materials_search_filters_no_forbidden() -> None:
    for slug, rows in build_materials_v2_search_filters().items():
        keys = {r[0] for r in rows}
        assert keys == MATERIALS_V2_SEARCH_EAV_KEYS, slug
        assert keys.isdisjoint(_FORBIDDEN_SEARCH), slug
        assert keys.isdisjoint(MATERIALS_CREATE_FORBIDDEN), slug
        assert keys.isdisjoint(MATERIALS_V2_SEARCH_EXCLUDE & keys), slug


def test_materials_search_seller_independent_contract() -> None:
    assert MATERIALS_SELLER_TARGET == _INDEPENDENT_SELLER
    banned = ("Оптовик", "Компания", "Импортёр", "Производитель", "Поставщик")
    for bad in banned:
        assert bad not in MATERIALS_SELLER_TARGET
    for slug, rows in build_materials_v2_search_filters().items():
        opts = _options_for(rows, MATERIALS_SELLER_KEY)
        labels = tuple(o.get("label") or o.get("value") for o in opts)
        assert labels == _INDEPENDENT_SELLER, slug


def test_materials_search_kind_options_match_create_per_l2() -> None:
    cores = build_materials_v2_core_fields()
    filters = build_materials_v2_search_filters()
    for section_key, slug in MATERIALS_V2_SECTION_SLUGS.items():
        create_kinds = {
            c["value"]
            for c in next(r for r in cores[slug] if r[0] == MATERIALS_KIND_KEY)[5][
                "choices"
            ]
        }
        search_kinds = {
            o["value"] for o in _options_for(filters[slug], MATERIALS_KIND_KEY)
        }
        assert search_kinds == create_kinds
        assert len(search_kinds) > 0
        assert set(MATERIALS_V2_SECTION_KINDS[section_key]) == create_kinds


def test_materials_all_117_search_audit() -> None:
    rows = materials_v2_all_search_kind_audit()
    assert len(rows) == 117
    for row in rows:
        assert row["search_materials_kind"] == "YES"
        assert row["search_seller"] == "YES"
        assert row["search_geo"] == "YES"
        assert row["search_condition"] == "NO"
        assert row["search_price_basis"] == "NO"
        assert row["search_price"] == "NO"
        assert row["search_quantity"] == "NO"
        assert row["search_tech"] == "NO"
        assert row["retired_resurrected"] is False
        assert row["ownership"] == "MATERIALS"
        assert MATERIALS_PRICE_BASIS_KEY not in row["visible_search_keys"]
        assert "condition" not in row["visible_search_keys"]


def test_materials_search_builder_idempotent() -> None:
    a = build_materials_v2_search_filters()
    b = build_materials_v2_search_filters()
    assert json.dumps(a, default=str, ensure_ascii=False) == json.dumps(
        b, default=str, ensure_ascii=False
    )


def test_materials_no_retired_slugs_in_search_map() -> None:
    filters = build_materials_v2_search_filters()
    assert set(filters).isdisjoint(MATERIALS_V2_RETIRED_SLUGS)
    assert "materials-textile" not in filters
    assert "materials-metal" not in filters
    assert "materials-chemical" not in filters
    assert "materials-import-i-optovye-postavki-syrya" not in filters


def test_food_tara_gap_still_open() -> None:
    assert FOOD_TARA_GAP_STATUS == "STILL_OPEN"
    kinds = {r["kind"] for r in materials_v2_all_search_kind_audit()}
    assert "Пищевая тара" not in kinds
    assert "Tara" not in kinds


@pytest.mark.asyncio
async def test_materials_search_filters_in_db_and_intelligence(client) -> None:
    await engine.dispose()
    expected = build_materials_v2_search_filters()
    async with async_session_maker() as session:
        for slug in sorted(MATERIALS_V2_RETIRED_SLUGS):
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

        for slug in sorted(MATERIALS_V2_CANONICAL_SLUGS):
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
            assert MATERIALS_PRICE_BASIS_KEY not in {r.filter_key for r in rows}
            assert "condition" not in {r.filter_key for r in rows}
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
            assert MATERIALS_KIND_KEY in keys
            assert MATERIALS_SELLER_KEY in keys
            assert MATERIALS_PRICE_BASIS_KEY not in keys
            assert "condition" not in keys
            kind_filter = next(
                f for f in body["filters"] if f["filter_key"] == MATERIALS_KIND_KEY
            )
            assert kind_filter["label"] == MATERIALS_KIND_LABEL
            core_keys = {f["field_key"] for f in body.get("core_fields") or []}
            assert MATERIALS_KIND_KEY in core_keys
            assert MATERIALS_PRICE_BASIS_KEY in core_keys
            assert "condition" not in core_keys


def _auth_as(user_id: int) -> None:
    now = datetime.now(UTC)

    async def _user() -> UserRead:
        return UserRead(
            id=user_id,
            phone="+79001234567",
            full_name="MaterialsSearchParity",
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
              :lid, '/media/test/materials-pb.jpg', 0, false,
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
async def test_materials_create_search_parity_cases_a_e_and_basis_isolation(
    client,
) -> None:
    """Real Create API → Search FOUND/NOT FOUND + price_basis isolation."""
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

            fabric_id = await _cid("materials-tkani-i-tekstilnoe-syre")
            metal_id = await _cid("materials-metally-metallicheskoe-syre")
            pack_id = await _cid("materials-upakovochnye-materialy")
            food_id = await _cid("materials-pischevoe-syre-i-ingredienty")
            other_id = await _cid("materials-prochee-syre-dlya-proizvodstva")

        shared_geo = {
            "region": "Чуйская область",
            "city": "Бишкек",
        }

        lid_a = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=fabric_id,
            title="PKG-B mat cotton A",
            fields={
                MATERIALS_KIND_KEY: "Хлопковые ткани",
                MATERIALS_SELLER_KEY: "Частное лицо",
                MATERIALS_PRICE_BASIS_KEY: "м",
                "contact_methods": "Чат + телефон",
                "negotiable": "Есть торг",
                **shared_geo,
            },
            price="150",
        )
        created_ids.append(lid_a)

        lid_b = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=metal_id,
            title="PKG-B mat sheet B",
            fields={
                MATERIALS_KIND_KEY: "Листовой прокат",
                MATERIALS_SELLER_KEY: "Магазин",
                MATERIALS_PRICE_BASIS_KEY: "кг",
                "contact_methods": "Только чат",
                "negotiable": "Без торга",
                **shared_geo,
            },
            price="95",
        )
        created_ids.append(lid_b)

        lid_c = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=pack_id,
            title="PKG-B mat stretch C",
            fields={
                MATERIALS_KIND_KEY: "Стретч-плёнка",
                MATERIALS_SELLER_KEY: "Другой",
                MATERIALS_PRICE_BASIS_KEY: "рулон",
                "contact_methods": "Чат + Wapp",
                **shared_geo,
            },
        )
        created_ids.append(lid_c)

        lid_d = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=food_id,
            title="PKG-B mat gelatin D",
            fields={
                MATERIALS_KIND_KEY: "Желатин",
                MATERIALS_SELLER_KEY: "Частное лицо",
                MATERIALS_PRICE_BASIS_KEY: "кг",
                "contact_methods": "Только телефон",
                **shared_geo,
            },
        )
        created_ids.append(lid_d)

        lid_e = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=other_id,
            title="PKG-B mat scrap E",
            fields={
                MATERIALS_KIND_KEY: "Вторсырьё",
                MATERIALS_SELLER_KEY: "Частное лицо",
                "contact_methods": "Чат + Тел. + Wapp",
                **shared_geo,
            },
        )
        created_ids.append(lid_e)

        lid_basis = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=fabric_id,
            title="PKG-B mat basis yes",
            fields={
                MATERIALS_KIND_KEY: "Шёлк",
                MATERIALS_SELLER_KEY: "Магазин",
                MATERIALS_PRICE_BASIS_KEY: "кг",
                "contact_methods": "Только чат",
                **shared_geo,
            },
        )
        created_ids.append(lid_basis)
        lid_nobasis = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=fabric_id,
            title="PKG-B mat basis no",
            fields={
                MATERIALS_KIND_KEY: "Шёлк",
                MATERIALS_SELLER_KEY: "Магазин",
                "contact_methods": "Только чат",
                **shared_geo,
            },
        )
        created_ids.append(lid_nobasis)

        # A FOUND
        ids = await _http_ids(
            client,
            category_id=fabric_id,
            attrs={
                MATERIALS_KIND_KEY: "Хлопковые ткани",
                MATERIALS_SELLER_KEY: "Частное лицо",
            },
        )
        assert lid_a in ids
        # wrong kind NOT FOUND
        miss = await _http_ids(
            client,
            category_id=fabric_id,
            attrs={
                MATERIALS_KIND_KEY: "Шёлк",
                MATERIALS_SELLER_KEY: "Частное лицо",
            },
        )
        assert lid_a not in miss

        # B FOUND without price_basis filter
        ids = await _http_ids(
            client,
            category_id=metal_id,
            attrs={
                MATERIALS_KIND_KEY: "Листовой прокат",
                MATERIALS_SELLER_KEY: "Магазин",
            },
        )
        assert lid_b in ids

        # C packaging FOUND
        ids = await _http_ids(
            client,
            category_id=pack_id,
            attrs={
                MATERIALS_KIND_KEY: "Стретч-плёнка",
                MATERIALS_SELLER_KEY: "Другой",
            },
        )
        assert lid_c in ids

        # D industrial food ingredient stays Materials
        ids = await _http_ids(
            client,
            category_id=food_id,
            attrs={
                MATERIALS_KIND_KEY: "Желатин",
                MATERIALS_SELLER_KEY: "Частное лицо",
            },
        )
        assert lid_d in ids
        async with async_session_maker() as session:
            cat = (
                await session.execute(select(Category).where(Category.id == food_id))
            ).scalar_one()
            assert cat.slug.startswith("materials-")

        # E scrap FOUND, no Condition
        ids = await _http_ids(
            client,
            category_id=other_id,
            attrs={
                MATERIALS_KIND_KEY: "Вторсырьё",
                MATERIALS_SELLER_KEY: "Частное лицо",
            },
        )
        assert lid_e in ids

        # price_basis isolation — both discoverable
        silk = await _http_ids(
            client,
            category_id=fabric_id,
            attrs={
                MATERIALS_KIND_KEY: "Шёлк",
                MATERIALS_SELLER_KEY: "Магазин",
            },
        )
        assert lid_basis in silk
        assert lid_nobasis in silk

        # Facets self-exclusion smoke
        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": fabric_id,
                "limit": 1,
                "facets": f"{MATERIALS_KIND_KEY},{MATERIALS_SELLER_KEY}",
                "attrs": json.dumps(
                    {MATERIALS_KIND_KEY: "Хлопковые ткани"},
                    ensure_ascii=False,
                ),
            },
        )
        assert resp.status_code == 200, resp.text
        facets = resp.json().get("facets") or {}
        assert MATERIALS_KIND_KEY in facets or MATERIALS_SELLER_KEY in facets

        detail = await client.get(f"/api/v1/listings/{lid_a}")
        assert detail.status_code == 200
        dfields = detail.json().get("fields") or {}
        assert dfields.get(MATERIALS_KIND_KEY) == "Хлопковые ткани"
        assert dfields.get(MATERIALS_PRICE_BASIS_KEY) == "м"
        assert "condition" not in dfields

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
                        WHERE c.slug LIKE 'materials-%'
                          AND l.title LIKE 'PKG-B mat%'
                        """
                    )
                )
            ).scalar_one()
            assert int(left or 0) == 0
