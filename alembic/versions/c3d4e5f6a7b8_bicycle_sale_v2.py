"""Bicycle Sale V2: leaf schemas + catalog cleanup + alias fix.

Revision ID: c3d4e5f6a7b8
Revises: b1c2d3e4f5a6
Create Date: 2026-11-02

- Seed leaf core_fields + filters for 7 active bicycle leaves
- Keep kids/folding/parts/accessories/service inactive
- Disable fake Gravel/Fixie brands; upsert typed catalogs + Другая марка
- Reassign alias «велосипед» from sports-equipment → transport-bicycles
- Do NOT create Gravel leaf; e-bike stays under bicycles
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

from app.seeds.bicycle_sale_catalogs import BICYCLE_SALE_BRANDS, BICYCLE_SALE_MODELS
from app.seeds.bicycle_sale_v2 import (
    BICYCLE_CORE_FIELDS_BY_SLUG,
    BICYCLE_FAKE_BRAND_SLUGS,
    BICYCLE_INACTIVE_LEGACY_SLUGS,
    BICYCLE_LEAF_LABELS,
    BICYCLE_LEAF_SORT,
    BICYCLE_PARENT_SLUG,
    BICYCLE_SEARCH_FILTERS_BY_SLUG,
)

revision = "c3d4e5f6a7b8"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    parent = bind.execute(
        text("SELECT id FROM categories WHERE slug = :s"),
        {"s": BICYCLE_PARENT_SLUG},
    ).fetchone()
    if parent is None:
        raise RuntimeError(f"Missing parent {BICYCLE_PARENT_SLUG}")
    parent_id = int(parent[0])

    for slug, label in BICYCLE_LEAF_LABELS.items():
        sort = BICYCLE_LEAF_SORT[slug]
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :s"),
            {"s": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Bicycle leaf missing: {slug}")
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

    for slug in BICYCLE_INACTIVE_LEGACY_SLUGS:
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

    # Alias: generic «велосипед» → Transport bicycles (not Sport equipment).
    bike_alias = bind.execute(
        text(
            """
            SELECT id, category_id FROM category_aliases
            WHERE alias_normalized = 'велосипед' AND locale = 'ru'
            LIMIT 1
            """
        )
    ).fetchone()
    if bike_alias is not None:
        bind.execute(
            text(
                """
                UPDATE category_aliases
                SET category_id = :cid,
                    alias = 'велосипед',
                    is_enabled = true,
                    weight = 100,
                    updated_at = now()
                WHERE id = :id
                """
            ),
            {"cid": parent_id, "id": int(bike_alias[0])},
        )
    else:
        bind.execute(
            text(
                """
                INSERT INTO category_aliases
                (category_id, alias, alias_normalized, alias_compact, locale,
                 weight, is_enabled, created_at, updated_at)
                VALUES
                (:cid, 'велосипед', 'велосипед', 'велосипед', 'ru',
                 100, true, now(), now())
                """
            ),
            {"cid": parent_id},
        )

    for slug, fields in BICYCLE_CORE_FIELDS_BY_SLUG.items():
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
        for key, label, ftype, sort, config in BICYCLE_SEARCH_FILTERS_BY_SLUG[slug]:
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

    # Disable fake type-as-brand rows (keep history; hide from pickers).
    for fake_slug in BICYCLE_FAKE_BRAND_SLUGS:
        bind.execute(
            text(
                """
                UPDATE vehicle_brands
                SET is_enabled = false, updated_at = now()
                WHERE slug = :slug
                """
            ),
            {"slug": fake_slug},
        )
        brand = bind.execute(
            text("SELECT id FROM vehicle_brands WHERE slug = :s"),
            {"s": fake_slug},
        ).fetchone()
        if brand is not None:
            bind.execute(
                text(
                    """
                    UPDATE vehicle_models
                    SET is_enabled = false, updated_at = now()
                    WHERE brand_id = :bid
                    """
                ),
                {"bid": int(brand[0])},
            )

    for slug, name, country, vtype in BICYCLE_SALE_BRANDS:
        vtype_val = vtype.value if hasattr(vtype, "value") else str(vtype)
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

    for brand_slug, models in BICYCLE_SALE_MODELS.items():
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
