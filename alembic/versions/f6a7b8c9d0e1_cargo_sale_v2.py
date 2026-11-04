"""Cargo Sale V2: leaf schemas + Other Brand + aliases.

Revision ID: f6a7b8c9d0e1cargov2
Revises: e5f6a7b8c9d0nophoto
Create Date: 2026-11-03

- Seed leaf core_fields + filters for 9 active Cargo sale leaves
- Keep legacy Commercial / Special Trucks / parent parts inactive
- Upsert Другая марка per typed cargo vehicle_type
- Canonical load_capacity_kg (deprecate live payload_kg on Cargo leaves/parent)
- Preserve parent 691 drafts; parent remains non-publishable branch
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

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

revision = "f6a7b8c9d0e1cargov2"
down_revision = "e5f6a7b8c9d0nophoto"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    parent = bind.execute(
        text("SELECT id FROM categories WHERE slug = :s"),
        {"s": CARGO_PARENT_SLUG},
    ).fetchone()
    if parent is None:
        raise RuntimeError(f"Missing parent {CARGO_PARENT_SLUG}")
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

    for slug, label in CARGO_LEAF_LABELS.items():
        sort = CARGO_LEAF_SORT[slug]
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :s"),
            {"s": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Cargo leaf missing: {slug}")
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

    for slug in CARGO_INACTIVE_LEGACY_SLUGS:
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

    for alias, leaf_slug in CARGO_LEAF_ALIASES.items():
        _upsert_alias(alias, leaf_slug)
    for alias, leaf_slug in EVACUATOR_SALE_ALIASES.items():
        _upsert_alias(alias, leaf_slug, weight=120)
    for alias, parent_slug in CARGO_PARENT_ALIASES.items():
        _upsert_alias(alias, parent_slug, weight=80)

    # Keep bare «эвакуатор» on Services if present (do not retarget).
    bare = bind.execute(
        text(
            """
            SELECT id FROM category_aliases
            WHERE alias_normalized = 'эвакуатор' AND locale = 'ru'
            LIMIT 1
            """
        )
    ).fetchone()
    if bare is not None:
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

    # Parent is picker-only: drop live Create/Search SoT (keep listing drafts).
    bind.execute(
        text("DELETE FROM category_core_fields WHERE category_id = :cid"),
        {"cid": parent_id},
    )
    bind.execute(
        text("DELETE FROM category_optional_fields WHERE category_id = :cid"),
        {"cid": parent_id},
    )
    bind.execute(
        text("DELETE FROM category_filters WHERE category_id = :cid"),
        {"cid": parent_id},
    )

    for slug, fields in CARGO_CORE_FIELDS_BY_SLUG.items():
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
        for key, label, ftype, sort, config in CARGO_SEARCH_FILTERS_BY_SLUG[slug]:
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

    for slug, name, country, vtype_str in cargo_other_brands():
        _upsert_brand(slug, name, country, vtype_str)

    for brand_slug, models in cargo_other_models().items():
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

    # Read-compat only: historical payload_kg → load_capacity_kg (no mass rewrite).
    # Zero live values expected; leave any rare rows readable via app mapping.


def downgrade() -> None:
    # Non-destructive: leaf schemas stay; do not recreate parent thin SoT.
    pass
