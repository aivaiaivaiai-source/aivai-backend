from __future__ import annotations

from sqlalchemy import Select, exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.locale import normalize_locale
from app.models.category_enums import (
    VehicleCatalogContext,
    VehicleExecution,
    VehicleType,
)
from app.models.vehicle import (
    VehicleAlias,
    VehicleBrand,
    VehicleModel,
    VehicleModelAllowedExecution,
)
from app.repositories.base import BaseRepository


class VehicleBrandRepository(BaseRepository[VehicleBrand]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, VehicleBrand)

    async def get_by_slug(
        self,
        slug: str,
        *,
        vehicle_type: VehicleType | None = None,
    ) -> VehicleBrand | None:
        stmt = select(VehicleBrand).where(
            VehicleBrand.slug == slug,
            VehicleBrand.is_enabled.is_(True),
        )
        if vehicle_type is not None:
            stmt = stmt.where(VehicleBrand.vehicle_type == vehicle_type)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_enabled(
        self,
        *,
        vehicle_type: VehicleType | None = None,
    ) -> list[VehicleBrand]:
        stmt = select(VehicleBrand).where(VehicleBrand.is_enabled.is_(True))
        if vehicle_type is not None:
            stmt = stmt.where(VehicleBrand.vehicle_type == vehicle_type)
        stmt = stmt.order_by(VehicleBrand.name)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_for_catalog_context(
        self,
        context: VehicleCatalogContext,
    ) -> list[VehicleBrand]:
        if context in (
            VehicleCatalogContext.car_sale,
            VehicleCatalogContext.passenger_parts,
        ):
            return await self.list_enabled(vehicle_type=VehicleType.car)

        if context == VehicleCatalogContext.cargo_parts:
            truck = await self.list_enabled(vehicle_type=VehicleType.truck)
            cargo_brand_ids = select(VehicleModel.brand_id).where(
                VehicleModel.is_enabled.is_(True),
                exists().where(
                    VehicleModelAllowedExecution.model_id == VehicleModel.id,
                    VehicleModelAllowedExecution.execution == VehicleExecution.cargo,
                ),
            )
            stmt = (
                select(VehicleBrand)
                .where(
                    VehicleBrand.is_enabled.is_(True),
                    VehicleBrand.id.in_(cargo_brand_ids),
                )
                .order_by(VehicleBrand.name)
            )
            lcv = list((await self._session.execute(stmt)).scalars().all())
            by_id = {b.id: b for b in truck}
            for b in lcv:
                by_id[b.id] = b
            return sorted(by_id.values(), key=lambda b: b.name.casefold())

        if context == VehicleCatalogContext.bus_parts:
            passenger_brand_ids = select(VehicleModel.brand_id).where(
                VehicleModel.is_enabled.is_(True),
                exists().where(
                    VehicleModelAllowedExecution.model_id == VehicleModel.id,
                    VehicleModelAllowedExecution.execution
                    == VehicleExecution.passenger,
                ),
            )
            stmt = (
                select(VehicleBrand)
                .where(
                    VehicleBrand.is_enabled.is_(True),
                    VehicleBrand.id.in_(passenger_brand_ids),
                )
                .order_by(VehicleBrand.name)
            )
            return list((await self._session.execute(stmt)).scalars().all())

        return await self.list_enabled()


class VehicleModelRepository(BaseRepository[VehicleModel]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, VehicleModel)

    async def get_by_brand_and_slug(self, brand_id: int, slug: str) -> VehicleModel | None:
        stmt = (
            select(VehicleModel)
            .where(
                VehicleModel.brand_id == brand_id,
                VehicleModel.slug == slug,
                VehicleModel.is_enabled.is_(True),
            )
            .options(selectinload(VehicleModel.allowed_executions))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    def _base_by_brand(self, brand_id: int) -> Select[tuple[VehicleModel]]:
        return (
            select(VehicleModel)
            .where(
                VehicleModel.brand_id == brand_id,
                VehicleModel.is_enabled.is_(True),
            )
            .options(selectinload(VehicleModel.allowed_executions))
            .order_by(VehicleModel.name)
        )

    async def list_by_brand_id(self, brand_id: int) -> list[VehicleModel]:
        result = await self._session.execute(self._base_by_brand(brand_id))
        return list(result.scalars().unique().all())

    async def list_for_catalog_context(
        self,
        brand_id: int,
        *,
        context: VehicleCatalogContext,
        brand_vehicle_type: VehicleType,
    ) -> list[VehicleModel]:
        stmt = self._base_by_brand(brand_id)

        if context in (
            VehicleCatalogContext.car_sale,
            VehicleCatalogContext.passenger_parts,
        ):
            # Exclude models under commercial execution policy.
            stmt = stmt.where(
                ~exists().where(
                    VehicleModelAllowedExecution.model_id == VehicleModel.id,
                )
            )
        elif context == VehicleCatalogContext.cargo_parts:
            if brand_vehicle_type == VehicleType.truck:
                pass  # truck brand models as-is
            else:
                stmt = stmt.where(
                    exists().where(
                        VehicleModelAllowedExecution.model_id == VehicleModel.id,
                        VehicleModelAllowedExecution.execution
                        == VehicleExecution.cargo,
                    )
                )
        elif context == VehicleCatalogContext.bus_parts:
            stmt = stmt.where(
                exists().where(
                    VehicleModelAllowedExecution.model_id == VehicleModel.id,
                    VehicleModelAllowedExecution.execution
                    == VehicleExecution.passenger,
                )
            )

        result = await self._session.execute(stmt)
        return list(result.scalars().unique().all())

    async def model_has_execution_policy(self, model_id: int) -> bool:
        stmt = select(VehicleModelAllowedExecution.id).where(
            VehicleModelAllowedExecution.model_id == model_id
        ).limit(1)
        return (await self._session.execute(stmt)).scalar_one_or_none() is not None


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
        for key, column in (
            (compact, VehicleAlias.alias_compact),
            (spaced, VehicleAlias.alias_normalized),
        ):
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
