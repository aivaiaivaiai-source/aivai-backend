"""Electric Sale V2: taxonomy re-parent + leaf schemas + vehicle types.

Revision ID: b1c2d3e4f5a6
Revises: a9b0c1d2e3f4
Create Date: 2026-11-01

- Add vehicle_type enum: e_motorcycle, e_atv
- Re-parent/activate e-motorcycle (754) + e-ATV (756) under transport-electric
- Seed leaf core_fields + filters for 9 Electric leaves
- Normalize electric sale brand/model catalogs (incl. move Sur-Ron/Talaria/Stark)
- Keep e-bike under bicycles; keep legacy baggi/kart/trike inactive
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

from app.seeds.electric_sale_catalogs import ELECTRIC_SALE_BRANDS, ELECTRIC_SALE_MODELS
from app.seeds.electric_sale_v2 import (
    ELECTRIC_CORE_FIELDS_BY_SLUG,
    ELECTRIC_INACTIVE_LEGACY_SLUGS,
    ELECTRIC_LEAF_LABELS,
    ELECTRIC_LEAF_SORT,
    ELECTRIC_PARENT_SLUG,
    ELECTRIC_SEARCH_FILTERS_BY_SLUG,
)

revision = "b1c2d3e4f5a6"
down_revision = "a9b0c1d2e3f4"
branch_labels = None
depends_on = None

_NEW_VEHICLE_TYPES = ("e_motorcycle", "e_atv")


def upgrade() -> None:
    bind = op.get_bind()
    # Postgres: new enum labels cannot be used in the same transaction as ADD VALUE.
    if bind.dialect.name == "postgresql":
        with op.get_context().autocommit_block():
            for value in _NEW_VEHICLE_TYPES:
                op.execute(
                    f"ALTER TYPE vehicle_type_enum ADD VALUE IF NOT EXISTS '{value}'"
                )

    parent = bind.execute(
        text("SELECT id FROM categories WHERE slug = :s"),
        {"s": ELECTRIC_PARENT_SLUG},
    ).fetchone()
    if parent is None:
        raise RuntimeError(f"Missing parent {ELECTRIC_PARENT_SLUG}")
    parent_id = int(parent[0])

    for slug, label in ELECTRIC_LEAF_LABELS.items():
        sort = ELECTRIC_LEAF_SORT[slug]
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :s"),
            {"s": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Electric leaf missing: {slug}")
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

    for slug in ELECTRIC_INACTIVE_LEGACY_SLUGS:
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

    for slug, fields in ELECTRIC_CORE_FIELDS_BY_SLUG.items():
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
        for key, label, ftype, sort, config in ELECTRIC_SEARCH_FILTERS_BY_SLUG[slug]:
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

    # Brand/model catalog upsert + re-type Sur-Ron/Talaria/Stark → e_motorcycle.
    for slug, name, country, vtype in ELECTRIC_SALE_BRANDS:
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

    for brand_slug, models in ELECTRIC_SALE_MODELS.items():
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

    # Brand aliases (best-effort).
    alias_rows = [
        ("surron", "Surron"),
        ("surron", "Sur Ron"),
        ("gotway", "Gotway"),
        ("gotway", "Begode"),
        ("zero-emotorcycle", "Zero Motorcycles"),
    ]
    for brand_slug, alias in alias_rows:
        brand = bind.execute(
            text("SELECT id FROM vehicle_brands WHERE slug = :s"),
            {"s": brand_slug},
        ).fetchone()
        if brand is None:
            continue
        compact = "".join(ch.lower() for ch in alias if ch.isalnum())
        normalized = alias.strip().lower()
        exists = bind.execute(
            text(
                """
                SELECT id FROM vehicle_aliases
                WHERE alias_compact = :c AND locale = 'ru'
                """
            ),
            {"c": compact},
        ).fetchone()
        if exists is not None:
            continue
        bind.execute(
            text(
                """
                INSERT INTO vehicle_aliases
                (alias, alias_normalized, alias_compact, target_type, brand_id,
                 locale, is_enabled, created_at, updated_at)
                VALUES
                (:a, :n, :c, CAST('brand' AS vehicle_alias_target_enum), :bid,
                 'ru', true, now(), now())
                """
            ),
            {
                "a": alias,
                "n": normalized,
                "c": compact,
                "bid": int(brand[0]),
            },
        )


def downgrade() -> None:
    pass
