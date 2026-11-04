# -*- coding: utf-8 -*-
"""Transport Tuning & Accessories V2 — taxonomy, schemas, search, aliases."""
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
from app.seeds.tuning_accessories_v2 import (
    ALWAYS_CONDITION_SLUGS,
    FILMS_SLUG,
    INTERIOR_SLUG,
    LEAF_ALIASES,
    LEAF_IDS,
    LEAF_LABELS,
    LEAF_SLUGS,
    LIGHTING_SLUG,
    NO_CONDITION_SLUGS,
    OTHER_SLUG,
    PARENT_ID,
    PARENT_SLUG,
    PRODUCT_TYPES_BY_SLUG,
    SECURITY_SLUG,
    SERVICE_BOUNDARY_ALIASES,
    TECHNICAL_SLUG,
    TUNING_CORE_FIELDS_BY_SLUG,
    TUNING_SEARCH_FILTERS_BY_SLUG,
)


def _auth_user(user_id: int = 1) -> None:
    now = datetime.now(UTC)

    async def _user() -> UserRead:
        return UserRead(
            id=user_id,
            phone="+79001234567",
            full_name="TuningV2Tester",
            is_active=True,
            balance=Decimal("0"),
            last_login=None,
            created_at=now,
            updated_at=now,
        )

    app.dependency_overrides[get_current_user] = _user


def _core_keys(fields: list) -> set[str]:
    return {f[0] for f in fields}


async def _slug_id(session, slug: str) -> int:
    return int(
        (
            await session.execute(
                text("SELECT id FROM categories WHERE slug = :s"),
                {"s": slug},
            )
        ).scalar_one()
    )


async def _insert_active(session, *, title, price, cid, oid, eav):
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


