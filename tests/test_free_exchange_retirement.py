"""free-exchange root retirement — not an AiVai product category."""
from __future__ import annotations

import pytest
from sqlalchemy import select

from app.db.session import async_session_maker
from app.models.category import Category
from app.models.category_field import CategoryCoreField, CategoryOptionalField
from app.models.category_filter import CategoryFilter
from app.models.category_alias import CategoryAlias
from app.seeds.category_data import ROOT_CATEGORIES, CORE_FIELDS, CATEGORY_ALIASES, ROUTING_RULES
from app.seeds.free_exchange_retirement import (
    AIVAI_ACTIVE_ROOT_COUNT,
    AIVAI_ACTIVE_ROOT_SLUGS,
    FREE_EXCHANGE_RETIRED_SLUGS,
    FREE_EXCHANGE_ROOT_SLUG,
    free_exchange_assert_retirement_contracts,
)


def test_free_exchange_retirement_contracts() -> None:
    free_exchange_assert_retirement_contracts()
    assert AIVAI_ACTIVE_ROOT_COUNT == 18
    assert FREE_EXCHANGE_ROOT_SLUG not in AIVAI_ACTIVE_ROOT_SLUGS
    assert FREE_EXCHANGE_ROOT_SLUG in FREE_EXCHANGE_RETIRED_SLUGS


def test_free_exchange_absent_from_active_seed_authority() -> None:
    root_slugs = {slug for slug, *_ in ROOT_CATEGORIES}
    assert FREE_EXCHANGE_ROOT_SLUG not in root_slugs
    assert set(root_slugs) == AIVAI_ACTIVE_ROOT_SLUGS
    for slug in FREE_EXCHANGE_RETIRED_SLUGS:
        assert slug not in CORE_FIELDS
        assert slug not in CATEGORY_ALIASES
    for _name, _pat, _desc, cfg in ROUTING_RULES:
        target = (cfg or {}).get("target_category_slug")
        assert target not in FREE_EXCHANGE_RETIRED_SLUGS


@pytest.mark.asyncio
async def test_live_free_exchange_inactive_no_sot_and_active_inventory() -> None:
    """Single async session: inactive SoT + active inventory (avoids event-loop flake)."""
    async with async_session_maker() as session:
        active_roots = (
            await session.execute(
                select(Category).where(
                    Category.parent_id.is_(None), Category.is_active.is_(True)
                )
            )
        ).scalars().all()
        active_root_slugs = {r.slug for r in active_roots}
        assert FREE_EXCHANGE_ROOT_SLUG not in active_root_slugs
        assert active_root_slugs == AIVAI_ACTIVE_ROOT_SLUGS
        assert len(active_root_slugs) == 18

        active_any = (
            await session.execute(
                select(Category.slug).where(Category.is_active.is_(True))
            )
        ).scalars().all()
        active_any_set = set(active_any)
        for slug in FREE_EXCHANGE_RETIRED_SLUGS:
            assert slug not in active_any_set

        for slug in sorted(FREE_EXCHANGE_RETIRED_SLUGS):
            row = (
                await session.execute(select(Category).where(Category.slug == slug))
            ).scalar_one_or_none()
            assert row is not None, slug
            assert row.is_active is False, slug
            cores = (
                await session.execute(
                    select(CategoryCoreField).where(
                        CategoryCoreField.category_id == row.id
                    )
                )
            ).scalars().all()
            opts = (
                await session.execute(
                    select(CategoryOptionalField).where(
                        CategoryOptionalField.category_id == row.id
                    )
                )
            ).scalars().all()
            filters = (
                await session.execute(
                    select(CategoryFilter).where(CategoryFilter.category_id == row.id)
                )
            ).scalars().all()
            aliases = (
                await session.execute(
                    select(CategoryAlias).where(CategoryAlias.category_id == row.id)
                )
            ).scalars().all()
            assert cores == [], slug
            assert opts == [], slug
            assert filters == [], slug
            assert aliases == [], slug
