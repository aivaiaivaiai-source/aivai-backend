# -*- coding: utf-8 -*-
"""Trailers Sale V2 — taxonomy, schemas, filters, remaps, search execution."""
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
from app.seeds.trailer_sale_v2 import (
    AXLE_COUNT_SENTINEL_5_PLUS,
    AXLE_COUNT_VALUES,
    CARAVAN_AMENITIES,
    SEMI_BODY_TYPES,
    TRAILER_CORE_FIELDS_BY_SLUG,
    TRAILER_INACTIVE_LEGACY_SLUGS,
    TRAILER_LEAF_SLUGS,
    TRAILER_LEAF_SORT,
    TRAILER_LEAF_VEHICLE_TYPE,
    TRAILER_OTHER_BRAND_TYPES,
    TRAILER_PARENT_SLUG,
    TRAILER_PURPOSES,
    TRAILER_REMAP_TARGETS,
    TRAILER_SEARCH_FILTERS_BY_SLUG,
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
            full_name="TrailerSaleV2Tester",
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
                {"s": TRAILER_PARENT_SLUG},
            )
        ).mappings().one()
        assert parent["is_active"] is True
        assert int(parent["id"]) == 693

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
                {"pid": 693},
            )
        ).mappings().all()
        assert [r["slug"] for r in active] == list(TRAILER_LEAF_SLUGS)
        assert {r["slug"]: r["sort_order"] for r in active} == TRAILER_LEAF_SORT
        assert {r["id"] for r in active} == {1226, 824, 1227}
        assert len({r["sort_order"] for r in active}) == 3

        for slug in TRAILER_INACTIVE_LEGACY_SLUGS:
            row = (
                await session.execute(
                    text(
                        "SELECT is_active FROM categories WHERE slug = :s"
                    ),
                    {"s": slug},
                )
            ).mappings().one()
            assert row["is_active"] is False

        assert TRAILER_REMAP_TARGETS[
            "transport-watercraft-pritsepy-dlya-vodnogo-transporta"
        ] == "transport-trailers-pritsepy"
        assert TRAILER_REMAP_TARGETS[
            "transport-farm-machinery-pritsepy-dlya-selhoztehniki"
        ] == "transport-trailers-pritsepy"

        parent_n = (
            await session.execute(
                text(
                    """
                    SELECT COUNT(*) FROM category_core_fields
                    WHERE category_id = 693
                    """
                )
            )
        ).scalar_one()
        assert parent_n == 0

        for slug in TRAILER_LEAF_SLUGS:
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
            assert len(fields) > 0
            by = {r["field_key"]: r for r in fields}
            for key in REQUIRED_KEYS:
                assert key in by
                assert by[key]["is_required"] is True
            for opt_key in ("brand", "model", "year"):
                assert by[opt_key]["is_required"] is False

            for r in fields:
                if r["field_type"] in {"enum", "multi_select"}:
                    opts = r["options"] or {}
                    choices = opts.get("choices") or opts.get("values") or []
                    assert choices, f"{slug}.{r['field_key']} null options"

        drawbar = {
            r["field_key"]: r
            for r in (
                await session.execute(
                    text(
                        """
                        SELECT ccf.field_key, ccf.options
                        FROM category_core_fields ccf
                        JOIN categories c ON c.id = ccf.category_id
                        WHERE c.slug = 'transport-trailers-pritsepy'
                        """
                    )
                )
            ).mappings()
        }
        purpose_vals = [
            c["value"]
            for c in (drawbar["trailer_purpose"]["options"] or {}).get(
                "choices", []
            )
        ]
        assert purpose_vals == list(TRAILER_PURPOSES)
        axle_vals = [
            c["value"]
            for c in (drawbar["axle_count"]["options"] or {}).get("choices", [])
        ]
        assert axle_vals == list(AXLE_COUNT_VALUES)
        assert AXLE_COUNT_SENTINEL_5_PLUS in axle_vals

        semi = {
            r["field_key"]: r
            for r in (
                await session.execute(
                    text(
                        """
                        SELECT ccf.field_key, ccf.options
                        FROM category_core_fields ccf
                        JOIN categories c ON c.id = ccf.category_id
                        WHERE c.slug = 'transport-trailers-polupritsepy'
                        """
                    )
                )
            ).mappings()
        }
        body_vals = [
            c["value"]
            for c in (semi["semi_body_type"]["options"] or {}).get(
                "choices", []
            )
        ]
        assert body_vals == list(SEMI_BODY_TYPES)
        assert "payload_kg" not in semi
        assert "load_capacity_kg" in semi
        tank_dep = (semi["tank_capacity_l"]["options"] or {}).get("depends_on")
        assert tank_dep["field"] == "semi_body_type"
        assert "Цистерна" in tank_dep["values"]
        dump_dep = (semi["body_volume_m3"]["options"] or {}).get("depends_on")
        assert "Самосвальный" in dump_dep["values"]
        lowbed_dep = (semi["length_m"]["options"] or {}).get("depends_on")
        assert "Трал / низкорамный" in lowbed_dep["values"]

        camper = {
            r["field_key"]: r
            for r in (
                await session.execute(
                    text(
                        """
                        SELECT ccf.field_key, ccf.is_required, ccf.options
                        FROM category_core_fields ccf
                        JOIN categories c ON c.id = ccf.category_id
                        WHERE c.slug = 'transport-trailers-zhilye-pritsepy-kempery'
                        """
                    )
                )
            ).mappings()
        }
        assert camper["sleeping_places"]["is_required"] is False
        am_vals = [
            c["value"]
            for c in (camper["amenities"]["options"] or {}).get("choices", [])
        ]
        assert am_vals == list(CARAVAN_AMENITIES)

        for slug in TRAILER_LEAF_SLUGS:
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
            assert keys
            assert "has_photo" not in keys
            assert len(TRAILER_SEARCH_FILTERS_BY_SLUG[slug]) == len(keys)

        for vt in TRAILER_OTHER_BRAND_TYPES:
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
            assert n >= 1

    assert TRAILER_LEAF_VEHICLE_TYPE["transport-trailers-pritsepy"] == (
        "drawbar_trailer"
    )
    assert TRAILER_LEAF_VEHICLE_TYPE["transport-trailers-polupritsepy"] == (
        "semi_trailer"
    )
    assert TRAILER_LEAF_VEHICLE_TYPE[
        "transport-trailers-zhilye-pritsepy-kempery"
    ] == "camper_trailer"
    assert set(TRAILER_CORE_FIELDS_BY_SLUG) == set(TRAILER_LEAF_SLUGS)

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
                drawbar_cid = await _slug_id(
                    session, "transport-trailers-pritsepy"
                )
                semi_cid = await _slug_id(
                    session, "transport-trailers-polupritsepy"
                )
                camper_cid = await _slug_id(
                    session, "transport-trailers-zhilye-pritsepy-kempery"
                )

                drawbar_id = await _insert_active(
                    session,
                    title="TrailerV2 boat purpose e2e",
                    price=80000,
                    cid=drawbar_cid,
                    oid=owner_id,
                    eav={
                        "trailer_purpose": "Для лодки",
                        "axle_count": "2",
                        "condition": "Хорошее",
                        "negotiable": "Есть торг",
                        "seller_type": "Частное лицо",
                    },
                )
                tanker_id = await _insert_active(
                    session,
                    title="TrailerV2 tanker e2e",
                    price=1500000,
                    cid=semi_cid,
                    oid=owner_id,
                    eav={
                        "semi_body_type": "Цистерна",
                        "tank_capacity_l": 30000,
                        "tanker_purpose": "Топливная",
                        "axle_count": "3",
                        "condition": "Хорошее",
                    },
                )
                dump_id = await _insert_active(
                    session,
                    title="TrailerV2 dump e2e",
                    price=900000,
                    cid=semi_cid,
                    oid=owner_id,
                    eav={
                        "semi_body_type": "Самосвальный",
                        "body_volume_m3": 28.0,
                        "load_capacity_kg": 25000,
                        "condition": "Хорошее",
                    },
                )
                lowbed_id = await _insert_active(
                    session,
                    title="TrailerV2 lowbed e2e",
                    price=2000000,
                    cid=semi_cid,
                    oid=owner_id,
                    eav={
                        "semi_body_type": "Трал / низкорамный",
                        "length_m": 12.5,
                        "load_capacity_kg": 40000,
                        "condition": "Хорошее",
                    },
                )
                caravan_id = await _insert_active(
                    session,
                    title="TrailerV2 caravan e2e",
                    price=450000,
                    cid=camper_cid,
                    oid=owner_id,
                    eav={
                        "sleeping_places": 4,
                        "length_m": 7.2,
                        "condition": "Хорошее",
                    },
                )
                await session.commit()
                created.extend(
                    [drawbar_id, tanker_id, dump_id, lowbed_id, caravan_id]
                )

            async def _ids(params: dict) -> set[int]:
                r = await client.get("/api/v1/listings", params=params)
                assert r.status_code == 200, r.text
                return {int(x["id"]) for x in r.json()["items"]}

            found = await _ids(
                {
                    "category_slug": "transport-trailers-pritsepy",
                    "attrs": json.dumps(
                        {"trailer_purpose": "Для лодки"}, ensure_ascii=False
                    ),
                    "limit": 100,
                }
            )
            assert drawbar_id in found
            not_found = await _ids(
                {
                    "category_slug": "transport-trailers-pritsepy",
                    "attrs": json.dumps(
                        {"trailer_purpose": "Сельскохозяйственный"},
                        ensure_ascii=False,
                    ),
                    "limit": 100,
                }
            )
            assert drawbar_id not in not_found

            found = await _ids(
                {
                    "category_slug": "transport-trailers-pritsepy",
                    "attrs": json.dumps({"axle_count": "2"}, ensure_ascii=False),
                    "limit": 100,
                }
            )
            assert drawbar_id in found
            not_found = await _ids(
                {
                    "category_slug": "transport-trailers-pritsepy",
                    "attrs": json.dumps({"axle_count": "3"}, ensure_ascii=False),
                    "limit": 100,
                }
            )
            assert drawbar_id not in not_found

            found = await _ids(
                {
                    "category_slug": "transport-trailers-polupritsepy",
                    "attrs": json.dumps(
                        {
                            "semi_body_type": "Цистерна",
                            "tanker_purpose": "Топливная",
                            "tank_capacity_l__min": "25000",
                        },
                        ensure_ascii=False,
                    ),
                    "limit": 100,
                }
            )
            assert tanker_id in found
            not_found = await _ids(
                {
                    "category_slug": "transport-trailers-polupritsepy",
                    "attrs": json.dumps(
                        {
                            "semi_body_type": "Цистерна",
                            "tanker_purpose": "Пищевая",
                        },
                        ensure_ascii=False,
                    ),
                    "limit": 100,
                }
            )
            assert tanker_id not in not_found

            found = await _ids(
                {
                    "category_slug": "transport-trailers-polupritsepy",
                    "attrs": json.dumps(
                        {
                            "semi_body_type": "Самосвальный",
                            "body_volume_m3__min": "20",
                        },
                        ensure_ascii=False,
                    ),
                    "limit": 100,
                }
            )
            assert dump_id in found

            found = await _ids(
                {
                    "category_slug": "transport-trailers-polupritsepy",
                    "attrs": json.dumps(
                        {
                            "semi_body_type": "Трал / низкорамный",
                            "length_m__min": "10",
                            "load_capacity_kg__min": "35000",
                        },
                        ensure_ascii=False,
                    ),
                    "limit": 100,
                }
            )
            assert lowbed_id in found

            found = await _ids(
                {
                    "category_slug": "transport-trailers-zhilye-pritsepy-kempery",
                    "attrs": json.dumps(
                        {"sleeping_places__min": "4"}, ensure_ascii=False
                    ),
                    "limit": 100,
                }
            )
            assert caravan_id in found
            not_found = await _ids(
                {
                    "category_slug": "transport-trailers-zhilye-pritsepy-kempery",
                    "attrs": json.dumps(
                        {"sleeping_places__min": "6"}, ensure_ascii=False
                    ),
                    "limit": 100,
                }
            )
            assert caravan_id not in not_found

            for leaf_id in (1226, 824, 1227):
                intel = await client.get(
                    f"/api/v1/categories/intelligence/{leaf_id}"
                )
                assert intel.status_code == 200, intel.text
                body = intel.json()
                keys = {f["field_key"] for f in body.get("core_fields", [])}
                assert REQUIRED_KEYS.issubset(keys)
                filt_keys = {f["filter_key"] for f in body.get("filters", [])}
                assert "has_photo" not in filt_keys
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


def test_trailer_sale_v2() -> None:
    asyncio.run(_run_all())
