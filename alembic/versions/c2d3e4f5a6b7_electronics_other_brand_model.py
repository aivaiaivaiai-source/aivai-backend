"""Electronics V2 — trailing other_brand / other_model options.

Revision ID: c2d3e4f5a6b7eleother
Revises: b1c2d3e4f5a6elecatexp
Create Date: 2026-11-08

Re-seeds Electronics L2 Create core fields so Brand/Model pickers include
open-catalog fallbacks. Does not change L2 taxonomy or closed enums.
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

revision = "c2d3e4f5a6b7eleother"
down_revision = "b1c2d3e4f5a6elecatexp"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.electronics_v2 import (
        ELECTRONICS_V2_CANONICAL_SLUGS,
        build_electronics_v2_core_fields,
    )

    bind = op.get_bind()
    core_by_slug = build_electronics_v2_core_fields()

    for slug in ELECTRONICS_V2_CANONICAL_SLUGS:
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Electronics Other: missing L2 {slug}")
        cid = int(row[0])
        fields = core_by_slug.get(slug)
        if not fields:
            raise RuntimeError(f"Electronics Other: no cores for {slug}")

        for table in (
            "category_core_fields",
            "category_optional_fields",
            "category_filters",
        ):
            bind.execute(
                text(f"DELETE FROM {table} WHERE category_id = :cid"),
                {"cid": cid},
            )

        for key, label, ftype, required, sort, options, hint in fields:
            if key in {"city", "title", "description", "photos", "region"}:
                continue
            bind.execute(
                text(
                    """
                    INSERT INTO category_core_fields (
                        category_id, field_key, label, field_type, is_required,
                        sort_order, ai_hint, options, create_intent,
                        created_at, updated_at
                    ) VALUES (
                        :cid, :key, :label, :ftype, :req,
                        :sort, :hint, CAST(:options AS jsonb), NULL,
                        now(), now()
                    )
                    """
                ),
                {
                    "cid": cid,
                    "key": key,
                    "label": label,
                    "ftype": ftype.value if hasattr(ftype, "value") else str(ftype),
                    "req": bool(required),
                    "sort": int(sort),
                    "hint": hint,
                    "options": json.dumps(options, ensure_ascii=False)
                    if options
                    else None,
                },
            )


def downgrade() -> None:
    # Re-seed from whatever build_electronics_v2_core_fields provides at
    # downgrade time is not reliable; leave cores as-is.
    pass
