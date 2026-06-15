#!/usr/bin/env python3
"""Count categories and verify seed idempotency."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import func, select

from app.db.session import async_session_maker
from app.models.category import Category
from app.seeds.loader import CategorySeedLoader


async def category_counts() -> dict[str, int]:
    async with async_session_maker() as session:
        total = (await session.execute(select(func.count()).select_from(Category))).scalar_one()
        roots = (
            await session.execute(
                select(func.count()).select_from(Category).where(Category.parent_id.is_(None))
            )
        ).scalar_one()
        dup_slugs = (
            await session.execute(
                select(func.count())
                .select_from(
                    select(Category.slug)
                    .group_by(Category.slug)
                    .having(func.count() > 1)
                    .subquery()
                )
            )
        ).scalar_one()
        return {"total": total, "roots": roots, "non_roots": total - roots, "duplicate_slug_groups": dup_slugs}


async def run_seed() -> dict:
    async with async_session_maker() as session:
        loader = CategorySeedLoader(session)
        return await loader.run()


async def main() -> None:
    before = await category_counts()
    print("BEFORE", before)
    stats1 = await run_seed()
    after1 = await category_counts()
    print("SEED_1", stats1)
    print("AFTER_1", after1)
    stats2 = await run_seed()
    after2 = await category_counts()
    print("SEED_2", stats2)
    print("AFTER_2", after2)
    idempotent = after1 == after2
    print("IDEMPOTENT", idempotent)


if __name__ == "__main__":
    asyncio.run(main())
