#!/usr/bin/env python3
"""Seed legacy + mobile skeleton categories only (no aliases/vehicles)."""
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


async def counts(session) -> dict[str, int]:
    total = (await session.execute(select(func.count()).select_from(Category))).scalar_one()
    roots = (
        await session.execute(
            select(func.count()).select_from(Category).where(Category.parent_id.is_(None))
        )
    ).scalar_one()
    dup = (
        await session.execute(
            select(func.count())
            .select_from(
                select(Category.slug).group_by(Category.slug).having(func.count() > 1).subquery()
            )
        )
    ).scalar_one()
    return {"total": total, "roots": roots, "non_roots": total - roots, "dup_slugs": dup}


async def seed_categories_only() -> dict:
    async with async_session_maker() as session:
        loader = CategorySeedLoader(session)
        await loader._seed_categories()
        mobile = await loader._seed_mobile_skeleton()
        await session.commit()
        c = await counts(session)
        return {"mobile": mobile, "counts": c}


async def main() -> None:
    async with async_session_maker() as session:
        before = await counts(session)
    print("BEFORE", before)
    r1 = await seed_categories_only()
    print("RUN1", r1)
    r2 = await seed_categories_only()
    print("RUN2", r2)
    print("IDEMPOTENT", r1["counts"] == r2["counts"] and r2["mobile"]["added"] == 0)


if __name__ == "__main__":
    asyncio.run(main())
