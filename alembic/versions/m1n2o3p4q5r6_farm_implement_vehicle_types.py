"""Add farm implement / attachment VehicleType values (Lalafo chips).

Revision ID: m1n2o3p4q5r6
Revises: l0m1n2o3p4q5
Create Date: 2026-10-09
"""
from __future__ import annotations

from alembic import op

revision = "m1n2o3p4q5r6"
down_revision = "l0m1n2o3p4q5"
branch_labels = None
depends_on = None

_NEW_VALUES = (
    "potato_planter",
    "plow",
    "harrow",
    "cultivator",
    "hiller",
    "ditcher",
    "mulcher",
    "mower",
    "walk_behind_mower",
    "baler",
    "header",
    "rake",
    "feed_mixer",
    "fertilizer_spreader",
    "manure_spreader",
    "potato_digger",
    "kun",
    "farm_crusher",
    "grain_thrower",
    "grain_cleaner",
    "film_layer",
    "ridge_former",
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
