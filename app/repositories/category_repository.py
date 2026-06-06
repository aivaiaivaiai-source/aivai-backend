from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import Category
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Category)

    async def get_by_slug(self, slug: str) -> Category | None:
        stmt = select(Category).where(Category.slug == slug)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_root_categories(self, *, active_only: bool = True) -> list[Category]:
        stmt = select(Category).where(Category.parent_id.is_(None))
        if active_only:
            stmt = stmt.where(Category.is_active.is_(True))
        stmt = stmt.order_by(Category.sort_order, Category.id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_children_by_parent_id(
        self,
        parent_id: int,
        *,
        active_only: bool = True,
    ) -> list[Category]:
        stmt = select(Category).where(Category.parent_id == parent_id)
        if active_only:
            stmt = stmt.where(Category.is_active.is_(True))
        stmt = stmt.order_by(Category.sort_order, Category.id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_intelligence(self, category_id: int) -> Category | None:
        stmt = (
            select(Category)
            .where(Category.id == category_id)
            .options(
                selectinload(Category.core_fields),
                selectinload(Category.optional_fields),
                selectinload(Category.filters),
                selectinload(Category.ai_rules),
                selectinload(Category.aliases),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_active(self) -> list[Category]:
        stmt = (
            select(Category)
            .where(Category.is_active.is_(True))
            .order_by(Category.sort_order, Category.id)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
