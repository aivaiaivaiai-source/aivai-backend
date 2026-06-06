from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category_enums import CategoryRuleType
from app.models.category_rule import CategoryRule
from app.repositories.category_rule_repository import CategoryRuleRepository


class CategoryRoutingRuleRepository(CategoryRuleRepository):
    """Routing-only rules — separated from moderation for clearer scaling."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_active_routing(self) -> list[CategoryRule]:
        return await self.get_active_rules(rule_type=CategoryRuleType.routing)
