"""Special Equipment Sale V2: leaf schemas + catalog hygiene + aliases.

Revision ID: d4e5f6a7b8c9specv2
Revises: a1b2c3d4e5f6busv2
Create Date: 2026-11-02

- Seed leaf core_fields + filters for 18 active Special Equipment leaves
- Keep legacy Road Equipment / Special Trucks / Special Evacuator inactive
- Normalize manipulator primary catalog to chassis; crane OEM disabled for picker
- Upsert Другая марка per typed special vehicle_type
- Sale-phrase evacuator aliases → Cargo evacuators; bare «эвакуатор» stays Services
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

from app.seeds.special_sale_catalogs import SPECIAL_SALE_BRANDS, SPECIAL_SALE_MODELS
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

revision = "d4e5f6a7b8c9specv2"
down_revision = "a1b2c3d4e5f6busv2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    parent = bind.execute(
        text("SELECT id FROM categories WHERE slug = :s"),
        {"s": SPECIAL_PARENT_SLUG},
    ).fetchone()
    if parent is None:
        raise RuntimeError(f"Missing parent {SPECIAL_PARENT_SLUG}")
    parent_id = int(parent[0])

    bind.execute(
        text(
            """
            UPDATE categories
            SET is_active = true, updated_at = now()
            WHERE id = :pid
            """
        ),
        {"pid": parent_id},
    )

    for slug, label in SPECIAL_LEAF_LABELS.items():
        sort = SPECIAL_LEAF_SORT[slug]
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :s"),
            {"s": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Special leaf missing: {slug}")
        bind.execute(
            text(
                """
                UPDATE categories
                SET parent_id = :pid,
                    name = :label,
                    is_active = true,
                    sort_order = :sort,
                    updated_at = now()
                WHERE slug = :slug
                """
            ),
            {
                "pid": parent_id,
                "label": label,
                "sort": sort,
                "slug": slug,
            },
        )

    for slug in SPECIAL_INACTIVE_LEGACY_SLUGS:
        bind.execute(
            text(
                """
                UPDATE categories
                SET is_active = false, updated_at = now()
                WHERE slug = :slug AND is_active = true
                """
            ),
            {"slug": slug},
        )

    def _upsert_alias(alias: str, target_slug: str, *, weight: int = 100) -> None:
        target = bind.execute(
            text("SELECT id FROM categories WHERE slug = :s"),
            {"s": target_slug},
        ).fetchone()
        if target is None:
            return
        cid = int(target[0])
        existing = bind.execute(
            text(
                """
                SELECT id FROM category_aliases
                WHERE alias_normalized = :a AND locale = 'ru'
                LIMIT 1
                """
            ),
            {"a": alias},
        ).fetchone()
        if existing is not None:
            bind.execute(
                text(
                    """
                    UPDATE category_aliases
                    SET category_id = :cid,
                        alias = :alias,
                        is_enabled = true,
                        weight = :w,
                        updated_at = now()
                    WHERE id = :id
                    """
                ),
                {"cid": cid, "alias": alias, "w": weight, "id": int(existing[0])},
            )
        else:
            bind.execute(
                text(
                    """
                    INSERT INTO category_aliases
                    (category_id, alias, alias_normalized, alias_compact, locale,
                     weight, is_enabled, created_at, updated_at)
                    VALUES
                    (:cid, :alias, :alias, :alias, 'ru',
                     :w, true, now(), now())
                    """
                ),
                {"cid": cid, "alias": alias, "w": weight},
            )

    for alias, leaf_slug in SPECIAL_LEAF_ALIASES.items():
        _upsert_alias(alias, leaf_slug)

    for alias, leaf_slug in EVACUATOR_SALE_ALIASES.items():
        _upsert_alias(alias, leaf_slug, weight=120)

    # Keep bare «эвакуатор» on Services if present (do not retarget).
    services_transport = bind.execute(
        text("SELECT id FROM categories WHERE slug = 'services-transport'")
    ).fetchone()
    if services_transport is not None:
        bare = bind.execute(
            text(
                """
                SELECT id, category_id FROM category_aliases
                WHERE alias_normalized = 'эвакуатор' AND locale = 'ru'
                LIMIT 1
                """
            )
        ).fetchone()
        if bare is not None:
            # Leave as-is if already services; only ensure enabled.
            bind.execute(
                text(
                    """
                    UPDATE category_aliases
                    SET is_enabled = true, updated_at = now()
                    WHERE id = :id
                    """
                ),
                {"id": int(bare[0])},
            )

    for slug, fields in SPECIAL_CORE_FIELDS_BY_SLUG.items():
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :s"),
            {"s": slug},
        ).fetchone()
        cid = int(row[0])
        bind.execute(
            text("DELETE FROM category_core_fields WHERE category_id = :cid"),
            {"cid": cid},
        )
        bind.execute(
            text("DELETE FROM category_optional_fields WHERE category_id = :cid"),
            {"cid": cid},
        )
        bind.execute(
            text("DELETE FROM category_filters WHERE category_id = :cid"),
            {"cid": cid},
        )
        for key, label, ftype, required, sort, options, hint in fields:
            ftype_val = ftype.value if hasattr(ftype, "value") else str(ftype)
            opts_json = json.dumps(options, ensure_ascii=False) if options else None
            bind.execute(
                text(
                    """
                    INSERT INTO category_core_fields
                    (category_id, field_key, label, field_type, is_required,
                     sort_order, options, ai_hint, create_intent, created_at, updated_at)
                    VALUES
                    (:cid, :key, :label, CAST(:ftype AS category_field_type_enum),
                     :req, :sort, CAST(:opts AS jsonb), :hint, NULL, now(), now())
                    """
                ),
                {
                    "cid": cid,
                    "key": key,
                    "label": label,
                    "ftype": ftype_val,
                    "req": required,
                    "sort": sort,
                    "opts": opts_json,
                    "hint": hint,
                },
            )
        for key, label, ftype, sort, config in SPECIAL_SEARCH_FILTERS_BY_SLUG[slug]:
            ftype_val = ftype.value if hasattr(ftype, "value") else str(ftype)
            cfg_json = json.dumps(config, ensure_ascii=False) if config else None
            bind.execute(
                text(
                    """
                    INSERT INTO category_filters
                    (category_id, filter_key, label, filter_type, sort_order,
                     config, search_intent, created_at, updated_at)
                    VALUES
                    (:cid, :key, :label, CAST(:ftype AS category_filter_type_enum),
                     :sort, CAST(:cfg AS jsonb), '', now(), now())
                    """
                ),
                {
                    "cid": cid,
                    "key": key,
                    "label": label,
                    "ftype": ftype_val,
                    "sort": sort,
                    "cfg": cfg_json,
                },
            )

    def _upsert_brand(slug: str, name: str, country: str | None, vtype_val: str) -> None:
        existing = bind.execute(
            text("SELECT id FROM vehicle_brands WHERE slug = :s"),
            {"s": slug},
        ).fetchone()
        if existing is None:
            bind.execute(
                text(
                    """
                    INSERT INTO vehicle_brands
                    (slug, name, country_origin, vehicle_type, is_enabled,
                     created_at, updated_at)
                    VALUES
                    (:slug, :name, :country,
                     CAST(:vt AS vehicle_type_enum), true, now(), now())
                    """
                ),
                {
                    "slug": slug,
                    "name": name,
                    "country": country,
                    "vt": vtype_val,
                },
            )
        else:
            bind.execute(
                text(
                    """
                    UPDATE vehicle_brands
                    SET name = :name,
                        country_origin = :country,
                        vehicle_type = CAST(:vt AS vehicle_type_enum),
                        is_enabled = true,
                        updated_at = now()
                    WHERE slug = :slug
                    """
                ),
                {
                    "slug": slug,
                    "name": name,
                    "country": country,
                    "vt": vtype_val,
                },
            )

    # Upsert existing special sale catalogs (typed).
    for slug, name, country, vtype in SPECIAL_SALE_BRANDS:
        vtype_val = vtype.value if hasattr(vtype, "value") else str(vtype)
        # Skip crane OEM rows that will be disabled for manipulator primary.
        if slug in MANIPULATOR_CRANE_OEM_BRAND_SLUGS:
            continue
        _upsert_brand(slug, name, country, vtype_val)

    for slug, name, country, vtype in MANIPULATOR_CHASSIS_BRANDS:
        vtype_val = vtype.value if hasattr(vtype, "value") else str(vtype)
        _upsert_brand(slug, name, country, vtype_val)

    for slug, name, country, vtype_str in special_other_brands():
        _upsert_brand(slug, name, country, vtype_str)

    # Disable crane OEM brands in primary manipulator catalog (preserve IDs).
    for slug in MANIPULATOR_CRANE_OEM_BRAND_SLUGS:
        bind.execute(
            text(
                """
                UPDATE vehicle_brands
                SET is_enabled = false, updated_at = now()
                WHERE slug = :slug AND vehicle_type = CAST('manipulator' AS vehicle_type_enum)
                """
            ),
            {"slug": slug},
        )

    all_models = dict(SPECIAL_SALE_MODELS)
    all_models.update(MANIPULATOR_CHASSIS_MODELS)
    all_models.update(special_other_models())
    for brand_slug, models in all_models.items():
        if brand_slug in MANIPULATOR_CRANE_OEM_BRAND_SLUGS:
            continue
        brand = bind.execute(
            text("SELECT id FROM vehicle_brands WHERE slug = :s"),
            {"s": brand_slug},
        ).fetchone()
        if brand is None:
            continue
        brand_id = int(brand[0])
        for model_slug, model_name in models:
            m = bind.execute(
                text(
                    """
                    SELECT id FROM vehicle_models
                    WHERE brand_id = :bid AND slug = :ms
                    """
                ),
                {"bid": brand_id, "ms": model_slug},
            ).fetchone()
            if m is None:
                bind.execute(
                    text(
                        """
                        INSERT INTO vehicle_models
                        (brand_id, slug, name, is_enabled, created_at, updated_at)
                        VALUES (:bid, :ms, :mn, true, now(), now())
                        """
                    ),
                    {"bid": brand_id, "ms": model_slug, "mn": model_name},
                )
            else:
                bind.execute(
                    text(
                        """
                        UPDATE vehicle_models
                        SET name = :mn, is_enabled = true, updated_at = now()
                        WHERE id = :id
                        """
                    ),
                    {"mn": model_name, "id": int(m[0])},
                )


def downgrade() -> None:
    pass
