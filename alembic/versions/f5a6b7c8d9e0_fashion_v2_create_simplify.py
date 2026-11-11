"""Fashion V2 Create simplification — size allowlist only.

Revision ID: f5a6b7c8d9e0fashsimp
Revises: e4f5a6b7c8d9fashiona
Create Date: 2026-11-10

- Drop season/gender/material/extras from Fashion Create cores
- Re-seed 17 L2 schemas from simplified fashion_v2 allowlist
- Preserve any existing Fashion listings (do not delete)
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

revision = "f5a6b7c8d9e0fashsimp"
down_revision = "e4f5a6b7c8d9fashiona"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.fashion_v2 import (
        FASHION_ROOT_SLUG,
        FASHION_V2_CANONICAL_LEAVES,
        build_fashion_v2_core_fields,
    )

    bind = op.get_bind()

    root = bind.execute(
        text("SELECT id FROM categories WHERE slug = :slug"),
        {"slug": FASHION_ROOT_SLUG},
    ).fetchone()
    if root is None:
        raise RuntimeError("fashion root missing")
    root_id = int(root[0])

    # Keep picker-only root clean.
    for table in (
        "category_core_fields",
        "category_optional_fields",
        "category_filters",
    ):
        bind.execute(
            text(f"DELETE FROM {table} WHERE category_id = :cid"),
            {"cid": root_id},
        )

    slug_to_id: dict[str, int] = {}
    for slug, _label, _sort in FASHION_V2_CANONICAL_LEAVES:
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Fashion simplify STOP: missing leaf {slug}")
        slug_to_id[slug] = int(row[0])

    core_by_slug = build_fashion_v2_core_fields()
    for slug, fields in core_by_slug.items():
        cid = slug_to_id[slug]
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

    active = bind.execute(
        text(
            """
            SELECT count(*) FROM categories
            WHERE parent_id = :pid AND is_active = true
            """
        ),
        {"pid": root_id},
    ).scalar_one()
    if int(active or 0) != 17:
        raise RuntimeError(
            f"Fashion simplify STOP: expected 17 active L2, got {active}"
        )


def downgrade() -> None:
    pass