async def _run_all() -> None:
    assert len(LEAF_SLUGS) == 13
    assert OTHER_SLUG in NO_CONDITION_SLUGS
    assert FILMS_SLUG in NO_CONDITION_SLUGS
    assert "product_type" not in _core_keys(TUNING_CORE_FIELDS_BY_SLUG[OTHER_SLUG])
    assert "product_condition" not in _core_keys(
        TUNING_CORE_FIELDS_BY_SLUG[FILMS_SLUG]
    )
    assert "product_condition" in _core_keys(
        TUNING_CORE_FIELDS_BY_SLUG[INTERIOR_SLUG]
    )
    assert "item_type" not in _core_keys(TUNING_CORE_FIELDS_BY_SLUG[INTERIOR_SLUG])
    assert "brand" not in _core_keys(TUNING_CORE_FIELDS_BY_SLUG[INTERIOR_SLUG])
    assert "product_model" not in _core_keys(
        TUNING_CORE_FIELDS_BY_SLUG[INTERIOR_SLUG]
    )
    # No TPMS / wheel fasteners in Tuning product types
    all_types = {
        v for pairs in PRODUCT_TYPES_BY_SLUG.values() for v, _ in pairs
    }
    assert "tpms" not in all_types
    assert "hubcaps" not in all_types
    assert "wheel_bolts" not in all_types

    async with async_session_maker() as session:
        parent = (
            await session.execute(
                text(
                    """
                    SELECT id, is_active, name
                    FROM categories WHERE slug = :s
                    """
                ),
                {"s": PARENT_SLUG},
            )
        ).mappings().one()
        assert int(parent["id"]) == PARENT_ID
        assert parent["is_active"] is True
        assert parent["name"] == "Аксессуары и тюнинг"

        parent_fields = (
            await session.execute(
                text(
                    "SELECT COUNT(*) FROM category_core_fields WHERE category_id = :id"
                ),
                {"id": PARENT_ID},
            )
        ).scalar_one()
        assert int(parent_fields) == 0

        active = (
            await session.execute(
                text(
                    """
                    SELECT id, slug, name, sort_order
                    FROM categories
                    WHERE parent_id = :pid AND is_active = true
                    ORDER BY sort_order, id
                    """
                ),
                {"pid": PARENT_ID},
            )
        ).mappings().all()
        assert len(active) == 13, [r["slug"] for r in active]
        assert {r["slug"] for r in active} == set(LEAF_SLUGS)
        for r in active:
            assert r["name"] == LEAF_LABELS[r["slug"]]
            assert int(r["id"]) == LEAF_IDS[r["slug"]]

        for slug in (
            "transport-accessories-tuning-avtomobilnye-prinadlezhnosti",
            "transport-accessories-tuning-ekipirovka-moto-velo",
            "transport-accessories-tuning-vodnye-prinadlezhnosti",
            "transport-accessories-tuning-avtosvet-i-tyuning-optiki",
        ):
            row = (
                await session.execute(
                    text("SELECT is_active FROM categories WHERE slug = :s"),
                    {"s": slug},
                )
            ).scalar_one_or_none()
            if row is not None:
                assert row is False, slug

        bad = (
            await session.execute(
                text(
                    """
                    SELECT c.slug, f.field_key
                    FROM category_core_fields f
                    JOIN categories c ON c.id = f.category_id
                    WHERE c.parent_id = :pid
                      AND f.field_type = 'string'
                      AND f.field_key NOT IN ('region')
                    """
                ),
                {"pid": PARENT_ID},
            )
        ).all()
        assert bad == [], bad

        for slug in LEAF_SLUGS:
            keys = {
                r[0]
                for r in (
                    await session.execute(
                        text(
                            """
                            SELECT f.field_key
                            FROM category_core_fields f
                            JOIN categories c ON c.id = f.category_id
                            WHERE c.slug = :s
                            """
                        ),
                        {"s": slug},
                    )
                ).all()
            }
            assert "price" in keys
            assert "seller_type" in keys
            assert "contact_methods" in keys
            if slug != OTHER_SLUG:
                assert "product_type" in keys
            if slug in ALWAYS_CONDITION_SLUGS:
                assert "product_condition" in keys
            if slug in NO_CONDITION_SLUGS:
                assert "product_condition" not in keys
            filters = (
                await session.execute(
                    text(
                        """
                        SELECT COUNT(*) FROM category_filters f
                        JOIN categories c ON c.id = f.category_id
                        WHERE c.slug = :s
                        """
                    ),
                    {"s": slug},
                )
            ).scalar_one()
            assert int(filters) > 0, slug

        for slug, pairs in PRODUCT_TYPES_BY_SLUG.items():
            assert pairs
            opts = (
                await session.execute(
                    text(
                        """
                        SELECT f.options
                        FROM category_core_fields f
                        JOIN categories c ON c.id = f.category_id
                        WHERE c.slug = :s AND f.field_key = 'product_type'
                        """
                    ),
                    {"s": slug},
                )
            ).scalar_one()
            assert opts is not None
            values = {x["value"] for x in opts["values"]}
            labels = {x["value"]: x["label"] for x in opts["values"]}
            for v, lab in pairs:
                assert v in values
                assert labels[v] == lab

        for alias, target in LEAF_ALIASES.items():
            row = (
                await session.execute(
                    text(
                        """
                        SELECT c.slug FROM category_aliases ca
                        JOIN categories c ON c.id = ca.category_id
                        WHERE ca.alias_normalized = :a AND ca.is_enabled
                        """
                    ),
                    {"a": alias},
                )
            ).scalar_one_or_none()
            assert row == target, (alias, row, target)

        for alias, target in SERVICE_BOUNDARY_ALIASES.items():
            row = (
                await session.execute(
                    text(
                        """
                        SELECT c.slug FROM category_aliases ca
                        JOIN categories c ON c.id = ca.category_id
                        WHERE ca.alias_normalized = :a AND ca.is_enabled
                        """
                    ),
                    {"a": alias},
                )
            ).scalar_one_or_none()
            assert row == target, (alias, row, target)

        kovrik = (
            await session.execute(
                text(
                    """
                    SELECT c.slug FROM category_aliases ca
                    JOIN categories c ON c.id = ca.category_id
                    WHERE ca.alias_normalized = 'коврик' AND ca.is_enabled
                    """
                )
            )
        ).scalar_one_or_none()
        assert kovrik is not None
        assert "accessories" not in kovrik

        kids = (
            await session.execute(
                text(
                    """
                    SELECT c.slug FROM category_aliases ca
                    JOIN categories c ON c.id = ca.category_id
                    WHERE ca.alias_normalized = 'детское автокресло'
                      AND ca.is_enabled
                    """
                )
            )
        ).scalar_one_or_none()
        assert kids == "kids-avtokresla-i-perenoski"

    # --- Real Search ---
    _auth_user()
    created: list[int] = []
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            async with async_session_maker() as session:
                owner_id = int(
                    (
                        await session.execute(
                            text("SELECT id FROM users ORDER BY id LIMIT 1")
                        )
                    ).scalar_one()
                )
                interior_cid = await _slug_id(session, INTERIOR_SLUG)
                lighting_cid = await _slug_id(session, LIGHTING_SLUG)
                technical_cid = await _slug_id(session, TECHNICAL_SLUG)
                films_cid = await _slug_id(session, FILMS_SLUG)
                security_cid = await _slug_id(session, SECURITY_SLUG)

                mats_id = await _insert_active(
                    session,
                    title="TAV2 floor mats Camry",
                    price=25000,
                    cid=interior_cid,
                    oid=owner_id,
                    eav={
                        "product_type": "floor_mats",
                        "product_condition": "Б/у",
                        "seller_type": "Магазин",
                        "vehicle_brand": "toyota",
                        "vehicle_model": "camry",
                        "city": "Бишкек",
                    },
                )
                created.append(mats_id)
                phone_id = await _insert_active(
                    session,
                    title="TAV2 phone holder",
                    price=500,
                    cid=interior_cid,
                    oid=owner_id,
                    eav={
                        "product_type": "phone_holder",
                        "product_condition": "Новое",
                        "seller_type": "Частное лицо",
                        "city": "Бишкек",
                    },
                )
                created.append(phone_id)
                led_id = await _insert_active(
                    session,
                    title="TAV2 LED bar",
                    price=8000,
                    cid=lighting_cid,
                    oid=owner_id,
                    eav={
                        "product_type": "led_bar",
                        "product_condition": "Новое",
                        "seller_type": "Магазин",
                        "city": "Бишкек",
                    },
                )
                created.append(led_id)
                coil_id = await _insert_active(
                    session,
                    title="TAV2 coilovers",
                    price=40000,
                    cid=technical_cid,
                    oid=owner_id,
                    eav={
                        "product_type": "coilovers",
                        "product_condition": "Б/у",
                        "seller_type": "Частное лицо",
                        "city": "Бишкек",
                    },
                )
                created.append(coil_id)
                gbo_id = await _insert_active(
                    session,
                    title="TAV2 GBO kit",
                    price=55000,
                    cid=technical_cid,
                    oid=owner_id,
                    eav={
                        "product_type": "gbo_kit",
                        "product_condition": "Новое",
                        "seller_type": "Магазин",
                        "city": "Бишкек",
                    },
                )
                created.append(gbo_id)
                tint_id = await _insert_active(
                    session,
                    title="TAV2 tint film",
                    price=1500,
                    cid=films_cid,
                    oid=owner_id,
                    eav={
                        "product_type": "tint_film",
                        "seller_type": "Магазин",
                        "city": "Бишкек",
                    },
                )
                created.append(tint_id)
                alarm_id = await _insert_active(
                    session,
                    title="TAV2 alarm",
                    price=12000,
                    cid=security_cid,
                    oid=owner_id,
                    eav={
                        "product_type": "alarm",
                        "product_condition": "Новое",
                        "seller_type": "Магазин",
                        "city": "Бишкек",
                    },
                )
                created.append(alarm_id)
                await session.commit()

            async def _ids(params: dict) -> set[int]:
                r = await client.get("/api/v1/listings", params=params)
                assert r.status_code == 200, r.text
                body = r.json()
                assert "total" in body
                assert int(body["total"]) != 55443
                return {int(x["id"]) for x in body["items"]}

            found = await _ids(
                {
                    "category_slug": INTERIOR_SLUG,
                    "attrs": json.dumps(
                        {"product_type": "floor_mats"}, ensure_ascii=False
                    ),
                    "limit": 100,
                }
            )
            assert mats_id in found

            found = await _ids(
                {
                    "category_slug": INTERIOR_SLUG,
                    "attrs": json.dumps(
                        {"product_type": "phone_holder"}, ensure_ascii=False
                    ),
                    "limit": 100,
                }
            )
            assert phone_id in found

            found = await _ids(
                {
                    "category_slug": LIGHTING_SLUG,
                    "attrs": json.dumps(
                        {"product_type": "led_bar"}, ensure_ascii=False
                    ),
                    "limit": 100,
                }
            )
            assert led_id in found

            found = await _ids(
                {
                    "category_slug": TECHNICAL_SLUG,
                    "attrs": json.dumps(
                        {"product_type": "coilovers"}, ensure_ascii=False
                    ),
                    "limit": 100,
                }
            )
            assert coil_id in found

            found = await _ids(
                {
                    "category_slug": TECHNICAL_SLUG,
                    "attrs": json.dumps(
                        {"product_type": "gbo_kit"}, ensure_ascii=False
                    ),
                    "limit": 100,
                }
            )
            assert gbo_id in found

            found = await _ids(
                {
                    "category_slug": FILMS_SLUG,
                    "attrs": json.dumps(
                        {"product_type": "tint_film"}, ensure_ascii=False
                    ),
                    "limit": 100,
                }
            )
            assert tint_id in found

            found = await _ids(
                {
                    "category_slug": SECURITY_SLUG,
                    "attrs": json.dumps(
                        {"product_type": "alarm"}, ensure_ascii=False
                    ),
                    "limit": 100,
                }
            )
            assert alarm_id in found

            miss = await _ids(
                {
                    "category_slug": INTERIOR_SLUG,
                    "attrs": json.dumps(
                        {"product_type": "alarm"}, ensure_ascii=False
                    ),
                    "limit": 100,
                }
            )
            assert mats_id not in miss

            assert any(
                f[0] == "product_type"
                for f in TUNING_SEARCH_FILTERS_BY_SLUG[INTERIOR_SLUG]
            )
            assert not any(
                f[0] == "product_condition"
                for f in TUNING_SEARCH_FILTERS_BY_SLUG[FILMS_SLUG]
            )
    finally:
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
        app.dependency_overrides.clear()
    print("test_tuning_accessories_v2 OK")


def test_tuning_accessories_v2() -> None:
    asyncio.run(_run_all())
