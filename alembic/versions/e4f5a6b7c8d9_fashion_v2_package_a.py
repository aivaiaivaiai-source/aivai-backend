"""Fashion V2 Package A — canonical 17 L2 + Create SoT.

Revision ID: e4f5a6b7c8d9fashiona
Revises: d3e4f5a6b7c8elepackb
Create Date: 2026-11-10

- Keep root fashion (picker-only, non-publishable)
- Ensure 17 canonical active goods L2 + live labels
- Retire legacy fashion-clothing/shoes/accessories + fashion-tkani-i-furnitura
- Seed Create core fields (fashion_kind + size multi_select + shared goods)
- STOP if unexpected listings appear on Fashion subtree
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

revision = "e4f5a6b7c8d9fashiona"
down_revision = "d3e4f5a6b7c8elepackb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.fashion_v2 import (
        FASHION_ROOT_LABEL,
        FASHION_ROOT_SLUG,
        FASHION_V2_CANONICAL_LEAVES,
        FASHION_V2_CANONICAL_SLUGS,
        FASHION_V2_RETIRED_SLUGS,
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

    total = bind.execute(
        text(
            """
            WITH RECURSIVE t AS (
              SELECT id FROM categories WHERE id = :rid
              UNION ALL
              SELECT c.id FROM categories c JOIN t ON c.parent_id = t.id
            )
            SELECT count(*) FROM listings l JOIN t ON l.category_id = t.id
            """
        ),
        {"rid": root_id},
    ).scalar_one()
    if int(total or 0) > 0:
        raise RuntimeError(
            f"Fashion V2 Package A STOP: unexpected listings ({total})"
        )

    bind.execute(
        text(
            """
            UPDATE categories
            SET name = :name, is_active = true, updated_at = now()
            WHERE id = :id
            """
        ),
        {"name": FASHION_ROOT_LABEL, "id": root_id},
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

    slug_to_id: dict[str, int] = {FASHION_ROOT_SLUG: root_id}

    for slug, label, sort_order in FASHION_V2_CANONICAL_LEAVES:
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(
                f"Fashion V2 Package A STOP: missing canonical leaf {slug}"
            )
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

    for slug in sorted(FASHION_V2_RETIRED_SLUGS):
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            continue
        cid = int(row[0])
        slug_to_id[slug] = cid
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
        if slug in FASHION_V2_CANONICAL_SLUGS:
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
            f"Fashion V2 Package A STOP: expected 17 active L2, got {active}"
        )


def downgrade() -> None:
    # Irreversible Package A overlay; restore from backup if needed.
    pass
