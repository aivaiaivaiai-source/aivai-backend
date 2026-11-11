"""Kids V2 — align shared Create fields to canonical goods contract.

Revision ID: k0f1a2b3c4d5kidsshared
Revises: j9e0f1a2b3c4kidspackafix
Create Date: 2026-11-11

Re-seed Kids Package A core fields so contact_methods / negotiable match
shared_goods_create_contract (Fashion/Electronics/car_sale standard).
Does not change Kids specialty decisions (size/age/condition/mounting/L2).
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

revision = "k0f1a2b3c4d5kidsshared"
down_revision = "j9e0f1a2b3c4kidspackafix"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.kids_v2 import (
        KIDS_V2_CANONICAL_GOODS_LEAVES,
        KIDS_V2_EXPECTED_L2_COUNT,
        KIDS_ROOT_SLUG,
        build_kids_v2_core_fields,
    )

    bind = op.get_bind()
    root = bind.execute(
        text("SELECT id FROM categories WHERE slug = :slug"),
        {"slug": KIDS_ROOT_SLUG},
    ).fetchone()
    if root is None:
        raise RuntimeError("kids root missing")
    root_id = int(root[0])

    slug_to_id: dict[str, int] = {}
    for slug, _label, _sort in KIDS_V2_CANONICAL_GOODS_LEAVES:
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Kids shared-contract STOP: missing leaf {slug}")
        slug_to_id[slug] = int(row[0])

    core_by_slug = build_kids_v2_core_fields()
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
    if int(active or 0) != KIDS_V2_EXPECTED_L2_COUNT:
        raise RuntimeError(
            f"Kids shared-contract STOP: expected {KIDS_V2_EXPECTED_L2_COUNT} "
            f"active L2, got {active}"
        )


def downgrade() -> None:
    pass
