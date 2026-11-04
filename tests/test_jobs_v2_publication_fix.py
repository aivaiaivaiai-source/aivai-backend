# -*- coding: utf-8 -*-
"""Jobs V2 publication fix: city geo + multi_select + time create/activate."""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text

from app.api.deps import get_current_user
from app.db.session import async_session_maker, engine
from app.main import app as fastapi_app
from app.models.category import Category
from app.models.enums import Currency, ListingStatus
from app.models.image_moderation_enums import MediaModerationStatus
from app.models.job_create_intent import HIRING, JOB_SEEKING
from app.models.media import Media
from app.models.media_enums import MediaLifecycleStatus
from app.models.user import User
from app.schemas.user import UserRead


async def _auth_as_first_user() -> UserRead:
    async with async_session_maker() as session:
        user = (
            await session.execute(select(User).order_by(User.id).limit(1))
        ).scalar_one()
        return UserRead(
            id=user.id,
            phone=user.phone,
            full_name=user.full_name or "T",
            is_active=True,
            balance=user.balance or Decimal("0"),
            last_login=None,
            created_at=user.created_at or datetime.now(UTC),
            updated_at=user.updated_at or datetime.now(UTC),
        )


async def _category_id(slug: str) -> int:
    async with async_session_maker() as session:
        row = (
            await session.execute(select(Category).where(Category.slug == slug))
        ).scalar_one()
        return row.id


def _hiring_fields() -> dict:
    """Samsung-equivalent fields — no listing-root price_currency."""
    return {
        "city": "Бишкек",
        "job_role": "Программист",
        "employer": "Компания",
        "work_format": "В офисе",
        "experience": "До 1 года",
        "pay_type": "Оклад",
        "work_schedule": "Полный день",
        "work_mode": "5/2",
        "work_hours_from": "09:00",
        "work_hours_to": "18:00",
        "job_conditions": "Обучение||Развоз||Бесплатное питание",
        "salary_payout": "Ежемесячно",
        "bonuses": "Есть",
        "contact_methods": "Чат + телефон",
        # Flutter UI companions that must be ignored if present:
        "price_currency": "СОМ",
        "price": "60000 СОМ",
    }


def _seeking_fields() -> dict:
    return {
        "city": "Бишкек",
        "job_role": "Программист",
        "employment": "Полная",
        "experience": "1–2 года",
        "work_schedule": "Полный день",
        "ready_to_start": "Сразу",
        "work_format": "Удалённо",
        "job_conditions": "Обучение||Развоз||Бесплатное питание",
        "contact_methods": "Чат + телефон",
        "price_currency": "СОМ",
        "price": "60000 СОМ",
    }


