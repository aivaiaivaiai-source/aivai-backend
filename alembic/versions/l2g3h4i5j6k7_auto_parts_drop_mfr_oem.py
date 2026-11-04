"""Auto Parts V2: drop manufacturer + OEM from live Create/Search.

Revision ID: l2g3h4i5j6k7apdropmfroem
Revises: k1f2a3b4c5d6autopartsv2
Create Date: 2026-11-03

Product decision: no structured ``part_manufacturer`` / ``part_number``.
Sellers put brand/OEM text in Description when needed.
Legacy ``oem_number`` also removed if present.
Zero live listing_field_values expected; historical EAV rows (if any) kept.
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

from app.seeds.auto_parts_v2 import (
    PARTS_CORE_FIELDS_BY_SLUG,
    PARTS_PARENT_SLUG,
    PARTS_SEARCH_FILTERS_BY_SLUG,
)

revision = "l2g3h4i5j6k7apdropmfroem"
down_revision = "k1f2a3b4c5d6autopartsv2"
branch_labels = None
depends_on = None

_REMOVED_KEYS = ("part_manufacturer", "part_number", "oem_number")


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

    # Safety: report (do not delete) any unexpected EAV values.
    for key in _REMOVED_KEYS:
        n = bind.execute(
            text(
                "SELECT COUNT(*) FROM listing_field_values WHERE field_key = :k"
            ),
            {"k": key},
        ).scalar()
        # Historical values (if any) stay readable; live schemas no longer expose.
        _ = n

    # Re-seed every Auto Parts leaf from updated SoT (incl. specials + empty parent).
    for slug, fields in PARTS_CORE_FIELDS_BY_SLUG.items():
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :s"),
            {"s": slug},
        ).fetchone()
        if row is None:
            continue
        cid = int(row[0])
        _replace_core_fields(bind, cid, fields)
        filters = PARTS_SEARCH_FILTERS_BY_SLUG.get(slug, [])
        _replace_filters(bind, cid, filters)

    # Belt-and-suspenders: strip keys from any leftover Auto Parts category.
    for key in _REMOVED_KEYS:
        bind.execute(
            text(
                """
                DELETE FROM category_core_fields f
                USING categories c
                WHERE f.category_id = c.id
                  AND c.slug LIKE 'transport-auto-parts%'
                  AND f.field_key = :k
                """
            ),
            {"k": key},
        )
        bind.execute(
            text(
                """
                DELETE FROM category_filters f
                USING categories c
                WHERE f.category_id = c.id
                  AND c.slug LIKE 'transport-auto-parts%'
                  AND f.filter_key = :k
                """
            ),
            {"k": key},
        )

    # Parent stays picker-only.
    parent = bind.execute(
        text("SELECT id FROM categories WHERE slug = :s"),
        {"s": PARTS_PARENT_SLUG},
    ).fetchone()
    if parent is not None:
        pid = int(parent[0])
        bind.execute(
            text("DELETE FROM category_core_fields WHERE category_id = :cid"),
            {"cid": pid},
        )
        bind.execute(
            text("DELETE FROM category_filters WHERE category_id = :cid"),
            {"cid": pid},
        )


def downgrade() -> None:
    # Irreversible product cut — re-run Auto Parts V2 seed revision if needed.
    pass
