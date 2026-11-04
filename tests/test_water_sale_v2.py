"""Water Transport Sale V2 — Backend SoT cutover."""
from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from decimal import Decimal

from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.api.deps import get_current_user
from app.db.session import async_session_maker
from app.main import app as fastapi_app
from app.schemas.user import UserRead
from app.seeds.transport_v2_1 import MERGE_LISTING_REMAP, RETIRE_LEAF_SLUGS
from app.seeds.water_sale_v2 import (
    BOAT_MOTOR_BRANDS,
    JET_SKI_DISABLE_BRAND_SLUGS,
    OTHER_WATERCRAFT_DISABLE_BRAND_SLUGS,
    WATER_CORE_FIELDS_BY_SLUG,
    WATER_INACTIVE_LEGACY_SLUGS,
    WATER_LEAF_ALIASES,
    WATER_LEAF_LABELS,
    WATER_LEAF_SLUGS,
    WATER_LEAF_VEHICLE_TYPE,
    WATER_OTHER_BRAND_TYPES,
    WATER_PARENT_SLUG,
    WATER_SEARCH_FILTERS_BY_SLUG,
    _BOAT_TYPES,
    _ENGINE_TYPES,
    _HULL,
    _SELLER,
    _STROKE,
)


async def _slug_id(session, slug: str) -> int:
    return int(
        (
            await session.execute(
                text("SELECT id FROM categories WHERE slug = :s"),
                {"s": slug},
            )
        ).scalar_one()
    )


def _auth_user(user_id: int = 1) -> None:
    now = datetime.now(UTC)

    async def _user() -> UserRead:
        return UserRead(
            id=user_id,
            phone="+79001234567",
            full_name="WaterSaleV2Tester",
            is_active=True,
            balance=Decimal("0"),
            last_login=None,
            created_at=now,
            updated_at=now,
        )

    fastapi_app.dependency_overrides[get_current_user] = _user


