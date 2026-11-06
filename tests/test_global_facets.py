"""Global counts: reference facets, column self-exclusion, multi-select, intents."""

import json
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
from app.models.vehicle import VehicleBrand, VehicleModel


def _bucket(body: dict, key: str) -> dict[str, int]:
    return {row["value"]: row["count"] for row in body["facets"][key]}


@pytest.mark.asyncio
async def test_global_facet_contract(client) -> None:
    await engine.dispose()
    ids: list[int] = []
    try:
        async with async_session_maker() as session:
            user = (
                await session.execute(select(User).order_by(User.id).limit(1))
            ).scalar_one()
            car = (
                await session.execute(
                    select(Category).where(Category.slug == "transport-car-sale")
                )
            ).scalar_one()
            sales = (
                await session.execute(
                    select(Category).where(
                        Category.slug == "jobs-prodazhi-i-torgovlya"
                    )
                )
            ).scalar_one()
            other = (
                await session.execute(
                    select(Category).where(Category.slug == "jobs-it-i-tehnologii")
                )
            ).scalar_one()
            brands = (
                await session.execute(
                    select(VehicleBrand).order_by(VehicleBrand.id).limit(2)
                )
            ).scalars().all()
            assert len(brands) == 2
            models = []
            for brand in brands:
                model = (
                    await session.execute(
                        select(VehicleModel)
                        .where(VehicleModel.brand_id == brand.id)
                        .limit(1)
                    )
                ).scalar_one()
                models.append(model)

            async def add_car(title: str, **fields) -> int:
                row = Listing(
                    title=title,
                    description="global-facets",
                    price=Decimal("1000"),
                    currency=Currency.USD,
                    status=ListingStatus.active,
                    owner_id=user.id,
                    category_id=car.id,
                )
                session.add(row)
                await session.flush()
                for key, value in fields.items():
                    if key == "ref_brand_id":
                        session.add(
                            ListingFieldValue(
                                listing_id=row.id,
                                field_key="brand",
                                ref_brand_id=value,
                            )
                        )
                    elif key == "ref_model_id":
                        session.add(
                            ListingFieldValue(
                                listing_id=row.id,
                                field_key="model",
                                ref_model_id=value,
                            )
                        )
                    else:
                        session.add(
                            ListingFieldValue(
                                listing_id=row.id,
                                field_key=key,
                                value_text=value,
                            )
                        )
                await session.flush()
                return row.id

            async def add_job(title: str, category, intent: str, experience: str) -> int:
                row = Listing(
                    title=title,
                    description="global-facets",
                    price=Decimal("1000"),
                    currency=Currency.KGS,
                    status=ListingStatus.active,
                    owner_id=user.id,
                    category_id=category.id,
                    job_intent=intent,
                )
                session.add(row)
                await session.flush()
                session.add(
                    ListingFieldValue(
                        listing_id=row.id,
                        field_key="experience",
                        value_text=experience,
                    )
                )
                session.add(
                    ListingFieldValue(
                        listing_id=row.id,
                        field_key="job_role",
                        value_text="Кассир",
                    )
                )
                await session.flush()
                return row.id

            ids.append(
                await add_car(
                    "GF brand A fuel petrol",
                    ref_brand_id=brands[0].id,
                    ref_model_id=models[0].id,
                    fuel="Бензин",
                    transmission="Автомат",
                )
            )
            ids.append(
                await add_car(
                    "GF brand B fuel diesel",
                    ref_brand_id=brands[1].id,
                    ref_model_id=models[1].id,
                    fuel="Дизель",
                    transmission="Механика",
                )
            )
            draft = Listing(
                title="GF draft ignored",
                description="global-facets",
                price=Decimal("1000"),
                currency=Currency.USD,
                status=ListingStatus.draft,
                owner_id=user.id,
                category_id=car.id,
            )
            session.add(draft)
            await session.flush()
            ids.append(draft.id)
            ids.append(
                await add_job("GF hiring sales 1", sales, HIRING, "1–2 года||Без опыта")
            )
            ids.append(
                await add_job("GF hiring sales 2", sales, HIRING, "1–2 года")
            )
            ids.append(
                await add_job("GF seeking sales", sales, JOB_SEEKING, "Без опыта")
            )
            await session.commit()
            car_id = car.id
            sales_id = sales.id
            other_id = other.id
            brand_ids = [brands[0].id, brands[1].id]
            model_ids = [models[0].id, models[1].id]
            brand_name = brands[0].name

        listed = await client.get(
            "/api/v1/listings",
            params={"category_id": car_id, "facets": "_category", "limit": 1},
        )
        assert listed.status_code == 200, listed.text
        categories = _bucket(listed.json(), "_category")
        assert categories[str(car_id)] >= 2

        brand_page = await client.get(
            "/api/v1/listings",
            params={
                "category_id": car_id,
                "facets": "brand,model,fuel,transmission",
                "brand": brand_name,
                "limit": 1,
            },
        )
        assert brand_page.status_code == 200, brand_page.text
        body = brand_page.json()
        brands_facet = _bucket(body, "brand")
        assert brands_facet[str(brand_ids[0])] >= 1
        assert brands_facet[str(brand_ids[1])] >= 1
        models_facet = _bucket(body, "model")
        assert models_facet[str(model_ids[0])] >= 1
        assert str(model_ids[1]) not in models_facet
        fuel = _bucket(body, "fuel")
        assert fuel["Бензин"] >= 1

        fuel_page = await client.get(
            "/api/v1/listings",
            params={
                "category_id": car_id,
                "facets": "fuel,transmission",
                "attrs": json.dumps({"fuel": "Бензин"}, ensure_ascii=False),
                "limit": 1,
            },
        )
        assert fuel_page.status_code == 200, fuel_page.text
        fuel_open = _bucket(fuel_page.json(), "fuel")
        assert fuel_open["Бензин"] >= 1
        assert fuel_open["Дизель"] >= 1
        transmission = _bucket(fuel_page.json(), "transmission")
        assert transmission["Автомат"] >= 1

        hiring = await client.get(
            "/api/v1/listings",
            params={
                "category_ids": f"{sales_id},{other_id}",
                "job_intent": HIRING,
                "facets": "_category,experience,job_role",
                "attrs": json.dumps({"experience": "1–2 года"}, ensure_ascii=False),
                "limit": 1,
            },
        )
        assert hiring.status_code == 200, hiring.text
        assert hiring.json()["total"] >= 2
        sectors = _bucket(hiring.json(), "_category")
        assert sectors[str(sales_id)] >= 2
        assert str(other_id) not in sectors or sectors[str(other_id)] >= 0
        experience = _bucket(hiring.json(), "experience")
        assert experience["1–2 года"] >= 2
        assert experience["Без опыта"] >= 1
        roles = _bucket(hiring.json(), "job_role")
        assert roles["Кассир"] >= 2

        seeking = await client.get(
            "/api/v1/listings",
            params={
                "category_id": sales_id,
                "job_intent": JOB_SEEKING,
                "q": "GF seeking sales",
                "limit": 5,
            },
        )
        assert seeking.status_code == 200, seeking.text
        seeking_titles = {item["title"] for item in seeking.json()["items"]}
        assert "GF seeking sales" in seeking_titles
        hiring_only = await client.get(
            "/api/v1/listings",
            params={
                "category_id": sales_id,
                "job_intent": HIRING,
                "q": "GF seeking sales",
                "limit": 5,
            },
        )
        assert hiring_only.status_code == 200, hiring_only.text
        assert hiring_only.json()["items"] == []
    finally:
        if ids:
            async with async_session_maker() as session:
                for listing_id in ids:
                    await session.execute(
                        text(
                            "DELETE FROM listing_field_values WHERE listing_id = :id"
                        ),
                        {"id": listing_id},
                    )
                    await session.execute(
                        text("DELETE FROM listings WHERE id = :id"),
                        {"id": listing_id},
                    )
                await session.commit()
