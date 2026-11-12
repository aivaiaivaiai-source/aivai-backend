"""Medical Goods V2 Package B — Search SoT + Create↔Search parity."""
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
from app.seeds.medical_v2 import (
    LICENSED_MEDICINES_BANNED,
    MED_CONDITION_KEY,
    MED_KIND_KEY,
    MED_SELLER_KEY,
    MEDICAL_CREATE_FORBIDDEN,
    MEDICAL_LEGACY_INCOMPLETE_LISTING_ID,
    MEDICAL_SELLER_TARGET,
    MEDICAL_V2_CANONICAL_SLUGS,
    MEDICAL_V2_EXPECTED_L2_COUNT,
    MEDICAL_V2_RETIRED_SLUGS,
    MEDICAL_V2_RETIRED_SUPPLEMENT_KINDS,
    MEDICAL_V2_SEARCH_ALLOWLIST,
    MEDICAL_V2_SEARCH_EAV_KEYS,
    MEDICAL_V2_SEARCH_EXCLUDE,
    MEDICAL_V2_SUPPLEMENTS_SLUG,
    build_medical_v2_core_fields,
    build_medical_v2_search_filters,
    medical_v2_all_search_kind_audit,
    medical_v2_assert_package_a_contracts,
    medical_v2_assert_package_b_contracts,
    medical_v2_condition_no_kinds,
    medical_v2_condition_yes_kinds,
    medical_v2_section_kinds,
)

_INDEPENDENT_SELLER = ("Частное лицо", "Магазин", "Другой")
_INDEPENDENT_CONDITION = ("Новое", "Б/у")
_INDEPENDENT_CONDITION_YES = frozenset(medical_v2_condition_yes_kinds())
_INDEPENDENT_CONDITION_NO = frozenset(medical_v2_condition_no_kinds())
_FORBIDDEN_SEARCH = frozenset(
    {
        "price",
        "negotiable",
        "contact_methods",
        "brand",
        "model",
        "dosage",
        "expiry",
        "quantity",
        "power",
        "voltage",
        "capacity",
        "currency",
    }
)
_REPR_SLUGS = (
    "medical-meditsinskie-pribory",
    "medical-rashodnye-med-materialy",
    "medical-meditsinskaya-odezhda",
    "medical-optika-i-tovary-dlya-zreniya",
    "medical-aptechki-i-pervaya-pomosch",
)
FORENSIC_LISTING_ID = MEDICAL_LEGACY_INCOMPLETE_LISTING_ID


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


def test_medical_package_a_still_locked() -> None:
    medical_v2_assert_package_a_contracts()
    assert (
        len(MEDICAL_V2_CANONICAL_SLUGS) == MEDICAL_V2_EXPECTED_L2_COUNT == 15
    )
    assert MEDICAL_V2_SUPPLEMENTS_SLUG in MEDICAL_V2_RETIRED_SLUGS
    cores = build_medical_v2_core_fields()
    assert len(cores) == 15
    for slug, fields in cores.items():
        keys = {r[0] for r in fields}
        assert MED_KIND_KEY in keys
        assert "price" in keys
        assert "brand" not in keys
        assert "dosage" not in keys


def test_medical_package_b_contracts() -> None:
    medical_v2_assert_package_b_contracts()


def test_medical_search_filters_cover_all_canonical_l2() -> None:
    filters = build_medical_v2_search_filters()
    assert set(filters) == MEDICAL_V2_CANONICAL_SLUGS
    assert len(filters) == 15


def test_medical_search_eav_keys_are_short_allowlist() -> None:
    assert MEDICAL_V2_SEARCH_EAV_KEYS <= MEDICAL_V2_SEARCH_ALLOWLIST
    assert MED_KIND_KEY in MEDICAL_V2_SEARCH_EAV_KEYS
    assert MED_SELLER_KEY in MEDICAL_V2_SEARCH_EAV_KEYS
    assert MED_CONDITION_KEY in MEDICAL_V2_SEARCH_EAV_KEYS
    assert "price" not in MEDICAL_V2_SEARCH_EAV_KEYS
    assert "region" not in MEDICAL_V2_SEARCH_EAV_KEYS
    assert "geo" in MEDICAL_V2_SEARCH_ALLOWLIST


