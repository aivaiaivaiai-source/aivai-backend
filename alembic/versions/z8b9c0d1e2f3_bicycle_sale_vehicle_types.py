"""Add bicycle sale VehicleType enum values.

Revision ID: z8b9c0d1e2f3
Revises: y7a8b9c0d1e2
Create Date: 2026-10-04
"""
from __future__ import annotations

from alembic import op

revision = "z8b9c0d1e2f3"
down_revision = "y7a8b9c0d1e2"
branch_labels = None
depends_on = None

_NEW_VALUES = (
    "mountain_bike",
    "city_bike",
    "road_bike",
    "bmx",
    "other_bicycle",
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