async def _run_all() -> None:
    async with async_session_maker() as session:
        parent = await _slug_id(session, WATER_PARENT_SLUG)
        assert parent == 692

        motor = (
            await session.execute(
                text(
                    """
                    SELECT id, parent_id, is_active, name
                    FROM categories
                    WHERE slug = 'transport-watercraft-lodochnye-motory'
                    """
                )
            )
        ).mappings().one()
        assert motor["id"] == 817
        assert motor["parent_id"] == 692
        assert motor["is_active"] is True
        assert motor["name"] == "Лодочные моторы"

        assert "transport-watercraft-lodochnye-motory" not in RETIRE_LEAF_SLUGS
        assert (
            "transport-watercraft-lodochnye-motory" not in MERGE_LISTING_REMAP
        )

        rows = (
            await session.execute(
                text(
                    """
                    SELECT id, slug, name, is_active, parent_id
                    FROM categories
                    WHERE parent_id = :pid
                    ORDER BY sort_order, id
                    """
                ),
                {"pid": parent},
            )
        ).mappings().all()
        active = [r for r in rows if r["is_active"]]
        assert len(active) == 6, [r["slug"] for r in active]
        assert {r["slug"] for r in active} == set(WATER_LEAF_SLUGS)
        for slug, label in WATER_LEAF_LABELS.items():
            match = next(r for r in active if r["slug"] == slug)
            assert match["name"] == label

        for slug in WATER_INACTIVE_LEGACY_SLUGS:
            row = (
                await session.execute(
                    text("SELECT is_active FROM categories WHERE slug = :s"),
                    {"s": slug},
                )
            ).scalar_one_or_none()
            if row is None:
                continue
            assert row is False, slug

        inflatable = (
            await session.execute(
                text(
                    """
                    SELECT is_active FROM categories
                    WHERE slug = 'transport-watercraft-naduvnye-lodki'
                    """
                )
            )
        ).scalar_one()
        assert inflatable is False

        for kayakish in (
            "каяк",
            "каное",
            "sup",
            "водный велосипед",
        ):
            hit = (
                await session.execute(
                    text(
                        """
                        SELECT COUNT(*) FROM categories
                        WHERE name ILIKE :n AND parent_id = :pid
                        """
                    ),
                    {"n": f"%{kayakish}%", "pid": parent},
                )
            ).scalar_one()
            assert int(hit) == 0, kayakish

        parent_fields = (
            await session.execute(
                text(
                    """
                    SELECT COUNT(*) FROM category_core_fields
                    WHERE category_id = :pid
                    """
                ),
                {"pid": parent},
            )
        ).scalar_one()
        assert int(parent_fields) == 0

        required_keys = {
            "condition",
            "price",
            "negotiable",
            "seller_type",
            "contact_methods",
        }
        for slug in WATER_LEAF_SLUGS:
            cid = await _slug_id(session, slug)
            fields = (
                await session.execute(
                    text(
                        """
                        SELECT field_key, is_required, options::text, field_type::text
                        FROM category_core_fields
                        WHERE category_id = :cid AND create_intent IS NULL
                        ORDER BY sort_order
                        """
                    ),
                    {"cid": cid},
                )
            ).mappings().all()
            assert fields, f"empty schema for {slug}"
            by_key = {f["field_key"]: f for f in fields}
            for key in required_keys:
                assert by_key[key]["is_required"] is True, f"{slug}.{key}"
            assert by_key["brand"]["is_required"] is False
            assert by_key["model"]["is_required"] is False
            assert "documents" not in by_key
            assert "trailer_included" not in by_key
            assert "engine_power_kw" not in by_key
            for key in (
                "condition",
                "negotiable",
                "seller_type",
                "contact_methods",
                "boat_type",
                "hull_material",
                "engine_included",
                "engine_type",
                "stroke",
                "fuel",
                "needs_investment",
                "exchange",
                "installment",
            ):
                if key in by_key:
                    assert by_key[key]["options"] not in (None, "", "{}"), f"{slug}.{key}"
            expected = {row[0] for row in WATER_CORE_FIELDS_BY_SLUG[slug]}
            assert set(by_key) == expected, f"{slug}: {set(by_key) ^ expected}"

            seller_opts = by_key["seller_type"]["options"]
            assert "Частное лицо" in seller_opts
            assert "Магазин" in seller_opts
            assert "Дилер" not in seller_opts
            assert "Компания" not in seller_opts

            filters = (
                await session.execute(
                    text(
                        """
                        SELECT filter_key FROM category_filters
                        WHERE category_id = :cid
                        """
                    ),
                    {"cid": cid},
                )
            ).scalars().all()
            assert filters, slug
            expected_f = {row[0] for row in WATER_SEARCH_FILTERS_BY_SLUG[slug]}
            assert set(filters) == expected_f, slug
            assert "has_photo" not in filters
            assert "sort" in filters
            assert "condition" in filters

        boat = await _slug_id(session, "transport-watercraft-lodki")
        boat_fields = {
            r["field_key"]: r
            for r in (
                await session.execute(
                    text(
                        """
                        SELECT field_key, options::text, is_required
                        FROM category_core_fields WHERE category_id = :cid
                        """
                    ),
                    {"cid": boat},
                )
            ).mappings().all()
        }
        assert "boat_type" in boat_fields
        assert boat_fields["boat_type"]["is_required"] is False
        for opt in _BOAT_TYPES:
            assert opt in boat_fields["boat_type"]["options"]
        assert "hull_material" in boat_fields
        for opt in _HULL:
            assert opt in boat_fields["hull_material"]["options"]
        assert "engine_included" in boat_fields
        assert "engine_power_hp" in boat_fields
        assert "depends_on" in boat_fields["engine_power_hp"]["options"]
        assert "engine_brand" not in boat_fields
        assert "engine_model" not in boat_fields

        motorboat = await _slug_id(session, "transport-watercraft-katera")
        mb_keys = {
            r
            for r in (
                await session.execute(
                    text(
                        """
                        SELECT field_key FROM category_core_fields
                        WHERE category_id = :cid
                        """
                    ),
                    {"cid": motorboat},
                )
            ).scalars().all()
        }
        assert "engine_included" not in mb_keys
        assert "engine_power_hp" in mb_keys
        assert "operating_hours" in mb_keys
        assert "length_m" in mb_keys

        jet = await _slug_id(session, "transport-watercraft-gidrotsikly")
        jet_keys = {
            r
            for r in (
                await session.execute(
                    text(
                        """
                        SELECT field_key FROM category_core_fields
                        WHERE category_id = :cid
                        """
                    ),
                    {"cid": jet},
                )
            ).scalars().all()
        }
        assert "hull_material" not in jet_keys
        assert "engine_power_hp" in jet_keys

        motor_leaf = await _slug_id(session, "transport-watercraft-lodochnye-motory")
        motor_fields = {
            r["field_key"]: r
            for r in (
                await session.execute(
                    text(
                        """
                        SELECT field_key, options::text
                        FROM category_core_fields WHERE category_id = :cid
                        """
                    ),
                    {"cid": motor_leaf},
                )
            ).mappings().all()
        }
        assert "engine_type" in motor_fields
        for opt in _ENGINE_TYPES:
            assert opt in motor_fields["engine_type"]["options"]
        assert "stroke" in motor_fields
        for opt in _STROKE:
            assert opt in motor_fields["stroke"]["options"]
        assert "engine_power_hp" in motor_fields
        assert "л.с." in motor_fields["engine_power_hp"]["options"]

        for vt in WATER_OTHER_BRAND_TYPES:
            slug = f"other-{vt.replace('_', '-')}"
            brand = (
                await session.execute(
                    text(
                        """
                        SELECT name, vehicle_type::text, is_enabled
                        FROM vehicle_brands WHERE slug = :s
                        """
                    ),
                    {"s": slug},
                )
            ).mappings().one()
            assert brand["name"] == "Другая марка"
            assert brand["vehicle_type"] == vt
            assert brand["is_enabled"] is True

        for slug, name, _country, vtype in BOAT_MOTOR_BRANDS:
            brand = (
                await session.execute(
                    text(
                        """
                        SELECT name, vehicle_type::text, is_enabled
                        FROM vehicle_brands WHERE slug = :s
                        """
                    ),
                    {"s": slug},
                )
            ).mappings().one()
            assert brand["name"] == name
            assert brand["vehicle_type"] == vtype.value
            assert brand["is_enabled"] is True

        mercury_bm = (
            await session.execute(
                text(
                    """
                    SELECT m.name FROM vehicle_models m
                    JOIN vehicle_brands b ON b.id = m.brand_id
                    WHERE b.slug = 'mercury-boat-motor' AND m.is_enabled
                    ORDER BY m.name
                    """
                )
            )
        ).scalars().all()
        assert "60 EFI" in mercury_bm
        assert "115 EFI" in mercury_bm
        assert "150 Pro XS" in mercury_bm
        for carish in (
            "Cougar",
            "Grand Marquis",
            "Milan",
            "Mountaineer",
            "Sable",
        ):
            assert carish not in mercury_bm

        for bad in JET_SKI_DISABLE_BRAND_SLUGS:
            enabled = (
                await session.execute(
                    text(
                        """
                        SELECT is_enabled FROM vehicle_brands WHERE slug = :s
                        """
                    ),
                    {"s": bad},
                )
            ).scalar_one_or_none()
            if enabled is not None:
                assert enabled is False, bad

        jet_brands = (
            await session.execute(
                text(
                    """
                    SELECT name FROM vehicle_brands
                    WHERE vehicle_type::text = 'jet_ski' AND is_enabled
                    ORDER BY name
                    """
                )
            )
        ).scalars().all()
        for polluted in ("Sea-Doo Spark", "Sea-Doo GTI", "Kawasaki Ultra"):
            assert polluted not in jet_brands, polluted
        assert "Sea-Doo" in jet_brands
        assert "Kawasaki" in jet_brands
        assert "Yamaha" in jet_brands

        for bad in OTHER_WATERCRAFT_DISABLE_BRAND_SLUGS:
            enabled = (
                await session.execute(
                    text(
                        """
                        SELECT is_enabled FROM vehicle_brands WHERE slug = :s
                        """
                    ),
                    {"s": bad},
                )
            ).scalar_one_or_none()
            if enabled is not None:
                assert enabled is False, bad

        other_brands = (
            await session.execute(
                text(
                    """
                    SELECT name FROM vehicle_brands
                    WHERE vehicle_type::text = 'other_watercraft' AND is_enabled
                    ORDER BY name
                    """
                )
            )
        ).scalars().all()
        assert "Mercury" not in other_brands
        assert "Volvo Penta" not in other_brands

        for alias, leaf_slug in WATER_LEAF_ALIASES.items():
            target = (
                await session.execute(
                    text(
                        """
                        SELECT c.slug FROM category_aliases a
                        JOIN categories c ON c.id = a.category_id
                        WHERE a.alias_normalized = :a AND a.locale = 'ru'
                        """
                    ),
                    {"a": alias},
                )
            ).scalar_one()
            assert target == leaf_slug, alias

        for slug, vt in WATER_LEAF_VEHICLE_TYPE.items():
            assert vt

        assert "Частное лицо" in _SELLER
        assert "Магазин" in _SELLER

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
    transport = ASGITransport(app=fastapi_app)
    created: list[int] = []
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async with async_session_maker() as session:
            owner_id = int(
                (
                    await session.execute(
                        text("SELECT id FROM users ORDER BY id LIMIT 1")
                    )
                ).scalar_one()
            )
            boat_id = await _slug_id(session, "transport-watercraft-lodki")
            cutter_id = await _slug_id(session, "transport-watercraft-katera")
            yacht_id = await _slug_id(session, "transport-watercraft-yahty")
            jet_id = await _slug_id(session, "transport-watercraft-gidrotsikly")
            motor_id = await _slug_id(
                session, "transport-watercraft-lodochnye-motory"
            )
            other_id = await _slug_id(
                session, "transport-watercraft-drugoy-vodnyy-transport"
            )

            boat_listing = await _insert_active(
                session,
                title="WaterV2 boat inflatable e2e",
                price=45000,
                cid=boat_id,
                oid=owner_id,
                eav={
                    "condition": "Хорошее",
                    "negotiable": "Есть торг",
                    "seller_type": "Частное лицо",
                    "boat_type": "Надувная",
                    "passenger_capacity": 4,
                    "engine_included": "Да",
                    "engine_power_hp": 40,
                },
            )
            cutter_listing = await _insert_active(
                session,
                title="WaterV2 cutter e2e",
                price=850000,
                cid=cutter_id,
                oid=owner_id,
                eav={
                    "condition": "Отличное",
                    "negotiable": "Без торга",
                    "seller_type": "Магазин",
                    "length_m": 5.5,
                    "engine_power_hp": 150,
                    "operating_hours": 320,
                },
            )
            yacht_listing = await _insert_active(
                session,
                title="WaterV2 yacht no brand e2e",
                price=2500000,
                cid=yacht_id,
                oid=owner_id,
                eav={
                    "condition": "Хорошее",
                    "negotiable": "Есть торг",
                    "seller_type": "Частное лицо",
                    "length_m": 12.0,
                },
            )
            jet_listing = await _insert_active(
                session,
                title="WaterV2 jet ski e2e",
                price=620000,
                cid=jet_id,
                oid=owner_id,
                eav={
                    "condition": "Хорошее",
                    "negotiable": "Есть торг",
                    "seller_type": "Магазин",
                    "engine_power_hp": 130,
                    "operating_hours": 80,
                    "passenger_capacity": 2,
                },
            )
            motor_listing = await _insert_active(
                session,
                title="WaterV2 boat motor e2e",
                price=95000,
                cid=motor_id,
                oid=owner_id,
                eav={
                    "condition": "Новое",
                    "negotiable": "Без торга",
                    "seller_type": "Магазин",
                    "engine_power_hp": 40,
                    "engine_type": "Подвесной",
                    "stroke": "4-тактный",
                    "operating_hours": 10,
                },
            )
            other_listing = await _insert_active(
                session,
                title="WaterV2 other e2e",
                price=30000,
                cid=other_id,
                oid=owner_id,
                eav={
                    "condition": "Удовлетворительное",
                    "negotiable": "Есть торг",
                    "seller_type": "Частное лицо",
                },
            )
            await session.commit()
            created.extend(
                [
                    boat_listing,
                    cutter_listing,
                    yacht_listing,
                    jet_listing,
                    motor_listing,
                    other_listing,
                ]
            )

        async def _ids(params: dict) -> set[int]:
            r = await client.get("/api/v1/listings", params=params)
            assert r.status_code == 200, r.text
            return {int(x["id"]) for x in r.json()["items"]}

        found_boat = await _ids(
            {
                "category_slug": "transport-watercraft-lodki",
                "attrs": json.dumps(
                    {"boat_type": "Надувная", "condition": "Хорошее"},
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert boat_listing in found_boat

        found_cutter = await _ids(
            {
                "category_slug": "transport-watercraft-katera",
                "attrs": json.dumps(
                    {"engine_power_hp__min": "100", "length_m__min": "5"},
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert cutter_listing in found_cutter

        not_cutter = await _ids(
            {
                "category_slug": "transport-watercraft-katera",
                "attrs": json.dumps(
                    {"engine_power_hp__min": "400"},
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert cutter_listing not in not_cutter

        found_jet = await _ids(
            {
                "category_slug": "transport-watercraft-gidrotsikly",
                "attrs": json.dumps(
                    {
                        "engine_power_hp__min": "100",
                        "operating_hours__max": "100",
                    },
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert jet_listing in found_jet

        found_motor = await _ids(
            {
                "category_slug": "transport-watercraft-lodochnye-motory",
                "attrs": json.dumps(
                    {
                        "engine_power_hp__min": "30",
                        "engine_type": "Подвесной",
                        "stroke": "4-тактный",
                    },
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert motor_listing in found_motor

        not_motor = await _ids(
            {
                "category_slug": "transport-watercraft-lodochnye-motory",
                "attrs": json.dumps(
                    {"engine_power_hp__min": "200"},
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert motor_listing not in not_motor

        found_yacht = await _ids(
            {
                "category_slug": "transport-watercraft-yahty",
                "attrs": json.dumps(
                    {"length_m__min": "10"},
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert yacht_listing in found_yacht

        found_other = await _ids(
            {
                "category_slug": "transport-watercraft-drugoy-vodnyy-transport",
                "attrs": json.dumps(
                    {"seller_type": "Частное лицо"},
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert other_listing in found_other

        intel = await client.get(
            f"/api/v1/categories/intelligence/{motor_id}"
        )
        assert intel.status_code == 200, intel.text
        body = intel.json()
        keys = {f["field_key"] for f in body.get("core_fields", [])}
        assert "engine_power_hp" in keys
        assert "engine_type" in keys
        filt_keys = {f["filter_key"] for f in body.get("filters", [])}
        assert "has_photo" not in filt_keys

    async with async_session_maker() as session:
        if created:
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


def test_water_sale_v2() -> None:
    asyncio.run(_run_all())