def test_medical_search_filters_no_forbidden() -> None:
    for slug, rows in build_medical_v2_search_filters().items():
        keys = {r[0] for r in rows}
        assert keys <= MEDICAL_V2_SEARCH_EAV_KEYS, slug
        assert MED_KIND_KEY in keys
        assert MED_SELLER_KEY in keys
        assert keys.isdisjoint(_FORBIDDEN_SEARCH), slug
        assert keys.isdisjoint(MEDICAL_CREATE_FORBIDDEN), slug
        assert keys.isdisjoint(MEDICAL_V2_SEARCH_EXCLUDE & keys), slug


def test_medical_search_seller_independent_contract() -> None:
    assert MEDICAL_SELLER_TARGET == _INDEPENDENT_SELLER
    assert "Аптека" not in MEDICAL_SELLER_TARGET
    assert "Компания" not in MEDICAL_SELLER_TARGET
    for slug, rows in build_medical_v2_search_filters().items():
        opts = _options_for(rows, MED_SELLER_KEY)
        labels = tuple(o.get("label") or o.get("value") for o in opts)
        assert labels == _INDEPENDENT_SELLER, slug


def test_medical_search_kind_options_match_create_per_l2() -> None:
    cores = build_medical_v2_core_fields()
    filters = build_medical_v2_search_filters()
    for slug in MEDICAL_V2_CANONICAL_SLUGS:
        create_kinds = {
            c["value"]
            for c in next(r for r in cores[slug] if r[0] == MED_KIND_KEY)[5][
                "choices"
            ]
        }
        search_kinds = {
            o["value"] for o in _options_for(filters[slug], MED_KIND_KEY)
        }
        assert search_kinds == create_kinds
        assert len(search_kinds) > 0
        assert set(medical_v2_section_kinds(slug)) == create_kinds
        assert search_kinds.isdisjoint(LICENSED_MEDICINES_BANNED)
        assert search_kinds.isdisjoint(MEDICAL_V2_RETIRED_SUPPLEMENT_KINDS)


def test_medical_search_condition_depends_on_independent_allowlist() -> None:
    assert len(_INDEPENDENT_CONDITION_YES) == 53
    assert len(_INDEPENDENT_CONDITION_NO) == 27
    assert "Шприцы" in _INDEPENDENT_CONDITION_NO
    assert "Медицинские халаты" in _INDEPENDENT_CONDITION_NO
    assert "Контактные линзы" in _INDEPENDENT_CONDITION_NO
    assert "Растворы для линз" in _INDEPENDENT_CONDITION_NO
    assert "Автомобильные аптечки" in _INDEPENDENT_CONDITION_NO
    assert "Очки для зрения" in _INDEPENDENT_CONDITION_YES
    assert "Оправы" in _INDEPENDENT_CONDITION_YES
    assert "Тонометры" in _INDEPENDENT_CONDITION_YES
    filters = build_medical_v2_search_filters()
    for slug, rows in filters.items():
        keys = {r[0] for r in rows}
        section_kinds = set(medical_v2_section_kinds(slug))
        cond_in_section = section_kinds & _INDEPENDENT_CONDITION_YES
        if not cond_in_section:
            assert MED_CONDITION_KEY not in keys, slug
            continue
        assert MED_CONDITION_KEY in keys, slug
        opts = _options_for(rows, MED_CONDITION_KEY)
        labels = tuple(o.get("label") or o.get("value") for o in opts)
        assert labels == _INDEPENDENT_CONDITION, slug
        dep = _depends_values(rows, MED_CONDITION_KEY)
        if dep is None:
            assert cond_in_section == section_kinds
        else:
            assert dep == cond_in_section
            assert dep.isdisjoint(_INDEPENDENT_CONDITION_NO)


