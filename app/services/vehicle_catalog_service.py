from __future__ import annotations

from app.core.exceptions import EntityNotFoundError
from app.models.category_enums import VehicleCatalogContext, VehicleType
from app.models.vehicle import VehicleBrand, VehicleModel
from app.repositories.vehicle_repository import VehicleBrandRepository, VehicleModelRepository
from app.schemas.vehicle import VehicleBrandRead, VehicleModelRead
from app.seeds.mobile_vehicle_catalog import MOBILE_POPULAR_BRAND_SLUGS
from app.services.vehicle_execution import (
    EXECUTION_PLACEMENT_SLUG,
    VEHICLE_EXECUTION_LABELS_RU,
)

_POPULAR_SORT_ORDER: dict[str, int] = {
    slug: (index + 1) * 10 for index, slug in enumerate(MOBILE_POPULAR_BRAND_SLUGS)
}


class VehicleCatalogService:
    def __init__(
        self,
        brand_repository: VehicleBrandRepository,
        model_repository: VehicleModelRepository,
    ) -> None:
        self._brands = brand_repository
        self._models = model_repository

    def _brand_to_read(self, row: VehicleBrand) -> VehicleBrandRead:
        is_popular = row.slug in _POPULAR_SORT_ORDER
        return VehicleBrandRead(
            id=row.id,
            slug=row.slug,
            name=row.name,
            is_popular=is_popular,
            country=row.country_origin,
            vehicle_type=row.vehicle_type,
            sort_order=_POPULAR_SORT_ORDER.get(row.slug, 9999),
        )

    def _model_to_read(self, row: VehicleModel, brand_slug: str) -> VehicleModelRead:
        allowed = [e.execution for e in (row.allowed_executions or [])]
        return VehicleModelRead(
            id=row.id,
            slug=row.slug,
            name=row.name,
            brand_slug=brand_slug,
            allowed_executions=allowed,
            allowed_execution_labels_ru={
                e.value: VEHICLE_EXECUTION_LABELS_RU[e] for e in allowed
            },
            requires_execution_choice=len(allowed) > 1,
            placement_by_execution={
                e.value: EXECUTION_PLACEMENT_SLUG[e] for e in allowed
            },
        )

    async def list_brands(
        self,
        *,
        popular_only: bool = False,
        vehicle_type: VehicleType | None = None,
        catalog_context: VehicleCatalogContext | None = None,
    ) -> list[VehicleBrandRead]:
        if catalog_context is not None:
            rows = await self._brands.list_for_catalog_context(catalog_context)
        else:
            rows = await self._brands.list_enabled(vehicle_type=vehicle_type)
        items = [self._brand_to_read(row) for row in rows]
        if popular_only:
            items = [item for item in items if item.is_popular]
            items.sort(key=lambda item: item.sort_order)
            return items
        items.sort(key=lambda item: item.name.casefold())
        return items

    async def list_models_for_brand(
        self,
        brand_slug: str,
        *,
        vehicle_type: VehicleType | None = None,
        catalog_context: VehicleCatalogContext | None = None,
    ) -> list[VehicleModelRead]:
        # Cargo/bus contexts may resolve car brands that host LCV models.
        force_type = vehicle_type
        if catalog_context in (
            VehicleCatalogContext.cargo_parts,
            VehicleCatalogContext.bus_parts,
        ):
            force_type = None
        elif catalog_context in (
            VehicleCatalogContext.car_sale,
            VehicleCatalogContext.passenger_parts,
        ):
            force_type = VehicleType.car

        brand = await self._brands.get_by_slug(brand_slug, vehicle_type=force_type)
        if brand is None:
            raise EntityNotFoundError(
                "VehicleBrand",
                message=f"VehicleBrand with slug={brand_slug} not found",
            )

        if catalog_context is not None:
            rows = await self._models.list_for_catalog_context(
                brand.id,
                context=catalog_context,
                brand_vehicle_type=brand.vehicle_type,
            )
        else:
            rows = await self._models.list_by_brand_id(brand.id)

        return [self._model_to_read(row, brand.slug) for row in rows]
