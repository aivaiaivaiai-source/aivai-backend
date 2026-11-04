"""Special Equipment Sale V2 — Backend SoT cutover."""
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
from app.seeds.special_sale_v2 import (
    EVACUATOR_SALE_ALIASES,
    MANIPULATOR_CRANE_OEM_BRAND_SLUGS,
    SPECIAL_CORE_FIELDS_BY_SLUG,
    SPECIAL_INACTIVE_LEGACY_SLUGS,
    SPECIAL_LEAF_ALIASES,
    SPECIAL_LEAF_LABELS,
    SPECIAL_LEAF_SLUGS,
    SPECIAL_LEAF_VEHICLE_TYPE,
    SPECIAL_PARENT_SLUG,
    SPECIAL_SEARCH_FILTERS_BY_SLUG,
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
            full_name="SpecialSaleV2Tester",
            is_active=True,
            balance=Decimal("0"),
            last_login=None,
            created_at=now,
            updated_at=now,
        )

    fastapi_app.dependency_overrides[get_current_user] = _user


async def _run_all() -> None:
    async with async_session_maker() as session:
        parent = await _slug_id(session, SPECIAL_PARENT_SLUG)
        assert parent == 690
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
        assert len(active) == 18, [r["slug"] for r in active]
        assert {r["slug"] for r in active} == set(SPECIAL_LEAF_SLUGS)
        for slug, label in SPECIAL_LEAF_LABELS.items():
            match = next(r for r in active if r["slug"] == slug)
            assert match["name"] == label

        for slug in SPECIAL_INACTIVE_LEGACY_SLUGS:
            active_flag = (
                await session.execute(
                    text("SELECT is_active FROM categories WHERE slug = :s"),
                    {"s": slug},
                )
            ).scalar_one()
            assert active_flag is False, slug

        cargo_evac = (
            await session.execute(
                text(
                    """
                    SELECT id, is_active, parent_id FROM categories
                    WHERE slug = 'transport-cargo-evakuatory'
                    """
                )
            )
        ).mappings().one()
        assert cargo_evac["is_active"] is True

        required_keys = {
            "condition",
            "price",
            "negotiable",
            "seller_type",
            "contact_methods",
        }
        for slug in SPECIAL_LEAF_SLUGS:
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
            if "year" in by_key:
                assert by_key["year"]["is_required"] is False
            for key in (
                "condition",
                "negotiable",
                "seller_type",
                "contact_methods",
                "equipment_type",
                "manipulator_brand",
                "fuel",
                "needs_investment",
                "exchange",
                "installment",
            ):
                if key in by_key:
                    assert by_key[key]["options"] not in (None, "", "{}"), f"{slug}.{key}"
            expected = {row[0] for row in SPECIAL_CORE_FIELDS_BY_SLUG[slug]}
            assert set(by_key) == expected, f"{slug}: {set(by_key) ^ expected}"

            # Attachment must not have machine hours/mileage/fuel.
            if slug.endswith("navesnoe-i-rabochee-oborudovanie"):
                assert "operating_hours" not in by_key
                assert "mileage" not in by_key
                assert "fuel" not in by_key

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
            expected_f = {row[0] for row in SPECIAL_SEARCH_FILTERS_BY_SLUG[slug]}
            assert set(filters) == expected_f, slug
            assert "price" in filters
            assert "condition" in filters
            assert "has_photo" not in filters
            assert "sort" in filters

        excavator = await _slug_id(session, "transport-special-equipment-ekskavatory")
        excav_fields = {
            r["field_key"]: r
            for r in (
                await session.execute(
                    text(
                        """
                        SELECT field_key, options::text
                        FROM category_core_fields WHERE category_id = :cid
                        """
                    ),
                    {"cid": excavator},
                )
            ).mappings().all()
        }
        assert "equipment_type" in excav_fields
        assert "Мини-экскаватор" in excav_fields["equipment_type"]["options"]
        assert "Экскаватор-погрузчик" in excav_fields["equipment_type"]["options"]
        assert "operating_hours" in excav_fields
        assert "digging_depth_m" in excav_fields

        manip = await _slug_id(session, "transport-special-equipment-manipulyatory")
        manip_fields = {
            r["field_key"]: r
            for r in (
                await session.execute(
                    text(
                        """
                        SELECT field_key, options::text
                        FROM category_core_fields WHERE category_id = :cid
                        """
                    ),
                    {"cid": manip},
                )
            ).mappings().all()
        }
        assert "manipulator_brand" in manip_fields
        assert "Palfinger" in manip_fields["manipulator_brand"]["options"]
        assert "load_capacity_kg" in manip_fields
        assert "boom_reach_m" in manip_fields

        for alias, leaf_slug in SPECIAL_LEAF_ALIASES.items():
            leaf_id = await _slug_id(session, leaf_slug)
            alias_cid = (
                await session.execute(
                    text(
                        """
                        SELECT category_id FROM category_aliases
                        WHERE alias_normalized = :a AND locale = 'ru'
                          AND is_enabled
                        """
                    ),
                    {"a": alias},
                )
            ).scalar_one()
            assert int(alias_cid) == leaf_id, alias

        for alias, leaf_slug in EVACUATOR_SALE_ALIASES.items():
            leaf_id = await _slug_id(session, leaf_slug)
            alias_cid = (
                await session.execute(
                    text(
                        """
                        SELECT category_id FROM category_aliases
                        WHERE alias_normalized = :a AND locale = 'ru'
                          AND is_enabled
                        """
                    ),
                    {"a": alias},
                )
            ).scalar_one()
            assert int(alias_cid) == leaf_id, alias

        bare_evac = (
            await session.execute(
                text(
                    """
                    SELECT c.slug FROM category_aliases a
                    JOIN categories c ON c.id = a.category_id
                    WHERE a.alias_normalized = 'эвакуатор' AND a.locale = 'ru'
                      AND a.is_enabled
                    """
                )
            )
        ).scalar_one()
        # Auto Services V2: bare «эвакуатор» → towing leaf (not services-transport).
        assert bare_evac == (
            "transport-auto-services-evakuatsiya-i-pomosch-na-doroge"
        )

        kamaz = (
            await session.execute(
                text(
                    """
                    SELECT c.slug FROM category_aliases a
                    JOIN categories c ON c.id = a.category_id
                    WHERE a.alias_normalized = 'камаз' AND a.locale = 'ru'
                      AND a.is_enabled
                    """
                )
            )
        ).scalar_one_or_none()
        if kamaz is not None:
            assert kamaz == "transport-cargo"

        # Manipulator primary brands: crane OEM disabled; chassis enabled.
        for slug in MANIPULATOR_CRANE_OEM_BRAND_SLUGS:
            enabled = (
                await session.execute(
                    text(
                        """
                        SELECT is_enabled FROM vehicle_brands
                        WHERE slug = :s
                          AND vehicle_type::text = 'manipulator'
                        """
                    ),
                    {"s": slug},
                )
            ).scalar_one_or_none()
            if enabled is not None:
                assert enabled is False, slug

        chassis_enabled = (
            await session.execute(
                text(
                    """
                    SELECT COUNT(*) FROM vehicle_brands
                    WHERE vehicle_type::text = 'manipulator'
                      AND is_enabled AND name != 'Другая марка'
                    """
                )
            )
        ).scalar_one()
        assert int(chassis_enabled) >= 5

        for slug, vt in SPECIAL_LEAF_VEHICLE_TYPE.items():
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

        excav_id = excavator
        manip_id = manip

    _auth_user()
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        intel = await client.get(f"/api/v1/categories/intelligence/{excav_id}")
        assert intel.status_code == 200, intel.text
        core = intel.json()["core_fields"]
        filters = intel.json()["filters"]
        assert core
        by_key = {f["field_key"]: f for f in core}
        assert by_key["price"]["is_required"] is True
        assert by_key["brand"]["is_required"] is False
        assert by_key["operating_hours"]["is_required"] is False
        assert by_key["equipment_type"]["is_required"] is False
        assert any(f["filter_key"] == "operating_hours" for f in filters)
        assert any(f["filter_key"] == "digging_depth_m" for f in filters)

        mh = await client.get(f"/api/v1/categories/intelligence/{manip_id}")
        assert mh.status_code == 200
        mh_by = {f["field_key"]: f for f in mh.json()["core_fields"]}
        assert mh_by["manipulator_brand"]["is_required"] is False
        assert mh_by["load_capacity_kg"]["is_required"] is False

        parent_intel = await client.get(f"/api/v1/categories/intelligence/{parent}")
        # Parent may still have thin legacy fields; Create must not publish on it.
        assert parent_intel.status_code == 200


def test_special_equipment_sale_v2_schema_create_search() -> None:
    asyncio.run(_run_all())
