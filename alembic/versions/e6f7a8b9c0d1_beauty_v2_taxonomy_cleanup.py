"""Beauty & Personal Care V2 — taxonomy + product-identity cleanup.

Revision ID: e6f7a8b9c0d1beauty
Revises: d5e6f7a8b9c0sphpb
Create Date: 2026-11-13

- Soft-retire legacy beauty-cosmetics / beauty-hair
- Keep 16 modern L2 active; rename manicure + tattoo labels
- Clear cores/filters on root + modern leaves (schema-less until Package A)
- STOP if Beauty subtree has listings
- Does NOT seed Package A Create cores / Search filters
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "e6f7a8b9c0d1beauty"
down_revision = "d5e6f7a8b9c0sphpb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.beauty_v2 import (
        BEAUTY_ROOT_LABEL,
        BEAUTY_ROOT_SLUG,
        BEAUTY_V2_CANONICAL_LEAVES,
        BEAUTY_V2_CANONICAL_SLUGS,
        BEAUTY_V2_RETIRED_SLUGS,
        beauty_v2_assert_cleanup_contracts,
    )

    beauty_v2_assert_cleanup_contracts()
    bind = op.get_bind()

    root = bind.execute(
        text("SELECT id FROM categories WHERE slug = :slug"),
        {"slug": BEAUTY_ROOT_SLUG},
    ).fetchone()
    if root is None:
        raise RuntimeError("beauty root missing")
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
            f"Beauty V2 taxonomy cleanup STOP: unexpected listings ({total})"
        )

    eav = bind.execute(
        text(
            """
            WITH RECURSIVE t AS (
              SELECT id FROM categories WHERE id = :rid
              UNION ALL
              SELECT c.id FROM categories c JOIN t ON c.parent_id = t.id
            )
            SELECT count(*)
            FROM listing_field_values lfv
            JOIN listings l ON l.id = lfv.listing_id
            JOIN t ON l.category_id = t.id
            """
        ),
        {"rid": root_id},
    ).scalar_one()
    if int(eav or 0) > 0:
        raise RuntimeError(
            f"Beauty V2 taxonomy cleanup STOP: unexpected EAV rows ({eav})"
        )

    bind.execute(
        text(
            """
            UPDATE categories
            SET name = :name, is_active = true, parent_id = NULL, updated_at = now()
            WHERE id = :id
            """
        ),
        {"name": BEAUTY_ROOT_LABEL, "id": root_id},
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

    for label, slug, sort_order in BEAUTY_V2_CANONICAL_LEAVES:
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Beauty V2 STOP: missing canonical leaf {slug}")
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
            {
                "name": label,
                "pid": root_id,
                "sort": sort_order,
                "id": cid,
            },
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

    for slug in sorted(BEAUTY_V2_RETIRED_SLUGS):
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
            "category_aliases",
        ):
            bind.execute(
                text(f"DELETE FROM {table} WHERE category_id = :cid"),
                {"cid": cid},
            )

    extras = bind.execute(
        text(
            """
            SELECT id, slug FROM categories
            WHERE parent_id = :pid AND is_active = true
            """
        ),
        {"pid": root_id},
    ).fetchall()
    for row in extras:
        if row[1] in BEAUTY_V2_CANONICAL_SLUGS:
            continue
        cid = int(row[0])
        bind.execute(
            text(
                "UPDATE categories SET is_active = false, updated_at = now() WHERE id = :id"
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
    # Soft-retire cleanup is not reversed automatically.
    pass
