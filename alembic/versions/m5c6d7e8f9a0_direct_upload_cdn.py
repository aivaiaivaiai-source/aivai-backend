"""direct upload fields + storage cleanup queue (Stage 5/7)

Revision ID: m5c6d7e8f9a0
Revises: l3b4c5d6e7f8
Create Date: 2026-08-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "m5c6d7e8f9a0"
down_revision: Union[str, None] = "l3b4c5d6e7f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_cleanup_status = postgresql.ENUM(
    "pending",
    "done",
    "dead",
    name="media_storage_cleanup_status_enum",
    create_type=False,
)


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE media_storage_cleanup_status_enum AS ENUM (
                'pending', 'done', 'dead'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
        """
    )

    op.add_column(
        "media",
        sa.Column("display_storage_key", sa.String(length=512), nullable=True),
    )
    op.add_column(
        "media",
        sa.Column("feed_storage_key", sa.String(length=512), nullable=True),
    )
    op.add_column(
        "media",
        sa.Column("thumb_storage_key", sa.String(length=512), nullable=True),
    )
    op.add_column(
        "media",
        sa.Column("upload_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "media",
        sa.Column("upload_completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "media",
        sa.Column("declared_content_type", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "media",
        sa.Column("declared_content_length", sa.Integer(), nullable=True),
    )

    status = _cleanup_status
    op.create_table(
        "media_storage_cleanup",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("media_id", sa.Integer(), nullable=True),
        sa.Column("reason", sa.String(length=64), nullable=False),
        sa.Column("status", status, nullable=False, server_default="pending"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_media_storage_cleanup_storage_key"),
        "media_storage_cleanup",
        ["storage_key"],
    )
    op.create_index(
        op.f("ix_media_storage_cleanup_media_id"),
        "media_storage_cleanup",
        ["media_id"],
    )
    op.create_index(
        op.f("ix_media_storage_cleanup_status"),
        "media_storage_cleanup",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_media_storage_cleanup_status"), table_name="media_storage_cleanup")
    op.drop_index(op.f("ix_media_storage_cleanup_media_id"), table_name="media_storage_cleanup")
    op.drop_index(
        op.f("ix_media_storage_cleanup_storage_key"),
        table_name="media_storage_cleanup",
    )
    op.drop_table("media_storage_cleanup")
    op.drop_column("media", "declared_content_length")
    op.drop_column("media", "declared_content_type")
    op.drop_column("media", "upload_completed_at")
    op.drop_column("media", "upload_expires_at")
    op.drop_column("media", "thumb_storage_key")
    op.drop_column("media", "feed_storage_key")
    op.drop_column("media", "display_storage_key")
    _cleanup_status.drop(op.get_bind(), checkfirst=True)
