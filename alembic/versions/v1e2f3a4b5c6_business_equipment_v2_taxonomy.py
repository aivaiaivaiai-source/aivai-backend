"""Business Equipment V2 taxonomy + platform coherence cleanup.

Revision ID: v1e2f3a4b5c6biztax
Revises: u0d1e2f3a4b5stationpb
Create Date: 2026-11-12

- Soft-retire legacy cafe / retail / industrial L2 (rows kept; cores/filters cleared)
- Keep 20 modern business-equipment-* L2 active; single Trade direction
- Root business-equipment picker-only; canonical label Бизнес-оборудование
- STOP if Business Equipment subtree has listings
- Does NOT seed Package A Create cores / Search filters
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "v1e2f3a4b5c6biztax"
down_revision = "u0d1e2f3a4b5stationpb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.business_equipment_v2 import (
        BUSINESS_EQUIPMENT_ROOT_LABEL,
        BUSINESS_EQUIPMENT_ROOT_SLUG,
        BUSINESS_EQUIPMENT_V2_CANONICAL_LEAVES,
        BUSINESS_EQUIPMENT_V2_CANONICAL_SLUGS,
        BUSINESS_EQUIPMENT_V2_RETIRED_SLUGS,
        business_equipment_v2_assert_cleanup_contracts,
    )

    business_equipment_v2_assert_cleanup_contracts()
    bind = op.get_bind()

    root = bind.execute(
        text("SELECT id FROM categories WHERE slug = :slug"),
        {"slug": BUSINESS_EQUIPMENT_ROOT_SLUG},
    ).fetchone()
    if root is None:
        raise RuntimeError("business-equipment root missing")
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
            f"Business Equipment V2 taxonomy cleanup STOP: unexpected listings ({total})"
        )

    bind.execute(
        text(
            """
            UPDATE categories
            SET name = :name, is_active = true, parent_id = NULL, updated_at = now()
            WHERE id = :id
            """
        ),
        {"name": BUSINESS_EQUIPMENT_ROOT_LABEL, "id": root_id},
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

    for label, slug, sort_order in BUSINESS_EQUIPMENT_V2_CANONICAL_LEAVES:
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Business Equipment V2 STOP: missing canonical leaf {slug}")
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

    for slug in sorted(BUSINESS_EQUIPMENT_V2_RETIRED_SLUGS):
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

    # Any other unexpected children under root → soft-retire (dual-tree guard).
    children = bind.execute(
        text("SELECT id, slug FROM categories WHERE parent_id = :pid"),
        {"pid": root_id},
    ).fetchall()
    for cid, slug in children:
        if slug in BUSINESS_EQUIPMENT_V2_CANONICAL_SLUGS:
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
    # Soft-retired legacy rows are not reactivated automatically.
    pass
