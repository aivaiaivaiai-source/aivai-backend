from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.locale import DEFAULT_LOCALE
from app.models.category import Category
from app.models.category_alias import CategoryAlias
from app.models.category_enums import (
    CategoryRuleType,
    ModerationAction,
    VehicleAliasTarget,
    VehicleType,
)
from app.models.category_field import CategoryCoreField, CategoryOptionalField
from app.models.category_filter import CategoryFilter
from app.models.category_rule import CategoryRule
from app.models.vehicle import (
    VehicleAlias,
    VehicleBrand,
    VehicleModel,
    VehicleModelAllowedExecution,
)
from app.services.vehicle_execution import APPROVED_MODEL_EXECUTIONS
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
from app.seeds.electric_sale_catalogs import (
    ELECTRIC_SALE_BRANDS,
    ELECTRIC_SALE_MODELS,
)
from app.seeds.bicycle_sale_catalogs import (
    BICYCLE_SALE_BRANDS,
    BICYCLE_SALE_MODELS,
)
from app.seeds.cargo_sale_catalogs import (
    CARGO_SALE_BRANDS,
    CARGO_SALE_MODELS,
)
from app.seeds.bus_sale_catalogs import (
    BUS_SALE_BRANDS,
    BUS_SALE_MODELS,
)
from app.seeds.special_sale_catalogs import (
    SPECIAL_SALE_BRANDS,
    SPECIAL_SALE_MODELS,
)
from app.seeds.farm_sale_catalogs import (
    FARM_DISABLE_BRAND_SLUGS,
    FARM_DISABLE_MODELS_BY_BRAND,
    FARM_SALE_BRANDS,
    FARM_SALE_MODELS,
)
from app.seeds.water_sale_catalogs import (
    WATER_SALE_BRANDS,
    WATER_SALE_MODELS,
)
from app.seeds.water_sale_v2 import (
    BOAT_MOTOR_BRANDS,
    BOAT_MOTOR_MODELS,
    JET_SKI_DISABLE_BRAND_SLUGS,
    OTHER_WATERCRAFT_DISABLE_BRAND_SLUGS,
)
from app.seeds.trailer_sale_catalogs import (
    TRAILER_SALE_BRANDS,
    TRAILER_SALE_MODELS,
)
from app.seeds.moto_sale_catalogs import MOTO_SALE_BRANDS, MOTO_SALE_MODELS
from app.seeds.parts_vehicle_catalogs import (
    CARGO_LCV_PARTS_MODELS,
    CARGO_PARTS_TRUCK_BRANDS,
    PARTS_CATALOG_BRANDS,
    PARTS_CATALOG_MODELS,
    TRUCK_CATALOG_MODELS,
    TRUCK_PARTS_DISABLED_MODELS,
)
from app.seeds.vehicle_data import BRAND_ALIASES, BRANDS, MODEL_ALIASES, MODELS
from app.seeds.transport_canonical import RETIRED_TRANSPORT_SLUGS
from app.seeds.transport_v2_1 import RETIRE_BRANCH_ROOT_SLUGS, RETIRE_LEAF_SLUGS
from app.seeds.home_garden_canonical import RETIRED_HOME_GARDEN_LEGACY_SLUGS
from app.seeds.jobs_create_fields import (
    JOBS_V2_INACTIVE_SECTOR_SLUGS,
    JOBS_V2_RETIRED_LEGACY_SLUGS,
)
from app.seeds.real_estate_v2 import RETIRED_REAL_ESTATE_SLUGS
from app.seeds.electronics_v2 import ELECTRONICS_V2_RETIRED_SLUGS
from app.seeds.fashion_v2 import FASHION_V2_RETIRED_SLUGS
from app.seeds.kids_v2 import KIDS_V2_RETIRED_SLUGS
from app.seeds.food_agri_v2 import FOOD_AGRI_V2_RETIRED_SLUGS
from app.seeds.animals_v2 import ANIMALS_V2_RETIRED_SLUGS
from app.seeds.repair_v2 import REPAIR_V2_RETIRED_SLUGS
from app.seeds.services_v2 import SERVICES_V2_RETIRED_SLUGS
from app.services.category_text import normalize_alias_keys

logger = logging.getLogger(__name__)
_DEFAULT_LOCALE = DEFAULT_LOCALE.value

_RETIRED_CATEGORY_SLUGS: frozenset[str] = (
    RETIRED_TRANSPORT_SLUGS
    | RETIRE_BRANCH_ROOT_SLUGS
    | RETIRE_LEAF_SLUGS
    | RETIRED_HOME_GARDEN_LEGACY_SLUGS
    | RETIRED_REAL_ESTATE_SLUGS
    | SERVICES_V2_RETIRED_SLUGS
    | REPAIR_V2_RETIRED_SLUGS
    | ELECTRONICS_V2_RETIRED_SLUGS
    | FASHION_V2_RETIRED_SLUGS
    | KIDS_V2_RETIRED_SLUGS
    | FOOD_AGRI_V2_RETIRED_SLUGS
    | ANIMALS_V2_RETIRED_SLUGS
)

# Alias/model nicknames must never be VehicleBrand.slug.
# Historical bug: MODEL_ALIASES text used as brand slug with marque display name.
_FORBIDDEN_BRAND_SLUGS: frozenset[str] = frozenset(
    alias.strip().lower() for alias, _brand, _model in MODEL_ALIASES
) | frozenset({"vw"})


