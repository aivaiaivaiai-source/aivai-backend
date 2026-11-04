"""Car Sale V2 — Backend SoT create/search cutover for transport-car-sale."""
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
from app.seeds.car_sale_v2 import (
    CAR_SALE_CORE_FIELDS,
    CAR_SALE_SEARCH_FILTERS,
    CAR_SALE_SLUG,
    ENGINE_VOLUME_EXACT_MAX,
    ENGINE_VOLUME_MIN,
    ENGINE_VOLUME_OVER_5_LABEL,
    ENGINE_VOLUME_OVER_5_VALUE,
    _engine_volume_choice_items,
)


async def _cat_id(session) -> int:
    row = (
        await session.execute(
            text("SELECT id FROM categories WHERE slug = :s"),
            {"s": CAR_SALE_SLUG},
        )
    ).scalar_one()
    return int(row)


def _auth_user(user_id: int = 1) -> None:
    now = datetime.now(UTC)

    async def _user() -> UserRead:
        return UserRead(
            id=user_id,
            phone="+79001234567",
            full_name="CarSaleV2Tester",
            is_active=True,
            balance=Decimal("0"),
            last_login=None,
            created_at=now,
            updated_at=now,
        )

    fastapi_app.dependency_overrides[get_current_user] = _user


async def _schema_checks() -> None:
    async with async_session_maker() as session:
        cid = await _cat_id(session)
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
        assert keys == [row[0] for row in CAR_SALE_CORE_FIELDS]
        assert "fresh_import" not in keys
        by = {r["field_key"]: r for r in core}
        assert by["engine_volume"]["field_type"] == "decimal"
        assert by["needs_investment"]["is_required"] is True
        assert by["after_accident"]["is_required"] is True
        assert by["steering_side"]["is_required"] is True

        filters = (
            await session.execute(
                text(
                    """
                    SELECT filter_key
                    FROM category_filters
                    WHERE category_id = :cid
                    ORDER BY sort_order, id
                    """
                ),
                {"cid": cid},
            )
        ).mappings().all()
        fkeys = [r["filter_key"] for r in filters]
        assert fkeys == [row[0] for row in CAR_SALE_SEARCH_FILTERS]
        assert "drive" in fkeys and "sort" in fkeys
        assert "has_photo" not in fkeys
        assert "color" not in fkeys

        opt = (
            await session.execute(
                text(
                    "SELECT COUNT(*) FROM category_optional_fields WHERE category_id = :cid"
                ),
                {"cid": cid},
            )
        ).scalar_one()
        assert int(opt) == 0

        drive_opts = (
            await session.execute(
                text(
                    """
                    SELECT options FROM category_core_fields
                    WHERE category_id = :cid AND field_key = 'drive'
                    """
                ),
                {"cid": cid},
            )
        ).scalar_one()
        choices = (drive_opts or {}).get("choices") or []
        values = [c.get("value") for c in choices]
        assert values == ["Передний", "Задний", "Полный"]

        eng_opts = (
            await session.execute(
                text(
                    """
                    SELECT options FROM category_core_fields
                    WHERE category_id = :cid AND field_key = 'engine_volume'
                    """
                ),
                {"cid": cid},
            )
        ).scalar_one()
        eng_choices = (eng_opts or {}).get("choices") or []
        eng_values = [c.get("value") for c in eng_choices]
        expected_items = _engine_volume_choice_items()
        assert eng_values == [i["value"] for i in expected_items]
        assert eng_values[0] == ENGINE_VOLUME_MIN
        assert ENGINE_VOLUME_EXACT_MAX in eng_values
        assert eng_values[-1] == ENGINE_VOLUME_OVER_5_VALUE
        assert eng_choices[-1]["label"] == ENGINE_VOLUME_OVER_5_LABEL
        assert "2.2" in eng_values


