# -*- coding: utf-8 -*-
"""Transport Rental V2 — taxonomy, schemas, filters, pricing unit search."""
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
from app.seeds.transport_rental_v2 import (
    BUS_COMBINED_ID,
    BUS_COMBINED_LABEL,
    BUS_COMBINED_SLUG,
    BUS_RETIRED_ID,
    ELECTRIC_RENTAL_ID,
    FARM_RENTAL_SLUG,
    OTHER_RENTAL_SLUG,
    PROVIDER_TYPE_CHOICES,
    RENTAL_CORE_FIELDS_BY_SLUG,
    RENTAL_LEAF_SLUGS,
    RENTAL_PARENT_ID,
    RENTAL_PARENT_SLUG,
    RENTAL_PRICE_UNIT_CHOICES,
    RENTAL_SEARCH_FILTERS_BY_SLUG,
    TRAILER_RENTAL_SLUG,
    format_rental_price,
)


REQUIRED_COMMON = {
    "price",
    "rental_price_unit",
    "provider_type",
    "contact_methods",
    "region",
    "city",
}

FORBIDDEN = {
    "condition",
    "negotiable",
    "with_driver",
    "with_operator",
    "rental_crew_mode",
    "seller_type",
}


def _auth_user(user_id: int = 1) -> None:
    now = datetime.now(UTC)

    async def _user() -> UserRead:
        return UserRead(
            id=user_id,
            phone="+79001234567",
            full_name="RentalV2Tester",
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
    assert format_rental_price(1000, "hour") == "1 000 сом / час"
    assert format_rental_price(3000, "day") == "3 000 сом / сутки"
    assert format_rental_price(15000, "week") == "15 000 сом / неделю"
    assert format_rental_price(50000, "month") == "50 000 сом / месяц"

    async with async_session_maker() as session:
        parent = (
            await session.execute(
                text("SELECT id, is_active FROM categories WHERE slug = :s"),
                {"s": RENTAL_PARENT_SLUG},
            )
        ).mappings().one()
        assert parent["is_active"] is True
        assert int(parent["id"]) == RENTAL_PARENT_ID

        parent_fields = (
            await session.execute(
                text(
                    "SELECT COUNT(*) FROM category_core_fields WHERE category_id = :id"
                ),
                {"id": RENTAL_PARENT_ID},
            )
        ).scalar_one()
        assert int(parent_fields) == 0

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
                {"pid": RENTAL_PARENT_ID},
            )
        ).mappings().all()
        assert len(active) == 9, [r["slug"] for r in active]
        assert [r["slug"] for r in active] == list(RENTAL_LEAF_SLUGS)

        bus = next(r for r in active if r["slug"] == BUS_COMBINED_SLUG)
        assert int(bus["id"]) == BUS_COMBINED_ID
        assert bus["name"] == BUS_COMBINED_LABEL

        retired_bus = (
            await session.execute(
                text("SELECT is_active FROM categories WHERE id = :id"),
                {"id": BUS_RETIRED_ID},
            )
        ).scalar_one()
        assert retired_bus is False

        electric = (
            await session.execute(
                text("SELECT is_active FROM categories WHERE id = :id"),
                {"id": ELECTRIC_RENTAL_ID},
            )
        ).scalar_one()
        assert electric is False

        for slug in (
            "transport-rental-vnedorozhniki-i-krossovery",
            "transport-rental-kommercheskiy-transport",
            "transport-rental-arenda-s-voditelem",
            "transport-rental-dolgosrochnaya-arenda",
        ):
            row = (
                await session.execute(
                    text(
                        "SELECT is_active FROM categories WHERE slug = :s"
                    ),
                    {"s": slug},
                )
            ).scalar_one()
            assert row is False, slug

        for slug in (TRAILER_RENTAL_SLUG, FARM_RENTAL_SLUG, OTHER_RENTAL_SLUG):
            assert any(r["slug"] == slug for r in active), slug

        for slug in RENTAL_LEAF_SLUGS:
            cid = await _slug_id(session, slug)
            fields = (
                await session.execute(
                    text(
                        """
                        SELECT field_key, is_required
                        FROM category_core_fields
                        WHERE category_id = :id
                        """
                    ),
                    {"id": cid},
                )
            ).mappings().all()
            keys = {r["field_key"] for r in fields}
            assert keys, slug
            for req in REQUIRED_COMMON:
                assert req in keys, f"{slug} missing {req}"
            for bad in FORBIDDEN:
                assert bad not in keys, f"{slug} has {bad}"
            required = {r["field_key"] for r in fields if r["is_required"]}
            assert REQUIRED_COMMON <= required, slug
            assert "brand" not in required
            assert "model" not in required
            assert "deposit_required" not in required

            unit_opts = (
                await session.execute(
                    text(
                        """
                        SELECT options FROM category_core_fields
                        WHERE category_id = :id AND field_key = 'rental_price_unit'
                        """
                    ),
                    {"id": cid},
                )
            ).scalar_one()
            assert unit_opts is not None
            choices = unit_opts.get("choices") or unit_opts.get("values") or []
            values = [c["value"] if isinstance(c, dict) else c for c in choices]
            assert values == [v for v, _ in RENTAL_PRICE_UNIT_CHOICES]

            prov = (
                await session.execute(
                    text(
                        """
                        SELECT options FROM category_core_fields
                        WHERE category_id = :id AND field_key = 'provider_type'
                        """
                    ),
                    {"id": cid},
                )
            ).scalar_one()
            pchoices = prov.get("choices") or prov.get("values") or []
            plabels = [
                c["label"] if isinstance(c, dict) else c for c in pchoices
            ]
            assert list(plabels) == list(PROVIDER_TYPE_CHOICES)

            filters = (
                await session.execute(
                    text(
                        """
                        SELECT filter_key FROM category_filters
                        WHERE category_id = :id ORDER BY sort_order
                        """
                    ),
                    {"id": cid},
                )
            ).scalars().all()
            assert "rental_price_unit" in filters
            assert "price" in filters
            assert "condition" not in filters
            assert "negotiable" not in filters
            assert "has_photo" not in filters
            expected = [f[0] for f in RENTAL_SEARCH_FILTERS_BY_SLUG[slug]]
            assert list(filters) == expected, slug

            # Seed parity
            assert slug in RENTAL_CORE_FIELDS_BY_SLUG

    # API search unit isolation
    _auth_user()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        car_id = None
        async with async_session_maker() as session:
            car_id = await _slug_id(session, "transport-rental-legkovye-avtomobili")

        # Direct DB fixtures for search isolation (Currency V2 FX fields required).
        created: list[int] = []
        try:
            async with async_session_maker() as session:
                owner = (
                    await session.execute(text("SELECT id FROM users LIMIT 1"))
                ).scalar_one()
                rate = (
                    await session.execute(
                        text(
                            "SELECT rate FROM fx_rates WHERE pair = 'USD_KGS' LIMIT 1"
                        )
                    )
                ).scalar_one_or_none() or 89
                for price, unit in ((1000, "hour"), (3000, "day"), (50000, "month")):
                    lid = (
                        await session.execute(
                            text(
                                """
                                INSERT INTO listings
                                (owner_id, category_id, title, description, price,
                                 currency, status, exchange_rate_snapshot,
                                 normalized_price_kgs, created_at, updated_at)
                                VALUES
                                (:oid, :cid, :title, :descr, :price,
                                 'KGS', 'active', :rate, :price, now(), now())
                                RETURNING id
                                """
                            ),
                            {
                                "oid": owner,
                                "cid": car_id,
                                "title": f"Rental {unit} hygiene",
                                "descr": "Тест аренды транспорта для unit isolation",
                                "price": price,
                                "rate": rate,
                            },
                        )
                    ).scalar_one()
                    await session.execute(
                        text(
                            """
                            INSERT INTO listing_field_values
                            (listing_id, field_key, value_text, created_at, updated_at)
                            VALUES
                            (:lid, 'rental_price_unit', :unit, now(), now()),
                            (:lid, 'provider_type', 'Компания', now(), now())
                            """
                        ),
                        {"lid": lid, "unit": unit},
                    )
                    created.append(int(lid))
                await session.commit()

            # day + max 3500 → only day listing
            r = await client.get(
                "/api/v1/listings",
                params={
                    "category_id": car_id,
                    "max_price": 3500,
                    "attrs": json.dumps({"rental_price_unit": "day"}),
                },
            )
            assert r.status_code == 200, r.text
            found_ids = {item["id"] for item in r.json()["items"]}
            assert created[1] in found_ids
            assert created[0] not in found_ids
            assert created[2] not in found_ids

            # price without unit → 400
            bad = await client.get(
                "/api/v1/listings",
                params={"category_id": car_id, "max_price": 3500},
            )
            assert bad.status_code == 400
            assert bad.json().get("code") == "RENTAL_PRICE_UNIT_REQUIRED" or \
                "rental_price_unit" in str(bad.json()).lower()
        finally:
            async with async_session_maker() as session:
                for lid in created:
                    await session.execute(
                        text("DELETE FROM listing_field_values WHERE listing_id = :id"),
                        {"id": lid},
                    )
                    await session.execute(
                        text("DELETE FROM media WHERE listing_id = :id"),
                        {"id": lid},
                    )
                    await session.execute(
                        text("DELETE FROM listings WHERE id = :id"),
                        {"id": lid},
                    )
                await session.commit()

    app.dependency_overrides.clear()


def test_transport_rental_v2() -> None:
    asyncio.run(_run_all())
