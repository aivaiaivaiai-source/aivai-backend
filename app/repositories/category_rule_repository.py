from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category_enums import CategoryRuleType
from app.models.category_rule import CategoryRule
from app.repositories.base import BaseRepository


class CategoryRuleRepository(BaseRepository[CategoryRule]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, CategoryRule)

    async def get_active_rules(
        self,
        rule_type: CategoryRuleType | None = None,
        category_id: int | None = None,
    ) -> list[CategoryRule]:
        stmt = select(CategoryRule).where(CategoryRule.is_active.is_(True))
        if rule_type is not None:
            stmt = stmt.where(CategoryRule.rule_type == rule_type)
        if category_id is not None:
            stmt = stmt.where(
                or_(
                    CategoryRule.category_id == category_id,
                    CategoryRule.category_id.is_(None),
                )
            )
        stmt = stmt.order_by(CategoryRule.priority.asc(), CategoryRule.id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
