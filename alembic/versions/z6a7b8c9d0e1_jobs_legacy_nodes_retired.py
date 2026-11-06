"""Retire legacy Jobs vacancy/resume nodes.

Revision ID: z6a7b8c9d0e1jobslegacy
Revises: y5z6a7b8c9d0jobswmexp
Create Date: 2026-11-06

Soft-deactivate vacancy/resume buckets that are not profession sectors.
Clears their Create/Search schema only when they have zero listings.
Does not touch jobs root, the 19 canonical sectors, abroad, aliases, or listings.
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "z6a7b8c9d0e1jobslegacy"
down_revision = "y5z6a7b8c9d0jobswmexp"
branch_labels = None
depends_on = None

_RETIRED = (
    "jobs-vacancies",
    "jobs-resume",
    "jobs-rezyume-soiskateley",
    "jobs-vakansii-bez-opyta",
)


def upgrade() -> None:
    bind = op.get_bind()
    for slug in _RETIRED:
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            continue
        cid = int(row[0])
        listings = bind.execute(
            text("SELECT count(*) FROM listings WHERE category_id = :cid"),
            {"cid": cid},
        ).scalar_one()
        if int(listings or 0) > 0:
            raise RuntimeError(
                f"refusing to retire Jobs legacy node with listings: {slug}"
            )
        kids = bind.execute(
            text(
                """
                SELECT count(*) FROM categories
                WHERE parent_id = :cid AND is_active IS TRUE
                """
            ),
            {"cid": cid},
        ).scalar_one()
        if int(kids or 0) > 0:
            raise RuntimeError(
                f"refusing to retire Jobs legacy node with active children: {slug}"
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
        bind.execute(
            text(
                """
                UPDATE categories
                SET is_active = false, updated_at = now()
                WHERE id = :cid
                """
            ),
            {"cid": cid},
        )


def downgrade() -> None:
    # Reactivate the rows only. Cleared schemas are not restored.
    bind = op.get_bind()
    for slug in _RETIRED:
        bind.execute(
            text(
                """
                UPDATE categories
                SET is_active = true, updated_at = now()
                WHERE slug = :slug
                """
            ),
            {"slug": slug},
        )