async def _create_search_e2e() -> None:
    await _schema_checks()

    async with async_session_maker() as session:
        cid = await _cat_id(session)
        owner = (
            await session.execute(text("SELECT id FROM users ORDER BY id LIMIT 1"))
        ).scalar()
        assert owner is not None
        owner_id = int(owner)

        brand = (
            await session.execute(
                text(
                    """
                    SELECT id, name, slug FROM vehicle_brands
                    ORDER BY CASE WHEN name = 'Toyota' THEN 0 ELSE 1 END, id
                    LIMIT 1
                    """
                )
            )
        ).mappings().one()
        model = (
            await session.execute(
                text(
                    """
                    SELECT id, name, slug FROM vehicle_models
                    WHERE brand_id = :bid
                    ORDER BY id LIMIT 1
                    """
                ),
                {"bid": brand["id"]},
            )
        ).mappings().one()

    _auth_user(owner_id)
    fields = {
        "region": "Чуйская область",
        "city": "Бишкек",
        "brand": brand["name"],
        "model": model["name"],
        "year": 2020,
        "steering_side": "Левый руль",
        "engine_volume": "2.5",
        "transmission": "Автомат",
        "drive": "Полный",
        "fuel": "Бензин",
        "color": "Белый",
        "mileage": 80000,
        "condition": "Хорошее",
        "needs_investment": "Нет",
        "after_accident": "Нет",
        "registration_country": "Кыргызстан",
        "available_in_kg": "В наличии",
        "customs_cleared_kg": "Да",
        "taxes_paid": "Оплачены",
        "negotiable": "Есть торг",
        "exchange": "Обмена нет",
        "installment": "Нет",
        "seller_type": "Собственник",
        "contact_methods": "Чат + телефон",
    }

    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://test",
    ) as client:
        intel = await client.get(f"/api/v1/categories/intelligence/{cid}")
        assert intel.status_code == 200, intel.text
        assert [f["field_key"] for f in intel.json()["core_fields"]] == [
            row[0] for row in CAR_SALE_CORE_FIELDS
        ]

        create = await client.post(
            "/api/v1/listings",
            headers={"Authorization": "Bearer test"},
            json={
                "title": "Car Sale V2 E2E Toyota",
                "description": "V2 petrol test listing",
                "price": "750000",
                "currency": "KGS",
                "category_id": cid,
                "fields": fields,
            },
        )
        assert create.status_code == 201, create.text
        listing = create.json()
        lid = listing["id"]
        read_fields = listing.get("fields") or {}
        assert read_fields.get("drive") == "Полный"
        assert read_fields.get("steering_side") == "Левый руль"
        assert read_fields.get("needs_investment") == "Нет"
        assert str(read_fields.get("engine_volume")).startswith("2.5")
        assert "fresh_import" not in read_fields
        brand_val = read_fields.get("brand")
        assert brand_val is not None
        if isinstance(brand_val, dict):
            assert brand_val.get("label")

        # Free-form engine volume not in picker → reject
        bad_vol = await client.patch(
            f"/api/v1/listings/{lid}",
            headers={"Authorization": "Bearer test"},
            json={"fields": {**fields, "engine_volume": "2.25"}},
        )
        assert bad_vol.status_code == 400

        # «Более 5.0» sentinel stores as 5.1 numeric
        over = await client.post(
            "/api/v1/listings",
            headers={"Authorization": "Bearer test"},
            json={
                "title": "Car Sale V2 Engine Over 5",
                "description": "over",
                "price": "900000",
                "currency": "KGS",
                "category_id": cid,
                "fields": {**fields, "engine_volume": ENGINE_VOLUME_OVER_5_VALUE},
            },
        )
        assert over.status_code == 201, over.text
        assert str(over.json()["fields"]["engine_volume"]).startswith("5.1")

        bad = await client.patch(
            f"/api/v1/listings/{lid}",
            headers={"Authorization": "Bearer test"},
            json={"fields": {**fields, "drive": "Полный (4WD/AWD)"}},
        )
        assert bad.status_code == 400

        elec_fields = {**fields, "fuel": "Электро"}
        elec_fields.pop("engine_volume", None)
        elec = await client.post(
            "/api/v1/listings",
            headers={"Authorization": "Bearer test"},
            json={
                "title": "Car Sale V2 E2E EV",
                "description": "electric",
                "price": "1200000",
                "currency": "KGS",
                "category_id": cid,
                "fields": elec_fields,
            },
        )
        assert elec.status_code == 201, elec.text
        assert "engine_volume" not in (elec.json().get("fields") or {})

        async with async_session_maker() as session:
            async def _insert(title: str, price: int, eav: dict) -> int:
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
                    {
                        "t": title,
                        "d": title,
                        "p": price,
                        "cid": cid,
                        "oid": owner_id,
                    },
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
                    elif isinstance(val, float):
                        await session.execute(
                            text(
                                """
                                INSERT INTO listing_field_values
                                (listing_id, field_key, value_decimal, created_at, updated_at)
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

            a = await _insert(
                "CSV2 Full Drive A",
                500000,
                {
                    "region": "Чуйская область",
                    "city": "Бишкек",
                    "year": 2020,
                    "steering_side": "Левый руль",
                    "drive": "Полный",
                    "fuel": "Бензин",
                    "transmission": "Автомат",
                    "condition": "Хорошее",
                    "needs_investment": "Нет",
                    "seller_type": "Собственник",
                    "engine_volume": 2.5,
                    "mileage": 80000,
                },
            )
            b = await _insert(
                "CSV2 Front Drive B",
                900000,
                {
                    "region": "Ошская область",
                    "city": "Ош",
                    "year": 2015,
                    "steering_side": "Правый руль",
                    "drive": "Передний",
                    "fuel": "Дизель",
                    "transmission": "Механика",
                    "condition": "Удовлетворительное",
                    "needs_investment": "Да",
                    "seller_type": "Дилер",
                    "engine_volume": 1.6,
                    "mileage": 200000,
                },
            )
            # Boundary fixtures: 0.3 / 5.0 / 5.1 («Более 5.0»)
            v03 = await _insert(
                "CSV2 Engine 0.3",
                410000,
                {"city": "Бишкек", "engine_volume": 0.3, "drive": "Передний"},
            )
            v50 = await _insert(
                "CSV2 Engine 5.0",
                420000,
                {"city": "Бишкек", "engine_volume": 5.0, "drive": "Передний"},
            )
            v51 = await _insert(
                "CSV2 Engine Over5",
                430000,
                {
                    "city": "Бишкек",
                    "engine_volume": float(ENGINE_VOLUME_OVER_5_VALUE),
                    "drive": "Передний",
                },
            )
            await session.commit()

        async def _ids(params: dict) -> set[int]:
            r = await client.get("/api/v1/listings", params=params)
            assert r.status_code == 200, r.text
            return {int(x["id"]) for x in r.json()["items"]}

        found = await _ids(
            {
                "category_slug": CAR_SALE_SLUG,
                "attrs": json.dumps({"drive": "Полный"}, ensure_ascii=False),
                "limit": 100,
            }
        )
        assert a in found and b not in found

        found = await _ids(
            {"category_slug": CAR_SALE_SLUG, "city": "Бишкек", "limit": 100}
        )
        assert a in found and b not in found

        found = await _ids(
            {
                "category_slug": CAR_SALE_SLUG,
                "year_min": 2018,
                "year_max": 2022,
                "limit": 100,
            }
        )
        assert a in found and b not in found

        found = await _ids(
            {
                "category_slug": CAR_SALE_SLUG,
                "min_price": 400000,
                "max_price": 600000,
                "limit": 100,
            }
        )
        assert a in found and b not in found

        found = await _ids(
            {
                "category_slug": CAR_SALE_SLUG,
                "attrs": json.dumps(
                    {"engine_volume__min": "2.0", "engine_volume__max": "3.0"},
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert a in found and b not in found

        found = await _ids(
            {
                "category_slug": CAR_SALE_SLUG,
                "attrs": json.dumps(
                    {"engine_volume__min": "0.3", "engine_volume__max": "0.3"},
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert v03 in found and v50 not in found and v51 not in found

        found = await _ids(
            {
                "category_slug": CAR_SALE_SLUG,
                "attrs": json.dumps(
                    {"engine_volume__min": "5.0", "engine_volume__max": "5.0"},
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert v50 in found and v51 not in found

        found = await _ids(
            {
                "category_slug": CAR_SALE_SLUG,
                "attrs": json.dumps(
                    {"engine_volume__min": ENGINE_VOLUME_OVER_5_VALUE},
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert v51 in found and v50 not in found and v03 not in found

        found = await _ids(
            {
                "category_slug": CAR_SALE_SLUG,
                "attrs": json.dumps({"engine_volume__max": "5.0"}, ensure_ascii=False),
                "limit": 100,
            }
        )
        assert v50 in found and v03 in found and v51 not in found

        found = await _ids(
            {
                "category_slug": CAR_SALE_SLUG,
                "attrs": json.dumps({"mileage__max": "100000"}, ensure_ascii=False),
                "limit": 100,
            }
        )
        assert a in found and b not in found

        found = await _ids(
            {
                "category_slug": CAR_SALE_SLUG,
                "attrs": json.dumps(
                    {
                        "condition": "Хорошее",
                        "needs_investment": "Нет",
                        "seller_type": "Собственник",
                        "fuel": "Бензин||Гибрид",
                        "transmission": "Автомат",
                    },
                    ensure_ascii=False,
                ),
                "limit": 100,
            }
        )
        assert a in found and b not in found

        r = await client.get(
            "/api/v1/listings",
            params={
                "category_slug": CAR_SALE_SLUG,
                "sort": "price_asc",
                "limit": 100,
            },
        )
        assert r.status_code == 200
        ids = [int(x["id"]) for x in r.json()["items"] if int(x["id"]) in {a, b}]
        assert ids == [a, b]


def test_car_sale_v2_schema_create_search() -> None:
    """Single asyncio.run — avoids Windows asyncpg dispose across tests."""
    asyncio.run(_create_search_e2e())
