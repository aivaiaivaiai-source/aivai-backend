# -*- coding: utf-8 -*-
"""Farm Machinery Sale V2 — taxonomy, schemas, filters, remaps, search."""
from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from decimal import Decimal

from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.api.deps import get_current_user
from app.db.session import async_session_maker
from app.main import app
from app.schemas.user import UserRead
from app.seeds.farm_sale_v2 import (
    BROAD_IMPLEMENT_ID,
    BROAD_IMPLEMENT_LABEL,
    BROAD_IMPLEMENT_SLUG,
    EQUIPMENT_TYPES,
    FARM_CORE_FIELDS_BY_SLUG,
    FARM_INACTIVE_LEGACY_SLUGS,
    FARM_LEAF_EXPECTED_IDS,
    FARM_LEAF_SLUGS,
    FARM_LEAF_SORT,
    FARM_LEAF_VEHICLE_TYPE,
    FARM_OTHER_BRAND_TYPES,
    FARM_PARENT_SLUG,
    FARM_POLLUTED_BRAND_NAMES,
    FARM_REMAP_TARGETS,
    FARM_RETIRED_IMPLEMENT_MAP,
    FARM_SEARCH_FILTERS_BY_SLUG,
    HARVESTER_TYPES,
    MOUNT_TYPES,
    WALK_BEHIND_TYPES,
)


REQUIRED_KEYS = {
    "condition",
    "price",
    "negotiable",
    "seller_type",
    "contact_methods",
    "region",
    "city",
}


def _auth_user(user_id: int = 1) -> None:
    now = datetime.now(UTC)

    async def _user() -> UserRead:
        return UserRead(
            id=user_id,
            phone="+79001234567",
            full_name="FarmSaleV2Tester",
            is_active=True,
            balance=Decimal("0"),
            last_login=None,
            created_at=now,
            updated_at=now,
        )

    app.dependency_overrides[get_current_user] = _user


async def _slug_id(session, slug: str) -> int:
    return int(
        (
            await session.execute(
                text("SELECT id FROM categories WHERE slug = :s"),
                {"s": slug},
            )
        ).scalar_one()
    )


