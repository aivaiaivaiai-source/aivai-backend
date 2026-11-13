"""Retire free-exchange root (Отдам бесплатно, обмен и находки).

Revision ID: b9c0d1e2f3a4freex
Revises: a8b9c0d1e2f3beautypb
Create Date: 2026-11-13

Product decision: free-exchange is NOT an AiVai category — soft-retire only.
- STOP if any listings exist under the subtree
- Soft-retire root + descendants (is_active=false)
- Clear cores / optional fields / filters / aliases
- Does NOT hard-delete category rows
- Does NOT invent Package A/B or listing_mode replacements
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "b9c0d1e2f3a4freex"
down_revision = "a8b9c0d1e2f3beautypb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.free_exchange_retirement import (
        FREE_EXCHANGE_RETIRED_SLUGS,
        FREE_EXCHANGE_ROOT_SLUG,
        free_exchange_assert_retirement_contracts,
    )

    free_exchange_assert_retirement_contracts()
    bind = op.get_bind()

    root = bind.execute(
        text("SELECT id FROM categories WHERE slug = :slug"),
        {"slug": FREE_EXCHANGE_ROOT_SLUG},
    ).fetchone()
    if root is None:
        # Already absent — ensure contracts still hold for seed authority.
        return
    root_id = int(root[0])

    listing_n = bind.execute(
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
    if int(listing_n or 0) > 0:
        raise RuntimeError(
            f"free-exchange retirement STOP: unexpected listings ({listing_n})"
        )

    eav_n = bind.execute(
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
    if int(eav_n or 0) > 0:
        raise RuntimeError(
            f"free-exchange retirement STOP: unexpected EAV rows ({eav_n})"
        )

    rows = bind.execute(
        text(
            """
            WITH RECURSIVE t AS (
              SELECT id, slug FROM categories WHERE id = :rid
              UNION ALL
              SELECT c.id, c.slug FROM categories c JOIN t ON c.parent_id = t.id
            )
            SELECT id, slug FROM t
            """
        ),
        {"rid": root_id},
    ).fetchall()

    for cid, slug in rows:
        if slug not in FREE_EXCHANGE_RETIRED_SLUGS and slug != FREE_EXCHANGE_ROOT_SLUG:
            # Unexpected extra child under free-exchange — still soft-retire.
            pass
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
            "category_aliases",
        ):
            bind.execute(
                text(f"DELETE FROM {table} WHERE category_id = :cid"),
                {"cid": int(cid)},
            )

    # Disable legacy routing rules that targeted free-exchange leaves.
    bind.execute(
        text(
            """
            UPDATE category_ai_rules
            SET is_active = false, updated_at = now()
            WHERE name IN ('free_sofa', 'found_documents')
               OR coalesce(config->>'target_category_slug', '') IN
                  ('free-give', 'free-found', 'free-exchange-swap', 'free-exchange')
            """
        )
    )


def downgrade() -> None:
    # Forward-only product retirement — do not resurrect free-exchange.
    pass
