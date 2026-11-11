"""Animals V2 taxonomy cleanup — retire legacy triad; keep modern L2.

Revision ID: p5e6f7a8b9c0animaltax
Revises: o4d5e6f7a8b9foodpackb
Create Date: 2026-11-11

- Soft-retire animals-pets / animals-livestock / animals-birds
- Clear cores/filters/optional on retired + ensure root picker-only
- Keep 16 modern Animals L2 active (incl. vetservices pending Services GAP)
- STOP if Animals subtree has listings
- Does NOT seed Package A Create cores / Search filters
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "p5e6f7a8b9c0animaltax"
down_revision = "o4d5e6f7a8b9foodpackb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.animals_v2 import (
        ANIMALS_ROOT_LABEL,
        ANIMALS_ROOT_SLUG,
        ANIMALS_V2_CANONICAL_LEAVES,
        ANIMALS_V2_CANONICAL_SLUGS,
        ANIMALS_V2_RETIRED_SLUGS,
        animals_v2_assert_cleanup_contracts,
    )

    animals_v2_assert_cleanup_contracts()
    bind = op.get_bind()

    root = bind.execute(
        text("SELECT id FROM categories WHERE slug = :slug"),
        {"slug": ANIMALS_ROOT_SLUG},
    ).fetchone()
    if root is None:
        raise RuntimeError("animals root missing")
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
            f"Animals V2 taxonomy cleanup STOP: unexpected listings ({total})"
        )

    bind.execute(
        text(
            """
            UPDATE categories
            SET name = :name, is_active = true, parent_id = NULL, updated_at = now()
            WHERE id = :id
            """
        ),
        {"name": ANIMALS_ROOT_LABEL, "id": root_id},
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

    for label, slug, sort_order in ANIMALS_V2_CANONICAL_LEAVES:
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Animals V2 STOP: missing canonical leaf {slug}")
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

    for slug in sorted(ANIMALS_V2_RETIRED_SLUGS):
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

    # Guard: no unexpected active Animals children outside canonical set.
    active_children = bind.execute(
        text(
            """
            SELECT slug FROM categories
            WHERE parent_id = :pid AND is_active = true
            ORDER BY slug
            """
        ),
        {"pid": root_id},
    ).fetchall()
    active_slugs = {r[0] for r in active_children}
    if active_slugs != set(ANIMALS_V2_CANONICAL_SLUGS):
        raise RuntimeError(
            "Animals V2 STOP: active L2 mismatch "
            f"extra={sorted(active_slugs - ANIMALS_V2_CANONICAL_SLUGS)} "
            f"missing={sorted(ANIMALS_V2_CANONICAL_SLUGS - active_slugs)}"
        )


def downgrade() -> None:
    # Soft retirement is intentionally one-way in ordinary milestone work.
    pass
