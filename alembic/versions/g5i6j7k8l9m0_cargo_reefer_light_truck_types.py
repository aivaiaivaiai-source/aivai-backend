"""Add refrigerated_truck and light_truck VehicleType enum values.

Revision ID: g5i6j7k8l9m0
Revises: f4h5i6j7k8l9
Create Date: 2026-10-04
"""
from __future__ import annotations

from alembic import op

revision = "g5i6j7k8l9m0"
down_revision = "f4h5i6j7k8l9"
branch_labels = None
depends_on = None

_NEW_VALUES = (
    "refrigerated_truck",
    "light_truck",
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
