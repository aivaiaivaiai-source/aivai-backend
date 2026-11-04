"""Add cargo-transport sale VehicleType enum values.

Revision ID: a9c0d1e2f3g4
Revises: z8b9c0d1e2f3
Create Date: 2026-10-04
"""
from __future__ import annotations

from alembic import op

revision = "a9c0d1e2f3g4"
down_revision = "z8b9c0d1e2f3"
branch_labels = None
depends_on = None

_NEW_VALUES = (
    "dump_truck",
    "tractor_unit",
    "flatbed_truck",
    "box_truck",
    "tanker_truck",
    "tow_truck",
    "other_truck",
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
