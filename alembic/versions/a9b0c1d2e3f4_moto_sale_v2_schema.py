"""Moto Sale V2: leaf Create/Search SoT + display label renames.

Revision ID: a9b0c1d2e3f4
Revises: w1x2y3z4a5b6
Create Date: 2026-11-01

- Rename display labels for Муравей / Картинги (IDs/slugs preserved)
- Seed category_core_fields + category_filters for 9 active moto leaves
- Do not activate electric/parts/services legacy leaves
- Parent transport-moto-tech legacy fields left untouched
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

from app.seeds.moto_sale_v2 import (
    MOTO_CORE_FIELDS_BY_SLUG,
    MOTO_INACTIVE_LEGACY_SLUGS,
    MOTO_LEAF_LABELS,
    MOTO_SEARCH_FILTERS_BY_SLUG,
)

revision = "a9b0c1d2e3f4"
down_revision = "w1x2y3z4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    for slug, label in MOTO_LEAF_LABELS.items():
        bind.execute(
            text(
                """
                UPDATE categories
                SET name = :label, updated_at = now()
                WHERE slug = :slug
                """
            ),
            {"slug": slug, "label": label},
        )

    # Keep electric / parts / services inactive.
    for slug in MOTO_INACTIVE_LEGACY_SLUGS:
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

    for slug, fields in MOTO_CORE_FIELDS_BY_SLUG.items():
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :s"),
            {"s": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Moto leaf missing: {slug}")
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

        filters = MOTO_SEARCH_FILTERS_BY_SLUG[slug]
        for key, label, ftype, sort, config in filters:
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


def downgrade() -> None:
    # Forward-only leaf SoT cutover.
    pass
