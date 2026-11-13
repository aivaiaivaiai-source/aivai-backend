"""Ready Business V2 — taxonomy + product identity cleanup.

Revision ID: e0f1a2b3c4d5rbrtax
Revises: d9e0f1a2b3c4matpb
Create Date: 2026-11-13

- Soft-retire legacy cafe/retail/online/franchise L2 (rows kept; cores cleared)
- Soft-retire Shares/Investment, Crypto, Turnkey modern L2
- Keep 16 cleaned modern L2 active; schema-less until Package A
- Root ready-business picker-only; canonical full label
- STOP if Ready Business subtree has listings
- Does NOT seed Package A Create cores / Search filters
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "e0f1a2b3c4d5rbrtax"
down_revision = "d9e0f1a2b3c4matpb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.ready_business_v2 import (
        READY_BUSINESS_ROOT_LABEL,
        READY_BUSINESS_ROOT_SLUG,
        READY_BUSINESS_V2_CANONICAL_LEAVES,
        READY_BUSINESS_V2_CANONICAL_SLUGS,
        READY_BUSINESS_V2_RETIRED_SLUGS,
        ready_business_v2_assert_cleanup_contracts,
    )

    ready_business_v2_assert_cleanup_contracts()
    bind = op.get_bind()

    root = bind.execute(
        text("SELECT id FROM categories WHERE slug = :slug"),
        {"slug": READY_BUSINESS_ROOT_SLUG},
    ).fetchone()
    if root is None:
        raise RuntimeError("ready-business root missing")
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
            f"Ready Business V2 taxonomy cleanup STOP: unexpected listings ({total})"
        )

    bind.execute(
        text(
            """
            UPDATE categories
            SET name = :name, is_active = true, parent_id = NULL, updated_at = now()
            WHERE id = :id
            """
        ),
        {"name": READY_BUSINESS_ROOT_LABEL, "id": root_id},
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

    for label, slug, sort_order in READY_BUSINESS_V2_CANONICAL_LEAVES:
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Ready Business V2 STOP: missing canonical leaf {slug}")
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

    for slug in sorted(READY_BUSINESS_V2_RETIRED_SLUGS):
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

    # Any other non-canonical child under root → soft-retire + clear schema.
    extras = bind.execute(
        text("SELECT id, slug FROM categories WHERE parent_id = :pid"),
        {"pid": root_id},
    ).fetchall()
    for cid, slug in extras:
        if slug in READY_BUSINESS_V2_CANONICAL_SLUGS:
            continue
        bind.execute(
            text(
                "UPDATE categories SET is_active = false, updated_at = now() WHERE id = :id"
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
    # Non-destructive downgrade intentionally omitted — taxonomy cleanup is forward-only.
    pass
