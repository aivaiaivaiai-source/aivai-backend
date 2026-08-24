"""media focus bbox fields

Revision ID: i0e1f2a3b4c5
Revises: h9d0e1f2a3b4
Create Date: 2026-08-22
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "i0e1f2a3b4c5"
down_revision: Union[str, None] = "h9d0e1f2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("media", sa.Column("focus_bbox_left", sa.Float(), nullable=True))
    op.add_column("media", sa.Column("focus_bbox_top", sa.Float(), nullable=True))
    op.add_column("media", sa.Column("focus_bbox_width", sa.Float(), nullable=True))
    op.add_column("media", sa.Column("focus_bbox_height", sa.Float(), nullable=True))
    op.add_column("media", sa.Column("focus_confidence", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("media", "focus_confidence")
    op.drop_column("media", "focus_bbox_height")
    op.drop_column("media", "focus_bbox_width")
    op.drop_column("media", "focus_bbox_top")
    op.drop_column("media", "focus_bbox_left")
