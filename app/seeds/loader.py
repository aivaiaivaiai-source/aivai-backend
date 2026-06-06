from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.locale import DEFAULT_LOCALE
from app.models.category import Category
from app.models.category_alias import CategoryAlias
from app.models.category_enums import CategoryRuleType, ModerationAction, VehicleAliasTarget
from app.models.category_field import CategoryCoreField, CategoryOptionalField
from app.models.category_filter import CategoryFilter
from app.models.category_rule import CategoryRule
from app.models.vehicle import VehicleAlias, VehicleBrand, VehicleModel
from app.seeds.category_data import (
    AI_DIALOGUE_HINTS,
    CATEGORY_ALIASES,
    CORE_FIELDS,
    MODERATION_RULES,
    OPTIONAL_FIELDS,
    ROOT_CATEGORIES,
    ROUTING_RULES,
    SEARCH_FILTERS,
    SUBCATEGORIES,
)
from app.seeds.vehicle_data import BRAND_ALIASES, BRANDS, MODEL_ALIASES, MODELS
from app.services.category_text import normalize_alias_keys

logger = logging.getLogger(__name__)
_DEFAULT_LOCALE = DEFAULT_LOCALE.value


class CategorySeedLoader:
    """Idempotent seed loader — safe to run multiple times."""

    def __init__(self, session: AsyncSession, *, locale: str = _DEFAULT_LOCALE) -> None:
        self._session = session
        self._locale = locale
        self._slug_to_id: dict[str, int] = {}

    async def run(self) -> dict[str, int]:
        await self._seed_categories()
        await self._seed_aliases()
        await self._seed_fields()
        await self._seed_filters()
        await self._seed_rules()
        v_stats = await self._seed_vehicles()
        await self._session.commit()
        return {
            "categories": len(self._slug_to_id),
            "vehicle_brands": v_stats["brands"],
            "vehicle_models": v_stats["models"],
            "vehicle_aliases": v_stats["aliases"],
        }

    async def _seed_categories(self) -> None:
        for slug, name, entity_type, sort_order in ROOT_CATEGORIES:
            await self._upsert_category(
                slug=slug,
                name=name,
                entity_type=entity_type,
                sort_order=sort_order,
                parent_id=None,
                hint=AI_DIALOGUE_HINTS.get(slug),
            )
            for sub_slug, sub_name, sub_entity in SUBCATEGORIES.get(slug, []):
                await self._upsert_category(
                    slug=sub_slug,
                    name=sub_name,
                    entity_type=sub_entity,
                    sort_order=0,
                    parent_id=self._slug_to_id[slug],
                    hint=None,
                )

    async def _upsert_category(
        self,
        *,
        slug: str,
        name: str,
        entity_type,
        sort_order: int,
        parent_id: int | None,
        hint: str | None,
    ) -> None:
        existing = await self._session.execute(select(Category).where(Category.slug == slug))
        row = existing.scalar_one_or_none()
        if row is None:
            row = Category(
                slug=slug,
                name=name,
                entity_type=entity_type,
                sort_order=sort_order,
                parent_id=parent_id,
                is_active=True,
                requires_city=True,
                ai_dialogue_hint=hint,
            )
            self._session.add(row)
            await self._session.flush()
        else:
            row.name = name
            row.entity_type = entity_type
            row.sort_order = sort_order
            row.parent_id = parent_id
            row.is_active = True
            row.requires_city = True
            if hint:
                row.ai_dialogue_hint = hint
        self._slug_to_id[slug] = row.id

    async def _seed_aliases(self) -> None:
        for cat_slug, aliases in CATEGORY_ALIASES.items():
            cat_id = self._slug_to_id.get(cat_slug)
            if cat_id is None:
                continue
            for alias in aliases:
                spaced, compact = normalize_alias_keys(alias)
                stmt = select(CategoryAlias).where(
                    CategoryAlias.category_id == cat_id,
                    CategoryAlias.alias_normalized == spaced,
                    CategoryAlias.locale == self._locale,
                )
                row = (await self._session.execute(stmt)).scalar_one_or_none()
                if row is None:
                    self._session.add(
                        CategoryAlias(
                            category_id=cat_id,
                            alias=alias,
                            alias_normalized=spaced,
                            alias_compact=compact,
                            locale=self._locale,
                            weight=100,
                            is_enabled=True,
                        )
                    )
                else:
                    row.alias = alias
                    row.alias_compact = compact
                    row.weight = 100
                    row.is_enabled = True

    async def _seed_fields(self) -> None:
        for cat_slug, fields in CORE_FIELDS.items():
            cat_id = self._slug_to_id.get(cat_slug)
            if cat_id is None:
                continue
            for sort_i, (key, label, ftype, hint) in enumerate(fields):
                await self._upsert_core_field(cat_id, key, label, ftype, sort_i, hint)
        for cat_slug, fields in OPTIONAL_FIELDS.items():
            cat_id = self._slug_to_id.get(cat_slug)
            if cat_id is None:
                continue
            for sort_i, (key, label, ftype) in enumerate(fields):
                await self._upsert_optional_field(cat_id, key, label, ftype, sort_i)

    async def _upsert_core_field(self, cat_id, key, label, ftype, sort_order, hint) -> None:
        stmt = select(CategoryCoreField).where(
            CategoryCoreField.category_id == cat_id,
            CategoryCoreField.field_key == key,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            self._session.add(
                CategoryCoreField(
                    category_id=cat_id,
                    field_key=key,
                    label=label,
                    field_type=ftype,
                    is_required=True,
                    sort_order=sort_order,
                    ai_hint=hint,
                )
            )
        else:
            row.label = label
            row.field_type = ftype
            row.sort_order = sort_order
            row.ai_hint = hint
            row.is_required = True

    async def _upsert_optional_field(self, cat_id, key, label, ftype, sort_order) -> None:
        stmt = select(CategoryOptionalField).where(
            CategoryOptionalField.category_id == cat_id,
            CategoryOptionalField.field_key == key,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            self._session.add(
                CategoryOptionalField(
                    category_id=cat_id,
                    field_key=key,
                    label=label,
                    field_type=ftype,
                    is_required=False,
                    sort_order=sort_order,
                )
            )
        else:
            row.label = label
            row.field_type = ftype
            row.sort_order = sort_order

    async def _seed_filters(self) -> None:
        for cat_slug, filters in SEARCH_FILTERS.items():
            cat_id = self._slug_to_id.get(cat_slug)
            if cat_id is None:
                continue
            for sort_i, (key, label, ftype) in enumerate(filters):
                stmt = select(CategoryFilter).where(
                    CategoryFilter.category_id == cat_id,
                    CategoryFilter.filter_key == key,
                )
                row = (await self._session.execute(stmt)).scalar_one_or_none()
                if row is None:
                    self._session.add(
                        CategoryFilter(
                            category_id=cat_id,
                            filter_key=key,
                            label=label,
                            filter_type=ftype,
                            sort_order=sort_i,
                        )
                    )
                else:
                    row.label = label
                    row.filter_type = ftype
                    row.sort_order = sort_i

    async def _seed_rules(self) -> None:
        for name, pattern, _desc, config in ROUTING_RULES:
            await self._upsert_rule(
                name=name,
                pattern=pattern,
                rule_type=CategoryRuleType.routing,
                action=ModerationAction.allow,
                config=config,
            )
        for _key, pattern, desc, action, config in MODERATION_RULES:
            rule_type = (
                CategoryRuleType.guardrail
                if action == ModerationAction.block
                else CategoryRuleType.moderation
            )
            await self._upsert_rule(
                name=desc,
                pattern=pattern,
                rule_type=rule_type,
                action=action,
                config=config,
            )

    async def _upsert_rule(self, name, pattern, rule_type, action, config) -> None:
        stmt = select(CategoryRule).where(CategoryRule.name == name)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            self._session.add(
                CategoryRule(
                    category_id=None,
                    rule_type=rule_type,
                    name=name,
                    pattern=pattern,
                    action=action,
                    priority=50,
                    config=config,
                    is_active=True,
                )
            )
        else:
            row.rule_type = rule_type
            row.pattern = pattern
            row.action = action
            row.config = config
            row.is_active = True

    async def _seed_vehicles(self) -> dict[str, int]:
        brand_ids: dict[str, int] = {}
        model_count = 0
        alias_count = 0

        for slug, name, country, vtype in BRANDS:
            stmt = select(VehicleBrand).where(VehicleBrand.slug == slug)
            row = (await self._session.execute(stmt)).scalar_one_or_none()
            if row is None:
                row = VehicleBrand(
                    slug=slug,
                    name=name,
                    country_origin=country,
                    vehicle_type=vtype,
                    is_enabled=True,
                )
                self._session.add(row)
                await self._session.flush()
            else:
                row.name = name
                row.country_origin = country
                row.vehicle_type = vtype
                row.is_enabled = True
            brand_ids[slug] = row.id

        for brand_slug, models in MODELS.items():
            brand_id = brand_ids.get(brand_slug)
            if brand_id is None:
                continue
            for model_slug, model_name in models:
                stmt = select(VehicleModel).where(
                    VehicleModel.brand_id == brand_id,
                    VehicleModel.slug == model_slug,
                )
                row = (await self._session.execute(stmt)).scalar_one_or_none()
                if row is None:
                    self._session.add(
                        VehicleModel(
                            brand_id=brand_id,
                            slug=model_slug,
                            name=model_name,
                            is_enabled=True,
                        )
                    )
                    model_count += 1
                else:
                    row.name = model_name
                    row.is_enabled = True

        await self._session.flush()

        model_key_to_id: dict[tuple[str, str], int] = {}
        for brand_slug in MODELS:
            brand_id = brand_ids[brand_slug]
            res = await self._session.execute(
                select(VehicleModel).where(VehicleModel.brand_id == brand_id)
            )
            for m in res.scalars().all():
                model_key_to_id[(brand_slug, m.slug)] = m.id

        for alias, brand_slug, target in BRAND_ALIASES:
            alias_count += await self._upsert_vehicle_alias(
                alias,
                brand_ids[brand_slug],
                None,
                target,
                model_key_to_id,
            )

        for alias, brand_slug, model_slug in MODEL_ALIASES:
            model_id = model_key_to_id.get((brand_slug, model_slug))
            if model_id is None:
                continue
            alias_count += await self._upsert_vehicle_alias(
                alias,
                brand_ids[brand_slug],
                model_id,
                VehicleAliasTarget.model,
                model_key_to_id,
            )

        return {"brands": len(brand_ids), "models": model_count, "aliases": alias_count}

    async def _upsert_vehicle_alias(
        self,
        alias: str,
        brand_id: int,
        model_id: int | None,
        target: VehicleAliasTarget,
        model_key_to_id: dict,
    ) -> int:
        spaced, compact = normalize_alias_keys(alias)
        stmt = select(VehicleAlias).where(
            VehicleAlias.alias_compact == compact,
            VehicleAlias.locale == self._locale,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            self._session.add(
                VehicleAlias(
                    alias=alias,
                    alias_normalized=spaced,
                    alias_compact=compact,
                    target_type=target,
                    brand_id=brand_id,
                    model_id=model_id,
                    locale=self._locale,
                    is_enabled=True,
                )
            )
            return 1
        row.alias = alias
        row.alias_normalized = spaced
        row.brand_id = brand_id
        row.model_id = model_id
        row.target_type = target
        row.is_enabled = True
        return 0
