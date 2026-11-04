# -*- coding: utf-8 -*-
"""Transport Auto Parts V2 — taxonomy, schemas, filters, search E2E."""
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
from app.seeds.auto_parts_v2 import (
    BODY_LEAF_ID,
    BODY_LEAF_SLUG,
    BODY_RETIRED_IDS,
    ELECTRICAL_PART_NAMES,
    ENGINE_PART_NAMES,
    OPTICS_LEAF_ID,
    PARTS_CORE_FIELDS_BY_SLUG,
    PARTS_LEAF_ALIASES,
    PARTS_PARENT_ID,
    PARTS_PARENT_SLUG,
    PARTS_PART_NAME_ALIASES,
    PARTS_SEARCH_FILTERS_BY_SLUG,
    PARTS_SERVICE_BOUNDARY_ALIASES,
    PASSENGER_SYSTEM_EXPECTED_IDS,
    PASSENGER_SYSTEM_LABELS,
    PASSENGER_SYSTEM_SLUGS,
    SPECIAL_SYSTEM_EXPECTED_IDS,
    SPECIAL_SYSTEM_SLUGS,
    UNIVERSAL_INACTIVE_ID,
    normalize_part_number,
)
from app.seeds.parts_passenger_cars import PASSENGER_CAR_SECTIONS


PHYSICAL_REQUIRED = {
    "part_name",
    "part_condition",
    "price",
    "seller_type",
    "contact_methods",
    "region",
    "city",
}

CONDITION_EXEMPT = {
    "transport-auto-parts-masla-zhidkosti-i-rashodniki",
    "transport-auto-parts-krepezh-rezinki-i-melkie-detali",
}


