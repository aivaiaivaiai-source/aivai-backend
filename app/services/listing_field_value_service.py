from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from app.core.exceptions import AppException
from app.models.category_enums import CategoryFieldType
from app.models.category_field import CategoryCoreField, CategoryOptionalField
from app.models.job_create_intent import HIRING
from app.models.listing_field_value import ListingFieldValue
from app.repositories.category_repository import CategoryRepository
from app.repositories.listing_field_value_repository import ListingFieldValueRepository
from app.repositories.vehicle_repository import (
    VehicleAliasRepository,
    VehicleBrandRepository,
    VehicleModelRepository,
)
from app.seeds.car_sale_v2 import LEGACY_ENUM_ALLOW
from app.seeds.jobs_create_fields import is_jobs_create_intent_required
from app.services.category_text import normalize_alias_keys, normalize_text

# Listing-root / UI companions — never treated as category EAV fields.
# `price_currency` is the Flutter UI key for listing.currency (same contract).
_SKIP_FIELD_KEYS = frozenset(
    {"title", "description", "price", "currency", "price_currency"}
)

# Requiredness for these lives on listing root / price contract — not EAV rows.
_REQUIRED_EAV_SKIP_KEYS = frozenset(
    {"title", "description", "price", "currency", "price_currency"}
)

# Pinned create-flow geo: may be persisted even when absent from category_core_fields
# (e.g. Jobs V2 — Region/City are UI-pinned, not schema fields).
_PINNED_GEO_FIELD_KEYS = frozenset({"city", "region"})

