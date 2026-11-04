"""Electric Sale V2 — Backend SoT create/search cutover for 9 electric leaves."""
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
from app.seeds.electric_sale_v2 import (
    ELECTRIC_CORE_FIELDS_BY_SLUG,
    ELECTRIC_FORBIDDEN_FIELD_KEYS,
    ELECTRIC_INACTIVE_LEGACY_SLUGS,
    ELECTRIC_LEAF_LABELS,
    ELECTRIC_LEAF_SLUGS,
    ELECTRIC_LEAF_VEHICLE_TYPE,
    ELECTRIC_PARENT_SLUG,
    ELECTRIC_SEARCH_FILTERS_BY_SLUG,
    ELECTRIC_SUBTYPE_CHOICES,
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
            full_name="ElectricSaleV2Tester",
            is_active=True,
            balance=Decimal("0"),
            last_login=None,
            created_at=now,
            updated_at=now,
        )

    fastapi_app.dependency_overrides[get_current_user] = _user


async def _brand_model(session, vehicle_type: str, *, prefer_slug: str | None = None):
    if prefer_slug:
        brand = (
            await session.execute(
                text(
                    """
                    SELECT id, name, slug FROM vehicle_brands
                    WHERE is_enabled AND vehicle_type::text = :vt AND slug = :s
                    """
                ),
                {"vt": vehicle_type, "s": prefer_slug},
            )
        ).mappings().first()
        if brand is None:
            prefer_slug = None
    if prefer_slug is None:
        brand = (
            await session.execute(
                text(
                    """
                    SELECT id, name, slug FROM vehicle_brands
                    WHERE is_enabled AND vehicle_type::text = :vt
                      AND name <> 'Другая марка'
                    ORDER BY id LIMIT 1
                    """
                ),
                {"vt": vehicle_type},
            )
        ).mappings().one()
    model = (
        await session.execute(
            text(
                """
                SELECT id, name, slug FROM vehicle_models
                WHERE brand_id = :bid AND is_enabled AND name <> 'Другая модель'
                ORDER BY id LIMIT 1
                """
            ),
            {"bid": brand["id"]},
        )
    ).mappings().one()
    return brand, model


