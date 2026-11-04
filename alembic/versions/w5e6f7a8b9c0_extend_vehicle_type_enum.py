"""Extend vehicle_type_enum for parts applicability catalogs.

Revision ID: w5e6f7a8b9c0
Revises: v4d5e6f7a8b9
Create Date: 2026-10-04

Adds agricultural / electric / bicycle / watercraft / trailer so parts Step1
applicability keys can map 1:1 onto VehicleBrand.vehicle_type.
"""
from __future__ import annotations

from alembic import op

revision = "w5e6f7a8b9c0"
down_revision = "v4d5e6f7a8b9"
branch_labels = None
depends_on = None

_NEW_VALUES = (
    "agricultural",
    "electric",
    "bicycle",
    "watercraft",
    "trailer",
)


def upgrade() -> None:
    # ADD VALUE cannot run inside a transaction block on older PG; IF NOT EXISTS
    # is safe for re-runs. Each statement commits implicitly via autocommit.
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    for value in _NEW_VALUES:
        op.execute(
            f"ALTER TYPE vehicle_type_enum ADD VALUE IF NOT EXISTS '{value}'"
        )


def downgrade() -> None:
    # Postgres cannot remove enum values safely without table rewrite.
    pass
