"""Add Lalafo-aligned special-equipment sale VehicleType values.

Revision ID: h6j7k8l9m0n1
Revises: g5i6j7k8l9m0
Create Date: 2026-10-09
"""
from __future__ import annotations

from alembic import op

revision = "h6j7k8l9m0n1"
down_revision = "g5i6j7k8l9m0"
branch_labels = None
depends_on = None

_NEW_VALUES = (
    "concrete_mixer",
    "concrete_pump",
    "septic_truck",
    "mini_dumper",
    "forklift",
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
