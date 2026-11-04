"""Add electric-transport sale VehicleType enum values.

Revision ID: y7a8b9c0d1e2
Revises: x6f7a8b9c0d1
Create Date: 2026-10-04
"""
from __future__ import annotations

from alembic import op

revision = "y7a8b9c0d1e2"
down_revision = "x6f7a8b9c0d1"
branch_labels = None
depends_on = None

_NEW_VALUES = (
    "e_scooter",
    "hoverboard",
    "monowheel",
    "segway",
    "golf_cart",
    "other_electric",
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
