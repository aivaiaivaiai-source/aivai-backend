"""Moto Sale V2 — Backend SoT create/search cutover for 9 moto leaves."""
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
from app.seeds.moto_sale_v2 import (
    ENGINE_CC_EXACT_MAX,
    ENGINE_CC_OVER_MAX_LABEL,
    ENGINE_CC_OVER_MAX_VALUE,
    ENGINE_CC_VALUES,
    MOTO_CORE_FIELDS_BY_SLUG,
    MOTO_FORBIDDEN_FIELD_KEYS,
    MOTO_INACTIVE_LEGACY_SLUGS,
    MOTO_LEAF_LABELS,
    MOTO_LEAF_SLUGS,
    MOTO_PARENT_SLUG,
    MOTO_SEARCH_FILTERS_BY_SLUG,
    _engine_cc_choice_items,
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
            full_name="MotoSaleV2Tester",
            is_active=True,
            balance=Decimal("0"),
            last_login=None,
            created_at=now,
            updated_at=now,
        )

    fastapi_app.dependency_overrides[get_current_user] = _user


async def _schema_checks() -> None:
    async with async_session_maker() as session:
        parent = (
            await session.execute(
                text(
                    "SELECT id, name, is_active FROM categories WHERE slug = :s"
                ),
                {"s": MOTO_PARENT_SLUG},
            )
        ).mappings().one()
        assert parent["is_active"] is True

        active = (
            await session.execute(
                text(
                    """
                    SELECT slug, name, is_active
                    FROM categories
                    WHERE parent_id = :pid
                    ORDER BY sort_order, id
                    """
                ),
                {"pid": parent["id"]},
            )
        ).mappings().all()
        active_slugs = [r["slug"] for r in active if r["is_active"]]
        assert active_slugs == list(MOTO_LEAF_SLUGS)
        assert len(active_slugs) == 9
        for slug, label in MOTO_LEAF_LABELS.items():
            row = next(r for r in active if r["slug"] == slug)
            assert row["name"] == label

        for slug in MOTO_INACTIVE_LEGACY_SLUGS:
            row = (
                await session.execute(
                    text("SELECT is_active FROM categories WHERE slug = :s"),
                    {"s": slug},
                )
            ).scalar_one()
            assert row is False

        for slug in MOTO_LEAF_SLUGS:
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
            expected = [row[0] for row in MOTO_CORE_FIELDS_BY_SLUG[slug]]
            assert keys == expected, slug
            assert not (set(keys) & MOTO_FORBIDDEN_FIELD_KEYS), slug
            by = {r["field_key"]: r for r in core}

            if slug == "transport-moto-tech-mototsikly":
                assert {"transmission", "documents", "after_accident"} <= set(keys)
                assert by["engine_cc"]["field_type"] == "number"
                assert by["engine_cc"]["is_required"] is True
            if slug == "transport-moto-tech-kvadrotsikly":
                assert "drive" in by
                assert "documents" not in by
                assert "after_accident" not in by
            if slug == "transport-moto-tech-baggi":
                assert "drive" in by
            if slug == "transport-moto-tech-karty":
                assert "documents" not in by
                assert "after_accident" not in by
                assert "exchange" not in by
                assert "installment" not in by
            if slug == "transport-moto-tech-drugaya-mototehnika":
                assert by["engine_cc"]["is_required"] is False

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
            assert fkeys == [row[0] for row in MOTO_SEARCH_FILTERS_BY_SLUG[slug]], slug
            assert {"price", "sort", "condition"} <= set(fkeys)
            assert "has_photo" not in fkeys
            assert "mileage" not in fkeys
            assert "engine_hours" not in fkeys
            if slug == "transport-moto-tech-mototsikly":
                assert "transmission" in fkeys
            if slug in {
                "transport-moto-tech-kvadrotsikly",
                "transport-moto-tech-baggi",
            }:
                assert "drive" in fkeys

        cid = await _slug_id(session, "transport-moto-tech-mototsikly")
        eng_opts = (
            await session.execute(
                text(
                    """
                    SELECT options FROM category_core_fields
                    WHERE category_id = :cid AND field_key = 'engine_cc'
                    """
                ),
                {"cid": cid},
            )
        ).scalar_one()
        eng_values = [c.get("value") for c in ((eng_opts or {}).get("choices") or [])]
        assert eng_values == [i["value"] for i in _engine_cc_choice_items()]
        assert eng_values[0] == str(ENGINE_CC_VALUES[0])
        assert str(ENGINE_CC_EXACT_MAX) in eng_values
        assert eng_values[-1] == str(ENGINE_CC_OVER_MAX_VALUE)
        assert ((eng_opts or {}).get("choices") or [])[-1]["label"] == ENGINE_CC_OVER_MAX_LABEL


