"""Add mototechnika sale VehicleType enum values.

Revision ID: x6f7a8b9c0d1
Revises: w5e6f7a8b9c0
Create Date: 2026-10-04
"""
from __future__ import annotations

from alembic import op

revision = "x6f7a8b9c0d1"
down_revision = "w5e6f7a8b9c0"
branch_labels = None
depends_on = None

_NEW_VALUES = (
    "scooter",
    "atv",
    "buggy",
    "tricycle",
    "snowmobile",
    "kart",
    "other_moto",
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
