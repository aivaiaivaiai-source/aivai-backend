"""Materials V2 Package B — Search filters SoT.

Revision ID: d9e0f1a2b3c4matpb
Revises: c8d9e0f1a2b3matpa
Create Date: 2026-11-13

- Seed category_filters from Materials Package B explicit Search allowlist
- Preserve Create cores / listings (do not rewrite taxonomy / Package A)
- Does NOT change Materials taxonomy or Create SoT
- Food Tara GAP remains STILL_OPEN
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

revision = "d9e0f1a2b3c4matpb"
down_revision = "c8d9e0f1a2b3matpa"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.materials_v2 import (
        MATERIALS_V2_CANONICAL_SLUGS,
        MATERIALS_V2_RETIRED_SLUGS,
        build_materials_v2_search_filters,
        materials_v2_assert_package_b_contracts,
    )

    materials_v2_assert_package_b_contracts()
    bind = op.get_bind()
    filters_by_slug = build_materials_v2_search_filters()
    if set(filters_by_slug) != MATERIALS_V2_CANONICAL_SLUGS:
        raise RuntimeError("Materials Package B Search map incomplete")

    for slug in sorted(MATERIALS_V2_RETIRED_SLUGS):
        row = bind.execute(
            text("SELECT id, is_active FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            continue
        if bool(row[1]):
            raise RuntimeError(
                f"Retired Materials slug still active at Package B: {slug}"
            )
        bind.execute(
            text("DELETE FROM category_filters WHERE category_id = :cid"),
            {"cid": int(row[0])},
        )

    for slug, filters in filters_by_slug.items():
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Materials leaf missing for Search seed: {slug}")
        cat_id = int(row[0])
        # Preserve Create cores — only rewrite Search filters.
        bind.execute(
            text("DELETE FROM category_filters WHERE category_id = :cid"),
            {"cid": cat_id},
        )
        for key, label, ftype, sort, config in filters:
            ft = ftype.value if hasattr(ftype, "value") else str(ftype)
            bind.execute(
                text(
                    """
                    INSERT INTO category_filters
                      (category_id, filter_key, label, filter_type, sort_order,
                       config, search_intent, created_at, updated_at)
                    VALUES
                      (:cid, :key, :label, CAST(:ftype AS category_filter_type_enum),
                       :sort, CAST(:config AS jsonb), '', NOW(), NOW())
                    """
                ),
                {
                    "cid": cat_id,
                    "key": key,
                    "label": label,
                    "ftype": ft,
                    "sort": int(sort),
                    "config": json.dumps(config or {}, ensure_ascii=False),
                },
            )


def downgrade() -> None:
    from app.seeds.materials_v2 import MATERIALS_V2_CANONICAL_SLUGS

    bind = op.get_bind()
    for slug in sorted(MATERIALS_V2_CANONICAL_SLUGS):
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            continue
        bind.execute(
            text("DELETE FROM category_filters WHERE category_id = :cid"),
            {"cid": int(row[0])},
        )
