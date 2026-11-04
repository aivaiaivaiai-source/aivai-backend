"""Add calibration_version to listing_visual_evidence (Substage 3C-2B)."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "r0a1b2c3d4e5"
down_revision: Union[str, None] = "q9a0b1c2d3e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "listing_visual_evidence",
        sa.Column("calibration_version", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("listing_visual_evidence", "calibration_version")