_MULTI_SELECT_SEPARATOR = "||"
_TIME_PATTERN = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")


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
        create_intent: str | None = None,
    ) -> list[ListingFieldValue]:
        definitions = await self._load_definitions(
            category_id,
            create_intent=create_intent,
        )
        rows = await self._build_rows(
            known_fields=known_fields,
            definitions=definitions,
        )
        return await self._field_values.replace_for_listing(listing_id, rows)

    async def assert_required_fields_present(
        self,
        *,
        category_id: int,
        known_fields: dict[str, Any] | None,
        create_intent: str | None = None,
    ) -> None:
        """Block activate/publish when required Create cores are absent from EAV.

        Listing-root companions (`price` / currency) are excluded — validated by
        the listing price contract. Drafts may omit required cores; callers must
        invoke this only on the active-publish path.
        """
        definitions = await self._load_definitions(
            category_id,
            create_intent=create_intent,
        )
        payload = {
            str(k).strip(): v
            for k, v in (known_fields or {}).items()
            if k is not None and str(k).strip()
        }
        missing: list[str] = []
        for key, definition in definitions.items():
            if not definition.is_required:
                continue
            if key in _REQUIRED_EAV_SKIP_KEYS:
                continue
            raw = payload.get(key)
            if raw is None or (isinstance(raw, str) and not str(raw).strip()):
                missing.append(key)
                continue
            if definition.field_type == CategoryFieldType.enum:
                allowed = self._enum_option_values(definition.options)
                if allowed:
                    text = str(raw).strip()
                    parts = [
                        p.strip()
                        for p in text.split(_MULTI_SELECT_SEPARATOR)
                        if p.strip()
                    ] or [text]
                    if any(p not in allowed for p in parts):
                        missing.append(key)
            elif definition.field_type == CategoryFieldType.multi_select:
                allowed = self._enum_option_values(definition.options)
                if allowed:
                    text = str(raw).strip()
                    parts = [
                        p.strip()
                        for p in text.split(_MULTI_SELECT_SEPARATOR)
                        if p.strip()
                    ]
                    if not parts or any(p not in allowed for p in parts):
                        missing.append(key)
        if missing:
            raise AppException(
                "Заполните обязательные поля: " + ", ".join(sorted(missing)),
                status_code=400,
                code="MISSING_REQUIRED_FIELDS",
            )

    @staticmethod
    def _enum_option_values(options: dict | None) -> set[str]:
        if not options:
            return set()
        rows = options.get("choices") or options.get("options") or options.get("values")
        if not isinstance(rows, list):
            return set()
        out: set[str] = set()
        for row in rows:
            if isinstance(row, dict):
                raw = row.get("value")
                if raw is None:
                    raw = row.get("label")
                if raw is not None and str(raw).strip():
                    out.add(str(raw).strip())
            elif row is not None and str(row).strip():
                out.add(str(row).strip())
        return out

    async def _load_definitions(
        self,
        category_id: int,
        *,
        create_intent: str | None = None,
    ) -> dict[str, _FieldDefinition]:
        category = await self._categories.get_with_intelligence(category_id)
        if category is None:
            raise AppException(
                f"Category with id={category_id} not found",
                status_code=404,
                code="ENTITY_NOT_FOUND",
            )
        intent = (create_intent or "").strip() or None
        if intent is None and is_jobs_create_intent_required(
            getattr(category, "slug", None)
        ):
            # Pre-V2 listings: treat as employer-side hiring schema.
            intent = HIRING
        defs: dict[str, _FieldDefinition] = {}
        for row in category.core_fields:
            row_intent = getattr(row, "create_intent", None)
            if intent is None:
                if row_intent is not None:
                    continue
            elif row_intent != intent:
                continue
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
                if field_key in _PINNED_GEO_FIELD_KEYS:
                    definition = _FieldDefinition(
                        field_key=field_key,
                        field_type=CategoryFieldType.city,
                        is_required=False,
                        options=None,
                    )
                else:
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
                brand_raw = (
                    known_fields.get("brand")
                    or known_fields.get("vehicle_brand")
                )
                model_id, brand_id = await self._resolve_model_id(
                    raw_value,
                    brand_id=resolved_brand_id
                    or (
                        await self._resolve_brand_id(brand_raw)
                        if brand_raw is not None
                        and str(brand_raw).strip()
                        else None
                    ),
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

        if text.isdigit():
            brand = await self._brands.get_by_id(int(text))
            if brand is not None and brand.is_enabled:
                return brand.id

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

        if text.isdigit():
            model = await self._models.get_by_id(int(text))
            if model is not None and model.is_enabled:
                if brand_id is not None and model.brand_id != brand_id:
                    raise AppException(
                        f"Unknown model '{text}' for brand_id={brand_id}",
                        status_code=400,
                        code="INVALID_LISTING_FIELD",
                    )
                return model.id, model.brand_id

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
                row.value_int = int(str(raw_value).strip().replace(" ", ""))
            except ValueError as exc:
                raise AppException(
                    f"Field '{definition.field_key}' must be an integer",
                    status_code=400,
                    code="INVALID_LISTING_FIELD",
                ) from exc
            ListingFieldValueService._validate_numeric_bounds(
                definition, float(row.value_int)
            )
            row.value_int = ListingFieldValueService._canonicalize_int_choice(
                definition, row.value_int
            )
            return

        if field_type in {CategoryFieldType.decimal, CategoryFieldType.price}:
            try:
                row.value_decimal = Decimal(str(raw_value).strip().replace(",", "."))
            except InvalidOperation as exc:
                raise AppException(
                    f"Field '{definition.field_key}' must be a decimal",
                    status_code=400,
                    code="INVALID_LISTING_FIELD",
                ) from exc
            ListingFieldValueService._validate_numeric_bounds(
                definition, float(row.value_decimal)
            )
            row.value_decimal = ListingFieldValueService._canonicalize_decimal_choice(
                definition, row.value_decimal
            )
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

        if field_type == CategoryFieldType.multi_select:
            values = ListingFieldValueService._parse_multi_select_values(raw_value)
            if not values:
                raise AppException(
                    f"Field '{definition.field_key}' cannot be empty",
                    status_code=400,
                    code="INVALID_LISTING_FIELD",
                )
            for value in values:
                ListingFieldValueService._validate_enum_option(definition, value)
            row.value_text = _MULTI_SELECT_SEPARATOR.join(values)
            return

        if field_type == CategoryFieldType.time:
            value = str(raw_value).strip()
            if not value:
                raise AppException(
                    f"Field '{definition.field_key}' cannot be empty",
                    status_code=400,
                    code="INVALID_LISTING_FIELD",
                )
            match = _TIME_PATTERN.match(value)
            if match is None:
                raise AppException(
                    f"Field '{definition.field_key}' must be HH:MM",
                    status_code=400,
                    code="INVALID_LISTING_FIELD",
                )
            hour = int(match.group(1))
            minute = match.group(2)
            # Prefer option spelling when present ("9:00" vs "09:00").
            candidates = [value, f"{hour}:{minute}", f"{hour:02d}:{minute}"]
            stored = ListingFieldValueService._first_allowed_option(
                definition,
                candidates,
            )
            if stored is None:
                options = definition.options or {}
                if options.get("values") or options.get("choices"):
                    raise AppException(
                        f"Invalid value for field '{definition.field_key}'",
                        status_code=400,
                        code="INVALID_LISTING_FIELD",
                    )
                stored = f"{hour:02d}:{minute}"
            row.value_text = stored
            return

        raise AppException(
            f"Unsupported field type for '{definition.field_key}'",
            status_code=400,
            code="INVALID_LISTING_FIELD",
        )

    @staticmethod
    def _parse_multi_select_values(raw_value: Any) -> list[str]:
        if isinstance(raw_value, (list, tuple)):
            return [
                str(item).strip()
                for item in raw_value
                if str(item).strip()
            ]
        text = str(raw_value).strip()
        if not text:
            return []
        if _MULTI_SELECT_SEPARATOR in text:
            return [
                part.strip()
                for part in text.split(_MULTI_SELECT_SEPARATOR)
                if part.strip()
            ]
        return [text]

    @staticmethod
    def _allowed_option_values(definition: _FieldDefinition) -> dict[str, str]:
        """Map normalized option → original option string for storage."""
        options = definition.options or {}
        allowed = options.get("values") or options.get("choices")
        if not allowed:
            return {}
        out: dict[str, str] = {}
        for item in allowed:
            if isinstance(item, dict):
                raw = item.get("value") or item.get("id") or item.get("key")
                if raw is None:
                    continue
                text = str(raw).strip()
            elif isinstance(item, (list, tuple)) and item:
                text = str(item[0]).strip()
            else:
                text = str(item).strip()
            if text:
                out[text.lower()] = text
        return out

    @staticmethod
    def _first_allowed_option(
        definition: _FieldDefinition,
        candidates: list[str],
    ) -> str | None:
        allowed = ListingFieldValueService._allowed_option_values(definition)
        if not allowed:
            return None
        for candidate in candidates:
            hit = allowed.get(candidate.strip().lower())
            if hit is not None:
                return hit
        return None

    @staticmethod
    def _validate_enum_option(definition: _FieldDefinition, value: str) -> None:
        allowed = ListingFieldValueService._allowed_option_values(definition)
        if not allowed:
            return
        normalized = value.strip().lower()
        if normalized in allowed:
            return
        legacy = LEGACY_ENUM_ALLOW.get(definition.field_key)
        if legacy and value.strip() in legacy:
            # Historical edit round-trip only — not offered as new Create options.
            return
        raise AppException(
            f"Invalid value for field '{definition.field_key}'",
            status_code=400,
            code="INVALID_LISTING_FIELD",
        )

    @staticmethod
    def _canonicalize_decimal_choice(
        definition: _FieldDefinition,
        value: Decimal,
    ) -> Decimal:
        """When schema exposes discrete picker choices, accept only those values.

        Exact Decimal match only — never round (e.g. 2.25 must not become 2.2).
        """
        allowed = ListingFieldValueService._allowed_option_values(definition)
        if not allowed:
            return value
        for opt in allowed.values():
            try:
                if Decimal(str(opt)) == value:
                    return Decimal(str(opt))
            except (InvalidOperation, TypeError, ValueError):
                continue
        raise AppException(
            f"Invalid value for field '{definition.field_key}'",
            status_code=400,
            code="INVALID_LISTING_FIELD",
        )

    @staticmethod
    def _canonicalize_int_choice(
        definition: _FieldDefinition,
        value: int,
    ) -> int:
        """When schema exposes discrete picker choices, accept only those ints."""
        allowed = ListingFieldValueService._allowed_option_values(definition)
        if not allowed:
            return value
        for opt in allowed.values():
            try:
                if int(str(opt).strip()) == value:
                    return int(str(opt).strip())
            except (TypeError, ValueError):
                continue
        raise AppException(
            f"Invalid value for field '{definition.field_key}'",
            status_code=400,
            code="INVALID_LISTING_FIELD",
        )

    @staticmethod
    def _validate_numeric_bounds(definition: _FieldDefinition, value: float) -> None:
        options = definition.options or {}
        raw_min = options.get("min")
        raw_max = options.get("max")
        if raw_min is not None:
            try:
                if value < float(raw_min):
                    raise AppException(
                        f"Field '{definition.field_key}' is below minimum",
                        status_code=400,
                        code="INVALID_LISTING_FIELD",
                    )
            except (TypeError, ValueError):
                pass
        if raw_max is not None:
            try:
                if value > float(raw_max):
                    raise AppException(
                        f"Field '{definition.field_key}' is above maximum",
                        status_code=400,
                        code="INVALID_LISTING_FIELD",
                    )
            except (TypeError, ValueError):
                pass
        if definition.field_key == "year":
            if value < 1960 or value > date.today().year + 1:
                raise AppException(
                    f"Field '{definition.field_key}' is out of range",
                    status_code=400,
                    code="INVALID_LISTING_FIELD",
                )
        if definition.field_key == "mileage" and value < 0:
            raise AppException(
                f"Field '{definition.field_key}' cannot be negative",
                status_code=400,
                code="INVALID_LISTING_FIELD",
            )
        if definition.field_key == "engine_volume" and value <= 0:
            raise AppException(
                f"Field '{definition.field_key}' must be positive",
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
