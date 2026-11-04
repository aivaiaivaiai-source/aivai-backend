"""Bicycle Sale V2 — Backend SoT create/search cutover for 7 bicycle leaves."""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.api.deps import get_current_user
from app.db.session import async_session_maker
from app.main import app as fastapi_app
from app.schemas.user import UserRead
from app.seeds.bicycle_sale_v2 import (
    BICYCLE_CORE_FIELDS_BY_SLUG,
    BICYCLE_FAKE_BRAND_SLUGS,
    BICYCLE_FORBIDDEN_FIELD_KEYS,
    BICYCLE_INACTIVE_LEGACY_SLUGS,
    BICYCLE_LEAF_LABELS,
    BICYCLE_LEAF_SLUGS,
    BICYCLE_LEAF_VEHICLE_TYPE,
    BICYCLE_PARENT_SLUG,
    BICYCLE_SEARCH_FILTERS_BY_SLUG,
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
            full_name="BicycleSaleV2Tester",
            is_active=True,
            balance=Decimal("0"),
            last_login=None,
            created_at=now,
            updated_at=now,
        )

    fastapi_app.dependency_overrides[get_current_user] = _user


async def _run_all() -> None:
    async with async_session_maker() as session:
        parent = await _slug_id(session, BICYCLE_PARENT_SLUG)
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
        assert len(active) == 7
        assert {r["slug"] for r in active} == set(BICYCLE_LEAF_SLUGS)
        for slug, label in BICYCLE_LEAF_LABELS.items():
            match = next(r for r in active if r["slug"] == slug)
            assert match["name"] == label
        for slug in BICYCLE_INACTIVE_LEGACY_SLUGS:
            row = (
                await session.execute(
                    text("SELECT is_active FROM categories WHERE slug = :s"),
                    {"s": slug},
                )
            ).scalar_one()
            assert row is False
        gravel = (
            await session.execute(
                text(
                    "SELECT id FROM categories WHERE name ILIKE '%грави%' "
                    "OR slug ILIKE '%gravel%'"
                )
            )
        ).first()
        assert gravel is None
        ebike_parent = (
            await session.execute(
                text(
                    """
                    SELECT p.slug FROM categories c
                    JOIN categories p ON p.id = c.parent_id
                    WHERE c.slug = 'transport-bicycles-elektrovelosipedy'
                    """
                )
            )
        ).scalar_one()
        assert ebike_parent == BICYCLE_PARENT_SLUG

        required_keys = {
            "condition",
            "price",
            "negotiable",
            "seller_type",
            "contact_methods",
        }
        for slug in BICYCLE_LEAF_SLUGS:
            cid = await _slug_id(session, slug)
            fields = (
                await session.execute(
                    text(
                        """
                        SELECT field_key, is_required, options::text
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
                assert by_key[key]["is_required"] is True
            assert by_key["brand"]["is_required"] is False
            assert by_key["model"]["is_required"] is False
            for key in ("condition", "negotiable", "seller_type", "wheel_size"):
                if key in by_key:
                    assert by_key[key]["options"] not in (None, "", "{}")
            forbidden = BICYCLE_FORBIDDEN_FIELD_KEYS & set(by_key)
            assert not forbidden, f"{slug} has forbidden {forbidden}"
            expected = {row[0] for row in BICYCLE_CORE_FIELDS_BY_SLUG[slug]}
            assert set(by_key) == expected
            if slug == "transport-bicycles-bmx":
                assert "suspension" not in by_key
                assert "gears" not in by_key
            if slug == "transport-bicycles-elektrovelosipedy":
                for ek in (
                    "power_w",
                    "range_km",
                    "battery_voltage_v",
                    "battery_capacity_ah",
                    "max_speed_kmh",
                ):
                    assert by_key[ek]["is_required"] is False
            if slug == "transport-bicycles-drugie":
                assert "foldable" in by_key

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
            assert filters
            assert "price" in filters
            assert "condition" in filters
            assert "has_photo" not in filters
            assert "sort" in filters
            assert "brand" in filters
            expected_f = {
                row[0] for row in BICYCLE_SEARCH_FILTERS_BY_SLUG[slug]
            }
            assert set(filters) == expected_f
            if slug == "transport-bicycles-elektrovelosipedy":
                assert "power_w" in filters
                assert "range_km" in filters

        for slug in BICYCLE_FAKE_BRAND_SLUGS:
            enabled = (
                await session.execute(
                    text(
                        "SELECT is_enabled FROM vehicle_brands WHERE slug = :s"
                    ),
                    {"s": slug},
                )
            ).scalar_one_or_none()
            assert enabled is False, slug
        alias_cid = (
            await session.execute(
                text(
                    """
                    SELECT category_id FROM category_aliases
                    WHERE alias_normalized = 'велосипед' AND locale = 'ru'
                      AND is_enabled
                    """
                )
            )
        ).scalar_one()
        assert int(alias_cid) == parent
        for slug, vt in BICYCLE_LEAF_VEHICLE_TYPE.items():
            count = (
                await session.execute(
                    text(
                        """
                        SELECT COUNT(*) FROM vehicle_brands
                        WHERE vehicle_type::text = :vt AND is_enabled
                        """
                    ),
                    {"vt": vt},
                )
            ).scalar_one()
            assert int(count) >= 5, f"{slug}/{vt} thin: {count}"
            other = (
                await session.execute(
                    text(
                        """
                        SELECT COUNT(*) FROM vehicle_brands
                        WHERE vehicle_type::text = :vt AND name = 'Другая марка'
                          AND is_enabled
                        """
                    ),
                    {"vt": vt},
                )
            ).scalar_one()
            assert int(other) >= 1, vt

        mtb_id = await _slug_id(session, "transport-bicycles-gornye-velosipedy")
        ebike_id = await _slug_id(
            session, "transport-bicycles-elektrovelosipedy"
        )

    _auth_user()
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        intel = await client.get(f"/api/v1/categories/intelligence/{mtb_id}")
        assert intel.status_code == 200, intel.text
        core = intel.json()["core_fields"]
        filters = intel.json()["filters"]
        assert core
        by_key = {f["field_key"]: f for f in core}
        assert by_key["price"]["is_required"] is True
        assert by_key["brand"]["is_required"] is False
        assert by_key["model"]["is_required"] is False
        assert by_key["wheel_size"]["is_required"] is False
        assert any(f["filter_key"] == "price" for f in filters)

        e_intel = await client.get(
            f"/api/v1/categories/intelligence/{ebike_id}"
        )
        assert e_intel.status_code == 200
        e_by = {f["field_key"]: f for f in e_intel.json()["core_fields"]}
        assert e_by["power_w"]["is_required"] is False
        assert e_by["range_km"]["field_type"] == "number"
        assert (e_by["power_w"].get("options") or {}).get("unit") == "W"
    fastapi_app.dependency_overrides.pop(get_current_user, None)


def test_bicycle_sale_v2_schema_create_search() -> None:
    asyncio.run(_run_all())
