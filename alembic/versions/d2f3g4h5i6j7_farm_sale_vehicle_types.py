"""Add farm-machinery sale VehicleType enum values.

Revision ID: d2f3g4h5i6j7
Revises: c1e2f3g4h5i6
Create Date: 2026-10-04
"""
from __future__ import annotations

from alembic import op

revision = "d2f3g4h5i6j7"
down_revision = "c1e2f3g4h5i6"
branch_labels = None
depends_on = None

_NEW_VALUES = (
    "tractor",
    "walk_behind",
    "combine",
    "seeder",
    "tillage",
    "forage",
    "sprayer",
    "other_agri",
)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    for value in _NEW_VALUES:
        op.execute(
            f"ALTER TYPE vehicle_type_enum ADD VALUE IF NOT EXISTS '{value}'"
        )


def downgrade() -> None:
    pass
