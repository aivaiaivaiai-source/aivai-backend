from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.locale import DEFAULT_LOCALE
from app.models.category import Category
from app.models.category_alias import CategoryAlias
from app.models.category_enums import CategoryRuleType, ModerationAction, VehicleAliasTarget, VehicleType
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
from app.seeds.mobile_category_skeleton import MOBILE_CATEGORY_SKELETON
from app.seeds.mobile_vehicle_catalog import MOBILE_VEHICLE_BRANDS, MOBILE_VEHICLE_MODELS
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
        mobile_stats = await self._seed_mobile_skeleton()
        alias_stats = await self._seed_aliases()
        await self._seed_fields()
        await self._seed_filters()
        await self._seed_rules()
        v_stats = await self._seed_vehicles()
        await self._session.commit()
        return {
            "categories": len(self._slug_to_id),
            "mobile_skeleton_added": mobile_stats["added"],
            "mobile_skeleton_skipped": mobile_stats["skipped"],
            "category_aliases_added": alias_stats["added"],
            "category_aliases_updated": alias_stats["updated"],
            "category_aliases_conflicts": alias_stats["conflicts"],
            "vehicle_brands": v_stats["brands"],
            "vehicle_models": v_stats["models"],
            "mobile_vehicle_brands_added": v_stats["mobile_brands_added"],
            "mobile_vehicle_models_added": v_stats["mobile_models_added"],
            "vehicle_aliases_added": v_stats["aliases_added"],
            "vehicle_aliases_updated": v_stats["aliases_updated"],
            "vehicle_aliases_conflicts": v_stats["aliases_conflicts"],
        }

    async def _seed_mobile_skeleton(self) -> dict[str, int]:
        """Seed mobile v2 category tree (L2/L3) without removing legacy categories."""
        existing = await self._session.execute(select(Category.slug, Category.id))
        for slug, cat_id in existing.all():
            self._slug_to_id.setdefault(slug, cat_id)

        pending = list(MOBILE_CATEGORY_SKELETON)
        added = 0
        skipped = 0
        max_passes = 8
        for _ in range(max_passes):
            if not pending:
                break
            next_pending: list[tuple] = []
            for parent_slug, slug, name, entity_type, sort_order in pending:
                if slug in self._slug_to_id:
                    skipped += 1
                    continue
                parent_id = self._slug_to_id.get(parent_slug)
                if parent_id is None:
                    next_pending.append((parent_slug, slug, name, entity_type, sort_order))
                    continue
                await self._upsert_category(
                    slug=slug,
                    name=name,
                    entity_type=entity_type,
                    sort_order=sort_order,
                    parent_id=parent_id,
                    hint=None,
                )
                added += 1
            pending = next_pending
        if pending:
            logger.warning(
                "Mobile skeleton: %d categories not seeded (missing parent slugs)",
                len(pending),
            )
        return {"added": added, "skipped": skipped}

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

    async def _seed_aliases(self) -> dict[str, int]:
        id_to_slug = {cat_id: slug for slug, cat_id in self._slug_to_id.items()}
        added = 0
        updated = 0
        conflicts = 0
        # Pending INSERTs are invisible to SELECT until flush — track within this run.
        seen: dict[tuple[str, str], tuple[int, CategoryAlias | None]] = {}

        for cat_slug, aliases in CATEGORY_ALIASES.items():
            cat_id = self._slug_to_id.get(cat_slug)
            if cat_id is None:
                continue
            for alias in aliases:
                spaced, compact = normalize_alias_keys(alias)
                key = (spaced, self._locale)

                if key in seen:
                    existing_cat_id, existing_row = seen[key]
                    if existing_cat_id == cat_id:
                        if existing_row is not None:
                            existing_row.alias = alias
                            existing_row.alias_compact = compact
                            existing_row.weight = 100
                            existing_row.is_enabled = True
                        updated += 1
                    else:
                        existing_slug = id_to_slug.get(existing_cat_id, str(existing_cat_id))
                        logger.warning(
                            "[SeedAliases] conflict alias=%s existing_category=%s new_category=%s skipped",
                            alias,
                            existing_slug,
                            cat_slug,
                        )
                        conflicts += 1
                    continue

                stmt = select(CategoryAlias).where(
                    CategoryAlias.alias_normalized == spaced,
                    CategoryAlias.locale == self._locale,
                )
                row = (await self._session.execute(stmt)).scalar_one_or_none()
                if row is None:
                    new_row = CategoryAlias(
                        category_id=cat_id,
                        alias=alias,
                        alias_normalized=spaced,
                        alias_compact=compact,
                        locale=self._locale,
                        weight=100,
                        is_enabled=True,
                    )
                    self._session.add(new_row)
                    seen[key] = (cat_id, new_row)
                    added += 1
                elif row.category_id == cat_id:
                    row.alias = alias
                    row.alias_compact = compact
                    row.weight = 100
                    row.is_enabled = True
                    seen[key] = (cat_id, row)
                    updated += 1
                else:
                    existing_slug = id_to_slug.get(row.category_id, str(row.category_id))
                    logger.warning(
                        "[SeedAliases] conflict alias=%s existing_category=%s new_category=%s skipped",
                        alias,
                        existing_slug,
                        cat_slug,
                    )
                    seen[key] = (row.category_id, row)
                    conflicts += 1

        await self._session.flush()
        return {"added": added, "updated": updated, "conflicts": conflicts}

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

    @staticmethod
    def _same_vehicle_alias_entity(
        row: VehicleAlias,
        brand_id: int,
        model_id: int | None,
        target: VehicleAliasTarget,
    ) -> bool:
        return (
            row.brand_id == brand_id
            and row.model_id == model_id
            and row.target_type == target
        )

    @staticmethod
    def _format_vehicle_alias_entity(
        brand_id: int | None,
        model_id: int | None,
        target: VehicleAliasTarget,
        id_to_brand_slug: dict[int, str],
        id_to_model_key: dict[int, tuple[str, str]],
    ) -> str:
        brand_slug = id_to_brand_slug.get(brand_id or 0, str(brand_id))
        if target == VehicleAliasTarget.model and model_id is not None:
            brand_slug, model_slug = id_to_model_key.get(model_id, (brand_slug, str(model_id)))
            return f"model:{brand_slug}/{model_slug}"
        return f"brand:{brand_slug}"

    async def _seed_mobile_vehicle_catalog(self, brand_ids: dict[str, int]) -> dict[str, int]:
        brands_added = 0
        models_added = 0

        for slug, name in MOBILE_VEHICLE_BRANDS:
            if slug in brand_ids:
                continue
            stmt = select(VehicleBrand).where(VehicleBrand.slug == slug)
            row = (await self._session.execute(stmt)).scalar_one_or_none()
            if row is None:
                row = VehicleBrand(
                    slug=slug,
                    name=name,
                    country_origin=None,
                    vehicle_type=VehicleType.car,
                    is_enabled=True,
                )
                self._session.add(row)
                await self._session.flush()
                brands_added += 1
            brand_ids[slug] = row.id

        for brand_slug, models in MOBILE_VEHICLE_MODELS.items():
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
                    models_added += 1
                else:
                    row.name = model_name
                    row.is_enabled = True

        return {"brands_added": brands_added, "models_added": models_added}

    async def _seed_vehicles(self) -> dict[str, int]:
        brand_ids: dict[str, int] = {}
        model_count = 0
        aliases_added = 0
        aliases_updated = 0
        aliases_conflicts = 0

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

        mobile_stats = await self._seed_mobile_vehicle_catalog(brand_ids)
        model_count += mobile_stats["models_added"]

        await self._session.flush()

        model_key_to_id: dict[tuple[str, str], int] = {}
        for brand_slug, brand_id in brand_ids.items():
            res = await self._session.execute(
                select(VehicleModel).where(VehicleModel.brand_id == brand_id)
            )
            for m in res.scalars().all():
                model_key_to_id[(brand_slug, m.slug)] = m.id

        id_to_brand_slug = {brand_id: slug for slug, brand_id in brand_ids.items()}
        id_to_model_key = {model_id: key for key, model_id in model_key_to_id.items()}
        vehicle_alias_seen: dict[tuple[str, str], VehicleAlias] = {}

        for alias, brand_slug, target in BRAND_ALIASES:
            result = await self._upsert_vehicle_alias(
                alias,
                brand_ids[brand_slug],
                None,
                target,
                vehicle_alias_seen,
                id_to_brand_slug,
                id_to_model_key,
            )
            if result == "added":
                aliases_added += 1
            elif result == "updated":
                aliases_updated += 1
            else:
                aliases_conflicts += 1

        for alias, brand_slug, model_slug in MODEL_ALIASES:
            model_id = model_key_to_id.get((brand_slug, model_slug))
            if model_id is None:
                continue
            result = await self._upsert_vehicle_alias(
                alias,
                brand_ids[brand_slug],
                model_id,
                VehicleAliasTarget.model,
                vehicle_alias_seen,
                id_to_brand_slug,
                id_to_model_key,
            )
            if result == "added":
                aliases_added += 1
            elif result == "updated":
                aliases_updated += 1
            else:
                aliases_conflicts += 1

        await self._session.flush()
        return {
            "brands": len(brand_ids),
            "models": model_count,
            "mobile_brands_added": mobile_stats["brands_added"],
            "mobile_models_added": mobile_stats["models_added"],
            "aliases_added": aliases_added,
            "aliases_updated": aliases_updated,
            "aliases_conflicts": aliases_conflicts,
        }

    async def _upsert_vehicle_alias(
        self,
        alias: str,
        brand_id: int,
        model_id: int | None,
        target: VehicleAliasTarget,
        seen: dict[tuple[str, str], VehicleAlias],
        id_to_brand_slug: dict[int, str],
        id_to_model_key: dict[int, tuple[str, str]],
    ) -> str:
        spaced, compact = normalize_alias_keys(alias)
        key = (compact, self._locale)
        new_entity = self._format_vehicle_alias_entity(
            brand_id, model_id, target, id_to_brand_slug, id_to_model_key
        )

        if key in seen:
            row = seen[key]
            if self._same_vehicle_alias_entity(row, brand_id, model_id, target):
                row.alias = alias
                row.alias_normalized = spaced
                row.is_enabled = True
                return "updated"
            existing_entity = self._format_vehicle_alias_entity(
                row.brand_id, row.model_id, row.target_type, id_to_brand_slug, id_to_model_key
            )
            logger.warning(
                "[SeedVehicleAliases] conflict alias=%s existing=%s new=%s skipped",
                alias,
                existing_entity,
                new_entity,
            )
            return "conflict"

        stmt = select(VehicleAlias).where(
            VehicleAlias.alias_compact == compact,
            VehicleAlias.locale == self._locale,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            new_row = VehicleAlias(
                alias=alias,
                alias_normalized=spaced,
                alias_compact=compact,
                target_type=target,
                brand_id=brand_id,
                model_id=model_id,
                locale=self._locale,
                is_enabled=True,
            )
            self._session.add(new_row)
            seen[key] = new_row
            return "added"
        if self._same_vehicle_alias_entity(row, brand_id, model_id, target):
            row.alias = alias
            row.alias_normalized = spaced
            row.is_enabled = True
            seen[key] = row
            return "updated"
        existing_entity = self._format_vehicle_alias_entity(
            row.brand_id, row.model_id, row.target_type, id_to_brand_slug, id_to_model_key
        )
        logger.warning(
            "[SeedVehicleAliases] conflict alias=%s existing=%s new=%s skipped",
            alias,
            existing_entity,
            new_entity,
        )
        seen[key] = row
        return "conflict"
