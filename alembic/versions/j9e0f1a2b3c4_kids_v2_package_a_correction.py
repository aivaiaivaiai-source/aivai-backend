"""Kids V2 Package A Samsung correction — school retire + Create simplify.

Revision ID: j9e0f1a2b3c4kidspackafix
Revises: i8d9e0f1a2b3kidspacka
Create Date: 2026-11-11

- Retire kids-tovary-dlya-shkoly (Stationery/Books owns school direction)
- Re-seed 16 active Kids Create cores (no diaper_size / shoe_size / formula age)
- Clear schemas on retired school L2
- Does not rewrite prior Kids migrations
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

revision = "j9e0f1a2b3c4kidspackafix"
down_revision = "i8d9e0f1a2b3kidspacka"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.kids_v2 import (
        KIDS_ROOT_LABEL,
        KIDS_ROOT_SLUG,
        KIDS_V2_CANONICAL_GOODS_LEAVES,
        KIDS_V2_CANONICAL_GOODS_SLUGS,
        KIDS_V2_EXPECTED_L2_COUNT,
        KIDS_V2_RETIRED_SLUGS,
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

    bind.execute(
        text(
            """
            UPDATE categories
            SET name = :name, is_active = true, parent_id = NULL, updated_at = now()
            WHERE id = :id
            """
        ),
        {"name": KIDS_ROOT_LABEL, "id": root_id},
    )
    for table in (
        "category_core_fields",
        "category_optional_fields",
        "category_filters",
    ):
        bind.execute(
            text(f"DELETE FROM {table} WHERE category_id = :cid"),
            {"cid": root_id},
        )

    slug_to_id: dict[str, int] = {KIDS_ROOT_SLUG: root_id}
    for slug, label, sort_order in KIDS_V2_CANONICAL_GOODS_LEAVES:
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Kids Package A fix STOP: missing leaf {slug}")
        cid = int(row[0])
        slug_to_id[slug] = cid
        bind.execute(
            text(
                """
                UPDATE categories
                SET parent_id = :pid,
                    name = :name,
                    is_active = true,
                    sort_order = :sort,
                    entity_type = 'object',
                    requires_city = true,
                    updated_at = now()
                WHERE id = :id
                """
            ),
            {"pid": root_id, "name": label, "sort": sort_order, "id": cid},
        )

    for slug in sorted(KIDS_V2_RETIRED_SLUGS):
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            continue
        cid = int(row[0])
        bind.execute(
            text(
                """
                UPDATE categories
                SET is_active = false, updated_at = now()
                WHERE id = :id
                """
            ),
            {"id": cid},
        )
        for table in (
            "category_core_fields",
            "category_optional_fields",
            "category_filters",
        ):
            bind.execute(
                text(f"DELETE FROM {table} WHERE category_id = :cid"),
                {"cid": cid},
            )

    children = bind.execute(
        text("SELECT id, slug FROM categories WHERE parent_id = :pid"),
        {"pid": root_id},
    ).fetchall()
    for cid, slug in children:
        if slug in KIDS_V2_CANONICAL_GOODS_SLUGS:
            continue
        bind.execute(
            text(
                """
                UPDATE categories
                SET is_active = false, updated_at = now()
                WHERE id = :id
                """
            ),
            {"id": int(cid)},
        )
        for table in (
            "category_core_fields",
            "category_optional_fields",
            "category_filters",
        ):
            bind.execute(
                text(f"DELETE FROM {table} WHERE category_id = :cid"),
                {"cid": int(cid)},
            )

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
            f"Kids Package A fix STOP: expected {KIDS_V2_EXPECTED_L2_COUNT} "
            f"active L2, got {active}"
        )


def downgrade() -> None:
    pass
