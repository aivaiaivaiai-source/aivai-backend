"""Kids V2 taxonomy cleanup — retire legacy + education, keep 17 goods L2.

Revision ID: h7c8d9e0f1a2kidstax
Revises: g6b7c8d9e0f1fashpackb
Create Date: 2026-11-11

- Root kids: active picker-only (0 cores / 0 filters)
- Activate 17 canonical goods L2 from mobile skeleton
- Retire legacy kids-toys / kids-clothes / kids-strollers
- Retire kids-detskie-sady-i-obrazovanie (services, not Kids goods)
- Clear Create/Search schemas on retired + root
- STOP if Kids subtree has listings
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "h7c8d9e0f1a2kidstax"
down_revision = "g6b7c8d9e0f1fashpackb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.kids_v2 import (
        KIDS_ROOT_LABEL,
        KIDS_ROOT_SLUG,
        KIDS_V2_CANONICAL_GOODS_LEAVES,
        KIDS_V2_RETIRED_SLUGS,
    )

    bind = op.get_bind()

    root = bind.execute(
        text("SELECT id FROM categories WHERE slug = :slug"),
        {"slug": KIDS_ROOT_SLUG},
    ).fetchone()
    if root is None:
        raise RuntimeError("kids root missing")
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
            f"Kids V2 taxonomy cleanup STOP: unexpected listings ({total})"
        )

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

    for slug, label, sort_order in KIDS_V2_CANONICAL_GOODS_LEAVES:
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Kids V2 STOP: missing canonical leaf {slug}")
        cid = int(row[0])
        bind.execute(
            text(
                """
                UPDATE categories
                SET name = :name,
                    parent_id = :pid,
                    sort_order = :sort,
                    is_active = true,
                    updated_at = now()
                WHERE id = :id
                """
            ),
            {"name": label, "pid": root_id, "sort": sort_order, "id": cid},
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


def downgrade() -> None:
    # Soft retirement is not auto-reversed; restore would reintroduce dual taxonomy.
    pass
