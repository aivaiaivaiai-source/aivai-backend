from __future__ import annotations

from app.core.exceptions import EntityNotFoundError
from app.models.vehicle import VehicleBrand
from app.repositories.vehicle_repository import VehicleBrandRepository, VehicleModelRepository
from app.schemas.vehicle import VehicleBrandRead, VehicleModelRead
from app.seeds.mobile_vehicle_catalog import MOBILE_POPULAR_BRAND_SLUGS

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
            sort_order=_POPULAR_SORT_ORDER.get(row.slug, 9999),
        )

    async def list_brands(self, *, popular_only: bool = False) -> list[VehicleBrandRead]:
        rows = await self._brands.list_enabled()
        items = [self._brand_to_read(row) for row in rows]
        if popular_only:
            items = [item for item in items if item.is_popular]
            items.sort(key=lambda item: item.sort_order)
            return items
        items.sort(key=lambda item: item.name.casefold())
        return items

    async def list_models_for_brand(self, brand_slug: str) -> list[VehicleModelRead]:
        brand = await self._brands.get_by_slug(brand_slug)
        if brand is None:
            raise EntityNotFoundError(
                "VehicleBrand",
                message=f"VehicleBrand with slug={brand_slug} not found",
            )
        rows = await self._models.list_by_brand_id(brand.id)
        return [
            VehicleModelRead(
                id=row.id,
                slug=row.slug,
                name=row.name,
                brand_slug=brand.slug,
            )
            for row in rows
        ]
