from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.locale import normalize_locale
from app.models.category_alias import CategoryAlias
from app.repositories.base import BaseRepository


class CategoryAliasRepository(BaseRepository[CategoryAlias]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, CategoryAlias)

    async def list_enabled(self, locale: str | None = None) -> list[CategoryAlias]:
        loc = normalize_locale(locale)
        stmt = (
            select(CategoryAlias)
            .where(
                CategoryAlias.is_enabled.is_(True),
                CategoryAlias.locale == loc,
            )
            .options(selectinload(CategoryAlias.category))
            .order_by(CategoryAlias.weight.desc(), CategoryAlias.id)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_keys(
        self,
        spaced: str,
        compact: str,
        *,
        locale: str | None = None,
    ) -> CategoryAlias | None:
        loc = normalize_locale(locale)
        for key, column in ((compact, CategoryAlias.alias_compact), (spaced, CategoryAlias.alias_normalized)):
            if not key:
                continue
            stmt = (
                select(CategoryAlias)
                .where(
                    column == key,
                    CategoryAlias.locale == loc,
                    CategoryAlias.is_enabled.is_(True),
                )
                .options(selectinload(CategoryAlias.category))
                .limit(1)
            )
            row = (await self._session.execute(stmt)).scalar_one_or_none()
            if row is not None:
                return row
        return None
