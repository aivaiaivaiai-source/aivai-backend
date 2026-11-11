"""Fashion V2 Package B — Search filters SoT.

Revision ID: g6b7c8d9e0f1fashpackb
Revises: f5a6b7c8d9e0fashsimp
Create Date: 2026-11-11

- Seed category_filters from Fashion Package B explicit Search allowlist
- Preserve Create cores / listings (do not delete)
- Does not rewrite Package A migrations
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

revision = "g6b7c8d9e0f1fashpackb"
down_revision = "f5a6b7c8d9e0fashsimp"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.fashion_v2 import (
        FASHION_V2_CANONICAL_SLUGS,
        build_fashion_v2_search_filters,
    )

    bind = op.get_bind()
    filters_by_slug = build_fashion_v2_search_filters()
    if set(filters_by_slug) != FASHION_V2_CANONICAL_SLUGS:
        raise RuntimeError("Fashion Package B Search map incomplete")

    for slug, filters in filters_by_slug.items():
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Fashion leaf missing for Search seed: {slug}")
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
    # Search filters are re-seedable; leave rows (forward-only product policy).
    pass