async def _brand_model(session, vehicle_type: str):
    brand = (
        await session.execute(
            text(
                """
                SELECT id, name, slug FROM vehicle_brands
                WHERE is_enabled AND vehicle_type::text = :vt
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
                WHERE brand_id = :bid AND is_enabled
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


async def _e2e() -> None:
    await _schema_checks()
    moto_slug = "transport-moto-tech-mototsikly"
    atv_slug = "transport-moto-tech-kvadrotsikly"
    kart_slug = "transport-moto-tech-karty"

    async with async_session_maker() as session:
        moto_cid = await _slug_id(session, moto_slug)
        atv_cid = await _slug_id(session, atv_slug)
        kart_cid = await _slug_id(session, kart_slug)
        owner = (
            await session.execute(text("SELECT id FROM users ORDER BY id LIMIT 1"))
        ).scalar()
        assert owner is not None
        owner_id = int(owner)
        m_brand, m_model = await _brand_model(session, "motorcycle")
        a_brand, a_model = await _brand_model(session, "atv")
        k_brand, k_model = await _brand_model(session, "kart")

    _auth_user(owner_id)
    # Use catalog IDs — display name «Honda» would resolve to car brand first.
    moto_fields = {
        "region": "Чуйская область",
        "city": "Бишкек",
        "brand": m_brand["id"],
        "model": m_model["id"],
        "year": 2018,
        "engine_cc": 250,
        "transmission": "Механика",
        "color": "Чёрный",
        "condition": "Хорошее",
        "needs_investment": "Нет",
        "after_accident": "Нет",
        "documents": "Есть",
        "negotiable": "Есть торг",
        "exchange": "Обмена нет",
        "installment": "Нет",
        "seller_type": "Частное лицо",
        "contact_methods": "Чат + телефон",
    }

    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://test",
    ) as client:
        for slug in MOTO_LEAF_SLUGS:
            cid = None
            async with async_session_maker() as session:
                cid = await _slug_id(session, slug)
            intel = await client.get(f"/api/v1/categories/intelligence/{cid}")
            assert intel.status_code == 200, intel.text
            body = intel.json()
            assert [f["field_key"] for f in body["core_fields"]] == [
                row[0] for row in MOTO_CORE_FIELDS_BY_SLUG[slug]
            ]
            assert body["filters"]

        # Create accepts canonical engine_cc; rejects free-form 237
        ok_create = await client.post(
            "/api/v1/listings",
            headers={"Authorization": "Bearer test"},
            json={
                "title": "Moto V2 motorcycle",
                "description": "moto e2e",
                "price": "150000",
                "currency": "KGS",
                "category_id": moto_cid,
                "fields": moto_fields,
            },
        )
        assert ok_create.status_code == 201, ok_create.text
        lid = ok_create.json()["id"]
        assert int(float(str(ok_create.json()["fields"]["engine_cc"]))) == 250

        bad = await client.patch(
            f"/api/v1/listings/{lid}",
            headers={"Authorization": "Bearer test"},
            json={"fields": {**moto_fields, "engine_cc": 237}},
        )
        assert bad.status_code == 400

        # Kart minimal — no documents/after_accident required
        kart_fields = {
            "region": "Чуйская область",
            "city": "Бишкек",
            "brand": k_brand["id"],
            "model": k_model["id"],
            "year": 2019,
            "engine_cc": 125,
            "condition": "Хорошее",
            "needs_investment": "Нет",
            "negotiable": "Есть торг",
            "seller_type": "Частное лицо",
            "contact_methods": "Только чат",
        }
        kart = await client.post(
            "/api/v1/listings",
            headers={"Authorization": "Bearer test"},
            json={
                "title": "Moto V2 kart",
                "description": "kart",
                "price": "90000",
                "currency": "KGS",
                "category_id": kart_cid,
                "fields": kart_fields,
            },
        )
        assert kart.status_code == 201, kart.text
        assert "documents" not in (kart.json().get("fields") or {})
        assert "after_accident" not in (kart.json().get("fields") or {})

        created_ids = [lid, kart.json()["id"]]

        async with async_session_maker() as session:
            a = await _insert_active(
                session,
                title="MotoV2 bike search",
                price=150000,
                cid=moto_cid,
                oid=owner_id,
                eav={
                    "city": "Бишкек",
                    "year": 2018,
                    "engine_cc": 250,
                    "transmission": "Механика",
                    "condition": "Хорошее",
                    "seller_type": "Частное лицо",
                    "brand": m_brand["name"],
                    "model": m_model["name"],
                },
            )
            b = await _insert_active(
                session,
                title="MotoV2 atv search",
                price=400000,
                cid=atv_cid,
                oid=owner_id,
                eav={
                    "city": "Бишкек",
                    "year": 2020,
                    "engine_cc": 500,
                    "drive": "4WD",
                    "condition": "Отличное",
                    "seller_type": "Мотосалон",
                    "brand": a_brand["name"],
                    "model": a_model["name"],
                },
            )
            await session.commit()
            created_ids.extend([a, b])

        async def _ids(params: dict) -> set[int]:
            r = await client.get("/api/v1/listings", params=params)
            assert r.status_code == 200, r.text
            return {int(x["id"]) for x in r.json()["items"]}

        found = await _ids(
            {
                "category_slug": moto_slug,
                "attrs": json.dumps(
                    {"engine_cc__min": "200", "engine_cc__max": "300"},
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert a in found

        found = await _ids(
            {
                "category_slug": moto_slug,
                "attrs": json.dumps(
                    {"engine_cc__min": "300", "engine_cc__max": "500"},
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert a not in found

        found = await _ids(
            {
                "category_slug": moto_slug,
                "attrs": json.dumps({"transmission": "Автомат"}, ensure_ascii=False),
                "limit": 100,
            }
        )
        assert a not in found

        found = await _ids(
            {
                "category_slug": moto_slug,
                "attrs": json.dumps(
                    {
                        "condition": "Новое||Хорошее",
                        "seller_type": "Частное лицо",
                    },
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert a in found

        found = await _ids(
            {
                "category_slug": moto_slug,
                "attrs": json.dumps(
                    {
                        "condition": "Новое||Хорошее",
                        "seller_type": "Дилер",
                    },
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert a not in found

        found = await _ids(
            {
                "category_slug": atv_slug,
                "attrs": json.dumps({"drive": "4WD"}, ensure_ascii=False),
                "limit": 100,
            }
        )
        assert b in found

        found = await _ids(
            {
                "category_slug": atv_slug,
                "attrs": json.dumps({"drive": "2WD"}, ensure_ascii=False),
                "limit": 100,
            }
        )
        assert b not in found

        found = await _ids(
            {"category_slug": moto_slug, "city": "Бишкек", "limit": 100}
        )
        assert a in found

        # Cleanup test rows (do not leave active fixtures).
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


def test_moto_sale_v2_schema_create_search() -> None:
    asyncio.run(_e2e())
