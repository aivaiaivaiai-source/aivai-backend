"""Animals V2 Package B — Search filters SoT.

Revision ID: r7a8b9c0d1e2animalpb
Revises: q6f7a8b9c0d1animalpa
Create Date: 2026-11-11

- Seed category_filters from Animals Package B explicit Search allowlist
- Preserve Create cores / listings (do not rewrite Package A / taxonomy migrations)
- Does NOT change Animals taxonomy, Services vet ownership, or Create SoT
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

revision = "r7a8b9c0d1e2animalpb"
down_revision = "q6f7a8b9c0d1animalpa"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.animals_v2 import (
        ANIMALS_V2_CANONICAL_SLUGS,
        ANIMALS_V2_RETIRED_SLUGS,
        build_animals_v2_search_filters,
    )

    bind = op.get_bind()
    filters_by_slug = build_animals_v2_search_filters()
    if set(filters_by_slug) != ANIMALS_V2_CANONICAL_SLUGS:
        raise RuntimeError("Animals Package B Search map incomplete")

    for slug in sorted(ANIMALS_V2_RETIRED_SLUGS):
        row = bind.execute(
            text("SELECT id, is_active FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            continue
        if bool(row[1]):
            raise RuntimeError(f"Retired Animals slug still active at Package B: {slug}")
        # Clear any leftover Search filters on retired L2.
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
            raise RuntimeError(f"Animals leaf missing for Search seed: {slug}")
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
