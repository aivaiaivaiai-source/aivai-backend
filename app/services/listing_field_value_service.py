from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from app.core.exceptions import AppException
from app.models.category_enums import CategoryFieldType
from app.models.category_field import CategoryCoreField, CategoryOptionalField
from app.models.listing_field_value import ListingFieldValue
from app.repositories.category_repository import CategoryRepository
from app.repositories.listing_field_value_repository import ListingFieldValueRepository
from app.repositories.vehicle_repository import (
    VehicleAliasRepository,
    VehicleBrandRepository,
    VehicleModelRepository,
)
from app.services.category_text import normalize_alias_keys, normalize_text

_SKIP_FIELD_KEYS = frozenset({"title", "description", "price", "currency"})


@dataclass(frozen=True)
class _FieldDefinition:
    field_key: str
    field_type: CategoryFieldType
    is_required: bool
    options: dict | None


class ListingFieldValueService:
    def __init__(
        self,
        categories: CategoryRepository,
        field_values: ListingFieldValueRepository,
        brands: VehicleBrandRepository,
        models: VehicleModelRepository,
        aliases: VehicleAliasRepository,
    ) -> None:
        self._categories = categories
        self._field_values = field_values
        self._brands = brands
        self._models = models
        self._aliases = aliases

    async def list_for_listing(self, listing_id: int) -> list[ListingFieldValue]:
        return await self._field_values.list_by_listing_id(listing_id)

    async def replace_from_known_fields(
        self,
        *,
        listing_id: int,
        category_id: int,
        known_fields: dict[str, Any],
    ) -> list[ListingFieldValue]:
        definitions = await self._load_definitions(category_id)
        rows = await self._build_rows(
            known_fields=known_fields,
            definitions=definitions,
        )
        return await self._field_values.replace_for_listing(listing_id, rows)

    async def _load_definitions(self, category_id: int) -> dict[str, _FieldDefinition]:
        category = await self._categories.get_with_intelligence(category_id)
        if category is None:
            raise AppException(
                f"Category with id={category_id} not found",
                status_code=404,
                code="ENTITY_NOT_FOUND",
            )
        defs: dict[str, _FieldDefinition] = {}
        for row in category.core_fields:
            defs[row.field_key] = _FieldDefinition(
                field_key=row.field_key,
                field_type=row.field_type,
                is_required=row.is_required,
                options=row.options,
            )
        for row in category.optional_fields:
            defs[row.field_key] = _FieldDefinition(
                field_key=row.field_key,
                field_type=row.field_type,
                is_required=row.is_required,
                options=row.options,
            )
        return defs

    async def _build_rows(
        self,
        *,
        known_fields: dict[str, Any],
        definitions: dict[str, _FieldDefinition],
    ) -> list[ListingFieldValue]:
        rows: list[ListingFieldValue] = []
        resolved_brand_id: int | None = None

        for raw_key, raw_value in known_fields.items():
            field_key = str(raw_key).strip()
            if not field_key or field_key in _SKIP_FIELD_KEYS:
                continue
            if raw_value is None:
                continue
            if isinstance(raw_value, str) and not raw_value.strip():
                continue

            definition = definitions.get(field_key)
            if definition is None:
                raise AppException(
                    f"Unknown field_key '{field_key}' for category",
                    status_code=400,
                    code="INVALID_LISTING_FIELD",
                )

            row = ListingFieldValue(field_key=field_key)
            if definition.field_type == CategoryFieldType.brand:
                brand_id = await self._resolve_brand_id(raw_value)
                row.ref_brand_id = brand_id
                resolved_brand_id = brand_id
            elif definition.field_type == CategoryFieldType.model:
                model_id, brand_id = await self._resolve_model_id(
                    raw_value,
                    brand_id=resolved_brand_id
                    or await self._resolve_brand_id(known_fields.get("brand")),
                )
                row.ref_model_id = model_id
                if brand_id is not None:
                    resolved_brand_id = brand_id
            else:
                self._assign_scalar_value(row, definition, raw_value)

            self._ensure_single_value(row)
            rows.append(row)

        return rows

    async def _resolve_brand_id(self, raw: Any) -> int:
        if isinstance(raw, int):
            brand = await self._brands.get_by_id(raw)
            if brand is None or not brand.is_enabled:
                raise AppException(
                    "Invalid brand reference",
                    status_code=400,
                    code="INVALID_LISTING_FIELD",
                )
            return brand.id

        text = str(raw).strip()
        if not text:
            raise AppException(
                "Brand value is required",
                status_code=400,
                code="INVALID_LISTING_FIELD",
            )

        slug = normalize_text(text).replace(" ", "-")
        brand = await self._brands.get_by_slug(slug)
        if brand is not None:
            return brand.id

        spaced, compact = normalize_alias_keys(text)
        alias = await self._aliases.find_by_keys(spaced, compact)
        if alias is not None and alias.brand_id is not None:
            return alias.brand_id

        raise AppException(
            f"Unknown brand '{text}'",
            status_code=400,
            code="INVALID_LISTING_FIELD",
        )

    async def _resolve_model_id(
        self,
        raw: Any,
        *,
        brand_id: int | None,
    ) -> tuple[int, int | None]:
        if isinstance(raw, int):
            model = await self._models.get_by_id(raw)
            if model is None or not model.is_enabled:
                raise AppException(
                    "Invalid model reference",
                    status_code=400,
                    code="INVALID_LISTING_FIELD",
                )
            return model.id, model.brand_id

        text = str(raw).strip()
        if not text:
            raise AppException(
                "Model value is required",
                status_code=400,
                code="INVALID_LISTING_FIELD",
            )

        if brand_id is None:
            spaced, compact = normalize_alias_keys(text)
            alias = await self._aliases.find_by_keys(spaced, compact)
            if alias is not None and alias.model_id is not None:
                return alias.model_id, alias.brand_id
            raise AppException(
                "Brand is required before model",
                status_code=400,
                code="INVALID_LISTING_FIELD",
            )

        slug = normalize_text(text).replace(" ", "-")
        model = await self._models.get_by_brand_and_slug(brand_id, slug)
        if model is None:
            alias = await self._aliases.find_by_keys(*normalize_alias_keys(text))
            if (
                alias is not None
                and alias.model_id is not None
                and alias.brand_id == brand_id
            ):
                return alias.model_id, brand_id
            raise AppException(
                f"Unknown model '{text}' for brand_id={brand_id}",
                status_code=400,
                code="INVALID_LISTING_FIELD",
            )
        return model.id, brand_id

    @staticmethod
    def _assign_scalar_value(
        row: ListingFieldValue,
        definition: _FieldDefinition,
        raw_value: Any,
    ) -> None:
        field_type = definition.field_type

        if field_type in {
            CategoryFieldType.string,
            CategoryFieldType.city,
            CategoryFieldType.enum,
        }:
            value = str(raw_value).strip()
            if not value:
                raise AppException(
                    f"Field '{definition.field_key}' cannot be empty",
                    status_code=400,
                    code="INVALID_LISTING_FIELD",
                )
            ListingFieldValueService._validate_enum_option(definition, value)
            row.value_text = value
            return

        if field_type in {CategoryFieldType.number, CategoryFieldType.year}:
            try:
                row.value_int = int(str(raw_value).strip())
            except ValueError as exc:
                raise AppException(
                    f"Field '{definition.field_key}' must be an integer",
                    status_code=400,
                    code="INVALID_LISTING_FIELD",
                ) from exc
            return

        if field_type in {CategoryFieldType.decimal, CategoryFieldType.price}:
            try:
                row.value_decimal = Decimal(str(raw_value).strip())
            except InvalidOperation as exc:
                raise AppException(
                    f"Field '{definition.field_key}' must be a decimal",
                    status_code=400,
                    code="INVALID_LISTING_FIELD",
                ) from exc
            return

        if field_type == CategoryFieldType.boolean:
            if isinstance(raw_value, bool):
                row.value_bool = raw_value
                return
            normalized = str(raw_value).strip().lower()
            if normalized in {"1", "true", "yes", "да"}:
                row.value_bool = True
                return
            if normalized in {"0", "false", "no", "нет"}:
                row.value_bool = False
                return
            raise AppException(
                f"Field '{definition.field_key}' must be a boolean",
                status_code=400,
                code="INVALID_LISTING_FIELD",
            )

        raise AppException(
            f"Unsupported field type for '{definition.field_key}'",
            status_code=400,
            code="INVALID_LISTING_FIELD",
        )

    @staticmethod
    def _validate_enum_option(definition: _FieldDefinition, value: str) -> None:
        options = definition.options or {}
        allowed = options.get("values") or options.get("choices")
        if not allowed:
            return
        normalized_allowed = {str(item).strip().lower() for item in allowed}
        if value.strip().lower() not in normalized_allowed:
            raise AppException(
                f"Invalid value for field '{definition.field_key}'",
                status_code=400,
                code="INVALID_LISTING_FIELD",
            )

    @staticmethod
    def _ensure_single_value(row: ListingFieldValue) -> None:
        populated = [
            row.value_text is not None,
            row.value_int is not None,
            row.value_decimal is not None,
            row.value_bool is not None,
            row.value_date is not None,
            row.ref_brand_id is not None,
            row.ref_model_id is not None,
        ]
        if sum(populated) != 1:
            raise AppException(
                f"Field '{row.field_key}' must populate exactly one value column",
                status_code=400,
                code="INVALID_LISTING_FIELD",
            )
