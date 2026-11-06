"""Work-mode ratios and experience multi-select. Values stay Russian labels."""
from __future__ import annotations

import pytest

from app.models.category_enums import CategoryFilterType
from app.seeds.jobs_create_fields import (
    CREATE_EXPERIENCE,
    JOBS_V2_CANONICAL_SLUGS,
    WORK_MODE,
    build_jobs_hiring_core_fields,
)
from app.seeds.jobs_search_filters import build_jobs_search_filters
from app.seeds.jobs_seeking_fields import build_jobs_seeking_core_fields
from app.services.listing_field_value_service import ListingFieldValueService

_ADDED = ("2/1", "1/2", "3/1")
_LADDER = ("Без опыта", "До 1 года", "1–2 года", "2–4 года")


def _field(fields, key: str):
    return next(field for field in fields if field[0] == key)


def _choices(field) -> list[str]:
    return [item["value"] for item in field[4]["choices"]]


def test_work_mode_includes_new_ratios_on_create_and_search() -> None:
    hiring = build_jobs_hiring_core_fields()
    search = build_jobs_search_filters()
    for slug in JOBS_V2_CANONICAL_SLUGS:
        create_modes = _choices(_field(hiring[slug], "work_mode"))
        assert create_modes == list(WORK_MODE)
        for label in _ADDED:
            assert label in create_modes
        seeking_keys = {item[0] for item in search[slug]["job_seeking"]}
        assert "work_mode" not in seeking_keys


def test_work_mode_search_options_match_create() -> None:
    search = build_jobs_search_filters()
    for slug in JOBS_V2_CANONICAL_SLUGS:
        row = next(item for item in search[slug]["hiring"] if item[0] == "work_mode")
        assert row[2] == CategoryFilterType.multi_select
        values = [item["value"] for item in row[4]["options"]]
        assert values == list(WORK_MODE)
        for label in _ADDED:
            assert label in values


def test_experience_create_is_multi_select_both_intents() -> None:
    hiring = build_jobs_hiring_core_fields()
    seeking = build_jobs_seeking_core_fields()
    for slug in JOBS_V2_CANONICAL_SLUGS:
        hire = _field(hiring[slug], "experience") if any(
            field[0] == "experience" for field in hiring[slug]
        ) else None
        if hire is not None:
            assert hire[2].value == "multi_select"
            assert _choices(hire) == list(CREATE_EXPERIENCE)
        seek = _field(seeking[slug], "experience")
        assert seek[2].value == "multi_select"
        assert _choices(seek) == list(CREATE_EXPERIENCE)
        if hire is not None:
            assert seek[2] == hire[2]


def test_experience_search_uses_conditions_multi_contract() -> None:
    search = build_jobs_search_filters()
    for slug in JOBS_V2_CANONICAL_SLUGS:
        for intent in ("hiring", "job_seeking"):
            rows = {item[0]: item for item in search[slug][intent]}
            if "experience" not in rows:
                continue
            experience = rows["experience"]
            conditions = rows["job_conditions"]
            assert experience[2] == conditions[2] == CategoryFilterType.multi_select
            values = [item["value"] for item in experience[4]["options"]]
            for label in _LADDER:
                assert label in values


def test_experience_storage_keeps_single_and_joins_many() -> None:
    parse = ListingFieldValueService._parse_multi_select_values
    assert parse("1–2 года") == ["1–2 года"]
    assert parse("Без опыта||До 1 года||1–2 года") == [
        "Без опыта",
        "До 1 года",
        "1–2 года",
    ]
    assert "||".join(parse("1–2 года||2–4 года")) == "1–2 года||2–4 года"


def test_seed_builders_twice_keep_work_mode_and_experience() -> None:
    first = build_jobs_hiring_core_fields()
    second = build_jobs_hiring_core_fields()
    slug = "jobs-prodazhi-i-torgovlya"
    assert _choices(_field(first[slug], "work_mode")) == _choices(
        _field(second[slug], "work_mode")
    )
    assert _field(first[slug], "experience")[2] == _field(second[slug], "experience")[2]


@pytest.mark.asyncio
async def test_experience_search_or_matches_single_or_multi_value(client) -> None:
    """Same ANY/OR contract as other Jobs multi-select filters."""
    import json
    from decimal import Decimal

    from sqlalchemy import select, text

    from app.db.session import async_session_maker, engine
    from app.models.category import Category
    from app.models.enums import Currency, ListingStatus
    from app.models.job_create_intent import HIRING
    from app.models.listing import Listing
    from app.models.listing_field_value import ListingFieldValue
    from app.models.user import User

    await engine.dispose()
    ids: list[int] = []
    try:
        async with async_session_maker() as session:
            category = (
                await session.execute(
                    select(Category).where(Category.slug == "jobs-it-i-tehnologii")
                )
            ).scalar_one()
            user = (
                await session.execute(select(User).order_by(User.id).limit(1))
            ).scalar_one()

            async def add(title: str, experience: str) -> int:
                row = Listing(
                    title=title,
                    description="jobs-experience-multi-e2e",
                    price=Decimal("1000"),
                    currency=Currency.KGS,
                    status=ListingStatus.active,
                    owner_id=user.id,
                    category_id=category.id,
                    job_intent=HIRING,
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
                await session.flush()
                return row.id

            ids.append(await add("EXP single 1-2", "1–2 года"))
            ids.append(await add("EXP multi none", "Без опыта||До 1 года"))
            await session.commit()
            category_id = category.id

        async def titles(experience: str) -> set[str]:
            response = await client.get(
                "/api/v1/listings",
                params={
                    "category_id": category_id,
                    "job_intent": HIRING,
                    "attrs": json.dumps(
                        {"experience": experience}, ensure_ascii=False
                    ),
                    "limit": 50,
                },
            )
            assert response.status_code == 200, response.text
            return {item["title"] for item in response.json()["items"]}

        both = await titles("1–2 года||Без опыта")
        assert "EXP single 1-2" in both
        assert "EXP multi none" in both
        only_old = await titles("1–2 года")
        assert "EXP single 1-2" in only_old
        assert "EXP multi none" not in only_old
        neither = await titles("2–4 года")
        assert "EXP single 1-2" not in neither
        assert "EXP multi none" not in neither
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