def test_medical_all_80_search_audit() -> None:
    rows = medical_v2_all_search_kind_audit()
    assert len(rows) == 80
    for row in rows:
        assert row["search_med_kind"] == "YES"
        assert row["search_seller"] == "YES"
        assert row["search_geo"] == "YES"
        assert row["search_brand"] == "NO"
        assert row["search_model"] == "NO"
        assert row["search_dosage"] == "NO"
        assert row["search_expiry"] == "NO"
        assert row["search_price"] == "NO"
        assert row["retired_resurrected"] is False
        assert row["ownership"] == "MEDICAL"
        if row["kind"] in _INDEPENDENT_CONDITION_NO:
            assert row["search_condition"] == "NO"
            assert MED_CONDITION_KEY not in row["visible_search_keys"]
        else:
            assert row["search_condition"] == "YES"
            assert MED_CONDITION_KEY in row["visible_search_keys"]


def test_medical_search_builder_idempotent() -> None:
    a = build_medical_v2_search_filters()
    b = build_medical_v2_search_filters()
    assert json.dumps(a, default=str, ensure_ascii=False) == json.dumps(
        b, default=str, ensure_ascii=False
    )


def test_medical_no_retired_slugs_in_search_map() -> None:
    filters = build_medical_v2_search_filters()
    assert set(filters).isdisjoint(MEDICAL_V2_RETIRED_SLUGS)
    assert MEDICAL_V2_SUPPLEMENTS_SLUG not in filters
    assert "medical-devices" not in filters
    assert "medical-care" not in filters


@pytest.mark.asyncio
async def test_medical_search_filters_in_db_and_intelligence(client) -> None:
    await engine.dispose()
    expected = build_medical_v2_search_filters()
    async with async_session_maker() as session:
        for slug in sorted(MEDICAL_V2_RETIRED_SLUGS):
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

        for slug in sorted(MEDICAL_V2_CANONICAL_SLUGS):
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
            assert "dosage" not in {r.filter_key for r in rows}

    async with async_session_maker() as session:
        for slug in _REPR_SLUGS:
            cat = (
                await session.execute(select(Category).where(Category.slug == slug))
            ).scalar_one()
            resp = await client.get(f"/api/v1/categories/intelligence/{cat.id}")
            assert resp.status_code == 200, slug
            body = resp.json()
            keys = {f["filter_key"] for f in body.get("filters") or []}
            assert MED_KIND_KEY in keys
            assert MED_SELLER_KEY in keys
            assert "brand" not in keys and "price" not in keys
            kind_filter = next(
                f for f in body["filters"] if f["filter_key"] == MED_KIND_KEY
            )
            assert kind_filter["label"] == "Товар"
            core_keys = {f["field_key"] for f in body.get("core_fields") or []}
            assert MED_KIND_KEY in core_keys
            assert "price" in core_keys