class CategorySeedLoader:
    """Idempotent seed loader — safe to run multiple times."""

    def __init__(self, session: AsyncSession, *, locale: str = _DEFAULT_LOCALE) -> None:
        self._session = session
        self._locale = locale
        self._slug_to_id: dict[str, int] = {}

    async def run(self) -> dict[str, int]:
        # Load all existing slugs first so canonical/retired rows are addressable.
        existing = await self._session.execute(select(Category.slug, Category.id, Category.is_active))
        for slug, cat_id, is_active in existing.all():
            self._slug_to_id.setdefault(slug, cat_id)
            if slug in RETIRED_TRANSPORT_SLUGS and is_active:
                logger.warning(
                    "Retired transport slug %s is still active — run migrate_transport_canonical_phase1",
                    slug,
                )

        await self._seed_categories()
        mobile_stats = await self._seed_mobile_skeleton()
        retired_home = await self._deactivate_retired_home_garden()
        stale_home = await self._deactivate_stale_home_garden_nodes()
        kids_cleanup = await self._seed_kids_v2_taxonomy_cleanup()
        food_cleanup = await self._seed_food_agri_v2_taxonomy_cleanup()
        alias_stats = await self._seed_aliases()
        await self._seed_fields()
        await self._seed_filters()
        # After legacy field seeding so animals-pets/livestock/birds cores stay cleared.
        animals_cleanup = await self._seed_animals_v2_taxonomy_cleanup()
        await self._retire_jobs_legacy_schemas()
        await self._seed_rules()
        v_stats = await self._seed_vehicles()
        await self._session.commit()
        return {
            "categories": len(self._slug_to_id),
            "mobile_skeleton_added": mobile_stats["added"],
            "mobile_skeleton_skipped": mobile_stats["skipped"],
            "home_garden_legacy_retired": retired_home,
            "home_garden_stale_retired": stale_home,
            "kids_v2_retired": kids_cleanup["retired"],
            "kids_v2_canonical_active": kids_cleanup["canonical_active"],
            "food_agri_v2_retired": food_cleanup["retired"],
            "food_agri_v2_canonical_active": food_cleanup["canonical_active"],
            "animals_v2_retired": animals_cleanup["retired"],
            "animals_v2_canonical_active": animals_cleanup["canonical_active"],
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
                if slug in _RETIRED_CATEGORY_SLUGS:
                    # Ensure already-seeded retired leaves stay inactive.
                    await self._upsert_category(
                        slug=slug,
                        name=name,
                        entity_type=entity_type,
                        sort_order=sort_order,
                        parent_id=self._slug_to_id.get(parent_slug),
                        hint=None,
                    )
                    skipped += 1
                    continue
                parent_id = self._slug_to_id.get(parent_slug)
                if parent_id is None:
                    next_pending.append((parent_slug, slug, name, entity_type, sort_order))
                    continue
                already = slug in self._slug_to_id
                await self._upsert_category(
                    slug=slug,
                    name=name,
                    entity_type=entity_type,
                    sort_order=sort_order,
                    parent_id=parent_id,
                    hint=None,
                )
                if already:
                    skipped += 1
                else:
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
                if sub_slug in _RETIRED_CATEGORY_SLUGS:
                    continue
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
        if slug in _RETIRED_CATEGORY_SLUGS:
            existing = await self._session.execute(select(Category).where(Category.slug == slug))
            row = existing.scalar_one_or_none()
            if row is not None:
                self._slug_to_id[slug] = row.id
                if row.is_active:
                    # Do not resurrect retired nodes via seed.
                    row.is_active = False
            return

        existing = await self._session.execute(select(Category).where(Category.slug == slug))
        row = existing.scalar_one_or_none()
        # Soft-inactive Jobs nodes stay inactive (abroad + legacy vacancy/resume).
        # jobs root is not in this set.
        keep_active = slug not in JOBS_V2_INACTIVE_SECTOR_SLUGS
        if row is None:
            row = Category(
                slug=slug,
                name=name,
                entity_type=entity_type,
                sort_order=sort_order,
                parent_id=parent_id,
                is_active=keep_active,
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
            # Non-retired catalog nodes must stay/become active (FINAL home-garden etc.),
            # except Jobs soft-inactive sectors which must not be resurrected.
            row.is_active = keep_active
            row.requires_city = True
            if hint:
                row.ai_dialogue_hint = hint
        self._slug_to_id[slug] = row.id

    async def _deactivate_retired_home_garden(self) -> int:
        """Keep legacy coarse home-garden L2 inactive; disable their aliases."""
        n = 0
        for slug in sorted(RETIRED_HOME_GARDEN_LEGACY_SLUGS):
            stmt = select(Category).where(Category.slug == slug)
            row = (await self._session.execute(stmt)).scalar_one_or_none()
            if row is None:
                continue
            self._slug_to_id[slug] = row.id
            if row.is_active:
                row.is_active = False
                n += 1
                logger.info("[SeedHomeGarden] retired legacy slug=%s id=%s", slug, row.id)
            alias_rows = (
                await self._session.execute(
                    select(CategoryAlias).where(CategoryAlias.category_id == row.id)
                )
            ).scalars().all()
            for alias in alias_rows:
                if alias.is_enabled:
                    alias.is_enabled = False
        return n

    async def _deactivate_stale_home_garden_nodes(self) -> int:
        """Retire active home-garden descendants not in the FINAL TARGET catalog."""
        from app.seeds.home_garden_catalog_final import HOME_GARDEN_NODES, HOME_GARDEN_ROOT_SLUG

        target = {s for _p, s, _n, _so, _d in HOME_GARDEN_NODES}
        root_id = self._slug_to_id.get(HOME_GARDEN_ROOT_SLUG)
        if root_id is None:
            return 0

        # Load all categories under home-garden by walking parent_id.
        all_rows = (
            await self._session.execute(select(Category))
        ).scalars().all()
        by_parent: dict[int | None, list[Category]] = {}
        for row in all_rows:
            by_parent.setdefault(row.parent_id, []).append(row)

        def walk(pid: int) -> list[Category]:
            out: list[Category] = []
            for ch in by_parent.get(pid, []):
                out.append(ch)
                out.extend(walk(ch.id))
            return out

        n = 0
        for row in walk(root_id):
            if row.slug in target:
                continue
            if not row.is_active:
                continue
            row.is_active = False
            n += 1
            logger.info("[SeedHomeGarden] retired stale slug=%s id=%s", row.slug, row.id)
            alias_rows = (
                await self._session.execute(
                    select(CategoryAlias).where(CategoryAlias.category_id == row.id)
                )
            ).scalars().all()
            for alias in alias_rows:
                if alias.is_enabled:
                    alias.is_enabled = False
        return n

    async def _seed_aliases(self) -> dict[str, int]:
        id_to_slug = {cat_id: slug for slug, cat_id in self._slug_to_id.items()}
        added = 0
        updated = 0
        conflicts = 0
        # Pending INSERTs are invisible to SELECT until flush — track within this run.
        seen: dict[tuple[str, str], tuple[int, CategoryAlias | None]] = {}

        for cat_slug, aliases in CATEGORY_ALIASES.items():
            if cat_slug in _RETIRED_CATEGORY_SLUGS:
                continue
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
                    if existing_slug in _RETIRED_CATEGORY_SLUGS:
                        # Reclaim alias from retired legacy category.
                        row.category_id = cat_id
                        row.alias = alias
                        row.alias_compact = compact
                        row.weight = 100
                        row.is_enabled = True
                        seen[key] = (cat_id, row)
                        updated += 1
                    else:
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
        from app.models.job_create_intent import HIRING, JOB_SEEKING
        from app.seeds.jobs_create_fields import build_jobs_create_core_fields
        from app.seeds.jobs_seeking_fields import build_jobs_seeking_core_fields

        merged: dict = dict(CORE_FIELDS)
        # Home & Garden Package A: Create cores (incl. price/seller/contacts)
        # are seeded by `_seed_home_garden_package_a_fields` — not this merge
        # (generic merge historically skipped `price` for goods).
        # Jobs create: strip jobs-* from unscoped merge — seeded with create_intent below.
        jobs_hiring = build_jobs_create_core_fields()
        jobs_seeking = build_jobs_seeking_core_fields()

        for cat_slug, fields in merged.items():
            if cat_slug in _RETIRED_CATEGORY_SLUGS:
                continue
            if str(cat_slug).startswith("jobs-"):
                continue
            if str(cat_slug).startswith("home-garden") or cat_slug == "home-garden":
                continue
            # Bus V2 leaf/parent SoT: bus_sale_v2 overlay (not thin CORE_FIELDS).
            if cat_slug in {
                "transport-buses-microbuses-motorhomes",
                "transport-commercial-avtobusy",
                "transport-commercial-mikroavtobusy",
                "transport-buses-avtodoma",
            }:
                continue
            # Special Equipment V2 leaf/parent SoT: special_sale_v2 overlay.
            if cat_slug == "transport-special-equipment" or cat_slug.startswith(
                "transport-special-equipment-"
            ):
                continue
            # Cargo V2 leaf/parent SoT: cargo_sale_v2 overlay.
            if cat_slug == "transport-cargo" or cat_slug.startswith(
                "transport-cargo-"
            ):
                continue
            # Water V2 leaf/parent SoT: water_sale_v2 overlay.
            if cat_slug == "transport-watercraft" or cat_slug.startswith(
                "transport-watercraft-"
            ):
                continue
            # Trailers V2 leaf/parent SoT: trailer_sale_v2 overlay.
            if cat_slug == "transport-trailers" or cat_slug.startswith(
                "transport-trailers-"
            ):
                continue
            # Farm V2 leaf/parent SoT: farm_sale_v2 overlay.
            if cat_slug == "transport-farm-machinery" or cat_slug.startswith(
                "transport-farm-machinery-"
            ):
                continue
            # Rental V2 leaf/parent SoT: transport_rental_v2 overlay.
            if cat_slug == "transport-rental" or cat_slug.startswith(
                "transport-rental-"
            ):
                continue
            # Auto Parts V2 leaf/parent SoT: auto_parts_v2 overlay.
            if cat_slug == "transport-auto-parts" or cat_slug.startswith(
                "transport-auto-parts-"
            ):
                continue
            # Tires / Tuning / Auto Services V2 overlays.
            if cat_slug == "transport-tires-wheels" or cat_slug.startswith(
                "transport-tires-wheels-"
            ):
                continue
            if cat_slug == "transport-accessories-tuning" or cat_slug.startswith(
                "transport-accessories-tuning-"
            ):
                continue
            if cat_slug == "transport-auto-services" or cat_slug.startswith(
                "transport-auto-services-"
            ):
                continue
            # Picker-only parents / V2 leaf overlays (moto / electric / bicycle).
            if cat_slug in {
                "transport-moto-tech",
                "transport-electric",
                "transport-bicycles",
            } or cat_slug.startswith(
                (
                    "transport-moto-tech-",
                    "transport-electric-",
                    "transport-bicycles-",
                )
            ):
                continue
            # Services V2 Package A overlay owns services-* Create SoT.
            if cat_slug == "services" or str(cat_slug).startswith("services-"):
                continue
            # Repair V2 Package A overlay owns repair-construction-* Create SoT.
            if (
                cat_slug == "repair-construction"
                or str(cat_slug).startswith("repair-construction-")
                or cat_slug in REPAIR_V2_RETIRED_SLUGS
            ):
                continue
            # Fashion V2 Package A overlay owns fashion-* Create SoT.
            if cat_slug == "fashion" or str(cat_slug).startswith("fashion-"):
                continue
            cat_id = self._slug_to_id.get(cat_slug)
            if cat_id is None:
                continue
            for sort_i, field in enumerate(fields):
                if len(field) == 4:
                    key, label, ftype, hint = field
                    await self._upsert_core_field(
                        cat_id, key, label, ftype, sort_i, hint, required=True, options=None
                    )
                else:
                    key, label, ftype, required, options, hint = field
                    # Pinned create UI: never seed city from intelligence.
                    if key in {"city", "title", "description", "photos"}:
                        continue
                    # Goods/HG keep price outside core; jobs salary is a create field.
                    if key == "price":
                        continue
                    await self._upsert_core_field(
                        cat_id,
                        key,
                        label,
                        ftype,
                        sort_i,
                        hint,
                        required=required,
                        options=options,
                    )

        for cat_slug, fields in jobs_hiring.items():
            if cat_slug in JOBS_V2_INACTIVE_SECTOR_SLUGS:
                continue
            cat_id = self._slug_to_id.get(cat_slug)
            if cat_id is None:
                continue
            for sort_i, field in enumerate(fields):
                key, label, ftype, required, options, hint = field
                if key in {"city", "title", "description", "photos"}:
                    continue
                await self._upsert_core_field(
                    cat_id,
                    key,
                    label,
                    ftype,
                    sort_i,
                    hint,
                    required=required,
                    options=options,
                    create_intent=HIRING,
                )
        for cat_slug, fields in jobs_seeking.items():
            if cat_slug in JOBS_V2_INACTIVE_SECTOR_SLUGS:
                continue
            cat_id = self._slug_to_id.get(cat_slug)
            if cat_id is None:
                continue
            for sort_i, field in enumerate(fields):
                key, label, ftype, required, options, hint = field
                await self._upsert_core_field(
                    cat_id,
                    key,
                    label,
                    ftype,
                    sort_i,
                    hint,
                    required=required,
                    options=options,
                    create_intent=JOB_SEEKING,
                )
        await self._seed_home_garden_package_a_fields()
        await self._seed_home_garden_search_filters()
        await self._seed_car_sale_v2_fields()
        await self._seed_moto_sale_v2_fields()
        await self._seed_electric_sale_v2_fields()
        await self._seed_bicycle_sale_v2_fields()
        await self._seed_bus_sale_v2_fields()
        await self._seed_special_sale_v2_fields()
        await self._seed_cargo_sale_v2_fields()
        await self._seed_water_sale_v2_fields()
        await self._seed_trailer_sale_v2_fields()
        await self._seed_farm_sale_v2_fields()
        await self._seed_transport_rental_v2_fields()
        await self._seed_tires_wheels_v2_fields()
        await self._seed_auto_parts_v2_fields()
        await self._seed_tuning_accessories_v2_fields()
        await self._seed_auto_services_v2_fields()
        await self._seed_real_estate_v2_fields()
        await self._seed_services_v2_fields()
        await self._seed_repair_v2_fields()
        await self._seed_electronics_v2_fields()
        await self._seed_fashion_v2_fields()
        await self._seed_kids_v2_fields()
        await self._seed_food_agri_v2_fields()
        await self._seed_animals_v2_fields()
        for cat_slug, fields in OPTIONAL_FIELDS.items():
            if cat_slug in _RETIRED_CATEGORY_SLUGS:
                continue
            if cat_slug == "transport-car-sale":
                continue
            if cat_slug in {
                "transport-moto-tech-mototsikly",
                "transport-moto-tech-skutery-i-mopedy",
                "transport-moto-tech-motorollery-muravey",
                "transport-moto-tech-kvadrotsikly",
                "transport-moto-tech-baggi",
                "transport-moto-tech-tritsikly",
                "transport-moto-tech-snegohody",
                "transport-moto-tech-karty",
                "transport-moto-tech-drugaya-mototehnika",
                "transport-electric-elektrosamokaty",
                "transport-electric-elektroskutery",
                "transport-moto-tech-elektromototsikly",
                "transport-moto-tech-elektrokvadrotsikly",
                "transport-electric-giroskutery",
                "transport-electric-monokolesa",
                "transport-electric-sigvei-i-mini-sigvei",
                "transport-electric-elektricheskie-mini-mobili",
                "transport-electric-drugoy-redkiy-elektrotransport",
                "transport-bicycles-gornye-velosipedy",
                "transport-bicycles-gorodskie-velosipedy",
                "transport-bicycles-shosseynye-velosipedy",
                "transport-bicycles-podrostkovye-velosipedy",
                "transport-bicycles-elektrovelosipedy",
                "transport-bicycles-bmx",
                "transport-bicycles-drugie",
                "transport-commercial-avtobusy",
                "transport-commercial-mikroavtobusy",
                "transport-buses-avtodoma",
            }:
                continue
            if cat_slug == "transport-special-equipment" or cat_slug.startswith(
                "transport-special-equipment-"
            ):
                continue
            if cat_slug == "transport-cargo" or cat_slug.startswith(
                "transport-cargo-"
            ):
                continue
            if cat_slug == "transport-watercraft" or cat_slug.startswith(
                "transport-watercraft-"
            ):
                continue
            if cat_slug == "transport-trailers" or cat_slug.startswith(
                "transport-trailers-"
            ):
                continue
            if cat_slug == "transport-farm-machinery" or cat_slug.startswith(
                "transport-farm-machinery-"
            ):
                continue
            cat_id = self._slug_to_id.get(cat_slug)
            if cat_id is None:
                continue
            for sort_i, (key, label, ftype) in enumerate(fields):
                await self._upsert_optional_field(cat_id, key, label, ftype, sort_i)

    async def _seed_car_sale_v2_fields(self) -> None:
        """Transport → Продажа авто V2 Create + Search SoT."""
        from app.seeds.car_sale_v2 import (
            CAR_SALE_CORE_FIELDS,
            CAR_SALE_SEARCH_FILTERS,
            CAR_SALE_SLUG,
        )

        cat_id = self._slug_to_id.get(CAR_SALE_SLUG)
        if cat_id is None:
            return

        wanted_keys = {row[0] for row in CAR_SALE_CORE_FIELDS}
        existing_core = (
            await self._session.execute(
                select(CategoryCoreField).where(
                    CategoryCoreField.category_id == cat_id,
                    CategoryCoreField.create_intent.is_(None),
                )
            )
        ).scalars().all()
        for row in existing_core:
            if row.field_key not in wanted_keys:
                await self._session.delete(row)

        existing_opt = (
            await self._session.execute(
                select(CategoryOptionalField).where(
                    CategoryOptionalField.category_id == cat_id
                )
            )
        ).scalars().all()
        for row in existing_opt:
            await self._session.delete(row)

        for sort_i, (key, label, ftype, required, sort, options, hint) in enumerate(
            CAR_SALE_CORE_FIELDS
        ):
            # Keep region/city in schema for requiredness + Edit hydrate;
            # Flutter pins them visually and skips duplicate render.
            await self._upsert_core_field(
                cat_id,
                key,
                label,
                ftype,
                sort if sort is not None else sort_i,
                hint,
                required=required,
                options=options,
            )

        wanted_filters = {row[0] for row in CAR_SALE_SEARCH_FILTERS}
        existing_filters = (
            await self._session.execute(
                select(CategoryFilter).where(CategoryFilter.category_id == cat_id)
            )
        ).scalars().all()
        for row in existing_filters:
            if row.filter_key not in wanted_filters:
                await self._session.delete(row)

        for sort_i, (key, label, ftype, sort, config) in enumerate(
            CAR_SALE_SEARCH_FILTERS
        ):
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
                        sort_order=sort if sort is not None else sort_i,
                        config=config,
                    )
                )
            else:
                row.label = label
                row.filter_type = ftype
                row.sort_order = sort if sort is not None else sort_i
                row.config = config

    async def _seed_moto_sale_v2_fields(self) -> None:
        """Transport → Мототехника V2 Create + Search SoT (per active leaf)."""
        from app.seeds.moto_sale_v2 import (
            MOTO_CORE_FIELDS_BY_SLUG,
            MOTO_INACTIVE_LEGACY_SLUGS,
            MOTO_LEAF_LABELS,
            MOTO_PARENT_SLUG,
            MOTO_SEARCH_FILTERS_BY_SLUG,
        )

        await self._clear_picker_parent_live_sot(self._slug_to_id.get(MOTO_PARENT_SLUG))

        for slug, label in MOTO_LEAF_LABELS.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            row = (
                await self._session.execute(
                    select(Category).where(Category.id == cat_id)
                )
            ).scalar_one_or_none()
            if row is not None and row.name != label:
                row.name = label

        for slug in MOTO_INACTIVE_LEGACY_SLUGS:
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            row = (
                await self._session.execute(
                    select(Category).where(Category.id == cat_id)
                )
            ).scalar_one_or_none()
            if row is not None and row.is_active:
                row.is_active = False

        for slug, fields in MOTO_CORE_FIELDS_BY_SLUG.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue

            wanted_keys = {row[0] for row in fields}
            existing_core = (
                await self._session.execute(
                    select(CategoryCoreField).where(
                        CategoryCoreField.category_id == cat_id,
                        CategoryCoreField.create_intent.is_(None),
                    )
                )
            ).scalars().all()
            for row in existing_core:
                if row.field_key not in wanted_keys:
                    await self._session.delete(row)

            existing_opt = (
                await self._session.execute(
                    select(CategoryOptionalField).where(
                        CategoryOptionalField.category_id == cat_id
                    )
                )
            ).scalars().all()
            for row in existing_opt:
                await self._session.delete(row)

            for sort_i, (key, label, ftype, required, sort, options, hint) in enumerate(
                fields
            ):
                await self._upsert_core_field(
                    cat_id,
                    key,
                    label,
                    ftype,
                    sort if sort is not None else sort_i,
                    hint,
                    required=required,
                    options=options,
                )

            filters = MOTO_SEARCH_FILTERS_BY_SLUG[slug]
            wanted_filters = {row[0] for row in filters}
            existing_filters = (
                await self._session.execute(
                    select(CategoryFilter).where(CategoryFilter.category_id == cat_id)
                )
            ).scalars().all()
            for row in existing_filters:
                if row.filter_key not in wanted_filters:
                    await self._session.delete(row)

            for sort_i, (key, label, ftype, sort, config) in enumerate(filters):
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
                            sort_order=sort if sort is not None else sort_i,
                            config=config,
                        )
                    )
                else:
                    row.label = label
                    row.filter_type = ftype
                    row.sort_order = sort if sort is not None else sort_i
                    row.config = config

    async def _seed_electric_sale_v2_fields(self) -> None:
        """Transport → Электротранспорт V2 Create + Search SoT (per active leaf)."""
        from app.seeds.electric_sale_v2 import (
            ELECTRIC_CORE_FIELDS_BY_SLUG,
            ELECTRIC_INACTIVE_LEGACY_SLUGS,
            ELECTRIC_LEAF_LABELS,
            ELECTRIC_LEAF_SORT,
            ELECTRIC_PARENT_SLUG,
            ELECTRIC_SEARCH_FILTERS_BY_SLUG,
        )

        parent_id = self._slug_to_id.get(ELECTRIC_PARENT_SLUG)
        if parent_id is None:
            return

        await self._clear_picker_parent_live_sot(parent_id)

        for slug, label in ELECTRIC_LEAF_LABELS.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            row = (
                await self._session.execute(
                    select(Category).where(Category.id == cat_id)
                )
            ).scalar_one_or_none()
            if row is None:
                continue
            row.name = label
            row.parent_id = parent_id
            row.is_active = True
            sort = ELECTRIC_LEAF_SORT.get(slug)
            if sort is not None:
                row.sort_order = sort

        for slug in ELECTRIC_INACTIVE_LEGACY_SLUGS:
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            row = (
                await self._session.execute(
                    select(Category).where(Category.id == cat_id)
                )
            ).scalar_one_or_none()
            if row is not None and row.is_active:
                row.is_active = False

        for slug, fields in ELECTRIC_CORE_FIELDS_BY_SLUG.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue

            wanted_keys = {row[0] for row in fields}
            existing_core = (
                await self._session.execute(
                    select(CategoryCoreField).where(
                        CategoryCoreField.category_id == cat_id,
                        CategoryCoreField.create_intent.is_(None),
                    )
                )
            ).scalars().all()
            for row in existing_core:
                if row.field_key not in wanted_keys:
                    await self._session.delete(row)

            existing_opt = (
                await self._session.execute(
                    select(CategoryOptionalField).where(
                        CategoryOptionalField.category_id == cat_id
                    )
                )
            ).scalars().all()
            for row in existing_opt:
                await self._session.delete(row)

            for sort_i, (key, label, ftype, required, sort, options, hint) in enumerate(
                fields
            ):
                await self._upsert_core_field(
                    cat_id,
                    key,
                    label,
                    ftype,
                    sort if sort is not None else sort_i,
                    hint,
                    required=required,
                    options=options,
                )

            filters = ELECTRIC_SEARCH_FILTERS_BY_SLUG[slug]
            wanted_filters = {row[0] for row in filters}
            existing_filters = (
                await self._session.execute(
                    select(CategoryFilter).where(CategoryFilter.category_id == cat_id)
                )
            ).scalars().all()
            for row in existing_filters:
                if row.filter_key not in wanted_filters:
                    await self._session.delete(row)

            for sort_i, (key, label, ftype, sort, config) in enumerate(filters):
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
                            sort_order=sort if sort is not None else sort_i,
                            config=config,
                        )
                    )
                else:
                    row.label = label
                    row.filter_type = ftype
                    row.sort_order = sort if sort is not None else sort_i
                    row.config = config

    async def _seed_bicycle_sale_v2_fields(self) -> None:
        """Transport → Велосипеды V2 Create + Search SoT (per active leaf)."""
        from app.seeds.bicycle_sale_v2 import (
            BICYCLE_CORE_FIELDS_BY_SLUG,
            BICYCLE_FAKE_BRAND_SLUGS,
            BICYCLE_INACTIVE_LEGACY_SLUGS,
            BICYCLE_LEAF_LABELS,
            BICYCLE_LEAF_SORT,
            BICYCLE_PARENT_SLUG,
            BICYCLE_SEARCH_FILTERS_BY_SLUG,
        )
        from app.models.vehicle import VehicleBrand, VehicleModel

        parent_id = self._slug_to_id.get(BICYCLE_PARENT_SLUG)
        if parent_id is None:
            return

        await self._clear_picker_parent_live_sot(parent_id)

        for slug, label in BICYCLE_LEAF_LABELS.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            row = (
                await self._session.execute(
                    select(Category).where(Category.id == cat_id)
                )
            ).scalar_one_or_none()
            if row is None:
                continue
            row.name = label
            row.parent_id = parent_id
            row.is_active = True
            sort = BICYCLE_LEAF_SORT.get(slug)
            if sort is not None:
                row.sort_order = sort

        for slug in BICYCLE_INACTIVE_LEGACY_SLUGS:
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            row = (
                await self._session.execute(
                    select(Category).where(Category.id == cat_id)
                )
            ).scalar_one_or_none()
            if row is not None and row.is_active:
                row.is_active = False

        for slug, fields in BICYCLE_CORE_FIELDS_BY_SLUG.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue

            wanted_keys = {row[0] for row in fields}
            existing_core = (
                await self._session.execute(
                    select(CategoryCoreField).where(
                        CategoryCoreField.category_id == cat_id,
                        CategoryCoreField.create_intent.is_(None),
                    )
                )
            ).scalars().all()
            for row in existing_core:
                if row.field_key not in wanted_keys:
                    await self._session.delete(row)

            existing_opt = (
                await self._session.execute(
                    select(CategoryOptionalField).where(
                        CategoryOptionalField.category_id == cat_id
                    )
                )
            ).scalars().all()
            for row in existing_opt:
                await self._session.delete(row)

            for sort_i, (key, label, ftype, required, sort, options, hint) in enumerate(
                fields
            ):
                await self._upsert_core_field(
                    cat_id,
                    key,
                    label,
                    ftype,
                    sort if sort is not None else sort_i,
                    hint,
                    required=required,
                    options=options,
                )

            filters = BICYCLE_SEARCH_FILTERS_BY_SLUG[slug]
            wanted_filters = {row[0] for row in filters}
            existing_filters = (
                await self._session.execute(
                    select(CategoryFilter).where(CategoryFilter.category_id == cat_id)
                )
            ).scalars().all()
            for row in existing_filters:
                if row.filter_key not in wanted_filters:
                    await self._session.delete(row)

            for sort_i, (key, label, ftype, sort, config) in enumerate(filters):
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
                            sort_order=sort if sort is not None else sort_i,
                            config=config,
                        )
                    )
                else:
                    row.label = label
                    row.filter_type = ftype
                    row.sort_order = sort if sort is not None else sort_i
                    row.config = config

        for fake_slug in BICYCLE_FAKE_BRAND_SLUGS:
            brand = (
                await self._session.execute(
                    select(VehicleBrand).where(VehicleBrand.slug == fake_slug)
                )
            ).scalar_one_or_none()
            if brand is None:
                continue
            brand.is_enabled = False
            models = (
                await self._session.execute(
                    select(VehicleModel).where(VehicleModel.brand_id == brand.id)
                )
            ).scalars().all()
            for model in models:
                model.is_enabled = False

    async def _seed_bus_sale_v2_fields(self) -> None:
        """Transport → Buses/Minibus/Motorhome V2 Create + Search SoT."""
        from app.seeds.bus_sale_v2 import (
            BUS_CORE_FIELDS_BY_SLUG,
            BUS_LEAF_LABELS,
            BUS_LEAF_SORT,
            BUS_PARENT_SLUG,
            BUS_SEARCH_FILTERS_BY_SLUG,
            MICROBUS_CARGO_MODEL_KEYS,
        )
        from app.models.vehicle import VehicleBrand, VehicleModel

        parent_id = self._slug_to_id.get(BUS_PARENT_SLUG)
        if parent_id is None:
            return

        await self._clear_picker_parent_live_sot(parent_id)

        for slug, label in BUS_LEAF_LABELS.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            row = (
                await self._session.execute(
                    select(Category).where(Category.id == cat_id)
                )
            ).scalar_one_or_none()
            if row is None:
                continue
            row.name = label
            row.parent_id = parent_id
            row.is_active = True
            sort = BUS_LEAF_SORT.get(slug)
            if sort is not None:
                row.sort_order = sort

        commercial = self._slug_to_id.get("transport-commercial")
        if commercial is not None:
            crow = (
                await self._session.execute(
                    select(Category).where(Category.id == commercial)
                )
            ).scalar_one_or_none()
            if crow is not None and crow.is_active:
                crow.is_active = False

        for slug, fields in BUS_CORE_FIELDS_BY_SLUG.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue

            wanted_keys = {row[0] for row in fields}
            existing_core = (
                await self._session.execute(
                    select(CategoryCoreField).where(
                        CategoryCoreField.category_id == cat_id,
                        CategoryCoreField.create_intent.is_(None),
                    )
                )
            ).scalars().all()
            for row in existing_core:
                if row.field_key not in wanted_keys:
                    await self._session.delete(row)

            existing_opt = (
                await self._session.execute(
                    select(CategoryOptionalField).where(
                        CategoryOptionalField.category_id == cat_id
                    )
                )
            ).scalars().all()
            for row in existing_opt:
                await self._session.delete(row)

            for sort_i, (key, label, ftype, required, sort, options, hint) in enumerate(
                fields
            ):
                await self._upsert_core_field(
                    cat_id,
                    key,
                    label,
                    ftype,
                    sort if sort is not None else sort_i,
                    hint,
                    required=required,
                    options=options,
                )

            filters = BUS_SEARCH_FILTERS_BY_SLUG[slug]
            wanted_filters = {row[0] for row in filters}
            existing_filters = (
                await self._session.execute(
                    select(CategoryFilter).where(CategoryFilter.category_id == cat_id)
                )
            ).scalars().all()
            for row in existing_filters:
                if row.filter_key not in wanted_filters:
                    await self._session.delete(row)

            for sort_i, (key, label, ftype, sort, config) in enumerate(filters):
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
                            sort_order=sort if sort is not None else sort_i,
                            config=config,
                        )
                    )
                else:
                    row.label = label
                    row.filter_type = ftype
                    row.sort_order = sort if sort is not None else sort_i
                    row.config = config

        for brand_slug, model_slug in MICROBUS_CARGO_MODEL_KEYS:
            brand = (
                await self._session.execute(
                    select(VehicleBrand).where(VehicleBrand.slug == brand_slug)
                )
            ).scalar_one_or_none()
            if brand is None:
                continue
            model = (
                await self._session.execute(
                    select(VehicleModel).where(
                        VehicleModel.brand_id == brand.id,
                        VehicleModel.slug == model_slug,
                    )
                )
            ).scalar_one_or_none()
            if model is not None:
                model.is_enabled = False

    async def _seed_special_sale_v2_fields(self) -> None:
        """Transport → Спецтехника V2 Create + Search SoT."""
        from app.seeds.special_sale_v2 import (
            EVACUATOR_SALE_ALIASES,
            MANIPULATOR_CHASSIS_BRANDS,
            MANIPULATOR_CHASSIS_MODELS,
            MANIPULATOR_CRANE_OEM_BRAND_SLUGS,
            SPECIAL_CORE_FIELDS_BY_SLUG,
            SPECIAL_INACTIVE_LEGACY_SLUGS,
            SPECIAL_LEAF_ALIASES,
            SPECIAL_LEAF_LABELS,
            SPECIAL_LEAF_SORT,
            SPECIAL_PARENT_SLUG,
            SPECIAL_SEARCH_FILTERS_BY_SLUG,
            special_other_brands,
            special_other_models,
        )
        from app.models.vehicle import VehicleBrand, VehicleModel

        parent_id = self._slug_to_id.get(SPECIAL_PARENT_SLUG)
        if parent_id is None:
            return

        await self._clear_picker_parent_live_sot(parent_id)

        for slug, label in SPECIAL_LEAF_LABELS.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            row = (
                await self._session.execute(
                    select(Category).where(Category.id == cat_id)
                )
            ).scalar_one_or_none()
            if row is None:
                continue
            row.name = label
            row.parent_id = parent_id
            row.is_active = True
            sort = SPECIAL_LEAF_SORT.get(slug)
            if sort is not None:
                row.sort_order = sort

        for slug in SPECIAL_INACTIVE_LEGACY_SLUGS:
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            row = (
                await self._session.execute(
                    select(Category).where(Category.id == cat_id)
                )
            ).scalar_one_or_none()
            if row is not None and row.is_active:
                row.is_active = False

        async def _upsert_alias(alias: str, target_slug: str, *, weight: int = 100) -> None:
            target_id = self._slug_to_id.get(target_slug)
            if target_id is None:
                return
            existing = (
                await self._session.execute(
                    select(CategoryAlias).where(
                        CategoryAlias.alias_normalized == alias,
                        CategoryAlias.locale == self._locale,
                    )
                )
            ).scalar_one_or_none()
            if existing is None:
                self._session.add(
                    CategoryAlias(
                        category_id=target_id,
                        alias=alias,
                        alias_normalized=alias,
                        alias_compact=alias.replace(" ", ""),
                        locale=self._locale,
                        weight=weight,
                        is_enabled=True,
                    )
                )
            else:
                existing.category_id = target_id
                existing.alias = alias
                existing.is_enabled = True
                existing.weight = weight

        for alias, leaf_slug in SPECIAL_LEAF_ALIASES.items():
            await _upsert_alias(alias, leaf_slug)
        for alias, leaf_slug in EVACUATOR_SALE_ALIASES.items():
            await _upsert_alias(alias, leaf_slug, weight=120)

        for slug, fields in SPECIAL_CORE_FIELDS_BY_SLUG.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue

            wanted_keys = {row[0] for row in fields}
            existing_core = (
                await self._session.execute(
                    select(CategoryCoreField).where(
                        CategoryCoreField.category_id == cat_id,
                        CategoryCoreField.create_intent.is_(None),
                    )
                )
            ).scalars().all()
            for row in existing_core:
                if row.field_key not in wanted_keys:
                    await self._session.delete(row)

            existing_opt = (
                await self._session.execute(
                    select(CategoryOptionalField).where(
                        CategoryOptionalField.category_id == cat_id
                    )
                )
            ).scalars().all()
            for row in existing_opt:
                await self._session.delete(row)

            for sort_i, (key, label, ftype, required, sort, options, hint) in enumerate(
                fields
            ):
                await self._upsert_core_field(
                    cat_id,
                    key,
                    label,
                    ftype,
                    sort if sort is not None else sort_i,
                    hint,
                    required=required,
                    options=options,
                )

            filters = SPECIAL_SEARCH_FILTERS_BY_SLUG[slug]
            wanted_filters = {row[0] for row in filters}
            existing_filters = (
                await self._session.execute(
                    select(CategoryFilter).where(CategoryFilter.category_id == cat_id)
                )
            ).scalars().all()
            for row in existing_filters:
                if row.filter_key not in wanted_filters:
                    await self._session.delete(row)

            for sort_i, (key, label, ftype, sort, config) in enumerate(filters):
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
                            sort_order=sort if sort is not None else sort_i,
                            config=config,
                        )
                    )
                else:
                    row.label = label
                    row.filter_type = ftype
                    row.sort_order = sort if sort is not None else sort_i
                    row.config = config

        for brand_slug in MANIPULATOR_CRANE_OEM_BRAND_SLUGS:
            brand = (
                await self._session.execute(
                    select(VehicleBrand).where(VehicleBrand.slug == brand_slug)
                )
            ).scalar_one_or_none()
            if brand is not None:
                brand.is_enabled = False

        async def _upsert_typed_brand(
            slug: str, name: str, country: str | None, vtype
        ) -> VehicleBrand | None:
            from app.models.category_enums import VehicleType

            vt = vtype if isinstance(vtype, VehicleType) else VehicleType(vtype)
            brand = (
                await self._session.execute(
                    select(VehicleBrand).where(VehicleBrand.slug == slug)
                )
            ).scalar_one_or_none()
            if brand is None:
                brand = VehicleBrand(
                    slug=slug,
                    name=name,
                    country_origin=country,
                    vehicle_type=vt,
                    is_enabled=True,
                )
                self._session.add(brand)
                await self._session.flush()
            else:
                brand.name = name
                brand.country_origin = country
                brand.vehicle_type = vt
                brand.is_enabled = True
            return brand

        for slug, name, country, vtype in MANIPULATOR_CHASSIS_BRANDS:
            await _upsert_typed_brand(slug, name, country, vtype)
        for slug, name, country, vtype_str in special_other_brands():
            await _upsert_typed_brand(slug, name, country, vtype_str)

        model_maps = {**MANIPULATOR_CHASSIS_MODELS, **special_other_models()}
        for brand_slug, models in model_maps.items():
            brand = (
                await self._session.execute(
                    select(VehicleBrand).where(VehicleBrand.slug == brand_slug)
                )
            ).scalar_one_or_none()
            if brand is None:
                continue
            for model_slug, model_name in models:
                model = (
                    await self._session.execute(
                        select(VehicleModel).where(
                            VehicleModel.brand_id == brand.id,
                            VehicleModel.slug == model_slug,
                        )
                    )
                ).scalar_one_or_none()
                if model is None:
                    self._session.add(
                        VehicleModel(
                            brand_id=brand.id,
                            slug=model_slug,
                            name=model_name,
                            is_enabled=True,
                        )
                    )
                else:
                    model.name = model_name
                    model.is_enabled = True

    async def _seed_cargo_sale_v2_fields(self) -> None:
        """Transport → Грузовой транспорт V2 Create + Search SoT."""
        from app.seeds.cargo_sale_v2 import (
            CARGO_CORE_FIELDS_BY_SLUG,
            CARGO_INACTIVE_LEGACY_SLUGS,
            CARGO_LEAF_ALIASES,
            CARGO_LEAF_LABELS,
            CARGO_LEAF_SORT,
            CARGO_PARENT_ALIASES,
            CARGO_PARENT_SLUG,
            CARGO_SEARCH_FILTERS_BY_SLUG,
            EVACUATOR_SALE_ALIASES,
            cargo_other_brands,
            cargo_other_models,
        )
        from app.models.vehicle import VehicleBrand, VehicleModel

        parent_id = self._slug_to_id.get(CARGO_PARENT_SLUG)
        if parent_id is None:
            return

        for slug, label in CARGO_LEAF_LABELS.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            row = (
                await self._session.execute(
                    select(Category).where(Category.id == cat_id)
                )
            ).scalar_one_or_none()
            if row is None:
                continue
            row.name = label
            row.parent_id = parent_id
            row.is_active = True
            sort = CARGO_LEAF_SORT.get(slug)
            if sort is not None:
                row.sort_order = sort

        for slug in CARGO_INACTIVE_LEGACY_SLUGS:
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            row = (
                await self._session.execute(
                    select(Category).where(Category.id == cat_id)
                )
            ).scalar_one_or_none()
            if row is not None and row.is_active:
                row.is_active = False

        # Parent picker-only: no live Create/Search SoT.
        for model_cls in (CategoryCoreField, CategoryOptionalField, CategoryFilter):
            existing_parent = (
                await self._session.execute(
                    select(model_cls).where(model_cls.category_id == parent_id)
                )
            ).scalars().all()
            for row in existing_parent:
                await self._session.delete(row)

        async def _upsert_alias(alias: str, target_slug: str, *, weight: int = 100) -> None:
            target_id = self._slug_to_id.get(target_slug)
            if target_id is None:
                return
            existing = (
                await self._session.execute(
                    select(CategoryAlias).where(
                        CategoryAlias.alias_normalized == alias,
                        CategoryAlias.locale == self._locale,
                    )
                )
            ).scalar_one_or_none()
            if existing is None:
                self._session.add(
                    CategoryAlias(
                        category_id=target_id,
                        alias=alias,
                        alias_normalized=alias,
                        alias_compact=alias.replace(" ", ""),
                        locale=self._locale,
                        weight=weight,
                        is_enabled=True,
                    )
                )
            else:
                existing.category_id = target_id
                existing.alias = alias
                existing.is_enabled = True
                existing.weight = weight

        for alias, leaf_slug in CARGO_LEAF_ALIASES.items():
            await _upsert_alias(alias, leaf_slug)
        for alias, leaf_slug in EVACUATOR_SALE_ALIASES.items():
            await _upsert_alias(alias, leaf_slug, weight=120)
        for alias, parent_slug in CARGO_PARENT_ALIASES.items():
            await _upsert_alias(alias, parent_slug, weight=80)

        for slug, fields in CARGO_CORE_FIELDS_BY_SLUG.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue

            wanted_keys = {row[0] for row in fields}
            existing_core = (
                await self._session.execute(
                    select(CategoryCoreField).where(
                        CategoryCoreField.category_id == cat_id,
                        CategoryCoreField.create_intent.is_(None),
                    )
                )
            ).scalars().all()
            for row in existing_core:
                if row.field_key not in wanted_keys:
                    await self._session.delete(row)

            existing_opt = (
                await self._session.execute(
                    select(CategoryOptionalField).where(
                        CategoryOptionalField.category_id == cat_id
                    )
                )
            ).scalars().all()
            for row in existing_opt:
                await self._session.delete(row)

            for sort_i, (key, label, ftype, required, sort, options, hint) in enumerate(
                fields
            ):
                await self._upsert_core_field(
                    cat_id,
                    key,
                    label,
                    ftype,
                    sort if sort is not None else sort_i,
                    hint,
                    required=required,
                    options=options,
                )

            filters = CARGO_SEARCH_FILTERS_BY_SLUG[slug]
            wanted_filters = {row[0] for row in filters}
            existing_filters = (
                await self._session.execute(
                    select(CategoryFilter).where(CategoryFilter.category_id == cat_id)
                )
            ).scalars().all()
            for row in existing_filters:
                if row.filter_key not in wanted_filters:
                    await self._session.delete(row)

            for sort_i, (key, label, ftype, sort, config) in enumerate(filters):
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
                            sort_order=sort if sort is not None else sort_i,
                            config=config,
                        )
                    )
                else:
                    row.label = label
                    row.filter_type = ftype
                    row.sort_order = sort if sort is not None else sort_i
                    row.config = config

        async def _upsert_typed_brand(
            slug: str, name: str, country: str | None, vtype
        ) -> VehicleBrand | None:
            from app.models.category_enums import VehicleType

            vt = vtype if isinstance(vtype, VehicleType) else VehicleType(vtype)
            brand = (
                await self._session.execute(
                    select(VehicleBrand).where(VehicleBrand.slug == slug)
                )
            ).scalar_one_or_none()
            if brand is None:
                brand = VehicleBrand(
                    slug=slug,
                    name=name,
                    country_origin=country,
                    vehicle_type=vt,
                    is_enabled=True,
                )
                self._session.add(brand)
                await self._session.flush()
            else:
                brand.name = name
                brand.country_origin = country
                brand.vehicle_type = vt
                brand.is_enabled = True
            return brand

        for slug, name, country, vtype_str in cargo_other_brands():
            await _upsert_typed_brand(slug, name, country, vtype_str)

        for brand_slug, models in cargo_other_models().items():
            brand = (
                await self._session.execute(
                    select(VehicleBrand).where(VehicleBrand.slug == brand_slug)
                )
            ).scalar_one_or_none()
            if brand is None:
                continue
            for model_slug, model_name in models:
                model = (
                    await self._session.execute(
                        select(VehicleModel).where(
                            VehicleModel.brand_id == brand.id,
                            VehicleModel.slug == model_slug,
                        )
                    )
                ).scalar_one_or_none()
                if model is None:
                    self._session.add(
                        VehicleModel(
                            brand_id=brand.id,
                            slug=model_slug,
                            name=model_name,
                            is_enabled=True,
                        )
                    )
                else:
                    model.name = model_name
                    model.is_enabled = True

    async def _seed_water_sale_v2_fields(self) -> None:
        """Transport → Водный транспорт V2 Create + Search SoT."""
        from app.seeds.water_sale_v2 import (
            WATER_CORE_FIELDS_BY_SLUG,
            WATER_INACTIVE_LEGACY_SLUGS,
            WATER_LEAF_ALIASES,
            WATER_LEAF_LABELS,
            WATER_LEAF_SORT,
            WATER_PARENT_ALIASES,
            WATER_PARENT_SLUG,
            WATER_SEARCH_FILTERS_BY_SLUG,
            water_other_brands,
            water_other_models,
        )
        from app.models.vehicle import VehicleBrand, VehicleModel

        parent_id = self._slug_to_id.get(WATER_PARENT_SLUG)
        if parent_id is None:
            return

        for slug, label in WATER_LEAF_LABELS.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            row = (
                await self._session.execute(
                    select(Category).where(Category.id == cat_id)
                )
            ).scalar_one_or_none()
            if row is None:
                continue
            row.name = label
            row.parent_id = parent_id
            row.is_active = True
            sort = WATER_LEAF_SORT.get(slug)
            if sort is not None:
                row.sort_order = sort

        for slug in WATER_INACTIVE_LEGACY_SLUGS:
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            row = (
                await self._session.execute(
                    select(Category).where(Category.id == cat_id)
                )
            ).scalar_one_or_none()
            if row is not None and row.is_active:
                row.is_active = False

        for model_cls in (CategoryCoreField, CategoryOptionalField, CategoryFilter):
            existing_parent = (
                await self._session.execute(
                    select(model_cls).where(model_cls.category_id == parent_id)
                )
            ).scalars().all()
            for row in existing_parent:
                await self._session.delete(row)

        async def _upsert_alias(alias: str, target_slug: str, *, weight: int = 100) -> None:
            target_id = self._slug_to_id.get(target_slug)
            if target_id is None:
                return
            existing = (
                await self._session.execute(
                    select(CategoryAlias).where(
                        CategoryAlias.alias_normalized == alias,
                        CategoryAlias.locale == self._locale,
                    )
                )
            ).scalar_one_or_none()
            if existing is None:
                self._session.add(
                    CategoryAlias(
                        category_id=target_id,
                        alias=alias,
                        alias_normalized=alias,
                        alias_compact=alias.replace(" ", ""),
                        locale=self._locale,
                        weight=weight,
                        is_enabled=True,
                    )
                )
            else:
                existing.category_id = target_id
                existing.alias = alias
                existing.is_enabled = True
                existing.weight = weight

        for alias, leaf_slug in WATER_LEAF_ALIASES.items():
            await _upsert_alias(alias, leaf_slug)
        for alias, parent_slug in WATER_PARENT_ALIASES.items():
            await _upsert_alias(alias, parent_slug, weight=80)

        for slug, fields in WATER_CORE_FIELDS_BY_SLUG.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue

            wanted_keys = {row[0] for row in fields}
            existing_core = (
                await self._session.execute(
                    select(CategoryCoreField).where(
                        CategoryCoreField.category_id == cat_id,
                        CategoryCoreField.create_intent.is_(None),
                    )
                )
            ).scalars().all()
            for row in existing_core:
                if row.field_key not in wanted_keys:
                    await self._session.delete(row)

            existing_opt = (
                await self._session.execute(
                    select(CategoryOptionalField).where(
                        CategoryOptionalField.category_id == cat_id
                    )
                )
            ).scalars().all()
            for row in existing_opt:
                await self._session.delete(row)

            for sort_i, (key, label, ftype, required, sort, options, hint) in enumerate(
                fields
            ):
                await self._upsert_core_field(
                    cat_id,
                    key,
                    label,
                    ftype,
                    sort if sort is not None else sort_i,
                    hint,
                    required=required,
                    options=options,
                )

            filters = WATER_SEARCH_FILTERS_BY_SLUG[slug]
            wanted_filters = {row[0] for row in filters}
            existing_filters = (
                await self._session.execute(
                    select(CategoryFilter).where(CategoryFilter.category_id == cat_id)
                )
            ).scalars().all()
            for row in existing_filters:
                if row.filter_key not in wanted_filters:
                    await self._session.delete(row)

            for sort_i, (key, label, ftype, sort, config) in enumerate(filters):
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
                            sort_order=sort if sort is not None else sort_i,
                            config=config,
                        )
                    )
                else:
                    row.label = label
                    row.filter_type = ftype
                    row.sort_order = sort if sort is not None else sort_i
                    row.config = config

        async def _upsert_typed_brand(
            slug: str, name: str, country: str | None, vtype
        ) -> VehicleBrand | None:
            from app.models.category_enums import VehicleType

            vt = vtype if isinstance(vtype, VehicleType) else VehicleType(vtype)
            brand = (
                await self._session.execute(
                    select(VehicleBrand).where(VehicleBrand.slug == slug)
                )
            ).scalar_one_or_none()
            if brand is None:
                brand = VehicleBrand(
                    slug=slug,
                    name=name,
                    country_origin=country,
                    vehicle_type=vt,
                    is_enabled=True,
                )
                self._session.add(brand)
                await self._session.flush()
            else:
                brand.name = name
                brand.country_origin = country
                brand.vehicle_type = vt
                brand.is_enabled = True
            return brand

        for slug, name, country, vtype in BOAT_MOTOR_BRANDS:
            await _upsert_typed_brand(slug, name, country, vtype)

        for brand_slug, models in BOAT_MOTOR_MODELS.items():
            brand = (
                await self._session.execute(
                    select(VehicleBrand).where(VehicleBrand.slug == brand_slug)
                )
            ).scalar_one_or_none()
            if brand is None:
                continue
            for model_slug, model_name in models:
                model = (
                    await self._session.execute(
                        select(VehicleModel).where(
                            VehicleModel.brand_id == brand.id,
                            VehicleModel.slug == model_slug,
                        )
                    )
                ).scalar_one_or_none()
                if model is None:
                    self._session.add(
                        VehicleModel(
                            brand_id=brand.id,
                            slug=model_slug,
                            name=model_name,
                            is_enabled=True,
                        )
                    )
                else:
                    model.name = model_name
                    model.is_enabled = True

        for slug, name, country, vtype_str in water_other_brands():
            await _upsert_typed_brand(slug, name, country, vtype_str)

        for brand_slug, models in water_other_models().items():
            brand = (
                await self._session.execute(
                    select(VehicleBrand).where(VehicleBrand.slug == brand_slug)
                )
            ).scalar_one_or_none()
            if brand is None:
                continue
            for model_slug, model_name in models:
                model = (
                    await self._session.execute(
                        select(VehicleModel).where(
                            VehicleModel.brand_id == brand.id,
                            VehicleModel.slug == model_slug,
                        )
                    )
                ).scalar_one_or_none()
                if model is None:
                    self._session.add(
                        VehicleModel(
                            brand_id=brand.id,
                            slug=model_slug,
                            name=model_name,
                            is_enabled=True,
                        )
                    )
                else:
                    model.name = model_name
                    model.is_enabled = True

        for bad_slug in (
            *JET_SKI_DISABLE_BRAND_SLUGS,
            *OTHER_WATERCRAFT_DISABLE_BRAND_SLUGS,
        ):
            brand = (
                await self._session.execute(
                    select(VehicleBrand).where(VehicleBrand.slug == bad_slug)
                )
            ).scalar_one_or_none()
            if brand is not None:
                brand.is_enabled = False

    async def _seed_trailer_sale_v2_fields(self) -> None:
        """Transport → Прицепы и полуприцепы V2 Create + Search SoT."""
        from app.seeds.trailer_sale_v2 import (
            TRAILER_CORE_FIELDS_BY_SLUG,
            TRAILER_INACTIVE_LEGACY_SLUGS,
            TRAILER_LEAF_ALIASES,
            TRAILER_LEAF_LABELS,
            TRAILER_LEAF_SORT,
            TRAILER_PARENT_ALIASES,
            TRAILER_PARENT_SLUG,
            TRAILER_SEARCH_FILTERS_BY_SLUG,
            trailer_other_brands,
            trailer_other_models,
        )
        from app.models.vehicle import VehicleBrand, VehicleModel

        parent_id = self._slug_to_id.get(TRAILER_PARENT_SLUG)
        if parent_id is None:
            return

        for slug, label in TRAILER_LEAF_LABELS.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            row = (
                await self._session.execute(
                    select(Category).where(Category.id == cat_id)
                )
            ).scalar_one_or_none()
            if row is None:
                continue
            row.name = label
            row.parent_id = parent_id
            row.is_active = True
            sort = TRAILER_LEAF_SORT.get(slug)
            if sort is not None:
                row.sort_order = sort

        for slug in TRAILER_INACTIVE_LEGACY_SLUGS:
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            row = (
                await self._session.execute(
                    select(Category).where(Category.id == cat_id)
                )
            ).scalar_one_or_none()
            if row is not None and row.is_active:
                row.is_active = False

        for model_cls in (CategoryCoreField, CategoryOptionalField, CategoryFilter):
            existing_parent = (
                await self._session.execute(
                    select(model_cls).where(model_cls.category_id == parent_id)
                )
            ).scalars().all()
            for row in existing_parent:
                await self._session.delete(row)

        async def _upsert_alias(alias: str, target_slug: str, *, weight: int = 100) -> None:
            target_id = self._slug_to_id.get(target_slug)
            if target_id is None:
                return
            existing = (
                await self._session.execute(
                    select(CategoryAlias).where(
                        CategoryAlias.alias_normalized == alias,
                        CategoryAlias.locale == self._locale,
                    )
                )
            ).scalar_one_or_none()
            if existing is None:
                self._session.add(
                    CategoryAlias(
                        category_id=target_id,
                        alias=alias,
                        alias_normalized=alias,
                        alias_compact=alias.replace(" ", ""),
                        locale=self._locale,
                        weight=weight,
                        is_enabled=True,
                    )
                )
            else:
                existing.category_id = target_id
                existing.alias = alias
                existing.is_enabled = True
                existing.weight = weight

        for alias, leaf_slug in TRAILER_LEAF_ALIASES.items():
            await _upsert_alias(alias, leaf_slug)
        for alias, parent_slug in TRAILER_PARENT_ALIASES.items():
            await _upsert_alias(alias, parent_slug, weight=80)

        for slug, fields in TRAILER_CORE_FIELDS_BY_SLUG.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue

            wanted_keys = {row[0] for row in fields}
            existing_core = (
                await self._session.execute(
                    select(CategoryCoreField).where(
                        CategoryCoreField.category_id == cat_id,
                        CategoryCoreField.create_intent.is_(None),
                    )
                )
            ).scalars().all()
            for row in existing_core:
                if row.field_key not in wanted_keys:
                    await self._session.delete(row)

            existing_opt = (
                await self._session.execute(
                    select(CategoryOptionalField).where(
                        CategoryOptionalField.category_id == cat_id
                    )
                )
            ).scalars().all()
            for row in existing_opt:
                await self._session.delete(row)

            for key, label, ftype, required, sort, options, hint in fields:
                await self._upsert_core_field(
                    cat_id,
                    key,
                    label,
                    ftype,
                    sort,
                    hint,
                    required=required,
                    options=options,
                )

            filters = TRAILER_SEARCH_FILTERS_BY_SLUG.get(slug) or []
            existing_filters = (
                await self._session.execute(
                    select(CategoryFilter).where(CategoryFilter.category_id == cat_id)
                )
            ).scalars().all()
            wanted_fkeys = {row[0] for row in filters}
            for row in existing_filters:
                if row.filter_key not in wanted_fkeys:
                    await self._session.delete(row)
            for key, label, ftype, sort, config in filters:
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
                            sort_order=sort,
                            config=config,
                        )
                    )
                else:
                    row.label = label
                    row.filter_type = ftype
                    row.sort_order = sort
                    row.config = config

        async def _upsert_typed_brand(
            slug: str, name: str, country: str | None, vtype_str: str
        ) -> VehicleBrand:
            from app.models.category_enums import VehicleType

            vtype = VehicleType(vtype_str)
            brand = (
                await self._session.execute(
                    select(VehicleBrand).where(VehicleBrand.slug == slug)
                )
            ).scalar_one_or_none()
            if brand is None:
                brand = VehicleBrand(
                    slug=slug,
                    name=name,
                    country_origin=country,
                    vehicle_type=vtype,
                    is_enabled=True,
                )
                self._session.add(brand)
                await self._session.flush()
            else:
                brand.name = name
                brand.country_origin = country
                brand.vehicle_type = vtype
                brand.is_enabled = True
            return brand

        for slug, name, country, vtype_str in trailer_other_brands():
            await _upsert_typed_brand(slug, name, country, vtype_str)

        for brand_slug, models in trailer_other_models().items():
            brand = (
                await self._session.execute(
                    select(VehicleBrand).where(VehicleBrand.slug == brand_slug)
                )
            ).scalar_one_or_none()
            if brand is None:
                continue
            for model_slug, model_name in models:
                model = (
                    await self._session.execute(
                        select(VehicleModel).where(
                            VehicleModel.brand_id == brand.id,
                            VehicleModel.slug == model_slug,
                        )
                    )
                ).scalar_one_or_none()
                if model is None:
                    self._session.add(
                        VehicleModel(
                            brand_id=brand.id,
                            slug=model_slug,
                            name=model_name,
                            is_enabled=True,
                        )
                    )
                else:
                    model.name = model_name
                    model.is_enabled = True

    async def _seed_farm_sale_v2_fields(self) -> None:
        """Transport → Сельхозтехника V2 Create + Search SoT."""
        from app.models.vehicle import VehicleBrand, VehicleModel
        from app.seeds.farm_sale_v2 import (
            BROAD_IMPLEMENT_ID,
            BROAD_IMPLEMENT_LABEL,
            BROAD_IMPLEMENT_SLUG,
            FARM_CORE_FIELDS_BY_SLUG,
            FARM_INACTIVE_LEGACY_SLUGS,
            FARM_LEAF_ALIASES,
            FARM_LEAF_LABELS,
            FARM_LEAF_SORT,
            FARM_PARENT_ALIASES,
            FARM_PARENT_SLUG,
            FARM_POLLUTED_BRAND_NAMES,
            FARM_SEARCH_FILTERS_BY_SLUG,
            farm_implement_brands,
            farm_other_brands,
            farm_other_models,
        )

        parent_id = self._slug_to_id.get(FARM_PARENT_SLUG)
        if parent_id is None:
            return

        # Ensure broad implement slug maps (reuse id 839 when present).
        broad = (
            await self._session.execute(
                select(Category).where(Category.id == BROAD_IMPLEMENT_ID)
            )
        ).scalar_one_or_none()
        if broad is not None:
            broad.slug = BROAD_IMPLEMENT_SLUG
            broad.name = BROAD_IMPLEMENT_LABEL
            broad.parent_id = parent_id
            broad.is_active = True
            broad.sort_order = FARM_LEAF_SORT[BROAD_IMPLEMENT_SLUG]
            self._slug_to_id[BROAD_IMPLEMENT_SLUG] = BROAD_IMPLEMENT_ID

        for slug, label in FARM_LEAF_LABELS.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None and slug == BROAD_IMPLEMENT_SLUG:
                cat_id = BROAD_IMPLEMENT_ID if broad is not None else None
            if cat_id is None:
                continue
            row = (
                await self._session.execute(
                    select(Category).where(Category.id == cat_id)
                )
            ).scalar_one_or_none()
            if row is None:
                continue
            row.name = label
            row.parent_id = parent_id
            row.is_active = True
            sort = FARM_LEAF_SORT.get(slug)
            if sort is not None:
                row.sort_order = sort
            if slug == BROAD_IMPLEMENT_SLUG:
                row.slug = BROAD_IMPLEMENT_SLUG

        for slug in FARM_INACTIVE_LEGACY_SLUGS:
            if slug == BROAD_IMPLEMENT_SLUG:
                continue
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            if cat_id == BROAD_IMPLEMENT_ID:
                continue
            row = (
                await self._session.execute(
                    select(Category).where(Category.id == cat_id)
                )
            ).scalar_one_or_none()
            if row is not None and row.is_active:
                row.is_active = False

        for model_cls in (CategoryCoreField, CategoryOptionalField, CategoryFilter):
            existing_parent = (
                await self._session.execute(
                    select(model_cls).where(model_cls.category_id == parent_id)
                )
            ).scalars().all()
            for row in existing_parent:
                await self._session.delete(row)

        async def _upsert_alias(alias: str, target_slug: str, *, weight: int = 100) -> None:
            target_id = self._slug_to_id.get(target_slug)
            if target_id is None and target_slug == BROAD_IMPLEMENT_SLUG:
                target_id = BROAD_IMPLEMENT_ID
            if target_id is None:
                return
            existing = (
                await self._session.execute(
                    select(CategoryAlias).where(
                        CategoryAlias.alias_normalized == alias,
                        CategoryAlias.locale == self._locale,
                    )
                )
            ).scalar_one_or_none()
            if existing is None:
                self._session.add(
                    CategoryAlias(
                        category_id=target_id,
                        alias=alias,
                        alias_normalized=alias,
                        alias_compact=alias.replace(" ", ""),
                        locale=self._locale,
                        weight=weight,
                        is_enabled=True,
                    )
                )
            else:
                existing.category_id = target_id
                existing.alias = alias
                existing.is_enabled = True
                existing.weight = weight

        for alias, leaf_slug in FARM_LEAF_ALIASES.items():
            await _upsert_alias(alias, leaf_slug)
        for alias, parent_slug in FARM_PARENT_ALIASES.items():
            await _upsert_alias(alias, parent_slug, weight=80)

        for slug, fields in FARM_CORE_FIELDS_BY_SLUG.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None and slug == BROAD_IMPLEMENT_SLUG:
                cat_id = BROAD_IMPLEMENT_ID
            if cat_id is None:
                continue
            for model_cls in (
                CategoryCoreField,
                CategoryOptionalField,
                CategoryFilter,
            ):
                existing = (
                    await self._session.execute(
                        select(model_cls).where(model_cls.category_id == cat_id)
                    )
                ).scalars().all()
                for row in existing:
                    await self._session.delete(row)
            # Flush deletes before recreate — otherwise pending DELETE can wipe
            # the same identity upserted later in this transaction.
            await self._session.flush()
            for field in fields:
                key, label, ftype, required, sort, options, hint = field
                await self._upsert_core_field(
                    cat_id,
                    key,
                    label,
                    ftype,
                    sort,
                    hint,
                    required=required,
                    options=options,
                )
            for key, label, ftype, sort, config in FARM_SEARCH_FILTERS_BY_SLUG[
                slug
            ]:
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
                            sort_order=sort,
                            config=config,
                        )
                    )
                else:
                    row.label = label
                    row.filter_type = ftype
                    row.sort_order = sort
                    row.config = config

        async def _upsert_typed_brand(
            slug: str, name: str, country: str | None, vtype_str: str
        ) -> VehicleBrand:
            from app.models.category_enums import VehicleType

            vtype = VehicleType(vtype_str)
            brand = (
                await self._session.execute(
                    select(VehicleBrand).where(VehicleBrand.slug == slug)
                )
            ).scalar_one_or_none()
            if brand is None:
                brand = VehicleBrand(
                    slug=slug,
                    name=name,
                    country_origin=country,
                    vehicle_type=vtype,
                    is_enabled=True,
                )
                self._session.add(brand)
                await self._session.flush()
            else:
                brand.name = name
                if country is not None:
                    brand.country_origin = country
                brand.vehicle_type = vtype
                brand.is_enabled = True
            return brand

        for slug, name, country, vtype_str in farm_other_brands():
            await _upsert_typed_brand(slug, name, country, vtype_str)
        for brand_slug, models in farm_other_models().items():
            brand = (
                await self._session.execute(
                    select(VehicleBrand).where(VehicleBrand.slug == brand_slug)
                )
            ).scalar_one_or_none()
            if brand is None:
                continue
            for model_slug, model_name in models:
                model = (
                    await self._session.execute(
                        select(VehicleModel).where(
                            VehicleModel.brand_id == brand.id,
                            VehicleModel.slug == model_slug,
                        )
                    )
                ).scalar_one_or_none()
                if model is None:
                    self._session.add(
                        VehicleModel(
                            brand_id=brand.id,
                            slug=model_slug,
                            name=model_name,
                            is_enabled=True,
                        )
                    )
                else:
                    model.name = model_name
                    model.is_enabled = True

        for slug, name, country, vtype_str in farm_implement_brands():
            await _upsert_typed_brand(slug, name, country, vtype_str)

        for name in FARM_POLLUTED_BRAND_NAMES:
            rows = (
                await self._session.execute(
                    select(VehicleBrand).where(VehicleBrand.name == name)
                )
            ).scalars().all()
            for brand in rows:
                brand.is_enabled = False

    async def _seed_transport_rental_v2_fields(self) -> None:
        """Transport → Аренда транспорта V2 Create + Search SoT."""
        from app.models.category_enums import CategoryEntityType
        from app.seeds.transport_rental_v2 import (
            BUS_COMBINED_ID,
            BUS_COMBINED_LABEL,
            BUS_COMBINED_OLD_SLUG,
            BUS_COMBINED_SLUG,
            BUS_RETIRED_ID,
            FARM_RENTAL_SLUG,
            OTHER_RENTAL_SLUG,
            RENTAL_CORE_FIELDS_BY_SLUG,
            RENTAL_INACTIVE_LEGACY_SLUGS,
            RENTAL_LEAF_ALIASES,
            RENTAL_LEAF_LABELS,
            RENTAL_LEAF_SORT,
            RENTAL_PARENT_ALIASES,
            RENTAL_PARENT_SLUG,
            RENTAL_SEARCH_FILTERS_BY_SLUG,
            RENTAL_SERVICE_BOUNDARY_ALIASES,
            TRAILER_RENTAL_SLUG,
        )

        parent_id = self._slug_to_id.get(RENTAL_PARENT_SLUG)
        if parent_id is None:
            return

        # Ensure combined Bus/Microbus leaf reuses id 845 when present.
        bus = (
            await self._session.execute(
                select(Category).where(Category.id == BUS_COMBINED_ID)
            )
        ).scalar_one_or_none()
        if bus is not None:
            bus.slug = BUS_COMBINED_SLUG
            bus.name = BUS_COMBINED_LABEL
            bus.parent_id = parent_id
            bus.is_active = True
            bus.sort_order = RENTAL_LEAF_SORT[BUS_COMBINED_SLUG]
            self._slug_to_id[BUS_COMBINED_SLUG] = BUS_COMBINED_ID
            self._slug_to_id.pop(BUS_COMBINED_OLD_SLUG, None)

        retired_bus = (
            await self._session.execute(
                select(Category).where(Category.id == BUS_RETIRED_ID)
            )
        ).scalar_one_or_none()
        if retired_bus is not None and retired_bus.is_active:
            retired_bus.is_active = False

        async def _ensure_leaf(slug: str, label: str, sort: int) -> int | None:
            cat_id = self._slug_to_id.get(slug)
            if cat_id is not None:
                row = (
                    await self._session.execute(
                        select(Category).where(Category.id == cat_id)
                    )
                ).scalar_one_or_none()
                if row is None:
                    return None
                row.name = label
                row.parent_id = parent_id
                row.is_active = True
                row.sort_order = sort
                return cat_id
            row = Category(
                slug=slug,
                name=label,
                parent_id=parent_id,
                entity_type=CategoryEntityType.object,
                is_active=True,
                sort_order=sort,
            )
            self._session.add(row)
            await self._session.flush()
            self._slug_to_id[slug] = row.id
            return row.id

        for slug, label in RENTAL_LEAF_LABELS.items():
            await _ensure_leaf(slug, label, RENTAL_LEAF_SORT[slug])

        for slug in RENTAL_INACTIVE_LEGACY_SLUGS:
            if slug in {BUS_COMBINED_SLUG, BUS_COMBINED_OLD_SLUG}:
                continue
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            if cat_id == BUS_COMBINED_ID:
                continue
            row = (
                await self._session.execute(
                    select(Category).where(Category.id == cat_id)
                )
            ).scalar_one_or_none()
            if row is not None and row.is_active:
                row.is_active = False

        for model_cls in (CategoryCoreField, CategoryOptionalField, CategoryFilter):
            existing_parent = (
                await self._session.execute(
                    select(model_cls).where(model_cls.category_id == parent_id)
                )
            ).scalars().all()
            for row in existing_parent:
                await self._session.delete(row)

        async def _upsert_alias(alias: str, target_slug: str, *, weight: int = 100) -> None:
            target_id = self._slug_to_id.get(target_slug)
            if target_id is None and target_slug == BUS_COMBINED_SLUG:
                target_id = BUS_COMBINED_ID
            if target_id is None:
                return
            existing = (
                await self._session.execute(
                    select(CategoryAlias).where(
                        CategoryAlias.alias_normalized == alias,
                        CategoryAlias.locale == self._locale,
                    )
                )
            ).scalar_one_or_none()
            if existing is None:
                self._session.add(
                    CategoryAlias(
                        category_id=target_id,
                        alias=alias,
                        alias_normalized=alias,
                        alias_compact=alias.replace(" ", ""),
                        locale=self._locale,
                        weight=weight,
                        is_enabled=True,
                    )
                )
            else:
                existing.category_id = target_id
                existing.alias = alias
                existing.is_enabled = True
                existing.weight = weight

        for alias, leaf_slug in RENTAL_LEAF_ALIASES.items():
            await _upsert_alias(alias, leaf_slug)
        for alias, parent_slug in RENTAL_PARENT_ALIASES.items():
            await _upsert_alias(alias, parent_slug, weight=80)
        for alias, target_slug in RENTAL_SERVICE_BOUNDARY_ALIASES.items():
            await _upsert_alias(alias, target_slug, weight=120)

        for slug, fields in RENTAL_CORE_FIELDS_BY_SLUG.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None and slug == BUS_COMBINED_SLUG:
                cat_id = BUS_COMBINED_ID
            if cat_id is None:
                continue
            for model_cls in (
                CategoryCoreField,
                CategoryOptionalField,
                CategoryFilter,
            ):
                existing = (
                    await self._session.execute(
                        select(model_cls).where(model_cls.category_id == cat_id)
                    )
                ).scalars().all()
                for row in existing:
                    await self._session.delete(row)
            await self._session.flush()
            for field in fields:
                key, label, ftype, required, sort, options, hint = field
                await self._upsert_core_field(
                    cat_id,
                    key,
                    label,
                    ftype,
                    sort,
                    hint,
                    required=required,
                    options=options,
                )
            for key, label, ftype, sort, config in RENTAL_SEARCH_FILTERS_BY_SLUG[
                slug
            ]:
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
                            sort_order=sort,
                            config=config,
                        )
                    )
                else:
                    row.label = label
                    row.filter_type = ftype
                    row.sort_order = sort
                    row.config = config

        # Touch new leaf slug map helpers for Trailer/Farm/Other if created above.
        for slug in (TRAILER_RENTAL_SLUG, FARM_RENTAL_SLUG, OTHER_RENTAL_SLUG):
            _ = self._slug_to_id.get(slug)

    async def _seed_tires_wheels_v2_fields(self) -> None:
        """Transport → Шины и диски V2 Create + Search SoT (content-authoritative)."""
        from app.seeds.tires_wheels_v2 import (
            LEAF_IDS,
            LEAF_LABELS,
            LEAF_SLUGS,
            LEAF_SORT,
            OTHER_LEAF_ID,
            OTHER_LEAF_SLUG,
            OTHER_LEGACY_SLUG,
            TIRES_CORE_FIELDS_BY_SLUG,
            TIRES_LEAF_ALIASES,
            TIRES_PARENT_ALIASES,
            TIRES_PARENT_SLUG,
            TIRES_SEARCH_FILTERS_BY_SLUG,
            TIRES_SERVICE_BOUNDARY_ALIASES,
        )

        parent_id = self._slug_to_id.get(TIRES_PARENT_SLUG)
        if parent_id is None:
            return

        other = (
            await self._session.execute(
                select(Category).where(Category.id == OTHER_LEAF_ID)
            )
        ).scalar_one_or_none()
        if other is not None:
            other.slug = OTHER_LEAF_SLUG
            other.name = LEAF_LABELS[OTHER_LEAF_SLUG]
            other.parent_id = parent_id
            other.is_active = True
            other.sort_order = LEAF_SORT[OTHER_LEAF_SLUG]
            self._slug_to_id[OTHER_LEAF_SLUG] = OTHER_LEAF_ID
            if OTHER_LEGACY_SLUG in self._slug_to_id:
                self._slug_to_id.pop(OTHER_LEGACY_SLUG, None)

        # Skeleton may recreate the legacy accessories slug as a parallel leaf.
        legacy_rows = (
            await self._session.execute(
                select(Category).where(
                    Category.slug == OTHER_LEGACY_SLUG,
                    Category.id != OTHER_LEAF_ID,
                )
            )
        ).scalars().all()
        for row in legacy_rows:
            row.is_active = False

        allowed_leaf_ids = set(LEAF_IDS.values())
        extras = (
            await self._session.execute(
                select(Category).where(
                    Category.parent_id == parent_id,
                    Category.is_active.is_(True),
                )
            )
        ).scalars().all()
        for row in extras:
            if row.id not in allowed_leaf_ids:
                row.is_active = False

        for slug in LEAF_SLUGS:
            cat_id = self._slug_to_id.get(slug) or LEAF_IDS.get(slug)
            if cat_id is None:
                continue
            row = (
                await self._session.execute(
                    select(Category).where(Category.id == cat_id)
                )
            ).scalar_one_or_none()
            if row is None:
                continue
            row.slug = slug
            row.name = LEAF_LABELS[slug]
            row.parent_id = parent_id
            row.is_active = True
            row.sort_order = LEAF_SORT[slug]
            self._slug_to_id[slug] = cat_id

        for model_cls in (CategoryCoreField, CategoryOptionalField, CategoryFilter):
            existing_parent = (
                await self._session.execute(
                    select(model_cls).where(model_cls.category_id == parent_id)
                )
            ).scalars().all()
            for row in existing_parent:
                await self._session.delete(row)
        await self._session.flush()

        async def _upsert_alias(alias: str, target_slug: str, *, weight: int = 100) -> None:
            target_id = self._slug_to_id.get(target_slug)
            if target_id is None:
                return
            existing = (
                await self._session.execute(
                    select(CategoryAlias).where(
                        CategoryAlias.alias_normalized == alias,
                        CategoryAlias.locale == self._locale,
                    )
                )
            ).scalar_one_or_none()
            if existing is None:
                self._session.add(
                    CategoryAlias(
                        category_id=target_id,
                        alias=alias,
                        alias_normalized=alias,
                        alias_compact=alias.replace(" ", ""),
                        locale=self._locale,
                        weight=weight,
                        is_enabled=True,
                    )
                )
            else:
                existing.category_id = target_id
                existing.alias = alias
                existing.is_enabled = True
                existing.weight = weight

        for alias, leaf_slug in TIRES_LEAF_ALIASES.items():
            await _upsert_alias(alias, leaf_slug)
        for alias, parent_slug in TIRES_PARENT_ALIASES.items():
            await _upsert_alias(alias, parent_slug, weight=80)
        for alias, target_slug in TIRES_SERVICE_BOUNDARY_ALIASES.items():
            await _upsert_alias(alias, target_slug, weight=130)

        for slug, fields in TIRES_CORE_FIELDS_BY_SLUG.items():
            if slug == TIRES_PARENT_SLUG:
                continue
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue

            wanted_keys = {row[0] for row in fields}
            existing_core = (
                await self._session.execute(
                    select(CategoryCoreField).where(
                        CategoryCoreField.category_id == cat_id,
                        CategoryCoreField.create_intent.is_(None),
                    )
                )
            ).scalars().all()
            for row in existing_core:
                if row.field_key not in wanted_keys:
                    await self._session.delete(row)

            existing_opt = (
                await self._session.execute(
                    select(CategoryOptionalField).where(
                        CategoryOptionalField.category_id == cat_id
                    )
                )
            ).scalars().all()
            for row in existing_opt:
                await self._session.delete(row)

            for sort_i, (key, label, ftype, required, sort, options, hint) in enumerate(
                fields
            ):
                await self._upsert_core_field(
                    cat_id,
                    key,
                    label,
                    ftype,
                    sort if sort is not None else sort_i,
                    hint,
                    required=required,
                    options=options,
                )

            filters = TIRES_SEARCH_FILTERS_BY_SLUG.get(slug, [])
            wanted_filters = {row[0] for row in filters}
            existing_filters = (
                await self._session.execute(
                    select(CategoryFilter).where(CategoryFilter.category_id == cat_id)
                )
            ).scalars().all()
            for row in existing_filters:
                if row.filter_key not in wanted_filters:
                    await self._session.delete(row)
            await self._session.flush()

            for key, label, ftype, sort, config in filters:
                stmt = select(CategoryFilter).where(
                    CategoryFilter.category_id == cat_id,
                    CategoryFilter.filter_key == key,
                )
                existing_f = (await self._session.execute(stmt)).scalar_one_or_none()
                if existing_f is None:
                    self._session.add(
                        CategoryFilter(
                            category_id=cat_id,
                            filter_key=key,
                            label=label,
                            filter_type=ftype,
                            sort_order=sort,
                            config=config,
                        )
                    )
                else:
                    existing_f.label = label
                    existing_f.filter_type = ftype
                    existing_f.sort_order = sort
                    existing_f.config = config

    async def _seed_auto_parts_v2_fields(self) -> None:
        """Transport → Автозапчасти V2 Create + Search SoT."""
        from app.seeds.auto_parts_v2 import (
            BODY_LEAF_ID,
            BODY_LEAF_LABEL,
            BODY_LEAF_SLUG,
            BODY_RETIRED_IDS,
            BODY_RETIRED_SLUGS,
            PARTS_CORE_FIELDS_BY_SLUG,
            PARTS_LEAF_ALIASES,
            PARTS_PARENT_ALIASES,
            PARTS_PARENT_SLUG,
            PARTS_SEARCH_FILTERS_BY_SLUG,
            PARTS_SERVICE_BOUNDARY_ALIASES,
            PASSENGER_SYSTEM_LABELS,
            PASSENGER_SYSTEM_SORT,
            PASSENGER_SYSTEM_SLUGS,
            SPECIAL_SYSTEM_LABELS,
            SPECIAL_SYSTEM_SORT,
            SPECIAL_SYSTEM_SLUGS,
            UNIVERSAL_INACTIVE_SLUG,
        )

        parent_id = self._slug_to_id.get(PARTS_PARENT_SLUG)
        if parent_id is None:
            return

        body = (
            await self._session.execute(
                select(Category).where(Category.id == BODY_LEAF_ID)
            )
        ).scalar_one_or_none()
        if body is not None:
            body.slug = BODY_LEAF_SLUG
            body.name = BODY_LEAF_LABEL
            body.parent_id = parent_id
            body.is_active = True
            body.sort_order = PASSENGER_SYSTEM_SORT[BODY_LEAF_SLUG]
            self._slug_to_id[BODY_LEAF_SLUG] = BODY_LEAF_ID

        for slug in PASSENGER_SYSTEM_SLUGS:
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            row = (
                await self._session.execute(
                    select(Category).where(Category.id == cat_id)
                )
            ).scalar_one_or_none()
            if row is None:
                continue
            row.name = PASSENGER_SYSTEM_LABELS[slug]
            row.parent_id = parent_id
            row.is_active = True
            row.sort_order = PASSENGER_SYSTEM_SORT[slug]

        for slug in SPECIAL_SYSTEM_SLUGS:
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            row = (
                await self._session.execute(
                    select(Category).where(Category.id == cat_id)
                )
            ).scalar_one_or_none()
            if row is None:
                continue
            row.name = SPECIAL_SYSTEM_LABELS[slug]
            row.parent_id = parent_id
            row.is_active = True
            row.sort_order = SPECIAL_SYSTEM_SORT[slug]

        for rid in BODY_RETIRED_IDS:
            row = (
                await self._session.execute(
                    select(Category).where(Category.id == rid)
                )
            ).scalar_one_or_none()
            if row is not None and row.is_active:
                row.is_active = False

        for slug in BODY_RETIRED_SLUGS:
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            row = (
                await self._session.execute(
                    select(Category).where(Category.id == cat_id)
                )
            ).scalar_one_or_none()
            if row is not None and row.is_active:
                row.is_active = False

        uni_id = self._slug_to_id.get(UNIVERSAL_INACTIVE_SLUG)
        if uni_id is not None:
            uni = (
                await self._session.execute(
                    select(Category).where(Category.id == uni_id)
                )
            ).scalar_one_or_none()
            if uni is not None and uni.is_active:
                uni.is_active = False

        for model_cls in (CategoryCoreField, CategoryOptionalField, CategoryFilter):
            existing_parent = (
                await self._session.execute(
                    select(model_cls).where(model_cls.category_id == parent_id)
                )
            ).scalars().all()
            for row in existing_parent:
                await self._session.delete(row)

        async def _upsert_alias(alias: str, target_slug: str, *, weight: int = 100) -> None:
            target_id = self._slug_to_id.get(target_slug)
            if target_id is None:
                return
            existing = (
                await self._session.execute(
                    select(CategoryAlias).where(
                        CategoryAlias.alias_normalized == alias,
                        CategoryAlias.locale == self._locale,
                    )
                )
            ).scalar_one_or_none()
            if existing is None:
                self._session.add(
                    CategoryAlias(
                        category_id=target_id,
                        alias=alias,
                        alias_normalized=alias,
                        alias_compact=alias.replace(" ", ""),
                        locale=self._locale,
                        weight=weight,
                        is_enabled=True,
                    )
                )
            else:
                existing.category_id = target_id
                existing.alias = alias
                existing.is_enabled = True
                existing.weight = weight

        for alias, leaf_slug in PARTS_LEAF_ALIASES.items():
            await _upsert_alias(alias, leaf_slug)
        for alias, parent_slug in PARTS_PARENT_ALIASES.items():
            await _upsert_alias(alias, parent_slug, weight=80)
        for alias, target_slug in PARTS_SERVICE_BOUNDARY_ALIASES.items():
            await _upsert_alias(alias, target_slug, weight=130)

        # Disable unsafe LED → Optics alias.
        optics_id = self._slug_to_id.get(
            "transport-auto-parts-optika-fary-i-fonari"
        )
        if optics_id is not None:
            led = (
                await self._session.execute(
                    select(CategoryAlias).where(
                        CategoryAlias.alias_normalized == "led",
                        CategoryAlias.category_id == optics_id,
                    )
                )
            ).scalar_one_or_none()
            if led is not None:
                led.is_enabled = False

        for slug, fields in PARTS_CORE_FIELDS_BY_SLUG.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            for model_cls in (
                CategoryCoreField,
                CategoryOptionalField,
                CategoryFilter,
            ):
                existing = (
                    await self._session.execute(
                        select(model_cls).where(model_cls.category_id == cat_id)
                    )
                ).scalars().all()
                for row in existing:
                    await self._session.delete(row)
            # Flush deletes before re-insert so uq_category_filters_key_intent
            # is not violated when the same keys are recreated in one transaction.
            await self._session.flush()
            for field in fields:
                key, label, ftype, required, sort, options, hint = field
                await self._upsert_core_field(
                    cat_id,
                    key,
                    label,
                    ftype,
                    sort,
                    hint,
                    required=required,
                    options=options,
                )
            for key, label, ftype, sort, config in PARTS_SEARCH_FILTERS_BY_SLUG.get(
                slug, []
            ):
                self._session.add(
                    CategoryFilter(
                        category_id=cat_id,
                        filter_key=key,
                        label=label,
                        filter_type=ftype,
                        sort_order=sort,
                        config=config,
                    )
                )

    async def _seed_real_estate_v2_fields(self) -> None:
        """Real Estate V2 — property-leaf Create + Search SoT; retire deal dual-tree."""
        from app.models.category_enums import CategoryEntityType
        from app.seeds.real_estate_v2 import (
            APARTMENTS_ID,
            APARTMENTS_SLUG,
            CANONICAL_LEAF_LABELS,
            CANONICAL_LEAF_SLUGS,
            CANONICAL_LEAF_SORT,
            COMMERCIAL_ID,
            COMMERCIAL_SLUG,
            GARAGES_ID,
            GARAGES_LABEL,
            GARAGES_SLUG,
            HOUSES_ID,
            HOUSES_SLUG,
            LAND_ID,
            LAND_SLUG,
            LEGACY_DEAL_IDS,
            LEGACY_DEAL_SLUGS,
            PARKING_LABEL,
            PARKING_SLUG,
            RE_ALIASES,
            RE_CORE_FIELDS_BY_SLUG,
            RE_SEARCH_FILTERS_BY_SLUG,
            RETIRED_SKELETON_IDS,
            RETIRED_SKELETON_SLUGS,
            ROOMS_ID,
            ROOMS_SLUG,
            ROOT_ID,
            ROOT_SLUG,
        )

        root_id = self._slug_to_id.get(ROOT_SLUG)
        if root_id is None:
            return
        root = (
            await self._session.execute(select(Category).where(Category.id == root_id))
        ).scalar_one_or_none()
        if root is None:
            return
        if root.id != ROOT_ID:
            # Keep historical ID if remapped; still treat as picker root.
            pass
        root.is_active = True
        root.name = "Недвижимость"
        root.parent_id = None

        # Clear live Create/Search schema on picker root.
        for model_cls in (CategoryCoreField, CategoryOptionalField, CategoryFilter):
            for row in (
                await self._session.execute(
                    select(model_cls).where(model_cls.category_id == root.id)
                )
            ).scalars().all():
                await self._session.delete(row)

        expected_ids = {
            APARTMENTS_SLUG: APARTMENTS_ID,
            HOUSES_SLUG: HOUSES_ID,
            ROOMS_SLUG: ROOMS_ID,
            LAND_SLUG: LAND_ID,
            COMMERCIAL_SLUG: COMMERCIAL_ID,
            GARAGES_SLUG: GARAGES_ID,
        }

        for slug, expected_id in expected_ids.items():
            row = (
                await self._session.execute(
                    select(Category).where(Category.id == expected_id)
                )
            ).scalar_one_or_none()
            if row is None:
                # Fallback: find by current slug map.
                cid = self._slug_to_id.get(slug)
                if cid is None:
                    continue
                row = (
                    await self._session.execute(
                        select(Category).where(Category.id == cid)
                    )
                ).scalar_one_or_none()
                if row is None:
                    continue
            row.slug = slug
            row.name = CANONICAL_LEAF_LABELS[slug]
            row.parent_id = root.id
            row.is_active = True
            row.sort_order = CANONICAL_LEAF_SORT[slug]
            row.entity_type = CategoryEntityType.object
            self._slug_to_id[slug] = row.id

        # Rename garages away from combined slug if still present.
        garage = (
            await self._session.execute(
                select(Category).where(Category.id == GARAGES_ID)
            )
        ).scalar_one_or_none()
        if garage is not None:
            garage.slug = GARAGES_SLUG
            garage.name = GARAGES_LABEL
            garage.parent_id = root.id
            garage.is_active = True
            garage.sort_order = CANONICAL_LEAF_SORT[GARAGES_SLUG]
            self._slug_to_id[GARAGES_SLUG] = GARAGES_ID
            self._slug_to_id.pop("real-estate-garazhi-i-parkovki", None)

        # Ensure Parking leaf exists (new).
        parking_id = self._slug_to_id.get(PARKING_SLUG)
        if parking_id is None:
            parking = Category(
                name=PARKING_LABEL,
                slug=PARKING_SLUG,
                parent_id=root.id,
                entity_type=CategoryEntityType.object,
                sort_order=CANONICAL_LEAF_SORT[PARKING_SLUG],
                is_active=True,
            )
            self._session.add(parking)
            await self._session.flush()
            parking_id = parking.id
            self._slug_to_id[PARKING_SLUG] = parking_id
        else:
            parking = (
                await self._session.execute(
                    select(Category).where(Category.id == parking_id)
                )
            ).scalar_one_or_none()
            if parking is not None:
                parking.name = PARKING_LABEL
                parking.slug = PARKING_SLUG
                parking.parent_id = root.id
                parking.is_active = True
                parking.sort_order = CANONICAL_LEAF_SORT[PARKING_SLUG]

        # Retire legacy deal homes + unused skeletons.
        for rid in (*LEGACY_DEAL_IDS, *RETIRED_SKELETON_IDS):
            row = (
                await self._session.execute(select(Category).where(Category.id == rid))
            ).scalar_one_or_none()
            if row is None:
                continue
            row.is_active = False
            for model_cls in (CategoryCoreField, CategoryOptionalField, CategoryFilter):
                for fr in (
                    await self._session.execute(
                        select(model_cls).where(model_cls.category_id == rid)
                    )
                ).scalars().all():
                    await self._session.delete(fr)

        for slug in LEGACY_DEAL_SLUGS | RETIRED_SKELETON_SLUGS:
            cid = self._slug_to_id.get(slug)
            if cid is None:
                continue
            row = (
                await self._session.execute(select(Category).where(Category.id == cid))
            ).scalar_one_or_none()
            if row is not None and row.is_active:
                row.is_active = False

        # Seed leaf schemas + filters.
        for slug in CANONICAL_LEAF_SLUGS:
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            fields = RE_CORE_FIELDS_BY_SLUG.get(slug, [])
            wanted_keys = {row[0] for row in fields}
            existing_core = (
                await self._session.execute(
                    select(CategoryCoreField).where(
                        CategoryCoreField.category_id == cat_id,
                        CategoryCoreField.create_intent.is_(None),
                    )
                )
            ).scalars().all()
            for row in existing_core:
                if row.field_key not in wanted_keys:
                    await self._session.delete(row)
            for row in (
                await self._session.execute(
                    select(CategoryOptionalField).where(
                        CategoryOptionalField.category_id == cat_id
                    )
                )
            ).scalars().all():
                await self._session.delete(row)

            for sort_i, (key, label, ftype, required, sort, options, hint) in enumerate(
                fields
            ):
                await self._upsert_core_field(
                    cat_id,
                    key,
                    label,
                    ftype,
                    sort if sort is not None else sort_i,
                    hint,
                    required=required,
                    options=options,
                )

            filters = RE_SEARCH_FILTERS_BY_SLUG.get(slug, [])
            wanted_filters = {row[0] for row in filters}
            for row in (
                await self._session.execute(
                    select(CategoryFilter).where(CategoryFilter.category_id == cat_id)
                )
            ).scalars().all():
                if row.filter_key not in wanted_filters:
                    await self._session.delete(row)
            for sort_i, (key, label, ftype, sort, config) in enumerate(filters):
                stmt = select(CategoryFilter).where(
                    CategoryFilter.category_id == cat_id,
                    CategoryFilter.filter_key == key,
                )
                existing_f = (await self._session.execute(stmt)).scalar_one_or_none()
                if existing_f is None:
                    self._session.add(
                        CategoryFilter(
                            category_id=cat_id,
                            filter_key=key,
                            label=label,
                            filter_type=ftype,
                            sort_order=sort if sort is not None else sort_i,
                            config=config,
                        )
                    )
                else:
                    existing_f.label = label
                    existing_f.filter_type = ftype
                    existing_f.sort_order = sort if sort is not None else sort_i
                    existing_f.config = config

        async def _upsert_alias(alias: str, target_slug: str, *, weight: int = 100) -> None:
            target_id = self._slug_to_id.get(target_slug)
            if target_id is None:
                return
            spaced, compact = normalize_alias_keys(alias)
            existing = (
                await self._session.execute(
                    select(CategoryAlias).where(
                        CategoryAlias.alias_normalized == spaced,
                        CategoryAlias.locale == self._locale,
                    )
                )
            ).scalar_one_or_none()
            if existing is None:
                self._session.add(
                    CategoryAlias(
                        category_id=target_id,
                        alias=alias,
                        alias_normalized=spaced,
                        alias_compact=compact,
                        locale=self._locale,
                        weight=weight,
                        is_enabled=True,
                    )
                )
            else:
                existing.category_id = target_id
                existing.alias = alias
                existing.alias_compact = compact
                existing.is_enabled = True
                existing.weight = weight

        for alias, target_slug, weight in RE_ALIASES:
            await _upsert_alias(alias, target_slug, weight=weight)

    async def _seed_tuning_accessories_v2_fields(self) -> None:
        """Transport → Аксессуары и тюнинг V2 Create + Search SoT."""
        from app.models.category_enums import CategoryEntityType
        from app.seeds.tuning_accessories_v2 import (
            AUDIO_LEGACY_SLUG,
            KIDS_BOUNDARY_ALIASES,
            LEAF_ALIASES,
            LEAF_IDS,
            LEAF_LABELS,
            LEAF_SLUGS,
            LEAF_SORT,
            PARENT_ALIASES,
            PARENT_ID,
            PARENT_LABEL,
            PARENT_SLUG,
            PARTS_BOUNDARY_ALIASES,
            RETIRE_OR_HIDE_IDS,
            SERVICE_BOUNDARY_ALIASES,
            TECHNICAL_LEGACY_SLUG,
            TUNING_CORE_FIELDS_BY_SLUG,
            TUNING_SEARCH_FILTERS_BY_SLUG,
        )

        parent_id = self._slug_to_id.get(PARENT_SLUG)
        if parent_id is None:
            return
        parent = (
            await self._session.execute(
                select(Category).where(Category.id == parent_id)
            )
        ).scalar_one_or_none()
        if parent is None:
            return
        parent.name = PARENT_LABEL
        parent.is_active = True
        if parent_id != PARENT_ID:
            # Prefer live id; constants document production identity.
            pass

        # Ensure each final leaf exists (create if skeleton missed fixed IDs).
        for slug in LEAF_SLUGS:
            want_id = LEAF_IDS[slug]
            row = (
                await self._session.execute(
                    select(Category).where(Category.id == want_id)
                )
            ).scalar_one_or_none()
            if row is None:
                by_slug = (
                    await self._session.execute(
                        select(Category).where(Category.slug == slug)
                    )
                ).scalar_one_or_none()
                if by_slug is not None:
                    row = by_slug
                else:
                    row = Category(
                        id=want_id,
                        parent_id=parent_id,
                        slug=slug,
                        name=LEAF_LABELS[slug],
                        entity_type=CategoryEntityType.object,
                        is_active=True,
                        sort_order=LEAF_SORT[slug],
                        requires_city=True,
                    )
                    self._session.add(row)
                    await self._session.flush()
            row.slug = slug
            row.name = LEAF_LABELS[slug]
            row.parent_id = parent_id
            row.is_active = True
            row.sort_order = LEAF_SORT[slug]
            self._slug_to_id[slug] = row.id

        # Deactivate legacy / competing / non-ordinary picker nodes.
        for rid in RETIRE_OR_HIDE_IDS:
            row = (
                await self._session.execute(
                    select(Category).where(Category.id == rid)
                )
            ).scalar_one_or_none()
            if row is not None:
                row.is_active = False

        for legacy_slug in (AUDIO_LEGACY_SLUG, TECHNICAL_LEGACY_SLUG):
            lid = self._slug_to_id.get(legacy_slug)
            if lid is None:
                cont = (
                    await self._session.execute(
                        select(Category).where(Category.slug == legacy_slug)
                    )
                ).scalar_one_or_none()
                if cont is None:
                    continue
                lid = cont.id
            # If legacy slug still points at a different row than final leaf, hide it.
            final_ids = set(LEAF_IDS.values())
            if lid not in final_ids:
                row = (
                    await self._session.execute(
                        select(Category).where(Category.id == lid)
                    )
                ).scalar_one_or_none()
                if row is not None:
                    row.is_active = False

        allowed = set()
        for slug in LEAF_SLUGS:
            cid = self._slug_to_id.get(slug)
            if cid is not None:
                allowed.add(cid)
        children = (
            await self._session.execute(
                select(Category).where(Category.parent_id == parent_id)
            )
        ).scalars().all()
        for ch in children:
            if ch.id not in allowed and ch.is_active:
                ch.is_active = False

        for model_cls in (CategoryCoreField, CategoryOptionalField, CategoryFilter):
            existing_parent = (
                await self._session.execute(
                    select(model_cls).where(model_cls.category_id == parent_id)
                )
            ).scalars().all()
            for row in existing_parent:
                await self._session.delete(row)

        async def _upsert_alias(alias: str, target_slug: str, *, weight: int = 100) -> None:
            target_id = self._slug_to_id.get(target_slug)
            if target_id is None:
                return
            existing = (
                await self._session.execute(
                    select(CategoryAlias).where(
                        CategoryAlias.alias_normalized == alias,
                        CategoryAlias.locale == self._locale,
                    )
                )
            ).scalar_one_or_none()
            if existing is None:
                self._session.add(
                    CategoryAlias(
                        category_id=target_id,
                        alias=alias,
                        alias_normalized=alias,
                        alias_compact=alias.replace(" ", ""),
                        locale=self._locale,
                        weight=weight,
                        is_enabled=True,
                    )
                )
            else:
                existing.category_id = target_id
                existing.alias = alias
                existing.is_enabled = True
                existing.weight = weight

        for alias, leaf_slug in LEAF_ALIASES.items():
            await _upsert_alias(alias, leaf_slug, weight=110)
        for alias, parent_slug in PARENT_ALIASES.items():
            await _upsert_alias(alias, parent_slug, weight=80)
        for alias, target_slug in SERVICE_BOUNDARY_ALIASES.items():
            await _upsert_alias(alias, target_slug, weight=140)
        for alias, target_slug in PARTS_BOUNDARY_ALIASES.items():
            await _upsert_alias(alias, target_slug, weight=120)
        for alias, target_slug in KIDS_BOUNDARY_ALIASES.items():
            await _upsert_alias(alias, target_slug, weight=130)

        for slug, fields in TUNING_CORE_FIELDS_BY_SLUG.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            for model_cls in (
                CategoryCoreField,
                CategoryOptionalField,
                CategoryFilter,
            ):
                existing = (
                    await self._session.execute(
                        select(model_cls).where(model_cls.category_id == cat_id)
                    )
                ).scalars().all()
                for row in existing:
                    await self._session.delete(row)
            await self._session.flush()
            for field in fields:
                key, label, ftype, required, sort, options, hint = field
                await self._upsert_core_field(
                    cat_id,
                    key,
                    label,
                    ftype,
                    sort,
                    hint,
                    required=required,
                    options=options,
                )
            for key, label, ftype, sort, config in TUNING_SEARCH_FILTERS_BY_SLUG.get(
                slug, []
            ):
                self._session.add(
                    CategoryFilter(
                        category_id=cat_id,
                        filter_key=key,
                        label=label,
                        filter_type=ftype,
                        sort_order=sort,
                        config=config,
                    )
                )

    async def _seed_auto_services_v2_fields(self) -> None:
        """Transport → Автоуслуги V2 Create + Search SoT."""
        from app.models.category_enums import CategoryEntityType
        from app.seeds.auto_services_v2 import (
            AUTO_SERVICES_CORE_FIELDS_BY_SLUG,
            AUTO_SERVICES_SEARCH_FILTERS_BY_SLUG,
            CARGO_EVACUATOR_ALIASES,
            LEAF_ALIASES,
            LEAF_IDS,
            LEAF_LABELS,
            LEAF_SLUGS,
            LEAF_SORT,
            PARENT_ALIASES,
            PARENT_ID,
            PARENT_LABEL,
            PARENT_SLUG,
            TOWING_SLUG,
        )

        parent_id = self._slug_to_id.get(PARENT_SLUG)
        if parent_id is None:
            return
        parent = (
            await self._session.execute(
                select(Category).where(Category.id == parent_id)
            )
        ).scalar_one_or_none()
        if parent is None:
            return
        parent.name = PARENT_LABEL
        parent.is_active = True
        if parent_id != PARENT_ID:
            pass

        for slug in LEAF_SLUGS:
            want_id = LEAF_IDS[slug]
            row = (
                await self._session.execute(
                    select(Category).where(Category.id == want_id)
                )
            ).scalar_one_or_none()
            if row is None:
                by_slug = (
                    await self._session.execute(
                        select(Category).where(Category.slug == slug)
                    )
                ).scalar_one_or_none()
                if by_slug is not None:
                    row = by_slug
                else:
                    row = Category(
                        id=want_id,
                        parent_id=parent_id,
                        slug=slug,
                        name=LEAF_LABELS[slug],
                        entity_type=CategoryEntityType.service,
                        is_active=True,
                        sort_order=LEAF_SORT[slug],
                        requires_city=True,
                    )
                    self._session.add(row)
                    await self._session.flush()
            row.slug = slug
            row.name = LEAF_LABELS[slug]
            row.parent_id = parent_id
            row.is_active = True
            row.sort_order = LEAF_SORT[slug]
            self._slug_to_id[slug] = row.id

        allowed = set()
        for slug in LEAF_SLUGS:
            cid = self._slug_to_id.get(slug)
            if cid is not None:
                allowed.add(cid)
        children = (
            await self._session.execute(
                select(Category).where(Category.parent_id == parent_id)
            )
        ).scalars().all()
        for ch in children:
            if ch.id not in allowed and ch.is_active:
                ch.is_active = False

        for model_cls in (CategoryCoreField, CategoryOptionalField, CategoryFilter):
            existing_parent = (
                await self._session.execute(
                    select(model_cls).where(model_cls.category_id == parent_id)
                )
            ).scalars().all()
            for row in existing_parent:
                await self._session.delete(row)

        async def _upsert_alias(alias: str, target_slug: str, *, weight: int = 100) -> None:
            target_id = self._slug_to_id.get(target_slug)
            if target_id is None:
                return
            existing = (
                await self._session.execute(
                    select(CategoryAlias).where(
                        CategoryAlias.alias_normalized == alias,
                        CategoryAlias.locale == self._locale,
                    )
                )
            ).scalar_one_or_none()
            if existing is None:
                self._session.add(
                    CategoryAlias(
                        category_id=target_id,
                        alias=alias,
                        alias_normalized=alias,
                        alias_compact=alias.replace(" ", ""),
                        locale=self._locale,
                        weight=weight,
                        is_enabled=True,
                    )
                )
            else:
                existing.category_id = target_id
                existing.alias = alias
                existing.is_enabled = True
                existing.weight = weight

        for alias, leaf_slug in LEAF_ALIASES.items():
            await _upsert_alias(alias, leaf_slug, weight=130)
        for alias, parent_slug in PARENT_ALIASES.items():
            await _upsert_alias(alias, parent_slug, weight=80)
        for alias, target_slug in CARGO_EVACUATOR_ALIASES.items():
            await _upsert_alias(alias, target_slug, weight=150)
        await _upsert_alias("эвакуатор", TOWING_SLUG, weight=140)

        for slug, fields in AUTO_SERVICES_CORE_FIELDS_BY_SLUG.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            for model_cls in (
                CategoryCoreField,
                CategoryOptionalField,
                CategoryFilter,
            ):
                existing = (
                    await self._session.execute(
                        select(model_cls).where(model_cls.category_id == cat_id)
                    )
                ).scalars().all()
                for row in existing:
                    await self._session.delete(row)
            await self._session.flush()
            for field in fields:
                key, label, ftype, required, sort, options, hint = field
                await self._upsert_core_field(
                    cat_id,
                    key,
                    label,
                    ftype,
                    sort,
                    hint,
                    required=required,
                    options=options,
                )
            for key, label, ftype, sort, config in AUTO_SERVICES_SEARCH_FILTERS_BY_SLUG.get(
                slug, []
            ):
                self._session.add(
                    CategoryFilter(
                        category_id=cat_id,
                        filter_key=key,
                        label=label,
                        filter_type=ftype,
                        sort_order=sort,
                        config=config,
                    )
                )

    async def _seed_home_garden_package_a_fields(self) -> None:
        """Home & Garden V2 Package A — leaf Create cores including goods base.

        Replaces core fields for every FINAL publishable leaf so seller / price /
        negotiable / contact_methods are Backend SoT (Flutter profile cutover).
        Search filters remain in `_seed_home_garden_search_filters` (Package B
        still owns Search UX).
        """
        from app.seeds.home_garden_filters import build_home_garden_core_fields

        core_by_slug = build_home_garden_core_fields()
        for slug, fields in core_by_slug.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            existing = (
                await self._session.execute(
                    select(CategoryCoreField).where(
                        CategoryCoreField.category_id == cat_id
                    )
                )
            ).scalars().all()
            for row in existing:
                await self._session.delete(row)
            await self._session.flush()
            for sort_i, field in enumerate(fields):
                key, label, ftype, required, options, hint = field
                if key in {"city", "title", "description", "photos", "region"}:
                    continue
                await self._upsert_core_field(
                    cat_id,
                    key,
                    label,
                    ftype,
                    sort_i,
                    hint,
                    required=required,
                    options=options if options else None,
                )
        await self._session.flush()

    async def _seed_home_garden_search_filters(self) -> None:
        from app.models.category_enums import CategoryFilterType
        from app.seeds.home_garden_filters import build_home_garden_search_filters

        for cat_slug, filters in build_home_garden_search_filters().items():
            cat_id = self._slug_to_id.get(cat_slug)
            if cat_id is None:
                continue
            # Replace set for leaf so retired keys disappear.
            existing = (
                await self._session.execute(
                    select(CategoryFilter).where(CategoryFilter.category_id == cat_id)
                )
            ).scalars().all()
            wanted = {f[0] for f in filters}
            for row in existing:
                if row.filter_key not in wanted:
                    await self._session.delete(row)
            for sort_i, (key, label, ftype, config) in enumerate(filters):
                stmt = select(CategoryFilter).where(
                    CategoryFilter.category_id == cat_id,
                    CategoryFilter.filter_key == key,
                )
                row = (await self._session.execute(stmt)).scalar_one_or_none()
                ft = CategoryFilterType(ftype)
                if row is None:
                    self._session.add(
                        CategoryFilter(
                            category_id=cat_id,
                            filter_key=key,
                            label=label,
                            filter_type=ft,
                            sort_order=sort_i,
                            config=config,
                        )
                    )
                else:
                    row.label = label
                    row.filter_type = ft
                    row.sort_order = sort_i
                    row.config = config

    async def _clear_picker_parent_live_sot(self, parent_id: int | None) -> None:
        """Picker-only parents must not keep competing live Create/Search schema."""
        if parent_id is None:
            return
        for model_cls in (CategoryCoreField, CategoryOptionalField, CategoryFilter):
            existing_parent = (
                await self._session.execute(
                    select(model_cls).where(model_cls.category_id == parent_id)
                )
            ).scalars().all()
            for row in existing_parent:
                await self._session.delete(row)

    async def _retire_jobs_legacy_schemas(self) -> None:
        """Inactive vacancy/resume nodes are not publishable schema homes.

        Aliases stay. jobs root and the 19 sectors are not touched.
        Abroad stays inactive and keeps its existing historical fields.
        Refuses to strip a node that already has listings.
        """
        from sqlalchemy import func

        from app.models.listing import Listing

        for slug in sorted(JOBS_V2_RETIRED_LEGACY_SLUGS):
            row = (
                await self._session.execute(select(Category).where(Category.slug == slug))
            ).scalar_one_or_none()
            if row is None:
                continue
            self._slug_to_id[slug] = row.id
            if row.is_active:
                row.is_active = False
            listing_count = await self._session.scalar(
                select(func.count()).select_from(Listing).where(Listing.category_id == row.id)
            )
            if int(listing_count or 0) > 0:
                raise RuntimeError(
                    f"refusing to retire Jobs legacy schema with listings: {slug}"
                )
            await self._clear_picker_parent_live_sot(row.id)
        await self._session.flush()

    async def _upsert_core_field(
        self,
        cat_id,
        key,
        label,
        ftype,
        sort_order,
        hint,
        *,
        required: bool = True,
        options: dict | None = None,
        create_intent: str | None = None,
    ) -> None:
        stmt = select(CategoryCoreField).where(
            CategoryCoreField.category_id == cat_id,
            CategoryCoreField.field_key == key,
            CategoryCoreField.create_intent.is_(None)
            if create_intent is None
            else CategoryCoreField.create_intent == create_intent,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            self._session.add(
                CategoryCoreField(
                    category_id=cat_id,
                    field_key=key,
                    label=label,
                    field_type=ftype,
                    is_required=required,
                    sort_order=sort_order,
                    ai_hint=hint,
                    options=options,
                    create_intent=create_intent,
                )
            )
        else:
            row.label = label
            row.field_type = ftype
            row.sort_order = sort_order
            row.ai_hint = hint
            row.is_required = required
            row.create_intent = create_intent
            if options is not None:
                row.options = options

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

    async def _seed_services_v2_fields(self) -> None:
        """Services V2 — canonical L2 + Create SoT + Search filters; retire dual tree."""
        from sqlalchemy import func

        from app.models.listing import Listing
        from app.seeds.services_v2 import (
            SERVICES_ROOT_LABEL,
            SERVICES_ROOT_SLUG,
            SERVICES_V2_ALIAS_REMAP,
            SERVICES_V2_CANONICAL_LEAVES,
            SERVICES_V2_CANONICAL_SLUGS,
            SERVICES_V2_ENTITY_TYPE,
            SERVICES_V2_RETIRED_SLUGS,
            build_services_v2_core_fields,
            build_services_v2_search_filters,
        )

        root_id = self._slug_to_id.get(SERVICES_ROOT_SLUG)
        if root_id is None:
            return
        root = (
            await self._session.execute(
                select(Category).where(Category.id == root_id)
            )
        ).scalar_one_or_none()
        if root is None:
            return
        root.name = SERVICES_ROOT_LABEL
        root.is_active = True
        await self._clear_picker_parent_live_sot(root_id)

        for slug, label, sort_order in SERVICES_V2_CANONICAL_LEAVES:
            row = (
                await self._session.execute(
                    select(Category).where(Category.slug == slug)
                )
            ).scalar_one_or_none()
            if row is None:
                row = Category(
                    parent_id=root_id,
                    slug=slug,
                    name=label,
                    entity_type=SERVICES_V2_ENTITY_TYPE,
                    is_active=True,
                    sort_order=sort_order,
                    requires_city=True,
                )
                self._session.add(row)
                await self._session.flush()
            else:
                row.parent_id = root_id
                row.name = label
                row.entity_type = SERVICES_V2_ENTITY_TYPE
                row.is_active = True
                row.sort_order = sort_order
                row.requires_city = True
            self._slug_to_id[slug] = row.id

        await self._session.flush()

        # Retire merged/legacy/out-of-scope Services nodes.
        for slug in sorted(SERVICES_V2_RETIRED_SLUGS):
            row = (
                await self._session.execute(
                    select(Category).where(Category.slug == slug)
                )
            ).scalar_one_or_none()
            if row is None:
                continue
            self._slug_to_id[slug] = row.id
            if row.is_active:
                row.is_active = False
            listing_count = await self._session.scalar(
                select(func.count())
                .select_from(Listing)
                .where(Listing.category_id == row.id)
            )
            # Preserve schema only when historical listings/drafts remain.
            if int(listing_count or 0) == 0:
                await self._clear_picker_parent_live_sot(row.id)

        # Any unexpected active Services L2 outside canonical → deactivate.
        children = (
            await self._session.execute(
                select(Category).where(Category.parent_id == root_id)
            )
        ).scalars().all()
        for ch in children:
            if ch.slug in SERVICES_V2_CANONICAL_SLUGS:
                continue
            if ch.is_active:
                ch.is_active = False
            listing_count = await self._session.scalar(
                select(func.count())
                .select_from(Listing)
                .where(Listing.category_id == ch.id)
            )
            if int(listing_count or 0) == 0:
                await self._clear_picker_parent_live_sot(ch.id)

        core_by_slug = build_services_v2_core_fields()
        filters_by_slug = build_services_v2_search_filters()
        for slug, fields in core_by_slug.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            for model_cls in (
                CategoryCoreField,
                CategoryOptionalField,
                CategoryFilter,
            ):
                existing = (
                    await self._session.execute(
                        select(model_cls).where(model_cls.category_id == cat_id)
                    )
                ).scalars().all()
                for row in existing:
                    await self._session.delete(row)
            await self._session.flush()
            for field in fields:
                key, label, ftype, required, sort, options, hint = field
                if key in {"city", "title", "description", "photos", "region"}:
                    continue
                await self._upsert_core_field(
                    cat_id,
                    key,
                    label,
                    ftype,
                    sort,
                    hint,
                    required=required,
                    options=options,
                )
            for key, label, ftype, sort, config in filters_by_slug.get(slug, []):
                self._session.add(
                    CategoryFilter(
                        category_id=cat_id,
                        filter_key=key,
                        label=label,
                        filter_type=ftype,
                        sort_order=sort,
                        config=config,
                        search_intent="",
                    )
                )

        async def _upsert_alias(alias: str, target_slug: str, *, weight: int = 120) -> None:
            target_id = self._slug_to_id.get(target_slug)
            if target_id is None:
                return
            existing = (
                await self._session.execute(
                    select(CategoryAlias).where(
                        CategoryAlias.alias_normalized == alias,
                        CategoryAlias.locale == self._locale,
                    )
                )
            ).scalar_one_or_none()
            if existing is None:
                self._session.add(
                    CategoryAlias(
                        category_id=target_id,
                        alias=alias,
                        alias_normalized=alias,
                        alias_compact=alias.replace(" ", ""),
                        locale=self._locale,
                        weight=weight,
                        is_enabled=True,
                    )
                )
            else:
                existing.category_id = target_id
                existing.alias = alias
                existing.is_enabled = True
                existing.weight = weight

        for alias, target in SERVICES_V2_ALIAS_REMAP.items():
            await _upsert_alias(alias, target)

        await self._session.flush()

    async def _seed_repair_v2_fields(self) -> None:
        """Repair V2 — 28 goods L2 + Create SoT + Package B Search filters."""
        from sqlalchemy import func

        from app.models.listing import Listing
        from app.seeds.repair_v2 import (
            REPAIR_ROOT_LABEL,
            REPAIR_ROOT_SLUG,
            REPAIR_V2_ALIAS_REMAP,
            REPAIR_V2_CANONICAL_LEAVES,
            REPAIR_V2_CANONICAL_SLUGS,
            REPAIR_V2_ENTITY_TYPE,
            REPAIR_V2_RETIRED_SLUGS,
            build_repair_v2_core_fields,
            build_repair_v2_search_filters,
        )

        root_id = self._slug_to_id.get(REPAIR_ROOT_SLUG)
        if root_id is None:
            return
        root = (
            await self._session.execute(
                select(Category).where(Category.id == root_id)
            )
        ).scalar_one_or_none()
        if root is None:
            return
        root.name = REPAIR_ROOT_LABEL
        root.is_active = True
        await self._clear_picker_parent_live_sot(root_id)

        for slug, label, sort_order in REPAIR_V2_CANONICAL_LEAVES:
            row = (
                await self._session.execute(
                    select(Category).where(Category.slug == slug)
                )
            ).scalar_one_or_none()
            if row is None:
                row = Category(
                    parent_id=root_id,
                    slug=slug,
                    name=label,
                    entity_type=REPAIR_V2_ENTITY_TYPE,
                    is_active=True,
                    sort_order=sort_order,
                    requires_city=True,
                )
                self._session.add(row)
                await self._session.flush()
            else:
                row.parent_id = root_id
                row.name = label
                row.entity_type = REPAIR_V2_ENTITY_TYPE
                row.is_active = True
                row.sort_order = sort_order
                row.requires_city = True
            self._slug_to_id[slug] = row.id

        await self._session.flush()

        for slug in sorted(REPAIR_V2_RETIRED_SLUGS):
            row = (
                await self._session.execute(
                    select(Category).where(Category.slug == slug)
                )
            ).scalar_one_or_none()
            if row is None:
                continue
            self._slug_to_id[slug] = row.id
            if row.is_active:
                row.is_active = False
            listing_count = await self._session.scalar(
                select(func.count())
                .select_from(Listing)
                .where(Listing.category_id == row.id)
            )
            if int(listing_count or 0) == 0:
                await self._clear_picker_parent_live_sot(row.id)

        children = (
            await self._session.execute(
                select(Category).where(Category.parent_id == root_id)
            )
        ).scalars().all()
        for ch in children:
            if ch.slug in REPAIR_V2_CANONICAL_SLUGS:
                continue
            if ch.is_active:
                ch.is_active = False
            listing_count = await self._session.scalar(
                select(func.count())
                .select_from(Listing)
                .where(Listing.category_id == ch.id)
            )
            if int(listing_count or 0) == 0:
                await self._clear_picker_parent_live_sot(ch.id)

        core_by_slug = build_repair_v2_core_fields()
        filters_by_slug = build_repair_v2_search_filters()
        for slug, fields in core_by_slug.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            for model_cls in (
                CategoryCoreField,
                CategoryOptionalField,
                CategoryFilter,
            ):
                existing = (
                    await self._session.execute(
                        select(model_cls).where(model_cls.category_id == cat_id)
                    )
                ).scalars().all()
                for row in existing:
                    await self._session.delete(row)
            await self._session.flush()
            for field in fields:
                key, label, ftype, required, sort, options, hint = field
                if key in {"city", "title", "description", "photos", "region"}:
                    continue
                await self._upsert_core_field(
                    cat_id,
                    key,
                    label,
                    ftype,
                    sort,
                    hint,
                    required=required,
                    options=options,
                )
            for key, label, ftype, sort, config in filters_by_slug.get(slug, []):
                self._session.add(
                    CategoryFilter(
                        category_id=cat_id,
                        filter_key=key,
                        label=label,
                        filter_type=ftype,
                        sort_order=sort,
                        config=config,
                        search_intent="",
                    )
                )

        async def _upsert_alias(alias: str, target_slug: str, *, weight: int = 120) -> None:
            target_id = self._slug_to_id.get(target_slug)
            if target_id is None:
                return
            existing = (
                await self._session.execute(
                    select(CategoryAlias).where(
                        CategoryAlias.alias_normalized == alias,
                        CategoryAlias.locale == self._locale,
                    )
                )
            ).scalar_one_or_none()
            if existing is None:
                self._session.add(
                    CategoryAlias(
                        category_id=target_id,
                        alias=alias,
                        alias_normalized=alias,
                        alias_compact=alias.replace(" ", ""),
                        locale=self._locale,
                        weight=weight,
                        is_enabled=True,
                    )
                )
            else:
                existing.category_id = target_id
                existing.alias = alias
                existing.is_enabled = True
                existing.weight = weight

        for alias, target in REPAIR_V2_ALIAS_REMAP.items():
            await _upsert_alias(alias, target)

        await self._session.flush()

    async def _seed_electronics_v2_fields(self) -> None:
        """Electronics V2 — 19 goods L2 + Create SoT + Package B Search filters."""
        from sqlalchemy import func

        from app.models.listing import Listing
        from app.seeds.electronics_v2 import (
            ELECTRONICS_ROOT_LABEL,
            ELECTRONICS_ROOT_SLUG,
            ELECTRONICS_V2_CANONICAL_LEAVES,
            ELECTRONICS_V2_CANONICAL_SLUGS,
            ELECTRONICS_V2_ENTITY_TYPE,
            ELECTRONICS_V2_RETIRED_SLUGS,
            build_electronics_v2_core_fields,
            build_electronics_v2_search_filters,
        )

        root_id = self._slug_to_id.get(ELECTRONICS_ROOT_SLUG)
        if root_id is None:
            return
        root = (
            await self._session.execute(
                select(Category).where(Category.id == root_id)
            )
        ).scalar_one_or_none()
        if root is None:
            return
        root.name = ELECTRONICS_ROOT_LABEL
        root.is_active = True
        await self._clear_picker_parent_live_sot(root_id)

        for slug, label, sort_order in ELECTRONICS_V2_CANONICAL_LEAVES:
            row = (
                await self._session.execute(
                    select(Category).where(Category.slug == slug)
                )
            ).scalar_one_or_none()
            if row is None:
                row = Category(
                    parent_id=root_id,
                    slug=slug,
                    name=label,
                    entity_type=ELECTRONICS_V2_ENTITY_TYPE,
                    is_active=True,
                    sort_order=sort_order,
                    requires_city=True,
                )
                self._session.add(row)
                await self._session.flush()
            else:
                row.parent_id = root_id
                row.name = label
                row.entity_type = ELECTRONICS_V2_ENTITY_TYPE
                row.is_active = True
                row.sort_order = sort_order
                row.requires_city = True
            self._slug_to_id[slug] = row.id

        await self._session.flush()

        for slug in sorted(ELECTRONICS_V2_RETIRED_SLUGS):
            row = (
                await self._session.execute(
                    select(Category).where(Category.slug == slug)
                )
            ).scalar_one_or_none()
            if row is None:
                continue
            self._slug_to_id[slug] = row.id
            if row.is_active:
                row.is_active = False
            listing_count = await self._session.scalar(
                select(func.count())
                .select_from(Listing)
                .where(Listing.category_id == row.id)
            )
            if int(listing_count or 0) == 0:
                await self._clear_picker_parent_live_sot(row.id)

        children = (
            await self._session.execute(
                select(Category).where(Category.parent_id == root_id)
            )
        ).scalars().all()
        for ch in children:
            if ch.slug in ELECTRONICS_V2_CANONICAL_SLUGS:
                continue
            if ch.is_active:
                ch.is_active = False
            listing_count = await self._session.scalar(
                select(func.count())
                .select_from(Listing)
                .where(Listing.category_id == ch.id)
            )
            if int(listing_count or 0) == 0:
                await self._clear_picker_parent_live_sot(ch.id)

        core_by_slug = build_electronics_v2_core_fields()
        filters_by_slug = build_electronics_v2_search_filters()
        for slug, fields in core_by_slug.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            for model_cls in (
                CategoryCoreField,
                CategoryOptionalField,
                CategoryFilter,
            ):
                existing = (
                    await self._session.execute(
                        select(model_cls).where(model_cls.category_id == cat_id)
                    )
                ).scalars().all()
                for row in existing:
                    await self._session.delete(row)
            await self._session.flush()
            for field in fields:
                key, label, ftype, required, sort, options, hint = field
                if key in {"city", "title", "description", "photos", "region"}:
                    continue
                await self._upsert_core_field(
                    cat_id,
                    key,
                    label,
                    ftype,
                    sort,
                    hint,
                    required=required,
                    options=options if options else None,
                )
            for key, label, ftype, sort, config in filters_by_slug.get(slug, []):
                self._session.add(
                    CategoryFilter(
                        category_id=cat_id,
                        filter_key=key,
                        label=label,
                        filter_type=ftype,
                        sort_order=sort,
                        config=config,
                        search_intent="",
                    )
                )

        await self._session.flush()

    async def _seed_kids_v2_taxonomy_cleanup(self) -> dict[str, int]:
        """Kids V2 taxonomy foundation — single active tree (Create cores via Package A)."""
        from app.models.category_enums import CategoryEntityType
        from app.seeds.kids_v2 import (
            KIDS_ROOT_LABEL,
            KIDS_ROOT_SLUG,
            KIDS_V2_CANONICAL_GOODS_LEAVES,
            KIDS_V2_RETIRED_SLUGS,
        )

        root_id = self._slug_to_id.get(KIDS_ROOT_SLUG)
        if root_id is None:
            return {"retired": 0, "canonical_active": 0}

        root = (
            await self._session.execute(select(Category).where(Category.id == root_id))
        ).scalar_one_or_none()
        if root is None:
            return {"retired": 0, "canonical_active": 0}

        root.name = KIDS_ROOT_LABEL
        root.is_active = True
        root.parent_id = None

        # Root is picker-only: no Create/Search schemas.
        for model_cls in (CategoryCoreField, CategoryOptionalField, CategoryFilter):
            rows = (
                await self._session.execute(
                    select(model_cls).where(model_cls.category_id == root_id)
                )
            ).scalars().all()
            for row in rows:
                await self._session.delete(row)

        retired_n = 0
        for slug in sorted(KIDS_V2_RETIRED_SLUGS):
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            cat = (
                await self._session.execute(select(Category).where(Category.id == cat_id))
            ).scalar_one_or_none()
            if cat is None:
                continue
            if cat.is_active:
                cat.is_active = False
                retired_n += 1
            for model_cls in (CategoryCoreField, CategoryOptionalField, CategoryFilter):
                rows = (
                    await self._session.execute(
                        select(model_cls).where(model_cls.category_id == cat_id)
                    )
                ).scalars().all()
                for row in rows:
                    await self._session.delete(row)

        canonical_active = 0
        for slug, label, sort_order in KIDS_V2_CANONICAL_GOODS_LEAVES:
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            cat = (
                await self._session.execute(select(Category).where(Category.id == cat_id))
            ).scalar_one_or_none()
            if cat is None:
                continue
            cat.name = label
            cat.parent_id = root_id
            cat.sort_order = sort_order
            cat.is_active = True
            cat.entity_type = CategoryEntityType.object
            cat.requires_city = True
            canonical_active += 1
            # Package A: do NOT wipe Create cores here — `_seed_kids_v2_fields` owns them.

        await self._session.flush()
        return {"retired": retired_n, "canonical_active": canonical_active}

    async def _seed_animals_v2_taxonomy_cleanup(self) -> dict[str, int]:
        """Animals V2 — retire legacy triad + vet-services; keep 15 goods L2."""
        from app.seeds.animals_v2 import (
            ANIMALS_ROOT_LABEL,
            ANIMALS_ROOT_SLUG,
            ANIMALS_V2_CANONICAL_LEAVES,
            ANIMALS_V2_CANONICAL_SLUGS,
            ANIMALS_V2_ENTITY_TYPE,
            ANIMALS_V2_RETIRED_SLUGS,
            animals_v2_assert_package_a_contracts,
        )

        animals_v2_assert_package_a_contracts()
        root_id = self._slug_to_id.get(ANIMALS_ROOT_SLUG)
        if root_id is None:
            return {"retired": 0, "canonical_active": 0}

        root = (
            await self._session.execute(select(Category).where(Category.id == root_id))
        ).scalar_one_or_none()
        if root is None:
            return {"retired": 0, "canonical_active": 0}

        root.name = ANIMALS_ROOT_LABEL
        root.is_active = True
        root.parent_id = None
        await self._clear_picker_parent_live_sot(root_id)

        retired_n = 0
        for slug in sorted(ANIMALS_V2_RETIRED_SLUGS):
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                row = (
                    await self._session.execute(
                        select(Category).where(Category.slug == slug)
                    )
                ).scalar_one_or_none()
                if row is None:
                    continue
                cat_id = row.id
                self._slug_to_id[slug] = cat_id
            else:
                row = (
                    await self._session.execute(
                        select(Category).where(Category.id == cat_id)
                    )
                ).scalar_one_or_none()
            if row is None:
                continue
            if row.is_active:
                row.is_active = False
                retired_n += 1
            await self._clear_picker_parent_live_sot(cat_id)

        canonical_active = 0
        for label, slug, sort_order in ANIMALS_V2_CANONICAL_LEAVES:
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                row = (
                    await self._session.execute(
                        select(Category).where(Category.slug == slug)
                    )
                ).scalar_one_or_none()
                if row is None:
                    row = Category(
                        parent_id=root_id,
                        slug=slug,
                        name=label,
                        entity_type=ANIMALS_V2_ENTITY_TYPE,
                        is_active=True,
                        sort_order=sort_order,
                        requires_city=True,
                    )
                    self._session.add(row)
                    await self._session.flush()
                cat_id = row.id
                self._slug_to_id[slug] = cat_id
            cat = (
                await self._session.execute(select(Category).where(Category.id == cat_id))
            ).scalar_one_or_none()
            if cat is None:
                continue
            cat.name = label
            cat.parent_id = root_id
            cat.sort_order = sort_order
            cat.is_active = True
            cat.entity_type = ANIMALS_V2_ENTITY_TYPE
            cat.requires_city = True
            canonical_active += 1

        children = (
            await self._session.execute(
                select(Category).where(Category.parent_id == root_id)
            )
        ).scalars().all()
        for ch in children:
            if ch.slug in ANIMALS_V2_CANONICAL_SLUGS:
                continue
            if ch.is_active:
                ch.is_active = False
                retired_n += 1
            await self._clear_picker_parent_live_sot(ch.id)

        await self._session.flush()
        return {"retired": retired_n, "canonical_active": canonical_active}

    async def _seed_animals_v2_fields(self) -> None:
        """Animals V2 Package A Create cores + Package B Search filters."""
        from app.seeds.animals_v2 import (
            ANIMALS_ROOT_LABEL,
            ANIMALS_ROOT_SLUG,
            ANIMALS_V2_CANONICAL_LEAVES,
            ANIMALS_V2_CANONICAL_SLUGS,
            ANIMALS_V2_ENTITY_TYPE,
            ANIMALS_V2_RETIRED_SLUGS,
            build_animals_v2_core_fields,
            build_animals_v2_search_filters,
        )

        root_id = self._slug_to_id.get(ANIMALS_ROOT_SLUG)
        if root_id is None:
            return
        root = (
            await self._session.execute(select(Category).where(Category.id == root_id))
        ).scalar_one_or_none()
        if root is None:
            return
        root.name = ANIMALS_ROOT_LABEL
        root.is_active = True
        await self._clear_picker_parent_live_sot(root_id)

        for label, slug, sort_order in ANIMALS_V2_CANONICAL_LEAVES:
            row = (
                await self._session.execute(select(Category).where(Category.slug == slug))
            ).scalar_one_or_none()
            if row is None:
                row = Category(
                    parent_id=root_id,
                    slug=slug,
                    name=label,
                    entity_type=ANIMALS_V2_ENTITY_TYPE,
                    is_active=True,
                    sort_order=sort_order,
                    requires_city=True,
                )
                self._session.add(row)
                await self._session.flush()
            else:
                row.parent_id = root_id
                row.name = label
                row.entity_type = ANIMALS_V2_ENTITY_TYPE
                row.is_active = True
                row.sort_order = sort_order
                row.requires_city = True
            self._slug_to_id[slug] = row.id

        await self._session.flush()

        for slug in sorted(ANIMALS_V2_RETIRED_SLUGS):
            row = (
                await self._session.execute(select(Category).where(Category.slug == slug))
            ).scalar_one_or_none()
            if row is None:
                continue
            self._slug_to_id[slug] = row.id
            if row.is_active:
                row.is_active = False
            await self._clear_picker_parent_live_sot(row.id)

        children = (
            await self._session.execute(
                select(Category).where(Category.parent_id == root_id)
            )
        ).scalars().all()
        for ch in children:
            if ch.slug in ANIMALS_V2_CANONICAL_SLUGS:
                continue
            if ch.is_active:
                ch.is_active = False
            await self._clear_picker_parent_live_sot(ch.id)

        core_by_slug = build_animals_v2_core_fields()
        filters_by_slug = build_animals_v2_search_filters()
        for slug, fields in core_by_slug.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            for model_cls in (
                CategoryCoreField,
                CategoryOptionalField,
                CategoryFilter,
            ):
                existing = (
                    await self._session.execute(
                        select(model_cls).where(model_cls.category_id == cat_id)
                    )
                ).scalars().all()
                for row in existing:
                    await self._session.delete(row)
            await self._session.flush()
            for field in fields:
                key, label, ftype, required, sort, options, hint = field
                if key in {"city", "title", "description", "photos", "region"}:
                    continue
                await self._upsert_core_field(
                    cat_id,
                    key,
                    label,
                    ftype,
                    sort,
                    hint,
                    required=required,
                    options=options if options else None,
                )
            for key, label, ftype, sort, config in filters_by_slug.get(slug, []):
                self._session.add(
                    CategoryFilter(
                        category_id=cat_id,
                        filter_key=key,
                        label=label,
                        filter_type=ftype,
                        sort_order=sort,
                        config=config,
                        search_intent="",
                    )
                )

        await self._session.flush()

    async def _seed_food_agri_v2_taxonomy_cleanup(self) -> dict[str, int]:
        """Food/Agri V2 — retire legacy/wholesale/eco/tara; keep edible L2 active."""
        from app.models.category_enums import CategoryEntityType
        from app.seeds.food_agri_v2 import (
            FOOD_AGRI_ROOT_LABEL,
            FOOD_AGRI_ROOT_SLUG,
            FOOD_AGRI_V2_CANONICAL_LEAVES,
            FOOD_AGRI_V2_CANONICAL_SLUGS,
            FOOD_AGRI_V2_RETIRED_SLUGS,
        )

        root_id = self._slug_to_id.get(FOOD_AGRI_ROOT_SLUG)
        if root_id is None:
            return {"retired": 0, "canonical_active": 0}

        root = (
            await self._session.execute(select(Category).where(Category.id == root_id))
        ).scalar_one_or_none()
        if root is None:
            return {"retired": 0, "canonical_active": 0}

        root.name = FOOD_AGRI_ROOT_LABEL
        root.is_active = True
        root.parent_id = None
        await self._clear_picker_parent_live_sot(root_id)

        retired_n = 0
        for slug in sorted(FOOD_AGRI_V2_RETIRED_SLUGS):
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                row = (
                    await self._session.execute(
                        select(Category).where(Category.slug == slug)
                    )
                ).scalar_one_or_none()
                if row is None:
                    continue
                cat_id = row.id
                self._slug_to_id[slug] = cat_id
            else:
                row = (
                    await self._session.execute(
                        select(Category).where(Category.id == cat_id)
                    )
                ).scalar_one_or_none()
            if row is None:
                continue
            if row.is_active:
                row.is_active = False
                retired_n += 1
            await self._clear_picker_parent_live_sot(cat_id)

        canonical_active = 0
        for label, slug, sort_order in FOOD_AGRI_V2_CANONICAL_LEAVES:
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            cat = (
                await self._session.execute(select(Category).where(Category.id == cat_id))
            ).scalar_one_or_none()
            if cat is None:
                continue
            cat.name = label
            cat.parent_id = root_id
            cat.sort_order = sort_order
            cat.is_active = True
            cat.entity_type = CategoryEntityType.food
            cat.requires_city = True
            canonical_active += 1
            # Package A Create cores not seeded here — taxonomy foundation only.
            await self._clear_picker_parent_live_sot(cat_id)

        children = (
            await self._session.execute(
                select(Category).where(Category.parent_id == root_id)
            )
        ).scalars().all()
        for ch in children:
            if ch.slug in FOOD_AGRI_V2_CANONICAL_SLUGS:
                continue
            if ch.is_active:
                ch.is_active = False
                retired_n += 1
            await self._clear_picker_parent_live_sot(ch.id)

        await self._session.flush()
        return {"retired": retired_n, "canonical_active": canonical_active}

    async def _seed_food_agri_v2_fields(self) -> None:
        """Food/Agri V2 — Create SoT + Package B Search filters for 23 edible L2."""
        from app.seeds.food_agri_v2 import (
            FOOD_AGRI_ROOT_LABEL,
            FOOD_AGRI_ROOT_SLUG,
            FOOD_AGRI_V2_CANONICAL_LEAVES,
            FOOD_AGRI_V2_CANONICAL_SLUGS,
            FOOD_AGRI_V2_ENTITY_TYPE,
            FOOD_AGRI_V2_RETIRED_SLUGS,
            build_food_agri_v2_core_fields,
            build_food_agri_v2_search_filters,
        )

        root_id = self._slug_to_id.get(FOOD_AGRI_ROOT_SLUG)
        if root_id is None:
            return
        root = (
            await self._session.execute(select(Category).where(Category.id == root_id))
        ).scalar_one_or_none()
        if root is None:
            return
        root.name = FOOD_AGRI_ROOT_LABEL
        root.is_active = True
        await self._clear_picker_parent_live_sot(root_id)

        for label, slug, sort_order in FOOD_AGRI_V2_CANONICAL_LEAVES:
            row = (
                await self._session.execute(select(Category).where(Category.slug == slug))
            ).scalar_one_or_none()
            if row is None:
                row = Category(
                    parent_id=root_id,
                    slug=slug,
                    name=label,
                    entity_type=FOOD_AGRI_V2_ENTITY_TYPE,
                    is_active=True,
                    sort_order=sort_order,
                    requires_city=True,
                )
                self._session.add(row)
                await self._session.flush()
            else:
                row.parent_id = root_id
                row.name = label
                row.entity_type = FOOD_AGRI_V2_ENTITY_TYPE
                row.is_active = True
                row.sort_order = sort_order
                row.requires_city = True
            self._slug_to_id[slug] = row.id

        await self._session.flush()

        for slug in sorted(FOOD_AGRI_V2_RETIRED_SLUGS):
            row = (
                await self._session.execute(select(Category).where(Category.slug == slug))
            ).scalar_one_or_none()
            if row is None:
                continue
            self._slug_to_id[slug] = row.id
            if row.is_active:
                row.is_active = False
            await self._clear_picker_parent_live_sot(row.id)

        children = (
            await self._session.execute(
                select(Category).where(Category.parent_id == root_id)
            )
        ).scalars().all()
        for ch in children:
            if ch.slug in FOOD_AGRI_V2_CANONICAL_SLUGS:
                continue
            if ch.is_active:
                ch.is_active = False
            await self._clear_picker_parent_live_sot(ch.id)

        core_by_slug = build_food_agri_v2_core_fields()
        filters_by_slug = build_food_agri_v2_search_filters()
        for slug, fields in core_by_slug.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            for model_cls in (
                CategoryCoreField,
                CategoryOptionalField,
                CategoryFilter,
            ):
                existing = (
                    await self._session.execute(
                        select(model_cls).where(model_cls.category_id == cat_id)
                    )
                ).scalars().all()
                for row in existing:
                    await self._session.delete(row)
            await self._session.flush()
            for field in fields:
                key, label, ftype, required, sort, options, hint = field
                if key in {"city", "title", "description", "photos", "region"}:
                    continue
                await self._upsert_core_field(
                    cat_id,
                    key,
                    label,
                    ftype,
                    sort,
                    hint,
                    required=required,
                    options=options if options else None,
                )
            for key, label, ftype, sort, config in filters_by_slug.get(slug, []):
                self._session.add(
                    CategoryFilter(
                        category_id=cat_id,
                        filter_key=key,
                        label=label,
                        filter_type=ftype,
                        sort_order=sort,
                        config=config,
                        search_intent="",
                    )
                )

        await self._session.flush()

    async def _seed_kids_v2_fields(self) -> None:
        """Kids V2 — 16 goods L2 Create SoT + Package B Search filters."""
        from app.seeds.kids_v2 import (
            KIDS_ROOT_LABEL,
            KIDS_ROOT_SLUG,
            KIDS_V2_CANONICAL_GOODS_LEAVES,
            KIDS_V2_CANONICAL_GOODS_SLUGS,
            KIDS_V2_ENTITY_TYPE,
            KIDS_V2_RETIRED_SLUGS,
            build_kids_v2_core_fields,
            build_kids_v2_search_filters,
        )

        root_id = self._slug_to_id.get(KIDS_ROOT_SLUG)
        if root_id is None:
            return
        root = (
            await self._session.execute(select(Category).where(Category.id == root_id))
        ).scalar_one_or_none()
        if root is None:
            return
        root.name = KIDS_ROOT_LABEL
        root.is_active = True
        await self._clear_picker_parent_live_sot(root_id)

        for slug, label, sort_order in KIDS_V2_CANONICAL_GOODS_LEAVES:
            row = (
                await self._session.execute(select(Category).where(Category.slug == slug))
            ).scalar_one_or_none()
            if row is None:
                row = Category(
                    parent_id=root_id,
                    slug=slug,
                    name=label,
                    entity_type=KIDS_V2_ENTITY_TYPE,
                    is_active=True,
                    sort_order=sort_order,
                    requires_city=True,
                )
                self._session.add(row)
                await self._session.flush()
            else:
                row.parent_id = root_id
                row.name = label
                row.entity_type = KIDS_V2_ENTITY_TYPE
                row.is_active = True
                row.sort_order = sort_order
                row.requires_city = True
            self._slug_to_id[slug] = row.id

        await self._session.flush()

        for slug in sorted(KIDS_V2_RETIRED_SLUGS):
            row = (
                await self._session.execute(select(Category).where(Category.slug == slug))
            ).scalar_one_or_none()
            if row is None:
                continue
            self._slug_to_id[slug] = row.id
            if row.is_active:
                row.is_active = False
            await self._clear_picker_parent_live_sot(row.id)

        children = (
            await self._session.execute(
                select(Category).where(Category.parent_id == root_id)
            )
        ).scalars().all()
        for ch in children:
            if ch.slug in KIDS_V2_CANONICAL_GOODS_SLUGS:
                continue
            if ch.is_active:
                ch.is_active = False
            await self._clear_picker_parent_live_sot(ch.id)

        core_by_slug = build_kids_v2_core_fields()
        filters_by_slug = build_kids_v2_search_filters()
        for slug, fields in core_by_slug.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            for model_cls in (
                CategoryCoreField,
                CategoryOptionalField,
                CategoryFilter,
            ):
                existing = (
                    await self._session.execute(
                        select(model_cls).where(model_cls.category_id == cat_id)
                    )
                ).scalars().all()
                for row in existing:
                    await self._session.delete(row)
            await self._session.flush()
            for field in fields:
                key, label, ftype, required, sort, options, hint = field
                if key in {"city", "title", "description", "photos", "region"}:
                    continue
                await self._upsert_core_field(
                    cat_id,
                    key,
                    label,
                    ftype,
                    sort,
                    hint,
                    required=required,
                    options=options if options else None,
                )
            for key, label, ftype, sort, config in filters_by_slug.get(slug, []):
                self._session.add(
                    CategoryFilter(
                        category_id=cat_id,
                        filter_key=key,
                        label=label,
                        filter_type=ftype,
                        sort_order=sort,
                        config=config,
                        search_intent="",
                    )
                )

        await self._session.flush()

    async def _seed_fashion_v2_fields(self) -> None:
        """Fashion V2 — 17 goods L2 + Create SoT + Package B Search filters."""
        from sqlalchemy import func

        from app.models.listing import Listing
        from app.seeds.fashion_v2 import (
            FASHION_ROOT_LABEL,
            FASHION_ROOT_SLUG,
            FASHION_V2_CANONICAL_LEAVES,
            FASHION_V2_CANONICAL_SLUGS,
            FASHION_V2_ENTITY_TYPE,
            FASHION_V2_RETIRED_SLUGS,
            build_fashion_v2_core_fields,
            build_fashion_v2_search_filters,
        )

        root_id = self._slug_to_id.get(FASHION_ROOT_SLUG)
        if root_id is None:
            return
        root = (
            await self._session.execute(
                select(Category).where(Category.id == root_id)
            )
        ).scalar_one_or_none()
        if root is None:
            return
        root.name = FASHION_ROOT_LABEL
        root.is_active = True
        await self._clear_picker_parent_live_sot(root_id)

        for slug, label, sort_order in FASHION_V2_CANONICAL_LEAVES:
            row = (
                await self._session.execute(
                    select(Category).where(Category.slug == slug)
                )
            ).scalar_one_or_none()
            if row is None:
                row = Category(
                    parent_id=root_id,
                    slug=slug,
                    name=label,
                    entity_type=FASHION_V2_ENTITY_TYPE,
                    is_active=True,
                    sort_order=sort_order,
                    requires_city=True,
                )
                self._session.add(row)
                await self._session.flush()
            else:
                row.parent_id = root_id
                row.name = label
                row.entity_type = FASHION_V2_ENTITY_TYPE
                row.is_active = True
                row.sort_order = sort_order
                row.requires_city = True
            self._slug_to_id[slug] = row.id

        await self._session.flush()

        for slug in sorted(FASHION_V2_RETIRED_SLUGS):
            row = (
                await self._session.execute(
                    select(Category).where(Category.slug == slug)
                )
            ).scalar_one_or_none()
            if row is None:
                continue
            self._slug_to_id[slug] = row.id
            if row.is_active:
                row.is_active = False
            listing_count = await self._session.scalar(
                select(func.count())
                .select_from(Listing)
                .where(Listing.category_id == row.id)
            )
            if int(listing_count or 0) == 0:
                await self._clear_picker_parent_live_sot(row.id)

        children = (
            await self._session.execute(
                select(Category).where(Category.parent_id == root_id)
            )
        ).scalars().all()
        for ch in children:
            if ch.slug in FASHION_V2_CANONICAL_SLUGS:
                continue
            if ch.is_active:
                ch.is_active = False
            listing_count = await self._session.scalar(
                select(func.count())
                .select_from(Listing)
                .where(Listing.category_id == ch.id)
            )
            if int(listing_count or 0) == 0:
                await self._clear_picker_parent_live_sot(ch.id)

        core_by_slug = build_fashion_v2_core_fields()
        filters_by_slug = build_fashion_v2_search_filters()
        for slug, fields in core_by_slug.items():
            cat_id = self._slug_to_id.get(slug)
            if cat_id is None:
                continue
            for model_cls in (
                CategoryCoreField,
                CategoryOptionalField,
                CategoryFilter,
            ):
                existing = (
                    await self._session.execute(
                        select(model_cls).where(model_cls.category_id == cat_id)
                    )
                ).scalars().all()
                for row in existing:
                    await self._session.delete(row)
            await self._session.flush()
            for field in fields:
                key, label, ftype, required, sort, options, hint = field
                if key in {"city", "title", "description", "photos", "region"}:
                    continue
                await self._upsert_core_field(
                    cat_id,
                    key,
                    label,
                    ftype,
                    sort,
                    hint,
                    required=required,
                    options=options if options else None,
                )
            for key, label, ftype, sort, config in filters_by_slug.get(slug, []):
                self._session.add(
                    CategoryFilter(
                        category_id=cat_id,
                        filter_key=key,
                        label=label,
                        filter_type=ftype,
                        sort_order=sort,
                        config=config,
                        search_intent="",
                    )
                )

        await self._session.flush()

    async def _seed_filters(self) -> None:
        for cat_slug, filters in SEARCH_FILTERS.items():
            if cat_slug in _RETIRED_CATEGORY_SLUGS:
                continue
            if cat_slug == "services" or str(cat_slug).startswith("services-"):
                # Services Search filters deferred to Package B.
                continue
            if (
                cat_slug == "repair-construction"
                or str(cat_slug).startswith("repair-construction-")
                or cat_slug in REPAIR_V2_RETIRED_SLUGS
            ):
                # Repair Search filters deferred to Package B.
                continue
            if (
                cat_slug == "electronics"
                or str(cat_slug).startswith("electronics-")
                or cat_slug in ELECTRONICS_V2_RETIRED_SLUGS
            ):
                # Electronics Search filters: Package B via _seed_electronics_v2_fields.
                continue
            if (
                cat_slug == "fashion"
                or str(cat_slug).startswith("fashion-")
                or cat_slug in FASHION_V2_RETIRED_SLUGS
            ):
                # Fashion Search filters: Package B via _seed_fashion_v2_fields.
                continue
            if (
                cat_slug == "kids"
                or str(cat_slug).startswith("kids-")
                or cat_slug in KIDS_V2_RETIRED_SLUGS
            ):
                # Kids Search filters: Package B via _seed_kids_v2_fields.
                continue
            if (
                cat_slug == "food-agri"
                or str(cat_slug).startswith("food-agri-")
                or cat_slug in FOOD_AGRI_V2_RETIRED_SLUGS
            ):
                # Food/Agri Search filters: Package B later.
                continue
            if (
                cat_slug == "animals"
                or str(cat_slug).startswith("animals-")
                or cat_slug in ANIMALS_V2_RETIRED_SLUGS
            ):
                # Animals Search filters: Package B via _seed_animals_v2_fields.
                continue
            if cat_slug == "transport-car-sale":
                continue
            if cat_slug.startswith("transport-moto-tech-"):
                # Leaf Search SoT: moto_sale_v2 / electric re-parented leaves.
                continue
            if cat_slug.startswith("transport-electric-"):
                # Leaf Search SoT: electric_sale_v2 overlay (not thin SEARCH_FILTERS).
                continue
            if cat_slug.startswith("transport-bicycles-"):
                # Leaf Search SoT: bicycle_sale_v2 overlay.
                continue
            if cat_slug == "transport-bicycles":
                # Parent thin filters are legacy — leaf SoT wins for Create/Search.
                continue
            if cat_slug in {
                "transport-buses-microbuses-motorhomes",
                "transport-commercial-avtobusy",
                "transport-commercial-mikroavtobusy",
                "transport-buses-avtodoma",
            }:
                # Bus V2 leaf Search SoT: bus_sale_v2 overlay.
                continue
            if cat_slug == "transport-special-equipment" or cat_slug.startswith(
                "transport-special-equipment-"
            ):
                # Special Equipment V2 leaf Search SoT: special_sale_v2 overlay.
                continue
            if cat_slug == "transport-cargo" or cat_slug.startswith(
                "transport-cargo-"
            ):
                # Cargo V2 leaf Search SoT: cargo_sale_v2 overlay.
                continue
            if cat_slug == "transport-watercraft" or cat_slug.startswith(
                "transport-watercraft-"
            ):
                # Water V2 leaf Search SoT: water_sale_v2 overlay.
                continue
            if cat_slug == "transport-trailers" or cat_slug.startswith(
                "transport-trailers-"
            ):
                # Trailers V2 leaf Search SoT: trailer_sale_v2 overlay.
                continue
            if cat_slug == "transport-farm-machinery" or cat_slug.startswith(
                "transport-farm-machinery-"
            ):
                # Farm V2 leaf Search SoT: farm_sale_v2 overlay.
                continue
            if cat_slug == "transport-rental" or cat_slug.startswith(
                "transport-rental-"
            ):
                # Rental V2 leaf Search SoT: transport_rental_v2 overlay.
                continue
            if cat_slug == "transport-auto-parts" or cat_slug.startswith(
                "transport-auto-parts-"
            ):
                # Auto Parts V2 leaf Search SoT: auto_parts_v2 overlay.
                continue
            if cat_slug == "transport-tires-wheels" or cat_slug.startswith(
                "transport-tires-wheels-"
            ):
                continue
            if cat_slug == "transport-accessories-tuning" or cat_slug.startswith(
                "transport-accessories-tuning-"
            ):
                continue
            if cat_slug == "transport-auto-services" or cat_slug.startswith(
                "transport-auto-services-"
            ):
                continue
            if cat_slug in {
                "transport-moto-tech",
                "transport-electric",
            }:
                continue
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

    async def _seed_parts_vehicle_catalogs(
        self, brand_ids: dict[str, int]
    ) -> dict[str, int]:
        brands_added = 0
        models_added = 0

        for slug, name, country, vtype in PARTS_CATALOG_BRANDS:
            if slug.strip().lower() in _FORBIDDEN_BRAND_SLUGS:
                logger.warning(
                    "[SeedVehicles] refusing parts brand slug=%s (alias/model nickname)",
                    slug,
                )
                continue
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
                brands_added += 1
            else:
                row.name = name
                row.country_origin = country
                row.vehicle_type = vtype
                row.is_enabled = True
            brand_ids[slug] = row.id

        for slug, name, country, vtype in (
            *CARGO_PARTS_TRUCK_BRANDS,
            *MOTO_SALE_BRANDS,
            *ELECTRIC_SALE_BRANDS,
            *BICYCLE_SALE_BRANDS,
            *CARGO_SALE_BRANDS,
            *BUS_SALE_BRANDS,
            *SPECIAL_SALE_BRANDS,
            *FARM_SALE_BRANDS,
            *WATER_SALE_BRANDS,
            *BOAT_MOTOR_BRANDS,
            *TRAILER_SALE_BRANDS,
        ):
            if slug.strip().lower() in _FORBIDDEN_BRAND_SLUGS:
                logger.warning(
                    "[SeedVehicles] refusing sale brand slug=%s (alias/model nickname)",
                    slug,
                )
                continue
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
                brands_added += 1
            else:
                row.name = name
                row.country_origin = country
                row.vehicle_type = vtype
                row.is_enabled = True
            brand_ids[slug] = row.id

        model_maps = (
            PARTS_CATALOG_MODELS,
            TRUCK_CATALOG_MODELS,
            CARGO_LCV_PARTS_MODELS,
            MOTO_SALE_MODELS,
            ELECTRIC_SALE_MODELS,
            BICYCLE_SALE_MODELS,
            CARGO_SALE_MODELS,
            BUS_SALE_MODELS,
            SPECIAL_SALE_MODELS,
            FARM_SALE_MODELS,
            WATER_SALE_MODELS,
            BOAT_MOTOR_MODELS,
            TRAILER_SALE_MODELS,
        )
        for model_map in model_maps:
            for brand_slug, models in model_map.items():
                brand_id = brand_ids.get(brand_slug)
                if brand_id is None:
                    stmt = select(VehicleBrand).where(VehicleBrand.slug == brand_slug)
                    existing = (
                        await self._session.execute(stmt)
                    ).scalar_one_or_none()
                    if existing is None:
                        continue
                    brand_id = existing.id
                    brand_ids[brand_slug] = brand_id
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

        for bad_slug in (
            *JET_SKI_DISABLE_BRAND_SLUGS,
            *OTHER_WATERCRAFT_DISABLE_BRAND_SLUGS,
            *FARM_DISABLE_BRAND_SLUGS,
        ):
            stmt = select(VehicleBrand).where(VehicleBrand.slug == bad_slug)
            bad = (await self._session.execute(stmt)).scalar_one_or_none()
            if bad is not None:
                bad.is_enabled = False

        for brand_slug, model_slugs in FARM_DISABLE_MODELS_BY_BRAND.items():
            brand = (
                await self._session.execute(
                    select(VehicleBrand).where(VehicleBrand.slug == brand_slug)
                )
            ).scalar_one_or_none()
            if brand is None:
                continue
            for model_slug in model_slugs:
                model = (
                    await self._session.execute(
                        select(VehicleModel).where(
                            VehicleModel.brand_id == brand.id,
                            VehicleModel.slug == model_slug,
                        )
                    )
                ).scalar_one_or_none()
                if model is not None:
                    model.is_enabled = False

        # Re-apply after brand upsert: vehicle seed re-enables rows that
        # farm_sale_v2 already marked as model-as-brand / equipment pollution.
        from app.seeds.farm_sale_v2 import FARM_POLLUTED_BRAND_NAMES

        for name in FARM_POLLUTED_BRAND_NAMES:
            rows = (
                await self._session.execute(
                    select(VehicleBrand).where(VehicleBrand.name == name)
                )
            ).scalars().all()
            for brand in rows:
                brand.is_enabled = False

        logger.info(
            "[SeedVehicles] parts catalogs brands_added=%s models_added=%s",
            brands_added,
            models_added,
        )
        return {"brands_added": brands_added, "models_added": models_added}

    async def _seed_mobile_vehicle_catalog(self, brand_ids: dict[str, int]) -> dict[str, int]:
        brands_added = 0
        models_added = 0

        for slug, name in MOBILE_VEHICLE_BRANDS:
            if slug.strip().lower() in _FORBIDDEN_BRAND_SLUGS:
                logger.warning(
                    "[SeedVehicles] refusing mobile brand slug=%s (alias/model nickname)",
                    slug,
                )
                continue
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
            blocked = TRUCK_PARTS_DISABLED_MODELS.get(brand_slug, frozenset())
            for model_slug, model_name in models:
                # Keep passenger/SUV pollution off truck brands (cargo parts SoT).
                if model_slug in blocked:
                    stmt = select(VehicleModel).where(
                        VehicleModel.brand_id == brand_id,
                        VehicleModel.slug == model_slug,
                    )
                    row = (await self._session.execute(stmt)).scalar_one_or_none()
                    if row is not None:
                        row.is_enabled = False
                    continue
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

    async def _sanitize_cargo_parts_catalog(
        self, brand_ids: dict[str, int]
    ) -> dict[str, int]:
        """Disable non-truck models on truck brands; ensure LCV execution rows."""
        disabled = 0
        executions_added = 0

        for brand_slug, model_slugs in TRUCK_PARTS_DISABLED_MODELS.items():
            brand_id = brand_ids.get(brand_slug)
            if brand_id is None:
                stmt = select(VehicleBrand).where(VehicleBrand.slug == brand_slug)
                brand = (await self._session.execute(stmt)).scalar_one_or_none()
                if brand is None:
                    continue
                brand_id = brand.id
                brand_ids[brand_slug] = brand_id
            rows = (
                await self._session.execute(
                    select(VehicleModel).where(
                        VehicleModel.brand_id == brand_id,
                        VehicleModel.slug.in_(sorted(model_slugs)),
                    )
                )
            ).scalars().all()
            for row in rows:
                if row.is_enabled:
                    row.is_enabled = False
                    disabled += 1

        for brand_slug, model_slug in APPROVED_MODEL_EXECUTIONS:
            brand_id = brand_ids.get(brand_slug)
            if brand_id is None:
                continue
            model = (
                await self._session.execute(
                    select(VehicleModel).where(
                        VehicleModel.brand_id == brand_id,
                        VehicleModel.slug == model_slug,
                    )
                )
            ).scalar_one_or_none()
            if model is None:
                continue
            model.is_enabled = True
            for execution in APPROVED_MODEL_EXECUTIONS[(brand_slug, model_slug)]:
                exists = (
                    await self._session.execute(
                        select(VehicleModelAllowedExecution).where(
                            VehicleModelAllowedExecution.model_id == model.id,
                            VehicleModelAllowedExecution.execution == execution,
                        )
                    )
                ).scalar_one_or_none()
                if exists is None:
                    self._session.add(
                        VehicleModelAllowedExecution(
                            model_id=model.id,
                            execution=execution,
                        )
                    )
                    executions_added += 1

        logger.info(
            "[SeedVehicles] cargo parts sanitize disabled=%s executions_added=%s",
            disabled,
            executions_added,
        )
        return {"models_disabled": disabled, "executions_added": executions_added}

    async def _seed_vehicles(self) -> dict[str, int]:
        brand_ids: dict[str, int] = {}
        model_count = 0
        aliases_added = 0
        aliases_updated = 0
        aliases_conflicts = 0

        for slug, name, country, vtype in BRANDS:
            if slug.strip().lower() in _FORBIDDEN_BRAND_SLUGS:
                logger.warning(
                    "[SeedVehicles] refusing brand slug=%s (alias/model nickname)",
                    slug,
                )
                continue
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

        # Parts applicability catalogs (bus / special / agri / moto / …)
        # + missing truck models for existing truck brands.
        parts_stats = await self._seed_parts_vehicle_catalogs(brand_ids)
        model_count += parts_stats["models_added"]

        mobile_stats = await self._seed_mobile_vehicle_catalog(brand_ids)
        model_count += mobile_stats["models_added"]

        cargo_sanitize = await self._sanitize_cargo_parts_catalog(brand_ids)

        # Bus V2: keep cargo-only models out of live microbus pickers.
        from app.seeds.bus_sale_v2 import MICROBUS_CARGO_MODEL_KEYS

        for brand_slug, model_slug in MICROBUS_CARGO_MODEL_KEYS:
            bid = brand_ids.get(brand_slug)
            if bid is None:
                brand_row = (
                    await self._session.execute(
                        select(VehicleBrand).where(VehicleBrand.slug == brand_slug)
                    )
                ).scalar_one_or_none()
                if brand_row is None:
                    continue
                bid = brand_row.id
            model = (
                await self._session.execute(
                    select(VehicleModel).where(
                        VehicleModel.brand_id == bid,
                        VehicleModel.slug == model_slug,
                    )
                )
            ).scalar_one_or_none()
            if model is not None and model.is_enabled:
                model.is_enabled = False

        await self._session.flush()

        # Quarantine any leftover alias-as-brand rows so re-seed stays clean.
        disabled_alias_brands = await self._quarantine_alias_brands()

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
            "alias_brands_disabled": disabled_alias_brands,
        }

    async def _quarantine_alias_brands(self) -> int:
        """Disable brands whose slug is a known model alias / nickname."""
        stmt = select(VehicleBrand).where(
            VehicleBrand.is_enabled.is_(True),
            VehicleBrand.slug.in_(sorted(_FORBIDDEN_BRAND_SLUGS)),
        )
        rows = list((await self._session.execute(stmt)).scalars().all())
        for row in rows:
            logger.warning(
                "[SeedVehicles] disabling alias-as-brand slug=%s name=%s id=%s",
                row.slug,
                row.name,
                row.id,
            )
            row.is_enabled = False
            models = (
                await self._session.execute(
                    select(VehicleModel).where(VehicleModel.brand_id == row.id)
                )
            ).scalars().all()
            for model in models:
                model.is_enabled = False
        return len(rows)

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
