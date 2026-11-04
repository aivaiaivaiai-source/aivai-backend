"""Cargo Sale V2 — Backend SoT cutover."""
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
from app.seeds.cargo_sale_v2 import (
    AXLE_VALUES,
    CARGO_CORE_FIELDS_BY_SLUG,
    CARGO_INACTIVE_LEGACY_SLUGS,
    CARGO_LEAF_ALIASES,
    CARGO_LEAF_LABELS,
    CARGO_LEAF_SLUGS,
    CARGO_LEAF_VEHICLE_TYPE,
    CARGO_OTHER_BRAND_TYPES,
    CARGO_PARENT_SLUG,
    CARGO_SEARCH_FILTERS_BY_SLUG,
    EVACUATOR_SALE_ALIASES,
    TANKER_PURPOSES,
    TRUCK_PURPOSES,
    VAN_TYPES,
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
            full_name="CargoSaleV2Tester",
            is_active=True,
            balance=Decimal("0"),
            last_login=None,
            created_at=now,
            updated_at=now,
        )

    fastapi_app.dependency_overrides[get_current_user] = _user


async def _run_all() -> None:
    async with async_session_maker() as session:
        parent = await _slug_id(session, CARGO_PARENT_SLUG)
        assert parent == 691

        parent_draft = (
            await session.execute(
                text(
                    """
                    SELECT id, status::text FROM listings
                    WHERE category_id = :pid AND lower(status::text) LIKE '%draft%'
                    ORDER BY id
                    """
                ),
                {"pid": parent},
            )
        ).mappings().all()
        assert any(r["id"] == 198 for r in parent_draft), parent_draft

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
        assert len(active) == 9, [r["slug"] for r in active]
        assert {r["slug"] for r in active} == set(CARGO_LEAF_SLUGS)
        for slug, label in CARGO_LEAF_LABELS.items():
            match = next(r for r in active if r["slug"] == slug)
            assert match["name"] == label

        for slug in CARGO_INACTIVE_LEGACY_SLUGS:
            row = (
                await session.execute(
                    text("SELECT is_active FROM categories WHERE slug = :s"),
                    {"s": slug},
                )
            ).scalar_one_or_none()
            if row is None:
                continue
            assert row is False, slug

        manip = (
            await session.execute(
                text(
                    """
                    SELECT id, is_active, parent_id FROM categories
                    WHERE slug = 'transport-special-equipment-manipulyatory'
                    """
                )
            )
        ).mappings().one()
        assert manip["is_active"] is True

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

        payload_live = (
            await session.execute(
                text(
                    """
                    SELECT COUNT(*) FROM category_core_fields ccf
                    JOIN categories c ON c.id = ccf.category_id
                    WHERE c.slug LIKE 'transport-cargo%'
                      AND ccf.field_key = 'payload_kg'
                    """
                )
            )
        ).scalar_one()
        assert int(payload_live) == 0

        required_keys = {
            "condition",
            "price",
            "negotiable",
            "seller_type",
            "contact_methods",
        }
        for slug in CARGO_LEAF_SLUGS:
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
            assert "drive" not in by_key
            assert "payload_kg" not in by_key
            for key in (
                "condition",
                "negotiable",
                "seller_type",
                "contact_methods",
                "fuel",
                "transmission",
                "axle_configuration",
                "cabin_sleeper",
                "van_type",
                "tanker_purpose",
                "truck_purpose",
                "needs_investment",
                "exchange",
                "installment",
            ):
                if key in by_key:
                    assert by_key[key]["options"] not in (None, "", "{}"), f"{slug}.{key}"
            expected = {row[0] for row in CARGO_CORE_FIELDS_BY_SLUG[slug]}
            assert set(by_key) == expected, f"{slug}: {set(by_key) ^ expected}"

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
            expected_f = {row[0] for row in CARGO_SEARCH_FILTERS_BY_SLUG[slug]}
            assert set(filters) == expected_f, slug
            assert "has_photo" not in filters
            assert "sort" in filters
            assert "condition" in filters

        dump = await _slug_id(session, "transport-cargo-samosvaly")
        dump_fields = {
            r["field_key"]: r
            for r in (
                await session.execute(
                    text(
                        """
                        SELECT field_key, options::text, is_required
                        FROM category_core_fields WHERE category_id = :cid
                        """
                    ),
                    {"cid": dump},
                )
            ).mappings().all()
        }
        assert "load_capacity_kg" in dump_fields
        assert dump_fields["load_capacity_kg"]["is_required"] is False
        assert "body_volume_m3" in dump_fields
        assert "axle_configuration" in dump_fields
        for v in AXLE_VALUES:
            assert v in dump_fields["axle_configuration"]["options"]

        van = await _slug_id(session, "transport-cargo-furgony")
        van_opts = (
            await session.execute(
                text(
                    """
                    SELECT options::text FROM category_core_fields
                    WHERE category_id = :cid AND field_key = 'van_type'
                    """
                ),
                {"cid": van},
            )
        ).scalar_one()
        for opt in VAN_TYPES:
            assert opt in van_opts
        assert "Рефрижератор" not in van_opts

        tanker = await _slug_id(session, "transport-cargo-tsisterny")
        tanker_opts = (
            await session.execute(
                text(
                    """
                    SELECT options::text FROM category_core_fields
                    WHERE category_id = :cid AND field_key = 'tanker_purpose'
                    """
                ),
                {"cid": tanker},
            )
        ).scalar_one()
        for opt in TANKER_PURPOSES:
            assert opt in tanker_opts

        other = await _slug_id(session, "transport-cargo-drugie-gruzoviki")
        other_opts = (
            await session.execute(
                text(
                    """
                    SELECT options::text FROM category_core_fields
                    WHERE category_id = :cid AND field_key = 'truck_purpose'
                    """
                ),
                {"cid": other},
            )
        ).scalar_one()
        for opt in TRUCK_PURPOSES:
            assert opt in other_opts

        for vt in CARGO_OTHER_BRAND_TYPES:
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

        for alias, leaf_slug in {**CARGO_LEAF_ALIASES, **EVACUATOR_SALE_ALIASES}.items():
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

        bare = (
            await session.execute(
                text(
                    """
                    SELECT c.slug FROM category_aliases a
                    JOIN categories c ON c.id = a.category_id
                    WHERE a.alias_normalized = 'эвакуатор' AND a.locale = 'ru'
                    """
                )
            )
        ).scalar_one()
        # Auto Services V2: bare «эвакуатор» → towing service (not generic services).
        assert "auto-services" in bare or bare.endswith("evakuatsiya-i-pomosch-na-doroge")

        for slug, vt in CARGO_LEAF_VEHICLE_TYPE.items():
            assert vt  # mapping preserved in seed SoT

    # --- Search FOUND / NOT FOUND via SQL fixtures + API attrs ---
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
            dump_id = await _slug_id(session, "transport-cargo-samosvaly")
            tractor_id = await _slug_id(session, "transport-cargo-tyagachi")
            van_id = await _slug_id(session, "transport-cargo-furgony")
            tanker_id = await _slug_id(session, "transport-cargo-tsisterny")
            tow_id = await _slug_id(session, "transport-cargo-evakuatory")
            other_id = await _slug_id(session, "transport-cargo-drugie-gruzoviki")

            dump_listing = await _insert_active(
                session,
                title="CargoV2 dump e2e",
                price=1500000,
                cid=dump_id,
                oid=owner_id,
                eav={
                    "condition": "Хорошее",
                    "negotiable": "Есть торг",
                    "seller_type": "Компания",
                    "load_capacity_kg": 20000,
                    "axle_configuration": "6x4",
                    "body_volume_m3": 12.0,
                },
            )
            tractor_listing = await _insert_active(
                session,
                title="CargoV2 tractor e2e",
                price=2200000,
                cid=tractor_id,
                oid=owner_id,
                eav={
                    "condition": "Хорошее",
                    "negotiable": "Без торга",
                    "seller_type": "Частное лицо",
                    "axle_configuration": "6x4",
                    "cabin_sleeper": "Есть",
                    "mileage": 350000,
                },
            )
            van_listing = await _insert_active(
                session,
                title="CargoV2 van e2e",
                price=980000,
                cid=van_id,
                oid=owner_id,
                eav={
                    "condition": "Отличное",
                    "negotiable": "Есть торг",
                    "seller_type": "Дилер",
                    "van_type": "Изотермический",
                    "load_capacity_kg": 3000,
                    "body_volume_m3": 18.0,
                },
            )
            tanker_listing = await _insert_active(
                session,
                title="CargoV2 tanker e2e",
                price=1100000,
                cid=tanker_id,
                oid=owner_id,
                eav={
                    "condition": "Хорошее",
                    "negotiable": "Есть торг",
                    "seller_type": "Компания",
                    "tank_capacity_l": 10000,
                    "tanker_purpose": "Для воды",
                },
            )
            tow_listing = await _insert_active(
                session,
                title="CargoV2 tow e2e",
                price=800000,
                cid=tow_id,
                oid=owner_id,
                eav={
                    "condition": "Хорошее",
                    "negotiable": "Без торга",
                    "seller_type": "Частное лицо",
                    "load_capacity_kg": 5000,
                },
            )
            other_listing = await _insert_active(
                session,
                title="CargoV2 other e2e",
                price=900000,
                cid=other_id,
                oid=owner_id,
                eav={
                    "condition": "Удовлетворительное",
                    "negotiable": "Есть торг",
                    "seller_type": "Компания",
                    "truck_purpose": "Автовоз",
                },
            )
            await session.commit()
            created.extend(
                [
                    dump_listing,
                    tractor_listing,
                    van_listing,
                    tanker_listing,
                    tow_listing,
                    other_listing,
                ]
            )

        async def _ids(params: dict) -> set[int]:
            r = await client.get("/api/v1/listings", params=params)
            assert r.status_code == 200, r.text
            return {int(x["id"]) for x in r.json()["items"]}

        found = await _ids(
            {
                "category_slug": "transport-cargo-samosvaly",
                "attrs": json.dumps(
                    {
                        "load_capacity_kg__min": "15000",
                        "axle_configuration": "6x4",
                        "condition": "Хорошее",
                    },
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert dump_listing in found, found

        not_found_cap = await _ids(
            {
                "category_slug": "transport-cargo-samosvaly",
                "attrs": json.dumps(
                    {
                        "load_capacity_kg__min": "25000",
                        "axle_configuration": "6x4",
                    },
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert dump_listing not in not_found_cap

        not_found_axle = await _ids(
            {
                "category_slug": "transport-cargo-samosvaly",
                "attrs": json.dumps(
                    {
                        "load_capacity_kg__min": "15000",
                        "axle_configuration": "4x2",
                    },
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert dump_listing not in not_found_axle

        found_tr = await _ids(
            {
                "category_slug": "transport-cargo-tyagachi",
                "attrs": json.dumps(
                    {"axle_configuration": "6x4", "cabin_sleeper": "Есть"},
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert tractor_listing in found_tr

        found_van = await _ids(
            {
                "category_slug": "transport-cargo-furgony",
                "attrs": json.dumps(
                    {
                        "van_type": "Изотермический",
                        "load_capacity_kg__min": "2000",
                    },
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert van_listing in found_van

        found_tank = await _ids(
            {
                "category_slug": "transport-cargo-tsisterny",
                "attrs": json.dumps(
                    {
                        "tank_capacity_l__min": "8000",
                        "tanker_purpose": "Для воды",
                    },
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert tanker_listing in found_tank

        wrong_purpose = await _ids(
            {
                "category_slug": "transport-cargo-tsisterny",
                "attrs": json.dumps(
                    {
                        "tank_capacity_l__min": "8000",
                        "tanker_purpose": "Пищевая",
                    },
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert tanker_listing not in wrong_purpose

        found_tow = await _ids(
            {
                "category_slug": "transport-cargo-evakuatory",
                "attrs": json.dumps(
                    {"load_capacity_kg__min": "4000"},
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert tow_listing in found_tow

        found_other = await _ids(
            {
                "category_slug": "transport-cargo-drugie-gruzoviki",
                "attrs": json.dumps(
                    {"truck_purpose": "Автовоз"},
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert other_listing in found_other

        dump_intel = await client.get(
            f"/api/v1/categories/intelligence/{dump_id}"
        )
        assert dump_intel.status_code == 200
        dump_core = {
            f["field_key"]: f for f in dump_intel.json()["core_fields"]
        }
        assert dump_core["brand"]["is_required"] is False
        assert dump_core["price"]["is_required"] is True
        assert "payload_kg" not in dump_core
        van_intel = await client.get(
            f"/api/v1/categories/intelligence/{van_id}"
        )
        assert "Рефрижератор" not in str(van_intel.json())

        async with async_session_maker() as session:
            for lid in created:
                await session.execute(
                    text(
                        "DELETE FROM listing_field_values WHERE listing_id = :id"
                    ),
                    {"id": lid},
                )
                await session.execute(
                    text("DELETE FROM listings WHERE id = :id"),
                    {"id": lid},
                )
            await session.commit()

    fastapi_app.dependency_overrides.clear()



def test_cargo_sale_v2() -> None:
    asyncio.run(_run_all())
