"""Auto Services: required service_price_type + backfill fixed.

Revision ID: q7r8s9t0u1v2autosvcprice
Revises: p6q7r8s9t0u1autosvcv2
Create Date: 2026-11-03

Adds Backend-driven ``service_price_type`` (fixed / negotiable) to all 10
Auto Services leaves for Create + Search. Existing listings without the
field are backfilled to ``fixed`` (pre-field contract was numeric fixed
price only — do not guess negotiable).
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

from app.seeds.auto_services_v2 import (
    AUTO_SERVICES_CORE_FIELDS_BY_SLUG,
    AUTO_SERVICES_SEARCH_FILTERS_BY_SLUG,
    LEAF_IDS,
    LEAF_SLUGS,
    PARENT_ID,
)

revision = "q7r8s9t0u1v2autosvcprice"
down_revision = "p6q7r8s9t0u1autosvcv2"
branch_labels = None
depends_on = None


def _replace_core_fields(bind, category_id: int, fields: list) -> None:
    bind.execute(
        text("DELETE FROM category_core_fields WHERE category_id = :cid"),
        {"cid": category_id},
    )
    for field in fields:
        key, label, ftype, required, sort, options, hint = field
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
                "cid": category_id,
                "key": key,
                "label": label,
                "ftype": ftype.value if hasattr(ftype, "value") else str(ftype),
                "req": required,
                "sort": sort,
                "opts": json.dumps(options) if options is not None else None,
                "hint": hint,
            },
        )


def _replace_filters(bind, category_id: int, filters: list) -> None:
    bind.execute(
        text("DELETE FROM category_filters WHERE category_id = :cid"),
        {"cid": category_id},
    )
    for filt in filters:
        key, label, ftype, sort, config = filt
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
                "cid": category_id,
                "key": key,
                "label": label,
                "ftype": ftype.value if hasattr(ftype, "value") else str(ftype),
                "sort": sort,
                "cfg": json.dumps(config or {}),
            },
        )


def upgrade() -> None:
    bind = op.get_bind()

    for slug in LEAF_SLUGS:
        cid = LEAF_IDS[slug]
        row = bind.execute(
            text("SELECT id FROM categories WHERE id = :id AND slug = :s"),
            {"id": cid, "s": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Missing Auto Services leaf {cid}/{slug}")
        _replace_core_fields(bind, cid, AUTO_SERVICES_CORE_FIELDS_BY_SLUG[slug])
        _replace_filters(bind, cid, AUTO_SERVICES_SEARCH_FILTERS_BY_SLUG[slug])

    # Backfill missing service_price_type → fixed (safe pre-V2-status default).
    leaf_ids = list(LEAF_IDS.values())
    inserted = 0
    for cid in leaf_ids:
        result = bind.execute(
            text(
                """
                INSERT INTO listing_field_values
                (listing_id, field_key, value_text, created_at, updated_at)
                SELECT l.id, 'service_price_type', 'fixed', now(), now()
                FROM listings l
                WHERE l.category_id = :cid
                  AND NOT EXISTS (
                    SELECT 1 FROM listing_field_values lfv
                    WHERE lfv.listing_id = l.id
                      AND lfv.field_key = 'service_price_type'
                  )
                """
            ),
            {"cid": cid},
        )
        inserted += int(getattr(result, "rowcount", 0) or 0)
    fixed_total = 0
    for cid in leaf_ids:
        n = bind.execute(
            text(
                """
                SELECT COUNT(*) FROM listing_field_values lfv
                JOIN listings l ON l.id = lfv.listing_id
                WHERE l.category_id = :cid
                  AND lfv.field_key = 'service_price_type'
                  AND lfv.value_text = 'fixed'
                """
            ),
            {"cid": cid},
        ).scalar()
        fixed_total += int(n or 0)
    print(
        f"[q7r8s9t0u1v2autosvcprice] backfilled_inserted={inserted} "
        f"fixed_total={fixed_total} parent_id={PARENT_ID}"
    )


def downgrade() -> None:
    # Non-destructive: keep EAV values; schema rollback would require prior
    # Auto Services V2 snapshot — leave fields in place.
    pass
