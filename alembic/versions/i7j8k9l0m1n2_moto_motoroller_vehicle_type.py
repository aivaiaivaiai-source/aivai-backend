"""Add motoroller VehicleType for Lalafo «Мотороллеры муравей».

Revision ID: i7j8k9l0m1n2
Revises: h6j7k8l9m0n1
Create Date: 2026-10-09
"""
from __future__ import annotations

from alembic import op

revision = "i7j8k9l0m1n2"
down_revision = "h6j7k8l9m0n1"
branch_labels = None
depends_on = None

_NEW_VALUES = ("motoroller",)


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
