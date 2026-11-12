"""Stationery & Books V2 Package B — Search filters SoT.

Revision ID: u0d1e2f3a4b5stationpb
Revises: t9c0d1e2f3a4stationpa
Create Date: 2026-11-12

- Seed category_filters from Stationery Package B explicit Search allowlist
- Preserve Create cores / listings (do not rewrite Package A / taxonomy migrations)
- Does NOT change Stationery taxonomy or Create SoT
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

revision = "u0d1e2f3a4b5stationpb"
down_revision = "t9c0d1e2f3a4stationpa"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.stationery_v2 import (
        STATIONERY_V2_CANONICAL_SLUGS,
        STATIONERY_V2_RETIRED_SLUGS,
        build_stationery_v2_search_filters,
        stationery_v2_assert_package_a_contracts,
    )

    stationery_v2_assert_package_a_contracts()
    bind = op.get_bind()
    filters_by_slug = build_stationery_v2_search_filters()
    if set(filters_by_slug) != STATIONERY_V2_CANONICAL_SLUGS:
        raise RuntimeError("Stationery Package B Search map incomplete")

    for slug in sorted(STATIONERY_V2_RETIRED_SLUGS):
        row = bind.execute(
            text("SELECT id, is_active FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            continue
        if bool(row[1]):
            raise RuntimeError(
                f"Retired Stationery slug still active at Package B: {slug}"
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
            raise RuntimeError(f"Stationery leaf missing for Search seed: {slug}")
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
                    "config": json.dumps(config, ensure_ascii=False)
                    if config is not None
                    else None,
                },
            )


def downgrade() -> None:
    pass
