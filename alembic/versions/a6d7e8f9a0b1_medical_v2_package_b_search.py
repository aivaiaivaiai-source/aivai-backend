"""Medical Goods V2 Package B — Search filters SoT.

Revision ID: a6d7e8f9a0b1medpb
Revises: z5c6d7e8f9a0medpa
Create Date: 2026-11-12

- Seed category_filters from Medical Package B explicit Search allowlist
- Preserve Create cores / listings (do not rewrite Package A / taxonomy migrations)
- Does NOT change Medical taxonomy or Create SoT
- Listing 3154 EAV untouched (LEGACY_INCOMPLETE)
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

revision = "a6d7e8f9a0b1medpb"
down_revision = "z5c6d7e8f9a0medpa"
branch_labels = None
depends_on = None

LEGACY_INCOMPLETE_LISTING_ID = 3154


def upgrade() -> None:
    from app.seeds.medical_v2 import (
        MEDICAL_V2_CANONICAL_SLUGS,
        MEDICAL_V2_RETIRED_SLUGS,
        build_medical_v2_search_filters,
        medical_v2_assert_package_b_contracts,
    )

    medical_v2_assert_package_b_contracts()
    bind = op.get_bind()
    filters_by_slug = build_medical_v2_search_filters()
    if set(filters_by_slug) != MEDICAL_V2_CANONICAL_SLUGS:
        raise RuntimeError("Medical Package B Search map incomplete")

    for slug in sorted(MEDICAL_V2_RETIRED_SLUGS):
        row = bind.execute(
            text("SELECT id, is_active FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            continue
        if bool(row[1]):
            raise RuntimeError(
                f"Retired Medical slug still active at Package B: {slug}"
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
            raise RuntimeError(f"Medical leaf missing for Search seed: {slug}")
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

    # Forensic listing must remain untouched.
    forensic = bind.execute(
        text("SELECT id FROM listings WHERE id = :lid"),
        {"lid": LEGACY_INCOMPLETE_LISTING_ID},
    ).fetchone()
    if forensic is not None:
        keys = bind.execute(
            text(
                """
                SELECT field_key FROM listing_field_values
                WHERE listing_id = :lid ORDER BY field_key
                """
            ),
            {"lid": LEGACY_INCOMPLETE_LISTING_ID},
        ).fetchall()
        _ = {r[0] for r in keys}


def downgrade() -> None:
    pass
