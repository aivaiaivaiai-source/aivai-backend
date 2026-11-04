# -*- coding: utf-8 -*-
"""Transport Tires & Wheels V2 — taxonomy, schemas, filters, search E2E."""
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
from app.seeds.tires_wheels_v2 import (
    COMPLETE_LEAF_SLUG,
    FASTENERS_LEAF_ID,
    FASTENERS_LEAF_SLUG,
    FASTENER_TYPE_CHOICES,
    LEAF_IDS,
    LEAF_LABELS,
    LEAF_SLUGS,
    OTHER_LEAF_ID,
    OTHER_LEAF_SLUG,
    OTHER_TYPE_CHOICES,
    PCD_APPLICABLE_CLASSES,
    RIMS_LEAF_SLUG,
    SEASON_CHOICES,
    SELLER_TYPE_CHOICES,
    TIRES_CORE_FIELDS_BY_SLUG,
    TIRES_LEAF_ALIASES,
    TIRES_LEAF_SLUG,
    TIRES_PARENT_ID,
    TIRES_PARENT_SLUG,
    TIRES_SEARCH_FILTERS_BY_SLUG,
    TIRES_SERVICE_BOUNDARY_ALIASES,
    TPMS_LEAF_ID,
    TPMS_LEAF_SLUG,
    VEHICLE_CLASS_OPTIONS,
    WHEEL_CONDITION_CHOICES,
    format_complete_wheel,
    format_rim_identity,
    format_tire_size,
)


