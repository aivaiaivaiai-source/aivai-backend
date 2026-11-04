"""Add trailer sale VehicleType enum values.

Revision ID: f4h5i6j7k8l9
Revises: e3g4h5i6j7k8
Create Date: 2026-10-04
"""
from __future__ import annotations

from alembic import op

revision = "f4h5i6j7k8l9"
down_revision = "e3g4h5i6j7k8"
branch_labels = None
depends_on = None

_NEW_VALUES = (
    "drawbar_trailer",
    "semi_trailer",
    "camper_trailer",
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