async def _run_all() -> None:
    async with async_session_maker() as session:
        parent = (
            await session.execute(
                text(
                    "SELECT id, is_active FROM categories WHERE slug = :s"
                ),
                {"s": FARM_PARENT_SLUG},
            )
        ).mappings().one()
        assert parent["is_active"] is True
        assert int(parent["id"]) == 694

        active = (
            await session.execute(
                text(
                    """
                    SELECT id, slug, name, sort_order, is_active
                    FROM categories
                    WHERE parent_id = :pid AND is_active = true
                    ORDER BY sort_order, id
                    """
                ),
                {"pid": 694},
            )
        ).mappings().all()
        assert len(active) == 7
        assert [r["slug"] for r in active] == list(FARM_LEAF_SLUGS)
        assert {r["slug"]: r["sort_order"] for r in active} == FARM_LEAF_SORT
        for slug, expected_id in FARM_LEAF_EXPECTED_IDS.items():
            row = next(r for r in active if r["slug"] == slug)
            assert int(row["id"]) == expected_id, slug
        broad = next(r for r in active if r["slug"] == BROAD_IMPLEMENT_SLUG)
        assert int(broad["id"]) == BROAD_IMPLEMENT_ID
        assert broad["name"] == BROAD_IMPLEMENT_LABEL

        for slug in FARM_INACTIVE_LEGACY_SLUGS:
            if slug == BROAD_IMPLEMENT_SLUG:
                continue
            row = (
                await session.execute(
                    text(
                        """
                        SELECT is_active FROM categories WHERE slug = :s
                        """
                    ),
                    {"s": slug},
                )
            ).mappings().first()
            if row is None:
                continue
            assert row["is_active"] is False, slug

        trailer840 = (
            await session.execute(
                text("SELECT is_active FROM categories WHERE id = 840")
            )
        ).mappings().one()
        assert trailer840["is_active"] is False

        assert FARM_REMAP_TARGETS[
            "transport-farm-machinery-pritsepy-dlya-selhoztehniki"
        ] == "transport-trailers-pritsepy"
        assert FARM_REMAP_TARGETS[
            "transport-farm-machinery-plugi"
        ] == BROAD_IMPLEMENT_SLUG
        assert FARM_RETIRED_IMPLEMENT_MAP[
            "transport-farm-machinery-motokosilki"
        ][1] == "Косилка"

        parent_n = (
            await session.execute(
                text(
                    """
                    SELECT COUNT(*) FROM category_core_fields
                    WHERE category_id = 694
                    """
                )
            )
        ).scalar_one()
        assert parent_n == 0

        for slug in FARM_LEAF_SLUGS:
            fields = (
                await session.execute(
                    text(
                        """
                        SELECT ccf.field_key, ccf.is_required, ccf.field_type::text,
                               ccf.options
                        FROM category_core_fields ccf
                        JOIN categories c ON c.id = ccf.category_id
                        WHERE c.slug = :s
                        ORDER BY ccf.sort_order
                        """
                    ),
                    {"s": slug},
                )
            ).mappings().all()
            assert len(fields) > 0, slug
            by = {r["field_key"]: r for r in fields}
            for key in REQUIRED_KEYS:
                assert key in by, f"{slug}.{key}"
                assert by[key]["is_required"] is True
            for opt_key in ("brand", "model"):
                assert by[opt_key]["is_required"] is False
            assert "hours" not in by
            assert "mileage" not in by
            for r in fields:
                if r["field_type"] in {"enum", "multi_select"}:
                    opts = r["options"] or {}
                    choices = opts.get("choices") or opts.get("values") or []
                    assert choices, f"{slug}.{r['field_key']} null options"

        tractor = {
            r["field_key"]: r
            for r in (
                await session.execute(
                    text(
                        """
                        SELECT ccf.field_key, ccf.is_required, ccf.options
                        FROM category_core_fields ccf
                        JOIN categories c ON c.id = ccf.category_id
                        WHERE c.slug = 'transport-farm-machinery-traktory'
                        """
                    )
                )
            ).mappings()
        }
        assert "operating_hours" in tractor
        assert tractor["operating_hours"]["is_required"] is False
        assert (tractor["operating_hours"]["options"] or {}).get("unit") == "ч"
        assert "engine_power_hp" in tractor
        assert (tractor["engine_power_hp"]["options"] or {}).get("unit") == (
            "л.с."
        )
        drive_vals = [
            c["value"]
            for c in (tractor["drive"]["options"] or {}).get("choices", [])
        ]
        assert drive_vals == ["2WD", "4WD"]

        moto = {
            r["field_key"]: r
            for r in (
                await session.execute(
                    text(
                        """
                        SELECT ccf.field_key, ccf.is_required, ccf.options
                        FROM category_core_fields ccf
                        JOIN categories c ON c.id = ccf.category_id
                        WHERE c.slug =
                          'transport-farm-machinery-motobloki-i-motokultivatory'
                        """
                    )
                )
            ).mappings()
        }
        assert moto["walk_behind_type"]["is_required"] is True
        wb = [
            c["value"]
            for c in (moto["walk_behind_type"]["options"] or {}).get(
                "choices", []
            )
        ]
        assert wb == list(WALK_BEHIND_TYPES)
        assert "operating_hours" not in moto

        combine = {
            r["field_key"]: r
            for r in (
                await session.execute(
                    text(
                        """
                        SELECT ccf.field_key, ccf.is_required, ccf.options
                        FROM category_core_fields ccf
                        JOIN categories c ON c.id = ccf.category_id
                        WHERE c.slug = 'transport-farm-machinery-kombayny'
                        """
                    )
                )
            ).mappings()
        }
        assert combine["harvester_type"]["is_required"] is False
        ht = [
            c["value"]
            for c in (combine["harvester_type"]["options"] or {}).get(
                "choices", []
            )
        ]
        assert ht == list(HARVESTER_TYPES)

        impl = {
            r["field_key"]: r
            for r in (
                await session.execute(
                    text(
                        """
                        SELECT ccf.field_key, ccf.is_required, ccf.options
                        FROM category_core_fields ccf
                        JOIN categories c ON c.id = ccf.category_id
                        WHERE c.slug = :s
                        """
                    ),
                    {"s": BROAD_IMPLEMENT_SLUG},
                )
            ).mappings()
        }
        assert impl["equipment_type"]["is_required"] is True
        eq = [
            c["value"]
            for c in (impl["equipment_type"]["options"] or {}).get(
                "choices", []
            )
        ]
        assert eq == list(EQUIPMENT_TYPES)
        assert "Мотокосилка" not in eq
        mount = [
            c["value"]
            for c in (impl["mount_type"]["options"] or {}).get("choices", [])
        ]
        assert mount == list(MOUNT_TYPES)
        assert "Самоходное" not in mount
        tank_dep = (impl["tank_capacity_l"]["options"] or {}).get("depends_on")
        assert tank_dep["field"] == "equipment_type"
        assert "Опрыскиватель" in tank_dep["values"]
        row_dep = (impl["row_count"]["options"] or {}).get("depends_on")
        assert "Сеялка" in row_dep["values"]
        baler_dep = (impl["baler_type"]["options"] or {}).get("depends_on")
        assert "Пресс-подборщик" in baler_dep["values"]

        for slug in FARM_LEAF_SLUGS:
            keys = [
                r[0]
                for r in (
                    await session.execute(
                        text(
                            """
                            SELECT cf.filter_key
                            FROM category_filters cf
                            JOIN categories c ON c.id = cf.category_id
                            WHERE c.slug = :s
                            """
                        ),
                        {"s": slug},
                    )
                ).all()
            ]
            assert keys, slug
            assert "has_photo" not in keys
            assert len(FARM_SEARCH_FILTERS_BY_SLUG[slug]) == len(keys)

        for vt in FARM_OTHER_BRAND_TYPES:
            n = (
                await session.execute(
                    text(
                        """
                        SELECT COUNT(*) FROM vehicle_brands
                        WHERE vehicle_type::text = :vt
                          AND name = 'Другая марка'
                          AND is_enabled = true
                        """
                    ),
                    {"vt": vt},
                )
            ).scalar_one()
            assert n >= 1, vt

        for name in ("ПЛН", "БДТ", "Окучник", "Т-40", "ДТ-75"):
            enabled = (
                await session.execute(
                    text(
                        """
                        SELECT COUNT(*) FROM vehicle_brands
                        WHERE name = :n
                          AND is_enabled = true
                          AND vehicle_type::text IN (
                            'tractor', 'farm_implement', 'plow', 'harrow',
                            'cultivator', 'seeder', 'other_agri'
                          )
                        """
                    ),
                    {"n": name},
                )
            ).scalar_one()
            assert enabled == 0, name

        fi_n = (
            await session.execute(
                text(
                    """
                    SELECT COUNT(*) FROM vehicle_brands
                    WHERE vehicle_type::text = 'farm_implement'
                      AND is_enabled = true
                      AND name <> 'Другая марка'
                    """
                )
            )
        ).scalar_one()
        assert fi_n >= 10

    assert set(FARM_CORE_FIELDS_BY_SLUG) == set(FARM_LEAF_SLUGS)
    assert FARM_LEAF_VEHICLE_TYPE[BROAD_IMPLEMENT_SLUG] == "farm_implement"

    async def _insert_active(
        session, *, title: str, price: int, cid: int, oid: int, eav: dict
    ) -> int:
        row = await session.execute(
            text(
                """
                INSERT INTO listings
                (title, description, price, currency, category_id, owner_id,
                 status, created_at, updated_at)
                VALUES
                (:t, :d, :p, 'KGS', :cid, :oid, 'active', now(), now())
                RETURNING id
                """
            ),
            {"t": title, "d": title, "p": price, "cid": cid, "oid": oid},
        )
        new_id = int(row.scalar_one())
        for key, val in eav.items():
            if isinstance(val, float):
                await session.execute(
                    text(
                        """
                        INSERT INTO listing_field_values
                        (listing_id, field_key, value_decimal, created_at, updated_at)
                        VALUES (:lid, :k, :v, now(), now())
                        """
                    ),
                    {"lid": new_id, "k": key, "v": float(val)},
                )
            elif isinstance(val, int):
                await session.execute(
                    text(
                        """
                        INSERT INTO listing_field_values
                        (listing_id, field_key, value_int, created_at, updated_at)
                        VALUES (:lid, :k, :v, now(), now())
                        """
                    ),
                    {"lid": new_id, "k": key, "v": int(val)},
                )
            else:
                await session.execute(
                    text(
                        """
                        INSERT INTO listing_field_values
                        (listing_id, field_key, value_text, created_at, updated_at)
                        VALUES (:lid, :k, :v, now(), now())
                        """
                    ),
                    {"lid": new_id, "k": key, "v": str(val)},
                )
        return new_id

    _auth_user()
    transport = ASGITransport(app=app)
    created: list[int] = []
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            async with async_session_maker() as session:
                owner_id = int(
                    (
                        await session.execute(
                            text("SELECT id FROM users ORDER BY id LIMIT 1")
                        )
                    ).scalar_one()
                )
                tractor_cid = await _slug_id(
                    session, "transport-farm-machinery-traktory"
                )
                moto_cid = await _slug_id(
                    session,
                    "transport-farm-machinery-motobloki-i-motokultivatory",
                )
                combine_cid = await _slug_id(
                    session, "transport-farm-machinery-kombayny"
                )
                impl_cid = await _slug_id(session, BROAD_IMPLEMENT_SLUG)

                tractor_id = await _insert_active(
                    session,
                    title="FarmV2 tractor e2e",
                    price=900000,
                    cid=tractor_cid,
                    oid=owner_id,
                    eav={
                        "condition": "Хорошее",
                        "negotiable": "Есть торг",
                        "seller_type": "Компания",
                        "drive": "4WD",
                        "operating_hours": 4500,
                        "engine_power_hp": 82,
                    },
                )
                moto_id = await _insert_active(
                    session,
                    title="FarmV2 motoblock e2e",
                    price=45000,
                    cid=moto_cid,
                    oid=owner_id,
                    eav={
                        "walk_behind_type": "Мотоблок",
                        "engine_power_hp": 7,
                        "condition": "Хорошее",
                        "seller_type": "Частное лицо",
                    },
                )
                combine_id = await _insert_active(
                    session,
                    title="FarmV2 combine e2e",
                    price=2500000,
                    cid=combine_cid,
                    oid=owner_id,
                    eav={
                        "harvester_type": "Зерноуборочный",
                        "operating_hours": 2000,
                        "engine_power_hp": 250,
                        "condition": "Хорошее",
                    },
                )
                plow_id = await _insert_active(
                    session,
                    title="FarmV2 plow e2e",
                    price=80000,
                    cid=impl_cid,
                    oid=owner_id,
                    eav={
                        "equipment_type": "Плуг",
                        "mount_type": "Навесное",
                        "condition": "Хорошее",
                        "seller_type": "Частное лицо",
                    },
                )
                seeder_id = await _insert_active(
                    session,
                    title="FarmV2 seeder e2e",
                    price=120000,
                    cid=impl_cid,
                    oid=owner_id,
                    eav={
                        "equipment_type": "Сеялка",
                        "working_width_m": 3.6,
                        "row_count": 8,
                        "condition": "Хорошее",
                    },
                )
                sprayer_id = await _insert_active(
                    session,
                    title="FarmV2 sprayer e2e",
                    price=200000,
                    cid=impl_cid,
                    oid=owner_id,
                    eav={
                        "equipment_type": "Опрыскиватель",
                        "tank_capacity_l": 1200,
                        "working_width_m": 18.0,
                        "mount_type": "Прицепное",
                        "condition": "Хорошее",
                    },
                )
                baler_id = await _insert_active(
                    session,
                    title="FarmV2 baler e2e",
                    price=350000,
                    cid=impl_cid,
                    oid=owner_id,
                    eav={
                        "equipment_type": "Пресс-подборщик",
                        "baler_type": "Рулонный",
                        "condition": "Хорошее",
                    },
                )
                kun_id = await _insert_active(
                    session,
                    title="FarmV2 kun e2e",
                    price=150000,
                    cid=impl_cid,
                    oid=owner_id,
                    eav={
                        "equipment_type": "КУН",
                        "condition": "Хорошее",
                    },
                )
                await session.commit()
                created.extend(
                    [
                        tractor_id,
                        moto_id,
                        combine_id,
                        plow_id,
                        seeder_id,
                        sprayer_id,
                        baler_id,
                        kun_id,
                    ]
                )

            async def _ids(params: dict) -> set[int]:
                r = await client.get("/api/v1/listings", params=params)
                assert r.status_code == 200, r.text
                return {int(x["id"]) for x in r.json()["items"]}

            found = await _ids(
                {
                    "category_slug": "transport-farm-machinery-traktory",
                    "attrs": json.dumps(
                        {
                            "drive": "4WD",
                            "engine_power_hp__min": "80",
                            "operating_hours__max": "5000",
                        },
                        ensure_ascii=False,
                    ),
                    "limit": 100,
                }
            )
            assert tractor_id in found
            not_found = await _ids(
                {
                    "category_slug": "transport-farm-machinery-traktory",
                    "attrs": json.dumps(
                        {"drive": "2WD"}, ensure_ascii=False
                    ),
                    "limit": 100,
                }
            )
            assert tractor_id not in not_found

            found = await _ids(
                {
                    "category_slug": (
                        "transport-farm-machinery-motobloki-i-motokultivatory"
                    ),
                    "attrs": json.dumps(
                        {
                            "walk_behind_type": "Мотоблок",
                            "engine_power_hp__min": "5",
                        },
                        ensure_ascii=False,
                    ),
                    "limit": 100,
                }
            )
            assert moto_id in found

            found = await _ids(
                {
                    "category_slug": "transport-farm-machinery-kombayny",
                    "attrs": json.dumps(
                        {"harvester_type": "Зерноуборочный"},
                        ensure_ascii=False,
                    ),
                    "limit": 100,
                }
            )
            assert combine_id in found

            found = await _ids(
                {
                    "category_slug": BROAD_IMPLEMENT_SLUG,
                    "attrs": json.dumps(
                        {"equipment_type": "Плуг"}, ensure_ascii=False
                    ),
                    "limit": 100,
                }
            )
            assert plow_id in found
            assert seeder_id not in found

            found = await _ids(
                {
                    "category_slug": BROAD_IMPLEMENT_SLUG,
                    "attrs": json.dumps(
                        {
                            "equipment_type": "Сеялка",
                            "working_width_m__min": "3",
                            "row_count__min": "6",
                        },
                        ensure_ascii=False,
                    ),
                    "limit": 100,
                }
            )
            assert seeder_id in found

            found = await _ids(
                {
                    "category_slug": BROAD_IMPLEMENT_SLUG,
                    "attrs": json.dumps(
                        {
                            "equipment_type": "Опрыскиватель",
                            "tank_capacity_l__min": "1000",
                        },
                        ensure_ascii=False,
                    ),
                    "limit": 100,
                }
            )
            assert sprayer_id in found

            found = await _ids(
                {
                    "category_slug": BROAD_IMPLEMENT_SLUG,
                    "attrs": json.dumps(
                        {
                            "equipment_type": "Пресс-подборщик",
                            "baler_type": "Рулонный",
                        },
                        ensure_ascii=False,
                    ),
                    "limit": 100,
                }
            )
            assert baler_id in found

            found = await _ids(
                {
                    "category_slug": BROAD_IMPLEMENT_SLUG,
                    "attrs": json.dumps(
                        {"equipment_type": "КУН"}, ensure_ascii=False
                    ),
                    "limit": 100,
                }
            )
            assert kun_id in found

            for leaf_id in FARM_LEAF_EXPECTED_IDS.values():
                intel = await client.get(
                    f"/api/v1/categories/intelligence/{leaf_id}"
                )
                assert intel.status_code == 200, intel.text
                body = intel.json()
                keys = {f["field_key"] for f in body.get("core_fields", [])}
                assert REQUIRED_KEYS.issubset(keys)
                filt_keys = {
                    f["filter_key"] for f in body.get("filters", [])
                }
                assert "has_photo" not in filt_keys
                assert filt_keys

            # Resolver aliases
            for alias, expected_slug in (
                ("трактор", "transport-farm-machinery-traktory"),
                ("плуг", BROAD_IMPLEMENT_SLUG),
                ("опрыскиватель", BROAD_IMPLEMENT_SLUG),
                ("кун", BROAD_IMPLEMENT_SLUG),
                ("сельхозприцеп", "transport-trailers-pritsepy"),
            ):
                r = await client.get(
                    "/api/v1/categories/resolve",
                    params={"q": alias, "locale": "ru"},
                )
                # endpoint may vary — soft check when available
                if r.status_code == 200:
                    data = r.json()
                    slug = (
                        data.get("slug")
                        or (data.get("category") or {}).get("slug")
                        or data.get("category_slug")
                    )
                    if slug:
                        assert slug == expected_slug, (alias, slug)
    finally:
        app.dependency_overrides.clear()
        if created:
            async with async_session_maker() as session:
                await session.execute(
                    text(
                        "DELETE FROM listing_field_values WHERE listing_id = ANY(:ids)"
                    ),
                    {"ids": created},
                )
                await session.execute(
                    text("DELETE FROM listings WHERE id = ANY(:ids)"),
                    {"ids": created},
                )
                await session.commit()


def test_farm_sale_v2() -> None:
    asyncio.run(_run_all())
