"""Bus / Minibus / Motorhome Sale V2 — Backend SoT cutover."""
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
from app.seeds.bus_sale_v2 import (
    BUS_CORE_FIELDS_BY_SLUG,
    BUS_FORBIDDEN_FIELD_KEYS,
    BUS_LEAF_ALIASES,
    BUS_LEAF_LABELS,
    BUS_LEAF_SLUGS,
    BUS_LEAF_VEHICLE_TYPE,
    BUS_PARENT_SLUG,
    BUS_SEARCH_FILTERS_BY_SLUG,
    MICROBUS_CARGO_MODEL_KEYS,
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
            full_name="BusSaleV2Tester",
            is_active=True,
            balance=Decimal("0"),
            last_login=None,
            created_at=now,
            updated_at=now,
        )

    fastapi_app.dependency_overrides[get_current_user] = _user


async def _run_all() -> None:
    async with async_session_maker() as session:
        parent = await _slug_id(session, BUS_PARENT_SLUG)
        assert parent == 1201
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
        assert len(active) == 3
        assert {r["slug"] for r in active} == set(BUS_LEAF_SLUGS)
        for slug, label in BUS_LEAF_LABELS.items():
            match = next(r for r in active if r["slug"] == slug)
            assert match["name"] == label
        for expected_id, slug in (
            (776, "transport-commercial-avtobusy"),
            (773, "transport-commercial-mikroavtobusy"),
            (1202, "transport-buses-avtodoma"),
        ):
            assert await _slug_id(session, slug) == expected_id

        commercial = (
            await session.execute(
                text(
                    "SELECT is_active FROM categories "
                    "WHERE slug = 'transport-commercial'"
                )
            )
        ).scalar_one()
        assert commercial is False
        cargo_van = (
            await session.execute(
                text(
                    "SELECT parent_id, is_active FROM categories "
                    "WHERE slug = 'transport-cargo-furgony'"
                )
            )
        ).mappings().one()
        assert cargo_van["is_active"] is True
        trailer = (
            await session.execute(
                text(
                    "SELECT parent_id, is_active FROM categories WHERE slug = "
                    "'transport-trailers-zhilye-pritsepy-kempery'"
                )
            )
        ).mappings().one()
        assert trailer["is_active"] is True

        required_keys = {
            "condition",
            "price",
            "negotiable",
            "seller_type",
            "contact_methods",
        }
        for slug in BUS_LEAF_SLUGS:
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
            assert by_key["year"]["is_required"] is False
            for key in ("condition", "negotiable", "seller_type", "fuel"):
                if key in by_key:
                    assert by_key[key]["options"] not in (None, "", "{}")
            forbidden = BUS_FORBIDDEN_FIELD_KEYS & set(by_key)
            assert not forbidden, f"{slug} has forbidden {forbidden}"
            expected = {row[0] for row in BUS_CORE_FIELDS_BY_SLUG[slug]}
            assert set(by_key) == expected
            if slug != "transport-buses-avtodoma":
                assert by_key["seats"]["is_required"] is False
                assert by_key["seats"]["field_type"] == "number"
            else:
                assert by_key["sleeping_places"]["is_required"] is False
                assert by_key["travel_seats"]["is_required"] is False
                assert by_key["motorhome_amenities"]["field_type"] == "multi_select"
                assert "seats" not in by_key
                assert "passenger_cargo" not in by_key

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
            expected_f = {row[0] for row in BUS_SEARCH_FILTERS_BY_SLUG[slug]}
            assert set(filters) == expected_f
            assert "price" in filters
            assert "condition" in filters
            assert "has_photo" not in filters
            assert "sort" in filters
            if slug == "transport-buses-avtodoma":
                assert "sleeping_places" in filters
                assert "motorhome_amenities" in filters
            else:
                assert "seats" in filters

        for alias, leaf_slug in BUS_LEAF_ALIASES.items():
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

        for brand_slug, model_slug in MICROBUS_CARGO_MODEL_KEYS:
            enabled = (
                await session.execute(
                    text(
                        """
                        SELECT m.is_enabled
                        FROM vehicle_models m
                        JOIN vehicle_brands b ON b.id = m.brand_id
                        WHERE b.slug = :bs AND m.slug = :ms
                        """
                    ),
                    {"bs": brand_slug, "ms": model_slug},
                )
            ).scalar_one_or_none()
            if enabled is not None:
                assert enabled is False, f"{brand_slug}/{model_slug}"

        for slug, vt in BUS_LEAF_VEHICLE_TYPE.items():
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

        bus_id = await _slug_id(session, "transport-commercial-avtobusy")
        mh_id = await _slug_id(session, "transport-buses-avtodoma")

    _auth_user()
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        intel = await client.get(f"/api/v1/categories/intelligence/{bus_id}")
        assert intel.status_code == 200, intel.text
        core = intel.json()["core_fields"]
        filters = intel.json()["filters"]
        assert core
        by_key = {f["field_key"]: f for f in core}
        assert by_key["price"]["is_required"] is True
        assert by_key["brand"]["is_required"] is False
        assert by_key["seats"]["is_required"] is False
        assert by_key["seller_type"]["is_required"] is True
        assert any(f["filter_key"] == "seats" for f in filters)
        assert any(f["filter_key"] == "price" for f in filters)

        mh = await client.get(f"/api/v1/categories/intelligence/{mh_id}")
        assert mh.status_code == 200
        mh_by = {f["field_key"]: f for f in mh.json()["core_fields"]}
        assert mh_by["sleeping_places"]["is_required"] is False
        assert mh_by["motorhome_amenities"]["field_type"] == "multi_select"
        assert "passenger_cargo" not in mh_by


def test_bus_sale_v2_schema_create_search() -> None:
    asyncio.run(_run_all())
