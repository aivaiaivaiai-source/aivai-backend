from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.locale import normalize_locale
from app.models.vehicle import VehicleAlias, VehicleBrand, VehicleModel
from app.repositories.base import BaseRepository


class VehicleBrandRepository(BaseRepository[VehicleBrand]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, VehicleBrand)

    async def get_by_slug(self, slug: str) -> VehicleBrand | None:
        stmt = select(VehicleBrand).where(
            VehicleBrand.slug == slug,
            VehicleBrand.is_enabled.is_(True),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class VehicleModelRepository(BaseRepository[VehicleModel]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, VehicleModel)

    async def get_by_brand_and_slug(self, brand_id: int, slug: str) -> VehicleModel | None:
        stmt = select(VehicleModel).where(
            VehicleModel.brand_id == brand_id,
            VehicleModel.slug == slug,
            VehicleModel.is_enabled.is_(True),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class VehicleAliasRepository(BaseRepository[VehicleAlias]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, VehicleAlias)

    async def list_enabled(self, locale: str | None = None) -> list[VehicleAlias]:
        loc = normalize_locale(locale)
        stmt = (
            select(VehicleAlias)
            .where(
                VehicleAlias.is_enabled.is_(True),
                VehicleAlias.locale == loc,
            )
            .options(
                selectinload(VehicleAlias.brand),
                selectinload(VehicleAlias.model).selectinload(VehicleModel.brand),
            )
            .order_by(VehicleAlias.id)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_keys(
        self,
        spaced: str,
        compact: str,
        *,
        locale: str | None = None,
    ) -> VehicleAlias | None:
        loc = normalize_locale(locale)
        for key, column in ((compact, VehicleAlias.alias_compact), (spaced, VehicleAlias.alias_normalized)):
            if not key:
                continue
            stmt = (
                select(VehicleAlias)
                .where(
                    column == key,
                    VehicleAlias.locale == loc,
                    VehicleAlias.is_enabled.is_(True),
                )
                .options(
                    selectinload(VehicleAlias.brand),
                    selectinload(VehicleAlias.model).selectinload(VehicleModel.brand),
                )
                .limit(1)
            )
            row = (await self._session.execute(stmt)).scalar_one_or_none()
            if row is not None:
                return row
        return None
