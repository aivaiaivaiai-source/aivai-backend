"""Car Sale V2: Backend SoT create schema + search filters for 681.

Revision ID: v0w1x2y3z4a5
Revises: u9v0w1x2y3z4
Create Date: 2026-10-30

- Replace category_core_fields for transport-car-sale with V2 schema
- Clear category_optional_fields for car-sale (moved into core)
- Replace category_filters with V2 Search SoT
- No DELETE of listing_field_values (fresh_import historical kept)
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

from app.seeds.car_sale_v2 import (
    CAR_SALE_CORE_FIELDS,
    CAR_SALE_SEARCH_FILTERS,
    CAR_SALE_SLUG,
)

revision = "v0w1x2y3z4a5"
down_revision = "u9v0w1x2y3z4"
branch_labels = None
depends_on = None


def _cat_id(bind) -> int:
    row = bind.execute(
        text("SELECT id FROM categories WHERE slug = :s"),
        {"s": CAR_SALE_SLUG},
    ).fetchone()
    if row is None:
        raise RuntimeError(f"{CAR_SALE_SLUG} missing")
    return int(row[0])


def upgrade() -> None:
    bind = op.get_bind()
    cid = _cat_id(bind)

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

    for key, label, ftype, required, sort, options, hint in CAR_SALE_CORE_FIELDS:
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

    for key, label, ftype, sort, config in CAR_SALE_SEARCH_FILTERS:
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
    # Forward-only schema cutover; restore via prior seed snapshot if needed.
    pass