def _auth_user(user_id: int = 1) -> None:
    now = datetime.now(UTC)

    async def _user() -> UserRead:
        return UserRead(
            id=user_id,
            phone="+79001234567",
            full_name="AutoPartsV2Tester",
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


def _core_keys(fields: list) -> set[str]:
    return {f[0] for f in fields}


async def _run_all() -> None:
    assert normalize_part_number("90915-YZZD2") == "90915yzzd2"
    assert normalize_part_number("90915 YZZD2") == "90915yzzd2"
    assert normalize_part_number(" 90915-yzzd2 ") == "90915yzzd2"

    for slug, fields in PARTS_CORE_FIELDS_BY_SLUG.items():
        keys = _core_keys(fields)
        assert "part_manufacturer" not in keys, slug
        assert "part_number" not in keys, slug
        assert "oem_number" not in keys, slug
    for slug, filters in PARTS_SEARCH_FILTERS_BY_SLUG.items():
        fkeys = {f[0] for f in filters}
        assert "part_manufacturer" not in fkeys, slug
        assert "part_number" not in fkeys, slug
        assert "oem_number" not in fkeys, slug

    # Engine must not list starter/generator; Electrical must.
    assert "Стартер" not in ENGINE_PART_NAMES
    assert "Генератор" not in ENGINE_PART_NAMES
    assert "Стартер" in ELECTRICAL_PART_NAMES
    assert "Генератор" in ELECTRICAL_PART_NAMES

    # Parts Catalog API: no live starter/generator under engine section.
    engine_sec = next(s for s in PASSENGER_CAR_SECTIONS if s[0] == "engine")
    engine_vals = {it[0] for it in engine_sec[2]}
    assert "starter" not in engine_vals
    assert "alternator" not in engine_vals

    async with async_session_maker() as session:
        parent = (
            await session.execute(
                text("SELECT id, is_active FROM categories WHERE slug = :s"),
                {"s": PARTS_PARENT_SLUG},
            )
        ).mappings().one()
        assert parent["is_active"] is True
        assert int(parent["id"]) == PARTS_PARENT_ID

        parent_fields = (
            await session.execute(
                text(
                    "SELECT COUNT(*) FROM category_core_fields WHERE category_id = :id"
                ),
                {"id": PARTS_PARENT_ID},
            )
        ).scalar_one()
        assert int(parent_fields) == 0

        parent_filters = (
            await session.execute(
                text(
                    "SELECT COUNT(*) FROM category_filters WHERE category_id = :id"
                ),
                {"id": PARTS_PARENT_ID},
            )
        ).scalar_one()
        assert int(parent_filters) == 0

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
                {"pid": PARTS_PARENT_ID},
            )
        ).mappings().all()

        passenger = [r for r in active if r["slug"] in PASSENGER_SYSTEM_SLUGS]
        special = [r for r in active if r["slug"] in SPECIAL_SYSTEM_SLUGS]
        assert len(passenger) == 17, [r["slug"] for r in passenger]
        assert {r["slug"] for r in passenger} == set(PASSENGER_SYSTEM_SLUGS)
        for r in passenger:
            assert r["name"] == PASSENGER_SYSTEM_LABELS[r["slug"]]
            assert int(r["id"]) == PASSENGER_SYSTEM_EXPECTED_IDS[r["slug"]]

        assert len(special) == 3, [r["slug"] for r in special]
        for slug, expected_id in SPECIAL_SYSTEM_EXPECTED_IDS.items():
            row = next(r for r in special if r["slug"] == slug)
            assert int(row["id"]) == expected_id

        # Body oversplit retired.
        for rid in BODY_RETIRED_IDS:
            active_flag = (
                await session.execute(
                    text("SELECT is_active FROM categories WHERE id = :id"),
                    {"id": rid},
                )
            ).scalar_one()
            assert active_flag is False

        optics = (
            await session.execute(
                text("SELECT is_active, name FROM categories WHERE id = :id"),
                {"id": OPTICS_LEAF_ID},
            )
        ).mappings().one()
        assert optics["is_active"] is True

        uni = (
            await session.execute(
                text("SELECT is_active FROM categories WHERE id = :id"),
                {"id": UNIVERSAL_INACTIVE_ID},
            )
        ).scalar_one()
        assert uni is False

        body = (
            await session.execute(
                text("SELECT slug, name, is_active FROM categories WHERE id = :id"),
                {"id": BODY_LEAF_ID},
            )
        ).mappings().one()
        assert body["slug"] == BODY_LEAF_SLUG
        assert body["name"] == "Кузов"
        assert body["is_active"] is True

        # Leaf schemas non-empty + requiredness.
        for slug in PASSENGER_SYSTEM_SLUGS:
            cid = await _slug_id(session, slug)
            rows = (
                await session.execute(
                    text(
                        """
                        SELECT field_key, is_required, field_type::text
                        FROM category_core_fields
                        WHERE category_id = :cid
                        ORDER BY sort_order
                        """
                    ),
                    {"cid": cid},
                )
            ).mappings().all()
            assert rows, f"empty core_fields for {slug}"
            keys = {r["field_key"] for r in rows}
            assert "vehicle_brand" in keys
            assert "vehicle_model" in keys
            assert "brand" not in keys
            assert "model" not in keys
            assert "oem_number" not in keys
            assert "part_number" not in keys
            assert "part_manufacturer" not in keys
            assert "seller_type" in keys
            assert "price" in keys
            # No free-text characteristic rows (region is pinned geo, not a
            # characteristics text input).
            string_keys = {
                r["field_key"]
                for r in rows
                if r["field_type"] == "string"
            }
            assert string_keys <= {"region"}, (
                f"{slug} unexpected string characteristics: {string_keys}"
            )

            filt_keys = {
                r[0]
                for r in (
                    await session.execute(
                        text(
                            "SELECT filter_key FROM category_filters "
                            "WHERE category_id = :cid"
                        ),
                        {"cid": cid},
                    )
                ).all()
            }
            assert "part_manufacturer" not in filt_keys
            assert "part_number" not in filt_keys
            assert "oem_number" not in filt_keys
            if slug in CONDITION_EXEMPT:
                assert "part_condition" not in keys
            else:
                assert "part_condition" in keys
                cond = next(r for r in rows if r["field_key"] == "part_condition")
                assert cond["is_required"] is True
            if slug not in (
                "transport-auto-parts-podshipniki",
                "transport-auto-parts-drugoe",
            ):
                assert "part_name" in keys
                pn = next(r for r in rows if r["field_key"] == "part_name")
                assert pn["is_required"] is True

            filt_count = (
                await session.execute(
                    text(
                        "SELECT COUNT(*) FROM category_filters WHERE category_id = :cid"
                    ),
                    {"cid": cid},
                )
            ).scalar_one()
            assert int(filt_count) > 0, slug

            # Seed SoT matches DB for key set.
            seed_keys = _core_keys(PARTS_CORE_FIELDS_BY_SLUG[slug])
            assert keys == seed_keys, (slug, keys ^ seed_keys)

        # Optics part_name options include Фара.
        optics_id = await _slug_id(
            session, "transport-auto-parts-optika-fary-i-fonari"
        )
        optics_opts = (
            await session.execute(
                text(
                    """
                    SELECT options FROM category_core_fields
                    WHERE category_id = :cid AND field_key = 'part_name'
                    """
                ),
                {"cid": optics_id},
            )
        ).scalar_one()
        labels = [c["label"] for c in (optics_opts or {}).get("choices", [])]
        assert "Фара" in labels
        assert "Задний фонарь" in labels

        # Seller vocabulary.
        seller_opts = (
            await session.execute(
                text(
                    """
                    SELECT options FROM category_core_fields
                    WHERE category_id = :cid AND field_key = 'seller_type'
                    """
                ),
                {"cid": optics_id},
            )
        ).scalar_one()
        seller_labels = [c["label"] for c in (seller_opts or {}).get("choices", [])]
        assert seller_labels == ["Частное лицо", "Магазин", "Авторазбор"]

        # Aliases.
        for alias, slug in PARTS_LEAF_ALIASES.items():
            target = (
                await session.execute(
                    text(
                        """
                        SELECT c.slug FROM category_aliases a
                        JOIN categories c ON c.id = a.category_id
                        WHERE a.alias_normalized = :a AND a.is_enabled
                        """
                    ),
                    {"a": alias},
                )
            ).scalar_one_or_none()
            assert target == slug, (alias, target, slug)

        for alias, slug in PARTS_SERVICE_BOUNDARY_ALIASES.items():
            target = (
                await session.execute(
                    text(
                        """
                        SELECT c.slug FROM category_aliases a
                        JOIN categories c ON c.id = a.category_id
                        WHERE a.alias_normalized = :a AND a.is_enabled
                        """
                    ),
                    {"a": alias},
                )
            ).scalar_one_or_none()
            assert target is not None, alias
            assert "services" in target or target == slug

        # LED must not point at Optics.
        led_optics = (
            await session.execute(
                text(
                    """
                    SELECT COUNT(*) FROM category_aliases
                    WHERE alias_normalized = 'led'
                      AND category_id = :oid
                      AND is_enabled = true
                    """
                ),
                {"oid": OPTICS_LEAF_ID},
            )
        ).scalar_one()
        assert int(led_optics) == 0

        for alias, (sys_slug, part_label) in PARTS_PART_NAME_ALIASES.items():
            assert PARTS_LEAF_ALIASES[alias] == sys_slug
            names = PARTS_CORE_FIELDS_BY_SLUG[sys_slug]
            part_field = next(f for f in names if f[0] == "part_name")
            choices = (part_field[5] or {}).get("choices", [])
            assert any(c["label"] == part_label for c in choices), (
                alias,
                part_label,
            )

    # --- Search E2E fixtures (direct DB, same pattern as Farm/Rental V2) ---
    async def _insert_active(
        session, *, title, price, cid, oid, eav, brand_id=None, model_id=None
    ):
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
        if brand_id is not None:
            await session.execute(
                text(
                    """
                    INSERT INTO listing_field_values
                    (listing_id, field_key, ref_brand_id, created_at, updated_at)
                    VALUES (:lid, 'vehicle_brand', :bid, now(), now())
                    """
                ),
                {"lid": new_id, "bid": brand_id},
            )
        if model_id is not None:
            await session.execute(
                text(
                    """
                    INSERT INTO listing_field_values
                    (listing_id, field_key, ref_model_id, created_at, updated_at)
                    VALUES (:lid, 'vehicle_model', :mid, now(), now())
                    """
                ),
                {"lid": new_id, "mid": model_id},
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
                optics_cid = await _slug_id(
                    session, "transport-auto-parts-optika-fary-i-fonari"
                )
                transmission_cid = await _slug_id(
                    session,
                    "transport-auto-parts-korobka-peredach-i-transmissiya",
                )
                consumable_cid = await _slug_id(
                    session,
                    "transport-auto-parts-masla-zhidkosti-i-rashodniki",
                )
                fastener_cid = await _slug_id(
                    session,
                    "transport-auto-parts-krepezh-rezinki-i-melkie-detali",
                )
                body_cid = await _slug_id(session, BODY_LEAF_SLUG)

                toyota = (
                    await session.execute(
                        text(
                            """
                            SELECT id, name FROM vehicle_brands
                            WHERE lower(name) = 'toyota' AND is_enabled
                            LIMIT 1
                            """
                        )
                    )
                ).mappings().first()
                hyundai = (
                    await session.execute(
                        text(
                            """
                            SELECT id, name FROM vehicle_brands
                            WHERE lower(name) = 'hyundai' AND is_enabled
                            LIMIT 1
                            """
                        )
                    )
                ).mappings().first()
                camry = None
                sonata = None
                if toyota:
                    camry = (
                        await session.execute(
                            text(
                                """
                                SELECT id, name FROM vehicle_models
                                WHERE brand_id = :bid AND lower(name) LIKE 'camry%'
                                  AND is_enabled LIMIT 1
                                """
                            ),
                            {"bid": toyota["id"]},
                        )
                    ).mappings().first()
                if hyundai:
                    sonata = (
                        await session.execute(
                            text(
                                """
                                SELECT id, name FROM vehicle_models
                                WHERE brand_id = :bid AND lower(name) LIKE 'sonata%'
                                  AND is_enabled LIMIT 1
                                """
                            ),
                            {"bid": hyundai["id"]},
                        )
                    ).mappings().first()

                lid_hl = await _insert_active(
                    session,
                    title="APV2 used headlight",
                    price=5000,
                    cid=optics_cid,
                    oid=owner_id,
                    eav={
                        "part_name": "Фара",
                        "part_condition": "Б/у",
                        "part_origin_type": "Оригинал",
                        "side": "Левая",
                        "seller_type": "Авторазбор",
                    },
                    brand_id=toyota["id"] if toyota else None,
                    model_id=camry["id"] if camry else None,
                )
                lid_gb = await _insert_active(
                    session,
                    title="APV2 gearbox",
                    price=80000,
                    cid=transmission_cid,
                    oid=owner_id,
                    eav={
                        "part_name": "КПП в сборе",
                        "part_condition": "Б/у",
                        "transmission_type": "АКПП",
                        "seller_type": "Магазин",
                    },
                    brand_id=hyundai["id"] if hyundai else None,
                    model_id=sonata["id"] if sonata else None,
                )
                lid_oil = await _insert_active(
                    session,
                    title="APV2 oil filter",
                    price=1000,
                    cid=consumable_cid,
                    oid=owner_id,
                    eav={
                        "part_name": "Масляный фильтр",
                        "part_origin_type": "Аналог",
                        "seller_type": "Магазин",
                    },
                )
                lid_fast = await _insert_active(
                    session,
                    title="APV2 clip",
                    price=50,
                    cid=fastener_cid,
                    oid=owner_id,
                    eav={
                        "part_name": "Клипса",
                        "seller_type": "Частное лицо",
                    },
                )
                lid_door = await _insert_active(
                    session,
                    title="APV2 door",
                    price=12000,
                    cid=body_cid,
                    oid=owner_id,
                    eav={
                        "part_name": "Дверь",
                        "part_condition": "Б/у",
                        "side": "Левая",
                        "position": "Передняя",
                        "seller_type": "Авторазбор",
                    },
                )
                lid_nb = await _insert_active(
                    session,
                    title="APV2 no-brand headlight",
                    price=7000,
                    cid=optics_cid,
                    oid=owner_id,
                    eav={
                        "part_name": "Фара",
                        "part_condition": "Новая",
                        "seller_type": "Магазин",
                    },
                )
                await session.commit()
                created.extend(
                    [lid_hl, lid_gb, lid_oil, lid_fast, lid_door, lid_nb]
                )
                toyota_name = toyota["name"] if toyota else None
                camry_name = camry["name"] if camry else None
                hyundai_name = hyundai["name"] if hyundai else None

            async def _ids(params: dict) -> set[int]:
                r = await client.get("/api/v1/listings", params=params)
                assert r.status_code == 200, r.text
                return {int(x["id"]) for x in r.json()["items"]}

            optics_slug = "transport-auto-parts-optika-fary-i-fonari"
            transmission_slug = (
                "transport-auto-parts-korobka-peredach-i-transmissiya"
            )
            body_slug = BODY_LEAF_SLUG

            found = await _ids(
                {
                    "category_slug": optics_slug,
                    "attrs": json.dumps({"part_name": "Фара"}, ensure_ascii=False),
                    "limit": 100,
                }
            )
            assert lid_hl in found
            wrong = await _ids(
                {
                    "category_slug": optics_slug,
                    "attrs": json.dumps(
                        {"part_name": "Задний фонарь"}, ensure_ascii=False
                    ),
                    "limit": 100,
                }
            )
            assert lid_hl not in wrong

            found = await _ids(
                {
                    "category_slug": optics_slug,
                    "attrs": json.dumps(
                        {"part_condition": "Б/у"}, ensure_ascii=False
                    ),
                    "limit": 100,
                }
            )
            assert lid_hl in found
            wrong = await _ids(
                {
                    "category_slug": optics_slug,
                    "attrs": json.dumps(
                        {"part_condition": "Новая"}, ensure_ascii=False
                    ),
                    "limit": 100,
                }
            )
            assert lid_hl not in wrong

            found = await _ids(
                {
                    "category_slug": optics_slug,
                    "attrs": json.dumps(
                        {"part_origin_type": "Оригинал"}, ensure_ascii=False
                    ),
                    "limit": 100,
                }
            )
            assert lid_hl in found
            wrong = await _ids(
                {
                    "category_slug": optics_slug,
                    "attrs": json.dumps(
                        {"part_origin_type": "Аналог"}, ensure_ascii=False
                    ),
                    "limit": 100,
                }
            )
            assert lid_hl not in wrong

            found = await _ids(
                {
                    "category_slug": optics_slug,
                    "attrs": json.dumps(
                        {"seller_type": "Авторазбор"}, ensure_ascii=False
                    ),
                    "limit": 100,
                }
            )
            assert lid_hl in found
            wrong = await _ids(
                {
                    "category_slug": optics_slug,
                    "attrs": json.dumps(
                        {"seller_type": "Магазин"}, ensure_ascii=False
                    ),
                    "limit": 100,
                }
            )
            assert lid_hl not in wrong

            found = await _ids(
                {
                    "category_slug": optics_slug,
                    "attrs": json.dumps({"side": "Левая"}, ensure_ascii=False),
                    "limit": 100,
                }
            )
            assert lid_hl in found
            wrong = await _ids(
                {
                    "category_slug": optics_slug,
                    "attrs": json.dumps({"side": "Правая"}, ensure_ascii=False),
                    "limit": 100,
                }
            )
            assert lid_hl not in wrong

            if toyota_name and camry_name:
                found = await _ids(
                    {
                        "category_slug": optics_slug,
                        "brand": toyota_name,
                        "model": camry_name,
                        "limit": 100,
                    }
                )
                assert lid_hl in found
                found = await _ids(
                    {
                        "category_slug": optics_slug,
                        "brand": toyota_name,
                        "limit": 100,
                    }
                )
                assert lid_hl in found
                if hyundai_name:
                    wrong = await _ids(
                        {
                            "category_slug": optics_slug,
                            "brand": hyundai_name,
                            "limit": 100,
                        }
                    )
                    assert lid_hl not in wrong

            found = await _ids(
                {
                    "category_slug": transmission_slug,
                    "attrs": json.dumps(
                        {
                            "part_name": "КПП в сборе",
                            "transmission_type": "АКПП",
                        },
                        ensure_ascii=False,
                    ),
                    "limit": 100,
                }
            )
            assert lid_gb in found
            wrong = await _ids(
                {
                    "category_slug": transmission_slug,
                    "attrs": json.dumps(
                        {
                            "part_name": "КПП в сборе",
                            "transmission_type": "МКПП",
                        },
                        ensure_ascii=False,
                    ),
                    "limit": 100,
                }
            )
            assert lid_gb not in wrong

            found = await _ids(
                {
                    "category_slug": body_slug,
                    "attrs": json.dumps(
                        {
                            "part_name": "Дверь",
                            "side": "Левая",
                            "position": "Передняя",
                        },
                        ensure_ascii=False,
                    ),
                    "limit": 100,
                }
            )
            assert lid_door in found
            wrong = await _ids(
                {
                    "category_slug": body_slug,
                    "attrs": json.dumps(
                        {
                            "part_name": "Дверь",
                            "side": "Правая",
                            "position": "Передняя",
                        },
                        ensure_ascii=False,
                    ),
                    "limit": 100,
                }
            )
            assert lid_door not in wrong

            assert lid_oil in created and lid_fast in created and lid_nb in created
            seed_consumable = PARTS_SEARCH_FILTERS_BY_SLUG[
                "transport-auto-parts-masla-zhidkosti-i-rashodniki"
            ]
            assert not any(f[0] == "part_condition" for f in seed_consumable)
    finally:
        if created:
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


def test_auto_parts_v2() -> None:
    asyncio.run(_run_all())
