"""Electronics V2 catalog expansion — brand/model marketplace depth.

Revision ID: b1c2d3e4f5a6elecatexp
Revises: a0b1c2d3e4f5electronicsa
Create Date: 2026-11-08

Re-seeds Electronics L2 Create core fields from expanded Backend SoT.
Does not rewrite Package A taxonomy / L2 structure.
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

revision = "b1c2d3e4f5a6elecatexp"
down_revision = "a0b1c2d3e4f5electronicsa"
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
            raise RuntimeError(f"Electronics catalog expansion: missing L2 {slug}")
        cid = int(row[0])
        fields = core_by_slug.get(slug)
        if not fields:
            raise RuntimeError(f"Electronics catalog expansion: no cores for {slug}")

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
    # Irreversible catalog overlay; restore from backup / re-run Package A cores.
    pass