async def _insert_active(session, *, title: str, price: int, cid: int, oid: int, eav: dict) -> int:
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
        if isinstance(val, int):
            await session.execute(
                text(
                    """
                    INSERT INTO listing_field_values
                    (listing_id, field_key, value_int, created_at, updated_at)
                    VALUES (:lid, :k, :v, now(), now())
                    """
                ),
                {"lid": new_id, "k": key, "v": val},
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


async def _schema_checks() -> None:
    async with async_session_maker() as session:
        parent = (
            await session.execute(
                text(
                    "SELECT id, name, is_active FROM categories WHERE slug = :s"
                ),
                {"s": ELECTRIC_PARENT_SLUG},
            )
        ).mappings().one()
        assert parent["is_active"] is True

        active = (
            await session.execute(
                text(
                    """
                    SELECT slug, name, is_active, parent_id
                    FROM categories
                    WHERE parent_id = :pid
                    ORDER BY sort_order, id
                    """
                ),
                {"pid": parent["id"]},
            )
        ).mappings().all()
        active_slugs = [r["slug"] for r in active if r["is_active"]]
        assert active_slugs == list(ELECTRIC_LEAF_SLUGS)
        assert len(active_slugs) == 9
        for slug, label in ELECTRIC_LEAF_LABELS.items():
            row = next(r for r in active if r["slug"] == slug)
            assert row["name"] == label
            assert row["parent_id"] == parent["id"]

        # E-bike not under Electric
        e_bike_parent = (
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
        assert e_bike_parent == "transport-bicycles"

        for slug in ELECTRIC_INACTIVE_LEGACY_SLUGS:
            row = (
                await session.execute(
                    text("SELECT is_active FROM categories WHERE slug = :s"),
                    {"s": slug},
                )
            ).scalar_one()
            assert row is False

        for slug in ELECTRIC_LEAF_SLUGS:
            cid = await _slug_id(session, slug)
            core = (
                await session.execute(
                    text(
                        """
                        SELECT field_key, field_type::text, is_required
                        FROM category_core_fields
                        WHERE category_id = :cid AND create_intent IS NULL
                        ORDER BY sort_order, id
                        """
                    ),
                    {"cid": cid},
                )
            ).mappings().all()
            keys = [r["field_key"] for r in core]
            expected = [row[0] for row in ELECTRIC_CORE_FIELDS_BY_SLUG[slug]]
            assert keys == expected, slug
            assert not (set(keys) & ELECTRIC_FORBIDDEN_FIELD_KEYS), slug
            by = {r["field_key"]: r for r in core}

            assert by["price"]["is_required"] is True
            assert by["negotiable"]["is_required"] is True
            assert by["seller_type"]["is_required"] is True
            assert by["contact_methods"]["is_required"] is True
            assert by["condition"]["is_required"] is True
            assert by["needs_investment"]["is_required"] is False
            assert by["exchange"]["is_required"] is False
            assert by["installment"]["is_required"] is False
            assert "power_w" in by
            assert "power_kw" not in by
            assert "battery_capacity" not in by

            if slug == "transport-electric-elektrosamokaty":
                assert by["year"]["is_required"] is False
                assert "documents" not in by
                assert by["brand"]["is_required"] is True
            if slug == "transport-electric-elektroskutery":
                assert by["year"]["is_required"] is True
                assert by["documents"]["is_required"] is False
            if slug == "transport-moto-tech-elektromototsikly":
                assert by["year"]["is_required"] is True
                assert by["documents"]["is_required"] is True
            if slug == "transport-electric-giroskutery":
                assert "documents" not in by
            if slug == "transport-electric-drugoy-redkiy-elektrotransport":
                assert by["electric_subtype"]["is_required"] is True
                assert by["brand"]["is_required"] is False
                assert by["model"]["is_required"] is False

            filters = (
                await session.execute(
                    text(
                        """
                        SELECT filter_key FROM category_filters
                        WHERE category_id = :cid
                        ORDER BY sort_order, id
                        """
                    ),
                    {"cid": cid},
                )
            ).mappings().all()
            fkeys = [r["filter_key"] for r in filters]
            assert fkeys == [
                row[0] for row in ELECTRIC_SEARCH_FILTERS_BY_SLUG[slug]
            ], slug
            assert {"price", "sort", "condition", "seller_type"} <= set(fkeys)
            assert "has_photo" not in fkeys
            assert "power_kw" not in fkeys
            assert "battery_capacity" not in fkeys

        # Catalog: e_motorcycle has Sur-Ron; not under other_electric
        surron = (
            await session.execute(
                text(
                    """
                    SELECT vehicle_type::text FROM vehicle_brands
                    WHERE slug = 'surron'
                    """
                )
            )
        ).scalar_one()
        assert surron == "e_motorcycle"
        other_surron = (
            await session.execute(
                text(
                    """
                    SELECT COUNT(*) FROM vehicle_brands
                    WHERE slug = 'surron' AND vehicle_type::text = 'other_electric'
                    """
                )
            )
        ).scalar_one()
        assert int(other_surron) == 0

        for vt in set(ELECTRIC_LEAF_VEHICLE_TYPE.values()):
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


async def _e2e() -> None:
    await _schema_checks()
    scooter_slug = "transport-electric-elektrosamokaty"
    moto_slug = "transport-moto-tech-elektromototsikly"
    other_slug = "transport-electric-drugoy-redkiy-elektrotransport"
    ice_moto_slug = "transport-moto-tech-mototsikly"

    async with async_session_maker() as session:
        scooter_cid = await _slug_id(session, scooter_slug)
        emoto_cid = await _slug_id(session, moto_slug)
        other_cid = await _slug_id(session, other_slug)
        ice_cid = await _slug_id(session, ice_moto_slug)
        owner = (
            await session.execute(text("SELECT id FROM users ORDER BY id LIMIT 1"))
        ).scalar()
        assert owner is not None
        owner_id = int(owner)
        s_brand, s_model = await _brand_model(
            session, "e_scooter", prefer_slug="xiaomi-escooter"
        )
        m_brand, m_model = await _brand_model(
            session, "e_motorcycle", prefer_slug="surron"
        )

    _auth_user(owner_id)

    scooter_fields = {
        "region": "Чуйская область",
        "city": "Бишкек",
        "brand": s_brand["id"],
        "model": s_model["id"],
        "condition": "Хорошее",
        "negotiable": "Есть торг",
        "seller_type": "Частное лицо",
        "contact_methods": "Чат + телефон",
        "power_w": 500,
        "range_km": 40,
    }
    emoto_fields = {
        "region": "Чуйская область",
        "city": "Бишкек",
        "brand": m_brand["id"],
        "model": m_model["id"],
        "year": 2023,
        "condition": "Отличное",
        "documents": "Есть",
        "negotiable": "Без торга",
        "seller_type": "Магазин",
        "contact_methods": "Чат + телефон",
        "power_w": 3000,
        "range_km": 80,
    }
    other_fields = {
        "region": "Чуйская область",
        "city": "Бишкек",
        "electric_subtype": ELECTRIC_SUBTYPE_CHOICES[1],  # Электробагги
        "condition": "Хорошее",
        "negotiable": "Есть торг",
        "seller_type": "Частное лицо",
        "contact_methods": "Только чат",
    }

    created_ids: list[int] = []
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://test",
    ) as client:
        for slug in ELECTRIC_LEAF_SLUGS:
            async with async_session_maker() as session:
                cid = await _slug_id(session, slug)
            intel = await client.get(f"/api/v1/categories/intelligence/{cid}")
            assert intel.status_code == 200, intel.text
            body = intel.json()
            assert [f["field_key"] for f in body["core_fields"]] == [
                row[0] for row in ELECTRIC_CORE_FIELDS_BY_SLUG[slug]
            ]
            assert body["filters"]

        ok = await client.post(
            "/api/v1/listings",
            headers={"Authorization": "Bearer test"},
            json={
                "title": "Electric V2 scooter",
                "description": "escooter e2e",
                "price": "45000",
                "currency": "KGS",
                "category_id": scooter_cid,
                "fields": scooter_fields,
            },
        )
        assert ok.status_code == 201, ok.text
        lid = ok.json()["id"]
        created_ids.append(lid)
        assert int(float(str(ok.json()["fields"]["power_w"]))) == 500

        em = await client.post(
            "/api/v1/listings",
            headers={"Authorization": "Bearer test"},
            json={
                "title": "Electric V2 motorcycle",
                "description": "emoto e2e",
                "price": "350000",
                "currency": "KGS",
                "category_id": emoto_cid,
                "fields": emoto_fields,
            },
        )
        assert em.status_code == 201, em.text
        em_id = em.json()["id"]
        created_ids.append(em_id)

        ot = await client.post(
            "/api/v1/listings",
            headers={"Authorization": "Bearer test"},
            json={
                "title": "Electric V2 other",
                "description": "other e2e",
                "price": "120000",
                "currency": "KGS",
                "category_id": other_cid,
                "fields": other_fields,
            },
        )
        assert ot.status_code == 201, ot.text
        created_ids.append(ot.json()["id"])

        async with async_session_maker() as session:
            a = await _insert_active(
                session,
                title="ElectricV2 search scooter",
                price=45000,
                cid=scooter_cid,
                oid=owner_id,
                eav={
                    "city": "Бишкек",
                    "condition": "Хорошее",
                    "seller_type": "Частное лицо",
                    "brand": s_brand["name"],
                    "model": s_model["name"],
                    "power_w": 500,
                    "range_km": 40,
                },
            )
            b = await _insert_active(
                session,
                title="ElectricV2 search emoto",
                price=350000,
                cid=emoto_cid,
                oid=owner_id,
                eav={
                    "city": "Бишкек",
                    "year": 2023,
                    "condition": "Отличное",
                    "seller_type": "Магазин",
                    "brand": m_brand["name"],
                    "model": m_model["name"],
                    "power_w": 3000,
                    "range_km": 80,
                    "documents": "Есть",
                },
            )
            c = await _insert_active(
                session,
                title="ElectricV2 search other",
                price=120000,
                cid=other_cid,
                oid=owner_id,
                eav={
                    "city": "Бишкек",
                    "electric_subtype": "Электробагги",
                    "condition": "Хорошее",
                    "seller_type": "Частное лицо",
                },
            )
            await session.commit()
            created_ids.extend([a, b, c])

        async def _ids(params: dict) -> set[int]:
            r = await client.get("/api/v1/listings", params=params)
            assert r.status_code == 200, r.text
            return {int(x["id"]) for x in r.json()["items"]}

        found = await _ids(
            {
                "category_slug": scooter_slug,
                "attrs": json.dumps(
                    {
                        "condition": "Хорошее",
                        "seller_type": "Частное лицо",
                        "power_w__min": "400",
                        "power_w__max": "600",
                        "range_km__min": "30",
                        "range_km__max": "50",
                    },
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert a in found

        found = await _ids(
            {
                "category_slug": scooter_slug,
                "attrs": json.dumps(
                    {"power_w__min": "1", "power_w__max": "200"},
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert a not in found

        found = await _ids(
            {
                "category_slug": moto_slug,
                "attrs": json.dumps(
                    {
                        "condition": "Отличное",
                        "seller_type": "Магазин",
                        "power_w__min": "2000",
                        "power_w__max": "4000",
                    },
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert b in found

        # Must not appear as ICE motorcycle
        found = await _ids(
            {
                "category_slug": ice_moto_slug,
                "limit": 100,
            }
        )
        assert b not in found

        found = await _ids(
            {
                "category_slug": other_slug,
                "attrs": json.dumps(
                    {"electric_subtype": "Электробагги"},
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert c in found

        found = await _ids(
            {
                "category_slug": other_slug,
                "attrs": json.dumps(
                    {"electric_subtype": "Электротрицикл"},
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert c not in found

        async with async_session_maker() as session:
            for x in created_ids:
                await session.execute(
                    text("DELETE FROM listing_field_values WHERE listing_id = :id"),
                    {"id": x},
                )
                await session.execute(
                    text("DELETE FROM listings WHERE id = :id"),
                    {"id": x},
                )
            await session.commit()


def test_electric_sale_v2_schema_create_search() -> None:
    asyncio.run(_e2e())
