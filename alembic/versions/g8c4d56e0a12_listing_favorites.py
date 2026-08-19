"""listing favorites

Revision ID: g8c4d56e0a12
Revises: a1c9e3f82b04
Create Date: 2026-08-17

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "g8c4d56e0a12"
down_revision: Union[str, None] = "a1c9e3f82b04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "listing_favorites",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("listing_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "listing_id",
            name="uq_listing_favorites_user_listing",
        ),
    )
    op.create_index(
        op.f("ix_listing_favorites_user_id"),
        "listing_favorites",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_listing_favorites_listing_id"),
        "listing_favorites",
        ["listing_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_listing_favorites_created_at"),
        "listing_favorites",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_listing_favorites_created_at"), table_name="listing_favorites")
    op.drop_index(op.f("ix_listing_favorites_listing_id"), table_name="listing_favorites")
    op.drop_index(op.f("ix_listing_favorites_user_id"), table_name="listing_favorites")
    op.drop_table("listing_favorites")
