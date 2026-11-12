"""Stationery & Books V2 taxonomy cleanup.

Revision ID: s8b9c0d1e2f3stationtax
Revises: r7a8b9c0d1e2animalpb
Create Date: 2026-11-12

- Soft-retire books-fiction / books-study (rows kept; cores/filters cleared)
- Keep 15 modern stationery-books-* L2 active; rename e-publications label
- Root stationery-books picker-only
- STOP if Stationery subtree has listings
- Does NOT seed Package A Create cores / Search filters
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "s8b9c0d1e2f3stationtax"
down_revision = "r7a8b9c0d1e2animalpb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.stationery_v2 import (
        STATIONERY_ROOT_LABEL,
        STATIONERY_ROOT_SLUG,
        STATIONERY_V2_CANONICAL_LEAVES,
        STATIONERY_V2_CANONICAL_SLUGS,
        STATIONERY_V2_RETIRED_SLUGS,
        stationery_v2_assert_cleanup_contracts,
    )

    stationery_v2_assert_cleanup_contracts()
    bind = op.get_bind()

    root = bind.execute(
        text("SELECT id FROM categories WHERE slug = :slug"),
        {"slug": STATIONERY_ROOT_SLUG},
    ).fetchone()
    if root is None:
        raise RuntimeError("stationery-books root missing")
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
            f"Stationery V2 taxonomy cleanup STOP: unexpected listings ({total})"
        )

    bind.execute(
        text(
            """
            UPDATE categories
            SET name = :name, is_active = true, parent_id = NULL, updated_at = now()
            WHERE id = :id
            """
        ),
        {"name": STATIONERY_ROOT_LABEL, "id": root_id},
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

    for label, slug, sort_order in STATIONERY_V2_CANONICAL_LEAVES:
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Stationery V2 STOP: missing canonical leaf {slug}")
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

    for slug in sorted(STATIONERY_V2_RETIRED_SLUGS):
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

    # Any other active child under root that is not canonical → soft-retire.
    children = bind.execute(
        text("SELECT id, slug, is_active FROM categories WHERE parent_id = :pid"),
        {"pid": root_id},
    ).fetchall()
    for cid, slug, is_active in children:
        if slug in STATIONERY_V2_CANONICAL_SLUGS:
            continue
        if not is_active and slug in STATIONERY_V2_RETIRED_SLUGS:
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
    # Forward-only taxonomy cleanup — do not resurrect dual tree.
    pass
