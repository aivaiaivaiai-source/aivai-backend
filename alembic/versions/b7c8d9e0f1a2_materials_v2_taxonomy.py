"""Materials / Raw Materials V2 taxonomy + platform coherence cleanup.

Revision ID: b7c8d9e0f1a2mattax
Revises: a6d7e8f9a0b1medpb
Create Date: 2026-11-12

- Soft-retire legacy triad materials-textile/metal/chemical (rows kept; cores cleared)
- Soft-retire Import/Wholesale L2 (sales mode ≠ product identity)
- Keep 18 modern materials-* L2 active; schema-less until Package A
- Root materials picker-only; canonical label
- STOP if Materials subtree has listings
- Does NOT seed Package A Create cores / Search filters
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "b7c8d9e0f1a2mattax"
down_revision = "a6d7e8f9a0b1medpb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.materials_v2 import (
        MATERIALS_ROOT_LABEL,
        MATERIALS_ROOT_SLUG,
        MATERIALS_V2_CANONICAL_LEAVES,
        MATERIALS_V2_CANONICAL_SLUGS,
        MATERIALS_V2_RETIRED_SLUGS,
        materials_v2_assert_cleanup_contracts,
    )

    materials_v2_assert_cleanup_contracts()
    bind = op.get_bind()

    root = bind.execute(
        text("SELECT id FROM categories WHERE slug = :slug"),
        {"slug": MATERIALS_ROOT_SLUG},
    ).fetchone()
    if root is None:
        raise RuntimeError("materials root missing")
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
            f"Materials V2 taxonomy cleanup STOP: unexpected listings ({total})"
        )

    bind.execute(
        text(
            """
            UPDATE categories
            SET name = :name, is_active = true, parent_id = NULL, updated_at = now()
            WHERE id = :id
            """
        ),
        {"name": MATERIALS_ROOT_LABEL, "id": root_id},
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

    for label, slug, sort_order in MATERIALS_V2_CANONICAL_LEAVES:
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Materials V2 STOP: missing canonical leaf {slug}")
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
            # Modern leaves stay schema-less until Package A.
            bind.execute(
                text(f"DELETE FROM {table} WHERE category_id = :cid"),
                {"cid": cid},
            )

    for slug in sorted(MATERIALS_V2_RETIRED_SLUGS):
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
        if slug in MATERIALS_V2_CANONICAL_SLUGS:
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
    # Soft-retired legacy / import rows are not reactivated automatically.
    pass
