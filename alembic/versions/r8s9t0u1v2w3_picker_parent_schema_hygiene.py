"""Clear stale live schema on Transport picker-only parents.

Revision ID: r8s9t0u1v2w3pickerparent
Revises: q7r8s9t0u1v2autosvcprice
Create Date: 2026-11-04

Parents with active children must not keep competing Create/Search SoT.
Leaf schemas are untouched. Does not mutate listings.
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "r8s9t0u1v2w3pickerparent"
down_revision = "q7r8s9t0u1v2autosvcprice"
branch_labels = None
depends_on = None

# Confirmed picker-only parents (active children; Create requires leaf).
_PICKER_PARENT_SLUGS: tuple[str, ...] = (
    "transport-moto-tech",
    "transport-electric",
    "transport-bicycles",
    "transport-buses-microbuses-motorhomes",
    "transport-special-equipment",
)


def upgrade() -> None:
    bind = op.get_bind()
    for slug in _PICKER_PARENT_SLUGS:
        cid = bind.execute(
            text("SELECT id FROM categories WHERE slug = :s"),
            {"s": slug},
        ).scalar_one_or_none()
        if cid is None:
            continue
        kids = bind.execute(
            text(
                """
                SELECT count(*) FROM categories
                WHERE parent_id = :cid AND is_active IS TRUE
                """
            ),
            {"cid": cid},
        ).scalar_one()
        if int(kids or 0) <= 0:
            continue
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
    # Stale parent schemas are not restored; leaf SoT remains authoritative.
    pass
