"""Sport / Recreation / Hobbies V2 — taxonomy + product-identity cleanup.

Revision ID: b3c4d5e6f7a8sphtax
Revises: a2b3c4d5e6f7rbpb
Create Date: 2026-11-13

- Soft-retire legacy sports-equipment / sports-tourism / sports-music
- Soft-retire national craft L2 (yurts, felt) — no destination
- Keep 13 cleaned modern L2 active; schema-less until Package A
- Root sports-hobby picker-only; canonical label
- STOP if Sport subtree has listings
- Does NOT seed Package A Create cores / Search filters
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "b3c4d5e6f7a8sphtax"
down_revision = "a2b3c4d5e6f7rbpb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.sport_v2 import (
        SPORT_ROOT_LABEL,
        SPORT_ROOT_SLUG,
        SPORT_V2_CANONICAL_LEAVES,
        SPORT_V2_CANONICAL_SLUGS,
        SPORT_V2_RETIRED_SLUGS,
        sport_v2_assert_cleanup_contracts,
    )

    sport_v2_assert_cleanup_contracts()
    bind = op.get_bind()

    root = bind.execute(
        text("SELECT id FROM categories WHERE slug = :slug"),
        {"slug": SPORT_ROOT_SLUG},
    ).fetchone()
    if root is None:
        raise RuntimeError("sports-hobby root missing")
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
            f"Sport V2 taxonomy cleanup STOP: unexpected listings ({total})"
        )

    bind.execute(
        text(
            """
            UPDATE categories
            SET name = :name, is_active = true, parent_id = NULL, updated_at = now()
            WHERE id = :id
            """
        ),
        {"name": SPORT_ROOT_LABEL, "id": root_id},
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

    for label, slug, sort_order in SPORT_V2_CANONICAL_LEAVES:
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Sport V2 STOP: missing canonical leaf {slug}")
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
        # Schema-less until Package A — clear any accidental cores/filters.
        for table in (
            "category_core_fields",
            "category_optional_fields",
            "category_filters",
        ):
            bind.execute(
                text(f"DELETE FROM {table} WHERE category_id = :cid"),
                {"cid": cid},
            )

    for slug in sorted(SPORT_V2_RETIRED_SLUGS):
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

    # Any other active child under root that is not canonical → retire.
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
        if row[1] in SPORT_V2_CANONICAL_SLUGS:
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
