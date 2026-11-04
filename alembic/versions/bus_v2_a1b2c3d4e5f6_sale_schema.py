"""Bus / Minibus / Motorhome Sale V2 leaf schemas + catalog hygiene.

Revision ID: a1b2c3d4e5f6busv2
Revises: c3d4e5f6a7b8
Create Date: 2026-11-02

- Seed leaf core_fields + filters for Bus 776 / Minibus 773 / Motorhome 1202
- Retarget aliases автобус/микроавтобус/автодом → leaves (not parent 1201)
- Disable cargo-only microbus models; upsert Другая марка
- Keep Commercial 688 inactive; do not move Cargo 808 / Trailer 1227
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

from app.seeds.bus_sale_catalogs import BUS_SALE_BRANDS, BUS_SALE_MODELS
from app.seeds.bus_sale_v2 import (
    BUS_CORE_FIELDS_BY_SLUG,
    BUS_LEAF_ALIASES,
    BUS_LEAF_LABELS,
    BUS_LEAF_SORT,
    BUS_OTHER_BRANDS,
    BUS_OTHER_MODELS,
    BUS_PARENT_SLUG,
    BUS_SEARCH_FILTERS_BY_SLUG,
    MICROBUS_CARGO_MODEL_KEYS,
)

revision = "a1b2c3d4e5f6busv2"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    parent = bind.execute(
        text("SELECT id FROM categories WHERE slug = :s"),
        {"s": BUS_PARENT_SLUG},
    ).fetchone()
    if parent is None:
        raise RuntimeError(f"Missing parent {BUS_PARENT_SLUG}")
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

    for slug, label in BUS_LEAF_LABELS.items():
        sort = BUS_LEAF_SORT[slug]
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :s"),
            {"s": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Bus branch leaf missing: {slug}")
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

    # Keep commercial shell inactive.
    bind.execute(
        text(
            """
            UPDATE categories
            SET is_active = false, updated_at = now()
            WHERE slug = 'transport-commercial' AND is_active = true
            """
        )
    )

    for alias, leaf_slug in BUS_LEAF_ALIASES.items():
        leaf = bind.execute(
            text("SELECT id FROM categories WHERE slug = :s"),
            {"s": leaf_slug},
        ).fetchone()
        if leaf is None:
            continue
        leaf_id = int(leaf[0])
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
                        weight = 100,
                        updated_at = now()
                    WHERE id = :id
                    """
                ),
                {"cid": leaf_id, "alias": alias, "id": int(existing[0])},
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
                     100, true, now(), now())
                    """
                ),
                {"cid": leaf_id, "alias": alias},
            )

    for slug, fields in BUS_CORE_FIELDS_BY_SLUG.items():
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
        for key, label, ftype, sort, config in BUS_SEARCH_FILTERS_BY_SLUG[slug]:
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

    # Disable cargo-only microbus models (keep history).
    for brand_slug, model_slug in MICROBUS_CARGO_MODEL_KEYS:
        brand = bind.execute(
            text("SELECT id FROM vehicle_brands WHERE slug = :s"),
            {"s": brand_slug},
        ).fetchone()
        if brand is None:
            continue
        bind.execute(
            text(
                """
                UPDATE vehicle_models
                SET is_enabled = false, updated_at = now()
                WHERE brand_id = :bid AND slug = :ms
                """
            ),
            {"bid": int(brand[0]), "ms": model_slug},
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

    for slug, name, country, vtype in BUS_SALE_BRANDS:
        vtype_val = vtype.value if hasattr(vtype, "value") else str(vtype)
        _upsert_brand(slug, name, country, vtype_val)

    for slug, name, country, vtype_str in BUS_OTHER_BRANDS:
        _upsert_brand(slug, name, country, vtype_str)

    all_models = dict(BUS_SALE_MODELS)
    all_models.update(BUS_OTHER_MODELS)
    for brand_slug, models in all_models.items():
        brand = bind.execute(
            text("SELECT id FROM vehicle_brands WHERE slug = :s"),
            {"s": brand_slug},
        ).fetchone()
        if brand is None:
            continue
        brand_id = int(brand[0])
        for model_slug, model_name in models:
            if (brand_slug, model_slug) in MICROBUS_CARGO_MODEL_KEYS:
                continue
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