@pytest.mark.asyncio
async def test_jobs_hiring_draft_create_persists_geo_multi_time(
    client: AsyncClient,
) -> None:
    await engine.dispose()
    cat_id = await _category_id("jobs-it-i-tehnologii")
    user = await _auth_as_first_user()
    fastapi_app.dependency_overrides[get_current_user] = lambda: user

    created_id: int | None = None
    try:
        resp = await client.post(
            "/api/v1/listings",
            json={
                "title": "PUBFIX hire IT",
                "description": "Jobs V2 hiring publication fix",
                "price": "60000",
                "category_id": cat_id,
                "currency": Currency.KGS.value,
                "job_intent": HIRING,
                "uses_placeholder_image": True,
                "fields": _hiring_fields(),
            },
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        created_id = body["id"]
        assert body["status"] == ListingStatus.draft.value
        assert body["job_intent"] == HIRING
        assert body["price"] == "60000.00"
        assert body["currency"] == Currency.KGS.value
        fields = body["fields"]
        assert fields.get("city") == "Бишкек"
        assert fields.get("job_conditions") == (
            "Обучение||Развоз||Бесплатное питание"
        )
        # Seed options use unpadded hour for single-digit values.
        assert fields.get("work_hours_from") in {"9:00", "09:00"}
        assert fields.get("work_hours_to") in {"18:00"}
        assert fields.get("job_role") == "Программист"
        assert fields.get("employer") == "Компания"
        assert "price_currency" not in fields
        assert "Unknown field_key" not in resp.text
        assert "Unsupported field type" not in resp.text

        # Round-trip read
        got = await client.get(f"/api/v1/listings/{created_id}")
        assert got.status_code == 200
        gbody = got.json()
        assert gbody["price"] == "60000.00"
        assert gbody["currency"] == Currency.KGS.value
        gfields = gbody["fields"]
        assert gfields["city"] == "Бишкек"
        assert gfields["job_conditions"] == (
            "Обучение||Развоз||Бесплатное питание"
        )
        assert gfields["work_hours_from"] in {"9:00", "09:00"}
        assert gfields["work_hours_to"] == "18:00"
        assert "price_currency" not in gfields

        # Activate with placeholder (Jobs policy)
        act = await client.patch(
            f"/api/v1/listings/{created_id}/status",
            json={"status": ListingStatus.active.value},
            headers={"Authorization": "Bearer test"},
        )
        assert act.status_code == 200, act.text
        assert act.json()["status"] == ListingStatus.active.value
    finally:
        if created_id is not None:
            async with async_session_maker() as session:
                await session.execute(
                    text("DELETE FROM listings WHERE id = :id"),
                    {"id": created_id},
                )
                await session.commit()


@pytest.mark.asyncio
async def test_jobs_seeking_draft_create_persists_multi_and_geo(
    client: AsyncClient,
) -> None:
    await engine.dispose()
    cat_id = await _category_id("jobs-it-i-tehnologii")
    user = await _auth_as_first_user()
    fastapi_app.dependency_overrides[get_current_user] = lambda: user

    created_id: int | None = None
    try:
        resp = await client.post(
            "/api/v1/listings",
            json={
                "title": "PUBFIX seek IT",
                "description": "Jobs V2 seeking publication fix",
                "price": "60000",
                "category_id": cat_id,
                "currency": Currency.KGS.value,
                "job_intent": JOB_SEEKING,
                "uses_placeholder_image": True,
                "fields": _seeking_fields(),
            },
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        created_id = body["id"]
        assert body["status"] == ListingStatus.draft.value
        assert body["job_intent"] == JOB_SEEKING
        assert body["price"] == "60000.00"
        assert body["currency"] == Currency.KGS.value
        fields = body["fields"]
        assert fields.get("city") == "Бишкек"
        assert fields.get("job_conditions") == (
            "Обучение||Развоз||Бесплатное питание"
        )
        assert fields.get("employment") == "Полная"
        assert fields.get("ready_to_start") == "Сразу"
        assert "price_currency" not in fields

        got = await client.get(f"/api/v1/listings/{created_id}")
        assert got.status_code == 200
        gbody = got.json()
        assert gbody["price"] == "60000.00"
        assert gbody["currency"] == Currency.KGS.value
        assert gbody["fields"]["job_conditions"] == (
            "Обучение||Развоз||Бесплатное питание"
        )
        assert "price_currency" not in gbody["fields"]

        act = await client.patch(
            f"/api/v1/listings/{created_id}/status",
            json={"status": ListingStatus.active.value},
            headers={"Authorization": "Bearer test"},
        )
        assert act.status_code == 200, act.text
        assert act.json()["status"] == ListingStatus.active.value
    finally:
        if created_id is not None:
            async with async_session_maker() as session:
                await session.execute(
                    text("DELETE FROM listings WHERE id = :id"),
                    {"id": created_id},
                )
                await session.commit()


@pytest.mark.asyncio
async def test_transport_car_sale_city_schema_field_still_works(
    client: AsyncClient,
) -> None:
    await engine.dispose()
    cat_id = await _category_id("transport-car-sale")
    user = await _auth_as_first_user()
    fastapi_app.dependency_overrides[get_current_user] = lambda: user

    created_id: int | None = None
    try:
        resp = await client.post(
            "/api/v1/listings",
            json={
                "title": "PUBFIX car control",
                "description": "city schema-field regression",
                "price": "500000",
                "category_id": cat_id,
                "currency": Currency.KGS.value,
                "fields": {
                    "city": "Ош",
                    "year": 2019,
                },
            },
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        created_id = body["id"]
        assert body["status"] == ListingStatus.draft.value
        assert body["fields"].get("city") == "Ош"

        # Attach approved real photo (goods require it), then activate.
        async with async_session_maker() as session:
            session.add(
                Media(
                    url="/media/test/pubfix-car.jpg",
                    listing_id=created_id,
                    order=0,
                    is_placeholder=False,
                    lifecycle_status=MediaLifecycleStatus.ready,
                    moderation_status=MediaModerationStatus.approved,
                )
            )
            await session.commit()

        act = await client.patch(
            f"/api/v1/listings/{created_id}/status",
            json={"status": ListingStatus.active.value},
            headers={"Authorization": "Bearer test"},
        )
        assert act.status_code == 200, act.text
        assert act.json()["status"] == ListingStatus.active.value
        assert act.json()["fields"].get("city") == "Ош"
    finally:
        if created_id is not None:
            async with async_session_maker() as session:
                await session.execute(
                    text("DELETE FROM listings WHERE id = :id"),
                    {"id": created_id},
                )
                await session.commit()