def _auth_as(user_id: int) -> None:
    now = datetime.now(UTC)

    async def _user() -> UserRead:
        return UserRead(
            id=user_id,
            phone="+79001234567",
            full_name="MedicalSearchParity",
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
              :lid, '/media/test/medical-pb.jpg', 0, false,
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
            "price": "2500",
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
async def test_medical_create_search_parity_cases_a_e_and_3154(client) -> None:
    """Real Create API → Search FOUND/NOT FOUND + forensic 3154 boundary."""
    await engine.dispose()
    created_ids: list[int] = []
    forensic_existed = False
    forensic_eav_before: dict[str, str] = {}
    forensic_category_id: int | None = None
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

            devices_id = await _cid("medical-meditsinskie-pribory")
            consumables_id = await _cid("medical-rashodnye-med-materialy")
            clothing_id = await _cid("medical-meditsinskaya-odezhda")
            optics_id = await _cid("medical-optika-i-tovary-dlya-zreniya")
            forensic = (
                await session.execute(
                    select(Listing).where(Listing.id == FORENSIC_LISTING_ID)
                )
            ).scalar_one_or_none()
            forensic_existed = forensic is not None
            if forensic_existed:
                forensic_category_id = int(forensic.category_id)
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
                forensic_eav_before = {r[0]: (r[1] or "") for r in eav_rows}

        # A durable device — Condition YES
        lid_a = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=devices_id,
            title="PKG-B med tonometr A",
            fields={
                MED_KIND_KEY: "Тонометры",
                MED_SELLER_KEY: "Частное лицо",
                MED_CONDITION_KEY: "Б/у",
                "contact_methods": "Только чат",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
        )
        created_ids.append(lid_a)
        found = await client.get(
            "/api/v1/listings",
            params={
                "category_id": devices_id,
                "attrs": json.dumps(
                    {
                        MED_KIND_KEY: "Тонометры",
                        MED_CONDITION_KEY: "Б/у",
                        MED_SELLER_KEY: "Частное лицо",
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
                "category_id": devices_id,
                "attrs": json.dumps(
                    {
                        MED_KIND_KEY: "Тонометры",
                        MED_CONDITION_KEY: "Новое",
                    },
                    ensure_ascii=False,
                ),
                "limit": 40,
            },
        )
        assert miss.status_code == 200
        miss_ids = [int(i["id"]) for i in miss.json().get("items") or []]
        assert lid_a not in miss_ids

        # B consumable Condition NO
        lid_b = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=consumables_id,
            title="PKG-B med syringes B",
            fields={
                MED_KIND_KEY: "Шприцы",
                MED_SELLER_KEY: "Магазин",
                "contact_methods": "Только чат",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
        )
        created_ids.append(lid_b)
        hit_b = await client.get(
            "/api/v1/listings",
            params={
                "category_id": consumables_id,
                "attrs": json.dumps(
                    {
                        MED_KIND_KEY: "Шприцы",
                        MED_SELLER_KEY: "Магазин",
                    },
                    ensure_ascii=False,
                ),
                "city": "Бишкек",
                "limit": 40,
            },
        )
        assert hit_b.status_code == 200
        assert lid_b in [int(i["id"]) for i in hit_b.json().get("items") or []]
        cons_filters = build_medical_v2_search_filters()[
            "medical-rashodnye-med-materialy"
        ]
        # Entire consumables section is Condition NO → no condition filter row
        assert MED_CONDITION_KEY not in {r[0] for r in cons_filters}

        # C medical clothing — no Condition
        lid_c = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=clothing_id,
            title="PKG-B med gown C",
            fields={
                MED_KIND_KEY: "Медицинские халаты",
                MED_SELLER_KEY: "Другой",
                "contact_methods": "Чат + телефон",
                "region": "Ошская область",
                "city": "Ош",
            },
        )
        created_ids.append(lid_c)
        hit_c = await client.get(
            "/api/v1/listings",
            params={
                "category_id": clothing_id,
                "attrs": json.dumps(
                    {
                        MED_KIND_KEY: "Медицинские халаты",
                        MED_SELLER_KEY: "Другой",
                    },
                    ensure_ascii=False,
                ),
                "limit": 40,
            },
        )
        assert hit_c.status_code == 200
        assert lid_c in [int(i["id"]) for i in hit_c.json().get("items") or []]
        clothing_filters = build_medical_v2_search_filters()[
            "medical-meditsinskaya-odezhda"
        ]
        assert MED_CONDITION_KEY not in {r[0] for r in clothing_filters}

        # D optics — reusable YES + consumable NO
        lid_d_yes = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=optics_id,
            title="PKG-B med glasses D",
            fields={
                MED_KIND_KEY: "Очки для зрения",
                MED_SELLER_KEY: "Частное лицо",
                MED_CONDITION_KEY: "Б/у",
                "contact_methods": "Только телефон",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
        )
        created_ids.append(lid_d_yes)
        lid_d_no = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=optics_id,
            title="PKG-B med lenses D",
            fields={
                MED_KIND_KEY: "Контактные линзы",
                MED_SELLER_KEY: "Магазин",
                "contact_methods": "Только чат",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
        )
        created_ids.append(lid_d_no)
        optics_filters = build_medical_v2_search_filters()[
            "medical-optika-i-tovary-dlya-zreniya"
        ]
        dep = _depends_values(optics_filters, MED_CONDITION_KEY)
        assert dep is not None
        assert "Очки для зрения" in dep
        assert "Оправы" in dep
        assert "Контактные линзы" not in dep
        assert "Растворы для линз" not in dep
        hit_d_yes = await client.get(
            "/api/v1/listings",
            params={
                "category_id": optics_id,
                "attrs": json.dumps(
                    {
                        MED_KIND_KEY: "Очки для зрения",
                        MED_CONDITION_KEY: "Б/у",
                    },
                    ensure_ascii=False,
                ),
                "limit": 40,
            },
        )
        assert hit_d_yes.status_code == 200
        assert lid_d_yes in [
            int(i["id"]) for i in hit_d_yes.json().get("items") or []
        ]
        hit_d_no = await client.get(
            "/api/v1/listings",
            params={
                "category_id": optics_id,
                "attrs": json.dumps(
                    {MED_KIND_KEY: "Контактные линзы"},
                    ensure_ascii=False,
                ),
                "limit": 40,
            },
        )
        assert hit_d_no.status_code == 200
        assert lid_d_no in [
            int(i["id"]) for i in hit_d_no.json().get("items") or []
        ]

        # E electronic medical device stays in Medical
        lid_e = await _create_activate(
            client,
            owner_id=owner_id,
            category_id=devices_id,
            title="PKG-B med pulseox E",
            fields={
                MED_KIND_KEY: "Пульсоксиметры",
                MED_SELLER_KEY: "Частное лицо",
                MED_CONDITION_KEY: "Новое",
                "contact_methods": "Только чат",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
        )
        created_ids.append(lid_e)
        hit_e = await client.get(
            "/api/v1/listings",
            params={
                "category_id": devices_id,
                "attrs": json.dumps(
                    {MED_KIND_KEY: "Пульсоксиметры"},
                    ensure_ascii=False,
                ),
                "limit": 40,
            },
        )
        assert hit_e.status_code == 200
        assert lid_e in [int(i["id"]) for i in hit_e.json().get("items") or []]

        # Facets self-exclusion smoke
        facets = await client.get(
            "/api/v1/listings",
            params={
                "category_id": devices_id,
                "attrs": json.dumps(
                    {MED_KIND_KEY: "Тонометры"},
                    ensure_ascii=False,
                ),
                "facets": f"{MED_KIND_KEY},{MED_SELLER_KEY},{MED_CONDITION_KEY}",
                "limit": 1,
            },
        )
        assert facets.status_code == 200
        body = facets.json()
        assert "total" in body
        assert isinstance(body.get("facets"), dict)

        # 3154: category-only may find; med_kind filter excludes; EAV untouched
        if forensic_existed and forensic_category_id is not None:
            cat_only = await client.get(
                "/api/v1/listings",
                params={"category_id": forensic_category_id, "limit": 100},
            )
            assert cat_only.status_code == 200
            filtered = await client.get(
                "/api/v1/listings",
                params={
                    "category_id": forensic_category_id,
                    "attrs": json.dumps(
                        {MED_KIND_KEY: "Тонометры"},
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
            assert MED_KIND_KEY not in eav_now
            assert MED_SELLER_KEY not in eav_now
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