def _auth_user(user_id: int = 1) -> None:
    now = datetime.now(UTC)

    async def _user() -> UserRead:
        return UserRead(
            id=user_id,
            phone="+79001234567",
            full_name="TiresWheelsV2Tester",
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


def _req_map(fields: list) -> dict[str, bool]:
    return {f[0]: bool(f[3]) for f in fields}


async def _run_all() -> None:
    assert format_tire_size("205", "55", "16") == "205/55 R16"
    assert format_rim_identity("17", "5x114.3") == "R17 · 5x114.3"
    assert (
        format_complete_wheel("205", "55", "16", "5x114.3")
        == "205/55 R16 · 5x114.3"
    )
    assert "bicycle" not in {v for v, _ in VEHICLE_CLASS_OPTIONS}
    assert set(PCD_APPLICABLE_CLASSES) == {"passenger", "cargo", "bus", "trailer"}

    async with async_session_maker() as session:
        parent = (
            await session.execute(
                text(
                    """
                    SELECT id, is_active, name
                    FROM categories WHERE slug = :s
                    """
                ),
                {"s": TIRES_PARENT_SLUG},
            )
        ).mappings().one()
        assert int(parent["id"]) == TIRES_PARENT_ID
        assert parent["is_active"] is True
        assert parent["name"] == "Шины и диски"

        parent_fields = (
            await session.execute(
                text(
                    "SELECT COUNT(*) FROM category_core_fields WHERE category_id = :id"
                ),
                {"id": TIRES_PARENT_ID},
            )
        ).scalar_one()
        assert int(parent_fields) == 0

        parent_filters = (
            await session.execute(
                text(
                    "SELECT COUNT(*) FROM category_filters WHERE category_id = :id"
                ),
                {"id": TIRES_PARENT_ID},
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
                {"pid": TIRES_PARENT_ID},
            )
        ).mappings().all()
        assert len(active) == 6, [r["slug"] for r in active]
        assert {r["slug"] for r in active} == set(LEAF_SLUGS)
        for r in active:
            assert r["name"] == LEAF_LABELS[r["slug"]]
            assert int(r["id"]) == LEAF_IDS[r["slug"]]

        other = (
            await session.execute(
                text("SELECT slug, name FROM categories WHERE id = :id"),
                {"id": OTHER_LEAF_ID},
            )
        ).mappings().one()
        assert other["slug"] == OTHER_LEAF_SLUG
        assert other["name"] == "Другое для шин и дисков"

        tpms = (
            await session.execute(
                text("SELECT id, slug, name, is_active FROM categories WHERE id = :id"),
                {"id": TPMS_LEAF_ID},
            )
        ).mappings().one()
        assert tpms["slug"] == TPMS_LEAF_SLUG
        assert tpms["is_active"] is True

        fasteners = (
            await session.execute(
                text("SELECT id, slug, name, is_active FROM categories WHERE id = :id"),
                {"id": FASTENERS_LEAF_ID},
            )
        ).mappings().one()
        assert fasteners["slug"] == FASTENERS_LEAF_SLUG
        assert fasteners["is_active"] is True

        for slug in LEAF_SLUGS:
            cid = await _slug_id(session, slug)
            rows = (
                await session.execute(
                    text(
                        """
                        SELECT field_key, is_required, field_type::text, options
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
            seed_keys = _core_keys(TIRES_CORE_FIELDS_BY_SLUG[slug])
            assert keys == seed_keys, (slug, keys ^ seed_keys)
            seed_req = _req_map(TIRES_CORE_FIELDS_BY_SLUG[slug])
            for r in rows:
                assert bool(r["is_required"]) == seed_req[r["field_key"]], (
                    slug,
                    r["field_key"],
                )

            string_keys = {
                r["field_key"] for r in rows if r["field_type"] == "string"
            }
            assert string_keys <= {"region"}, (
                f"{slug} unexpected string characteristics: {string_keys}"
            )

            # No vehicle Brand/Model passport.
            assert "brand" not in keys
            assert "model" not in keys
            assert "vehicle_brand" not in keys
            assert "vehicle_model" not in keys

            filt_count = (
                await session.execute(
                    text(
                        "SELECT COUNT(*) FROM category_filters WHERE category_id = :cid"
                    ),
                    {"cid": cid},
                )
            ).scalar_one()
            assert int(filt_count) > 0, slug
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
            seed_fkeys = {f[0] for f in TIRES_SEARCH_FILTERS_BY_SLUG[slug]}
            assert filt_keys == seed_fkeys, (slug, filt_keys ^ seed_fkeys)
            assert "has_photo" not in filt_keys
            assert "photo" not in filt_keys

            # Required pickers must have non-empty options.
            for r in rows:
                if not r["is_required"]:
                    continue
                if r["field_type"] not in ("enum", "multi_select"):
                    continue
                opts = r["options"] or {}
                choices = opts.get("choices") or opts.get("values") or []
                assert choices, f"{slug}.{r['field_key']} empty options"

        # Tires requiredness.
        tires_req = _req_map(TIRES_CORE_FIELDS_BY_SLUG[TIRES_LEAF_SLUG])
        for k in (
            "vehicle_class",
            "tire_width",
            "tire_profile",
            "rim_diameter",
            "season",
            "wheel_condition",
            "price",
            "seller_type",
            "contact_methods",
            "region",
            "city",
        ):
            assert tires_req[k] is True, k
        for k in ("studded", "tire_brand", "quantity", "negotiable"):
            assert tires_req[k] is False, k

        # Rims requiredness.
        rims_req = _req_map(TIRES_CORE_FIELDS_BY_SLUG[RIMS_LEAF_SLUG])
        for k in (
            "vehicle_class",
            "rim_diameter",
            "pcd",
            "wheel_condition",
            "price",
            "seller_type",
            "contact_methods",
        ):
            assert rims_req[k] is True, k
        for k in ("rim_width", "rim_material", "rim_brand", "quantity", "negotiable"):
            assert rims_req[k] is False, k
        assert "et" not in rims_req
        assert "dia" not in rims_req

        # Complete wheels.
        complete_req = _req_map(TIRES_CORE_FIELDS_BY_SLUG[COMPLETE_LEAF_SLUG])
        for k in (
            "vehicle_class",
            "tire_width",
            "tire_profile",
            "rim_diameter",
            "season",
            "pcd",
            "wheel_condition",
            "price",
            "seller_type",
            "contact_methods",
        ):
            assert complete_req[k] is True, k

        # TPMS — no size/PCD required.
        tpms_keys = _core_keys(TIRES_CORE_FIELDS_BY_SLUG[TPMS_LEAF_SLUG])
        assert "tire_width" not in tpms_keys
        assert "pcd" not in tpms_keys
        assert "oem_frequency" not in tpms_keys
        tpms_req = _req_map(TIRES_CORE_FIELDS_BY_SLUG[TPMS_LEAF_SLUG])
        assert tpms_req["price"] is True
        assert tpms_req["seller_type"] is True
        assert tpms_req.get("wheel_condition", False) is False

        # Fasteners / Other.
        fast_keys = _core_keys(TIRES_CORE_FIELDS_BY_SLUG[FASTENERS_LEAF_SLUG])
        assert "wheel_fastener_type" in fast_keys
        assert "wheel_condition" not in fast_keys
        other_keys = _core_keys(TIRES_CORE_FIELDS_BY_SLUG[OTHER_LEAF_SLUG])
        assert "wheel_other_type" in other_keys
        assert "wheel_condition" not in other_keys

        # Season / studded dependency in DB options.
        tires_cid = await _slug_id(session, TIRES_LEAF_SLUG)
        studded_row = (
            await session.execute(
                text(
                    """
                    SELECT options FROM category_core_fields
                    WHERE category_id = :cid AND field_key = 'studded'
                    """
                ),
                {"cid": tires_cid},
            )
        ).mappings().one()
        deps = (studded_row["options"] or {}).get("depends_on") or {}
        assert deps.get("field") == "season"
        assert "Зимние" in (deps.get("values") or [])

        # Condition vocabulary.
        cond_row = (
            await session.execute(
                text(
                    """
                    SELECT options FROM category_core_fields
                    WHERE category_id = :cid AND field_key = 'wheel_condition'
                    """
                ),
                {"cid": tires_cid},
            )
        ).mappings().one()
        labels = [
            c.get("value") or c.get("label")
            for c in (cond_row["options"] or {}).get("choices") or []
        ]
        assert set(labels) == set(WHEEL_CONDITION_CHOICES)
        assert "Восстановленные" not in labels

        # Seller vocabulary.
        seller_row = (
            await session.execute(
                text(
                    """
                    SELECT options FROM category_core_fields
                    WHERE category_id = :cid AND field_key = 'seller_type'
                    """
                ),
                {"cid": tires_cid},
            )
        ).mappings().one()
        seller_vals = [
            c.get("value") or c.get("label")
            for c in (seller_row["options"] or {}).get("choices") or []
        ]
        assert set(seller_vals) == set(SELLER_TYPE_CHOICES)
        assert "Авторазбор" not in seller_vals
        assert "Дилер" not in seller_vals

        # Season options exact.
        season_row = (
            await session.execute(
                text(
                    """
                    SELECT options FROM category_core_fields
                    WHERE category_id = :cid AND field_key = 'season'
                    """
                ),
                {"cid": tires_cid},
            )
        ).mappings().one()
        season_vals = [
            c.get("value") or c.get("label")
            for c in (season_row["options"] or {}).get("choices") or []
        ]
        assert set(season_vals) == set(SEASON_CHOICES)

        # Fastener / Other type options.
        fast_cid = await _slug_id(session, FASTENERS_LEAF_SLUG)
        fast_type = (
            await session.execute(
                text(
                    """
                    SELECT options FROM category_core_fields
                    WHERE category_id = :cid AND field_key = 'wheel_fastener_type'
                    """
                ),
                {"cid": fast_cid},
            )
        ).mappings().one()
        ft_vals = [
            c.get("value") or c.get("label")
            for c in (fast_type["options"] or {}).get("choices") or []
        ]
        assert set(ft_vals) == set(FASTENER_TYPE_CHOICES)

        other_cid = await _slug_id(session, OTHER_LEAF_SLUG)
        other_type = (
            await session.execute(
                text(
                    """
                    SELECT options FROM category_core_fields
                    WHERE category_id = :cid AND field_key = 'wheel_other_type'
                    """
                ),
                {"cid": other_cid},
            )
        ).mappings().one()
        ot_vals = [
            c.get("value") or c.get("label")
            for c in (other_type["options"] or {}).get("choices") or []
        ]
        assert set(ot_vals) == set(OTHER_TYPE_CHOICES)
        assert "Секретки" not in ot_vals
        assert "TPMS" not in ot_vals

        # Aliases.
        for alias, target in TIRES_LEAF_ALIASES.items():
            row = (
                await session.execute(
                    text(
                        """
                        SELECT c.slug
                        FROM category_aliases a
                        JOIN categories c ON c.id = a.category_id
                        WHERE a.alias_normalized = :a
                          AND a.locale = 'ru'
                          AND a.is_enabled
                        LIMIT 1
                        """
                    ),
                    {"a": alias},
                )
            ).scalar_one()
            assert row == target, (alias, row, target)

        for alias, target in TIRES_SERVICE_BOUNDARY_ALIASES.items():
            row = (
                await session.execute(
                    text(
                        """
                        SELECT c.slug
                        FROM category_aliases a
                        JOIN categories c ON c.id = a.category_id
                        WHERE a.alias_normalized = :a
                          AND a.locale = 'ru'
                          AND a.is_enabled
                        LIMIT 1
                        """
                    ),
                    {"a": alias},
                )
            ).scalar_one()
            assert row == target, (alias, row, target)

        # Auto Parts must not own TPMS / wheel-specific fasteners as leaves.
        ap_tpms = (
            await session.execute(
                text(
                    """
                    SELECT id FROM categories
                    WHERE parent_id = (
                      SELECT id FROM categories WHERE slug = 'transport-auto-parts'
                    )
                    AND (
                      slug ILIKE '%tpms%'
                      OR name ILIKE '%TPMS%'
                      OR name ILIKE '%датчик%давлен%'
                    )
                    AND is_active
                    """
                )
            )
        ).fetchall()
        assert not ap_tpms

        # Auto Services shinomontazh still exists.
        shino = (
            await session.execute(
                text(
                    """
                    SELECT slug, is_active FROM categories
                    WHERE slug = 'transport-auto-services-shinomontazh'
                    """
                )
            )
        ).mappings().one()
        assert shino["is_active"] is True

    # --- Real Search FOUND / NOT FOUND ---
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
                tires_cid = await _slug_id(session, TIRES_LEAF_SLUG)
                rims_cid = await _slug_id(session, RIMS_LEAF_SLUG)
                complete_cid = await _slug_id(session, COMPLETE_LEAF_SLUG)
                tpms_cid = await _slug_id(session, TPMS_LEAF_SLUG)
                fast_cid = await _slug_id(session, FASTENERS_LEAF_SLUG)
                other_cid = await _slug_id(session, OTHER_LEAF_SLUG)

                lid_tire = await _insert_active(
                    session,
                    title="TWV2 winter tires 205/55 R16",
                    price=20000,
                    cid=tires_cid,
                    oid=owner_id,
                    eav={
                        "vehicle_class": "passenger",
                        "tire_width": "205",
                        "tire_profile": "55",
                        "rim_diameter": "16",
                        "season": "Зимние",
                        "wheel_condition": "Б/у",
                        "quantity": "4",
                        "seller_type": "Частное лицо",
                    },
                )
                lid_rim = await _insert_active(
                    session,
                    title="TWV2 rims R17 5x114.3",
                    price=25000,
                    cid=rims_cid,
                    oid=owner_id,
                    eav={
                        "vehicle_class": "passenger",
                        "rim_diameter": "17",
                        "pcd": "5x114.3",
                        "wheel_condition": "Б/у",
                        "rim_material": "Литые",
                        "seller_type": "Магазин",
                    },
                )
                lid_complete = await _insert_active(
                    session,
                    title="TWV2 complete 205/55 R16 5x114.3",
                    price=45000,
                    cid=complete_cid,
                    oid=owner_id,
                    eav={
                        "vehicle_class": "passenger",
                        "tire_width": "205",
                        "tire_profile": "55",
                        "rim_diameter": "16",
                        "season": "Зимние",
                        "pcd": "5x114.3",
                        "wheel_condition": "Б/у",
                        "seller_type": "Магазин",
                    },
                )
                lid_tpms = await _insert_active(
                    session,
                    title="TWV2 TPMS sensors",
                    price=8000,
                    cid=tpms_cid,
                    oid=owner_id,
                    eav={
                        "wheel_condition": "Новые",
                        "seller_type": "Магазин",
                    },
                )
                lid_fast = await _insert_active(
                    session,
                    title="TWV2 locking nuts",
                    price=1500,
                    cid=fast_cid,
                    oid=owner_id,
                    eav={
                        "wheel_fastener_type": "Секретки",
                        "seller_type": "Частное лицо",
                    },
                )
                lid_other = await _insert_active(
                    session,
                    title="TWV2 hubcaps",
                    price=900,
                    cid=other_cid,
                    oid=owner_id,
                    eav={
                        "wheel_other_type": "Колпаки",
                        "seller_type": "Магазин",
                    },
                )
                await session.commit()
                created.extend(
                    [
                        lid_tire,
                        lid_rim,
                        lid_complete,
                        lid_tpms,
                        lid_fast,
                        lid_other,
                    ]
                )

            async def _ids(params: dict) -> set[int]:
                r = await client.get("/api/v1/listings", params=params)
                assert r.status_code == 200, r.text
                body = r.json()
                assert "total" in body
                return {int(x["id"]) for x in body["items"]}

            async def _total(params: dict) -> int:
                r = await client.get("/api/v1/listings", params=params)
                assert r.status_code == 200, r.text
                return int(r.json()["total"])

            # Tires size FOUND / NOT FOUND
            found = await _ids(
                {
                    "category_slug": TIRES_LEAF_SLUG,
                    "attrs": json.dumps(
                        {
                            "tire_width": "205",
                            "tire_profile": "55",
                            "rim_diameter": "16",
                            "season": "Зимние",
                        },
                        ensure_ascii=False,
                    ),
                    "limit": 100,
                }
            )
            assert lid_tire in found

            for wrong_attrs in (
                {"tire_width": "215", "tire_profile": "55", "rim_diameter": "16"},
                {"tire_width": "205", "tire_profile": "60", "rim_diameter": "16"},
                {"tire_width": "205", "tire_profile": "55", "rim_diameter": "17"},
                {"tire_width": "205", "tire_profile": "55", "rim_diameter": "16", "season": "Летние"},
            ):
                miss = await _ids(
                    {
                        "category_slug": TIRES_LEAF_SLUG,
                        "attrs": json.dumps(wrong_attrs, ensure_ascii=False),
                        "limit": 100,
                    }
                )
                assert lid_tire not in miss, wrong_attrs

            # Price total semantics — listing price not divided.
            tire_hit = await client.get(
                "/api/v1/listings",
                params={
                    "category_slug": TIRES_LEAF_SLUG,
                    "attrs": json.dumps(
                        {"tire_width": "205", "rim_diameter": "16"},
                        ensure_ascii=False,
                    ),
                    "limit": 100,
                },
            )
            assert tire_hit.status_code == 200
            tire_item = next(
                x for x in tire_hit.json()["items"] if int(x["id"]) == lid_tire
            )
            assert float(tire_item["price"]) == 20000.0

            # Rims PCD
            found = await _ids(
                {
                    "category_slug": RIMS_LEAF_SLUG,
                    "attrs": json.dumps(
                        {"rim_diameter": "17", "pcd": "5x114.3"},
                        ensure_ascii=False,
                    ),
                    "limit": 100,
                }
            )
            assert lid_rim in found
            miss = await _ids(
                {
                    "category_slug": RIMS_LEAF_SLUG,
                    "attrs": json.dumps({"pcd": "5x112"}, ensure_ascii=False),
                    "limit": 100,
                }
            )
            assert lid_rim not in miss
            miss = await _ids(
                {
                    "category_slug": RIMS_LEAF_SLUG,
                    "attrs": json.dumps(
                        {"rim_diameter": "18", "pcd": "5x114.3"},
                        ensure_ascii=False,
                    ),
                    "limit": 100,
                }
            )
            assert lid_rim not in miss

            # Complete wheels
            found = await _ids(
                {
                    "category_slug": COMPLETE_LEAF_SLUG,
                    "attrs": json.dumps(
                        {
                            "tire_width": "205",
                            "tire_profile": "55",
                            "rim_diameter": "16",
                            "season": "Зимние",
                            "pcd": "5x114.3",
                        },
                        ensure_ascii=False,
                    ),
                    "limit": 100,
                }
            )
            assert lid_complete in found
            miss = await _ids(
                {
                    "category_slug": COMPLETE_LEAF_SLUG,
                    "attrs": json.dumps({"pcd": "5x112"}, ensure_ascii=False),
                    "limit": 100,
                }
            )
            assert lid_complete not in miss

            # TPMS leaf isolation
            found = await _ids(
                {"category_slug": TPMS_LEAF_SLUG, "limit": 100}
            )
            assert lid_tpms in found
            rims_hit = await _ids(
                {"category_slug": RIMS_LEAF_SLUG, "limit": 100}
            )
            assert lid_tpms not in rims_hit
            tires_hit = await _ids(
                {"category_slug": TIRES_LEAF_SLUG, "limit": 100}
            )
            assert lid_tpms not in tires_hit

            # Fasteners subtype
            found = await _ids(
                {
                    "category_slug": FASTENERS_LEAF_SLUG,
                    "attrs": json.dumps(
                        {"wheel_fastener_type": "Секретки"}, ensure_ascii=False
                    ),
                    "limit": 100,
                }
            )
            assert lid_fast in found
            miss = await _ids(
                {
                    "category_slug": FASTENERS_LEAF_SLUG,
                    "attrs": json.dumps(
                        {"wheel_fastener_type": "Болты"}, ensure_ascii=False
                    ),
                    "limit": 100,
                }
            )
            assert lid_fast not in miss

            # Other subtype
            found = await _ids(
                {
                    "category_slug": OTHER_LEAF_SLUG,
                    "attrs": json.dumps(
                        {"wheel_other_type": "Колпаки"}, ensure_ascii=False
                    ),
                    "limit": 100,
                }
            )
            assert lid_other in found
            miss = await _ids(
                {
                    "category_slug": OTHER_LEAF_SLUG,
                    "attrs": json.dumps(
                        {"wheel_other_type": "Камеры"}, ensure_ascii=False
                    ),
                    "limit": 100,
                }
            )
            assert lid_other not in miss

            # Real totals
            total = await _total(
                {
                    "category_slug": TIRES_LEAF_SLUG,
                    "attrs": json.dumps(
                        {
                            "tire_width": "205",
                            "tire_profile": "55",
                            "rim_diameter": "16",
                            "season": "Зимние",
                        },
                        ensure_ascii=False,
                    ),
                    "limit": 100,
                }
            )
            assert total >= 1
            assert total != 55443

            # Sort
            for sort in ("newest", "price_asc", "price_desc"):
                r = await client.get(
                    "/api/v1/listings",
                    params={
                        "category_slug": TIRES_LEAF_SLUG,
                        "sort": sort,
                        "limit": 10,
                    },
                )
                assert r.status_code == 200, (sort, r.text)

            # Intelligence endpoint non-empty for leaves
            for slug in LEAF_SLUGS:
                r = await client.get(
                    f"/api/v1/categories/intelligence/{LEAF_IDS[slug]}"
                )
                assert r.status_code == 200, (slug, r.status_code, r.text)
                data = r.json()
                core = data.get("core_fields") or data.get("coreFields") or []
                assert core, slug
    finally:
        async with async_session_maker() as session:
            for lid in created:
                await session.execute(
                    text("DELETE FROM listing_field_values WHERE listing_id = :id"),
                    {"id": lid},
                )
                await session.execute(
                    text("DELETE FROM listings WHERE id = :id"),
                    {"id": lid},
                )
            await session.commit()
        app.dependency_overrides.pop(get_current_user, None)


def test_tires_wheels_v2() -> None:
    asyncio.run(_run_all())
