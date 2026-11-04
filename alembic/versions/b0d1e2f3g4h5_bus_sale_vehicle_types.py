"""Add bus-branch sale VehicleType enum values.

Revision ID: b0d1e2f3g4h5
Revises: a9c0d1e2f3g4
Create Date: 2026-10-04
"""
from __future__ import annotations

from alembic import op

revision = "b0d1e2f3g4h5"
down_revision = "a9c0d1e2f3g4"
branch_labels = None
depends_on = None

_NEW_VALUES = (
    "microbus",
    "motorhome",
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
