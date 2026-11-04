"""Add special-equipment sale VehicleType enum values.

Revision ID: c1e2f3g4h5i6
Revises: b0d1e2f3g4h5
Create Date: 2026-10-04
"""
from __future__ import annotations

from alembic import op

revision = "c1e2f3g4h5i6"
down_revision = "b0d1e2f3g4h5"
branch_labels = None
depends_on = None

_NEW_VALUES = (
    "excavator",
    "loader",
    "truck_crane",
    "aerial_platform",
    "bulldozer",
    "road_roller",
    "grader",
    "manipulator",
    "concrete_equipment",
    "municipal",
    "drilling",
    "crushing_screening",
    "attachment",
    "other_special",
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
