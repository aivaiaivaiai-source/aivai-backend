"""Add water-transport sale VehicleType enum values.

Revision ID: e3g4h5i6j7k8
Revises: d2f3g4h5i6j7
Create Date: 2026-10-04
"""
from __future__ import annotations

from alembic import op

revision = "e3g4h5i6j7k8"
down_revision = "d2f3g4h5i6j7"
branch_labels = None
depends_on = None

_NEW_VALUES = (
    "boat",
    "motorboat",
    "yacht",
    "jet_ski",
    "other_watercraft",
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
