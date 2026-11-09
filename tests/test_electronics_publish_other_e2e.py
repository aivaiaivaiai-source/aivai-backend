"""Electronics Create publish — valid seller + other_brand/other_model."""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select, text

from app.api.deps import get_current_user
from app.db.session import async_session_maker, engine
from app.main import app
from app.models.category import Category
from app.models.listing_field_value import ListingFieldValue
from app.models.user import User
from app.schemas.user import UserRead
from app.seeds.electronics_sections_catalog import (
    OTHER_BRAND_VALUE,
    OTHER_MODEL_VALUE,
)


def _auth_as(user_id: int, phone: str = "+79001234567") -> None:
    now = datetime.now(UTC)

    async def _user() -> UserRead:
        return UserRead(
            id=user_id,
            phone=phone,
            full_name="ElectronicsPublishTester",
            is_active=True,
            balance=Decimal("0"),
            last_login=None,
            created_at=now,
            updated_at=now,
        )

    app.dependency_overrides[get_current_user] = _user


async def _category_id(session, slug: str) -> int:
    cat = (
        await session.execute(select(Category).where(Category.slug == slug))
    ).scalar_one()
    return int(cat.id)


@pytest.mark.asyncio
async def test_electronics_publish_known_model_and_other_variants(client) -> None:
    await engine.dispose()
    async with async_session_maker() as session:
        owner = (
            await session.execute(select(User).order_by(User.id.asc()).limit(1))
        ).scalar_one()
        owner_id = int(owner.id)
        foto_id = await _category_id(session, "electronics-foto-i-videotehnika")
        phones_id = await _category_id(session, "electronics-smartfony-i-telefony")

        brand_opts = (
            await session.execute(
                text(
                    """
                    SELECT options::text FROM category_core_fields
                    WHERE category_id = :cid AND field_key = 'electronics_brand'
                    """
                ),
                {"cid": foto_id},
            )
        ).scalar_one()
        assert OTHER_BRAND_VALUE in brand_opts
        assert "Другая марка" in brand_opts

        model_opts = (
            await session.execute(
                text(
                    """
                    SELECT options::text FROM category_core_fields
                    WHERE category_id = :cid AND field_key = 'electronics_model'
                    """
                ),
                {"cid": phones_id},
            )
        ).scalar_one()

    _auth_as(owner_id)

    # 1) Known Canon model
    r = await client.post(
        "/api/v1/listings",
        json={
            "title": "Canon EOS R6 Mark II",
            "description": "Фотоаппарат Canon EOS R6 Mark II в отличном состоянии.",
            "price": "45000",
            "currency": "KGS",
            "category_id": foto_id,
            "status": "draft",
            "fields": {
                "electronics_kind": "Фотоаппараты",
                "electronics_brand": "Canon",
                "electronics_model": "EOS R6 Mark II",
                "seller_type": "Частное лицо",
                "condition": "Б/у",
                "negotiable": "Есть торг",
                "contact_methods": "Чат + телефон",
                "region": "Чуйская область",
                "city": "Бишкек",
            },
        },
        headers={"Authorization": "Bearer test"},
    )
    assert r.status_code in (200, 201), r.text
    listing_id = r.json()["id"]

    bad = await client.patch(
        f"/api/v1/listings/{listing_id}",
        json={"fields": {"seller_type": "Собственник"}},
        headers={"Authorization": "Bearer test"},
    )
    assert bad.status_code == 400, bad.text
    assert bad.json().get("code") == "INVALID_LISTING_FIELD"

    # 2) Other model under Canon
    r2 = await client.post(
        "/api/v1/listings",
        json={
            "title": "Canon другая модель",
            "description": "Точная модель: Canon PowerShot G7 X Mark III.",
            "price": "22000",
            "currency": "KGS",
            "category_id": foto_id,
            "status": "draft",
            "fields": {
                "electronics_kind": "Фотоаппараты",
                "electronics_brand": "Canon",
                "electronics_model": OTHER_MODEL_VALUE,
                "seller_type": "Магазин",
                "condition": "Новое",
                "contact_methods": "Только чат",
                "city": "Бишкек",
                "region": "Чуйская область",
            },
        },
        headers={"Authorization": "Bearer test"},
    )
    assert r2.status_code in (200, 201), r2.text

    # 3) Other brand — no model
    r3 = await client.post(
        "/api/v1/listings",
        json={
            "title": "Другая марка камера",
            "description": "Точная марка/модель: Fujifilm X-T5.",
            "price": "70000",
            "currency": "KGS",
            "category_id": foto_id,
            "status": "draft",
            "fields": {
                "electronics_kind": "Фотоаппараты",
                "electronics_brand": OTHER_BRAND_VALUE,
                "seller_type": "Частное лицо",
                "condition": "Б/у",
                "contact_methods": "Чат + Wapp",
                "city": "Бишкек",
                "region": "Чуйская область",
            },
        },
        headers={"Authorization": "Bearer test"},
    )
    assert r3.status_code in (200, 201), r3.text

    iphone = "iPhone 15" if "iPhone 15" in model_opts else "iPhone 16"
    r4 = await client.post(
        "/api/v1/listings",
        json={
            "title": f"Apple {iphone}",
            "description": f"Продаю {iphone}, полный комплект.",
            "price": "55000",
            "currency": "KGS",
            "category_id": phones_id,
            "status": "draft",
            "fields": {
                "electronics_kind": "Смартфоны",
                "electronics_brand": "Apple",
                "electronics_model": iphone,
                "seller_type": "Частное лицо",
                "condition": "Б/у",
                "storage": "128gb",
                "contact_methods": "Чат + телефон",
                "city": "Бишкек",
                "region": "Чуйская область",
            },
        },
        headers={"Authorization": "Bearer test"},
    )
    assert r4.status_code in (200, 201), r4.text

    async with async_session_maker() as session:
        lid = r2.json()["id"]
        eav = (
            await session.execute(
                select(ListingFieldValue).where(
                    ListingFieldValue.listing_id == lid,
                    ListingFieldValue.field_key == "electronics_model",
                )
            )
        ).scalar_one()
        assert eav.value_text == OTHER_MODEL_VALUE

        brand_eav = (
            await session.execute(
                select(ListingFieldValue).where(
                    ListingFieldValue.listing_id == r3.json()["id"],
                    ListingFieldValue.field_key == "electronics_brand",
                )
            )
        ).scalar_one()
        assert brand_eav.value_text == OTHER_BRAND_VALUE
        # Intentionally no assert on mutable user listing ids (e.g. 1891).
