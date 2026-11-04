# -*- coding: utf-8 -*-
"""Jobs Search E2E: foreign country + «Другие страны» city findability."""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import select, text

from app.db.session import async_session_maker, engine
from app.models.category import Category
from app.models.enums import Currency, ListingStatus
from app.models.job_create_intent import HIRING, JOB_SEEKING
from app.models.listing import Listing
from app.models.listing_field_value import ListingFieldValue
from app.models.user import User


@pytest.mark.asyncio
async def test_jobs_search_foreign_country_and_other_countries(client) -> None:
    await engine.dispose()
    ids: list[int] = []
    try:
        async with async_session_maker() as session:
            sto = (
                await session.execute(
                    select(Category).where(Category.slug == "jobs-sto-i-avtoservis")
                )
            ).scalar_one()
            it = (
                await session.execute(
                    select(Category).where(Category.slug == "jobs-it-i-tehnologii")
                )
            ).scalar_one()
            user = (
                await session.execute(select(User).order_by(User.id).limit(1))
            ).scalar_one()

            async def add(title: str, cat_id: int, intent: str, city: str) -> int:
                row = Listing(
                    title=title,
                    description="jobs-foreign-geo-e2e",
                    price=Decimal("1000"),
                    currency=Currency.KGS,
                    status=ListingStatus.active,
                    owner_id=user.id,
                    category_id=cat_id,
                    job_intent=intent,
                )
                session.add(row)
                await session.flush()
                session.add(
                    ListingFieldValue(
                        listing_id=row.id, field_key="city", value_text=city
                    )
                )
                await session.flush()
                return row.id

            ru_id = await add("E2E Jobs RU", sto.id, HIRING, "Россия")
            other_id = await add(
                "E2E Jobs Other", it.id, JOB_SEEKING, "Другие страны"
            )
            ids.extend([ru_id, other_id])
            await session.commit()
            sto_id, it_id = sto.id, it.id

        r_ru = await client.get(
            "/api/v1/listings",
            params={
                "category_id": sto_id,
                "job_intent": HIRING,
                "city": "Россия",
                "limit": 50,
            },
        )
        assert r_ru.status_code == 200
        assert "E2E Jobs RU" in {i["title"] for i in r_ru.json()["items"]}

        r_other = await client.get(
            "/api/v1/listings",
            params={
                "category_id": it_id,
                "job_intent": JOB_SEEKING,
                "city": "Другие страны",
                "limit": 50,
            },
        )
        assert r_other.status_code == 200
        assert "E2E Jobs Other" in {i["title"] for i in r_other.json()["items"]}

        # Cross-geo isolation
        miss = await client.get(
            "/api/v1/listings",
            params={
                "category_id": sto_id,
                "job_intent": HIRING,
                "city": "Другие страны",
                "limit": 50,
            },
        )
        assert miss.status_code == 200
        assert "E2E Jobs RU" not in {i["title"] for i in miss.json()["items"]}
    finally:
        async with async_session_maker() as session:
            for lid in ids:
                await session.execute(
                    text("DELETE FROM listing_field_values WHERE listing_id = :id"),
                    {"id": lid},
                )
                await session.execute(
                    text("DELETE FROM listings WHERE id = :id"),
                    {"id": lid},
                )
            await session.commit()
