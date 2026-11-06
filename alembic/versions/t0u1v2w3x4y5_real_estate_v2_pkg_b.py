"""Real Estate V2 Package B: numeric area field metadata refresh.

Revision ID: t0u1v2w3x4y5realestatev2b
Revises: s9t0u1v2w3x4realestatev2
Create Date: 2026-11-05

- Re-seed canonical leaf core_fields / category_filters from real_estate_v2
  (adds decimal ``area`` + area range filters; rooms area optional/conditional)
- No listing data backfill (historical null area allowed)
- No fabricated area values
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

from app.seeds.real_estate_v2 import (
    CANONICAL_LEAF_SLUGS,
    RE_CORE_FIELDS_BY_SLUG,
    RE_SEARCH_FILTERS_BY_SLUG,
)

revision = "t0u1v2w3x4y5realestatev2b"
down_revision = "s9t0u1v2w3x4realestatev2"
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
                "opts": json.dumps(options, ensure_ascii=False)
                if options is not None
                else None,
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
                "cfg": json.dumps(config or {}, ensure_ascii=False),
            },
        )


def upgrade() -> None:
    bind = op.get_bind()
    for slug in CANONICAL_LEAF_SLUGS:
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :s"),
            {"s": slug},
        ).fetchone()
        if row is None:
            continue
        cid = int(row[0])
        _replace_core_fields(bind, cid, RE_CORE_FIELDS_BY_SLUG[slug])
        _replace_filters(bind, cid, RE_SEARCH_FILTERS_BY_SLUG[slug])


def downgrade() -> None:
    # Area metadata is additive; do not wipe user listing EAV on downgrade.
    pass
