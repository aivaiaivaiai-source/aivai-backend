"""Food/Agri V2 taxonomy cleanup — retire legacy/wholesale/eco/tara.

Revision ID: m2b3c4d5e6f7foodtax
Revises: l1a2b3c4d5e6kidspackb
Create Date: 2026-11-11

- Root food-agri: active picker-only (0 cores / 0 filters)
- Keep 23 edible canonical L2 active
- Retire legacy products/farm/feed + wholesale + eco + tara
- Clear Create/Search schemas on retired + root + canonical (Package A later)
- STOP if Food/Agri subtree has listings
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "m2b3c4d5e6f7foodtax"
down_revision = "l1a2b3c4d5e6kidspackb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.food_agri_v2 import (
        FOOD_AGRI_ROOT_LABEL,
        FOOD_AGRI_ROOT_SLUG,
        FOOD_AGRI_V2_CANONICAL_LEAVES,
        FOOD_AGRI_V2_CANONICAL_SLUGS,
        FOOD_AGRI_V2_RETIRED_SLUGS,
    )

    bind = op.get_bind()

    root = bind.execute(
        text("SELECT id FROM categories WHERE slug = :slug"),
        {"slug": FOOD_AGRI_ROOT_SLUG},
    ).fetchone()
    if root is None:
        raise RuntimeError("food-agri root missing")
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
            f"Food/Agri V2 taxonomy cleanup STOP: unexpected listings ({total})"
        )

    bind.execute(
        text(
            """
            UPDATE categories
            SET name = :name, is_active = true, parent_id = NULL, updated_at = now()
            WHERE id = :id
            """
        ),
        {"name": FOOD_AGRI_ROOT_LABEL, "id": root_id},
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

    for label, slug, sort_order in FOOD_AGRI_V2_CANONICAL_LEAVES:
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Food/Agri V2 STOP: missing canonical leaf {slug}")
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

    for slug in sorted(FOOD_AGRI_V2_RETIRED_SLUGS):
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

    # Any other active child under food-agri that is not canonical → retire.
    children = bind.execute(
        text(
            """
            SELECT id, slug FROM categories
            WHERE parent_id = :pid AND is_active = true
            """
        ),
        {"pid": root_id},
    ).fetchall()
    for cid, slug in children:
        if slug in FOOD_AGRI_V2_CANONICAL_SLUGS:
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


def downgrade() -> None:
    # Soft retirement is not auto-reversed; restore would reintroduce dual taxonomy.
    pass
