"""Kids V2 Package B — Search filters SoT.

Revision ID: l1a2b3c4d5e6kidspackb
Revises: k0f1a2b3c4d5kidsshared
Create Date: 2026-11-11

- Seed category_filters from Kids Package B explicit Search allowlist
- Preserve Create cores / listings (do not rewrite Package A migrations)
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

revision = "l1a2b3c4d5e6kidspackb"
down_revision = "k0f1a2b3c4d5kidsshared"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.kids_v2 import (
        KIDS_V2_CANONICAL_GOODS_SLUGS,
        build_kids_v2_search_filters,
    )

    bind = op.get_bind()
    filters_by_slug = build_kids_v2_search_filters()
    if set(filters_by_slug) != KIDS_V2_CANONICAL_GOODS_SLUGS:
        raise RuntimeError("Kids Package B Search map incomplete")

    for slug, filters in filters_by_slug.items():
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Kids leaf missing for Search seed: {slug}")
        cat_id = int(row[0])
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
