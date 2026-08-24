"""media lifecycle foundation (Stage 1/7)

Revision ID: j1f2a3b4c5d6
Revises: i0e1f2a3b4c5
Create Date: 2026-08-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "j1f2a3b4c5d6"
down_revision: Union[str, None] = "i0e1f2a3b4c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_lifecycle_enum = sa.Enum(
    "uploading",
    "queued",
    "processing",
    "ready",
    "rejected",
    "failed",
    name="media_lifecycle_status_enum",
)


def upgrade() -> None:
    _lifecycle_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "media",
        sa.Column(
            "lifecycle_status",
            _lifecycle_enum,
            nullable=False,
            server_default="ready",
        ),
    )
    op.add_column("media", sa.Column("client_upload_id", sa.Uuid(), nullable=True))
    op.add_column("media", sa.Column("content_sha256", sa.String(length=64), nullable=True))
    op.add_column("media", sa.Column("pipeline_version", sa.String(length=32), nullable=True))
    op.add_column(
        "media",
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("media", sa.Column("error_code", sa.String(length=64), nullable=True))
    op.add_column("media", sa.Column("error_message", sa.String(length=512), nullable=True))
    op.add_column("media", sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("media", sa.Column("original_url", sa.String(length=2048), nullable=True))
    op.add_column("media", sa.Column("display_url", sa.String(length=2048), nullable=True))
    op.add_column("media", sa.Column("feed_url", sa.String(length=2048), nullable=True))
    op.add_column("media", sa.Column("thumb_url", sa.String(length=2048), nullable=True))

    # Legacy rows: uploaded file URL is the only variant today.
    op.execute(
        """
        UPDATE media
        SET original_url = url,
            display_url = url
        WHERE chat_id IS NULL
          AND is_placeholder = false
          AND url IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE media
        SET processed_at = COALESCE(moderated_at, created_at)
        WHERE lifecycle_status = 'ready'
        """
    )
    op.execute(
        """
        UPDATE media
        SET lifecycle_status = 'rejected'
        WHERE moderation_status = 'rejected'
        """
    )

    op.create_index(
        "uq_media_listing_client_upload_id",
        "media",
        ["listing_id", "client_upload_id"],
        unique=True,
        postgresql_where=sa.text("client_upload_id IS NOT NULL"),
        sqlite_where=sa.text("client_upload_id IS NOT NULL"),
    )
    op.create_index(
        op.f("ix_media_lifecycle_status"),
        "media",
        ["lifecycle_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_media_lifecycle_status"), table_name="media")
    op.drop_index("uq_media_listing_client_upload_id", table_name="media")
    op.drop_column("media", "thumb_url")
    op.drop_column("media", "feed_url")
    op.drop_column("media", "display_url")
    op.drop_column("media", "original_url")
    op.drop_column("media", "processed_at")
    op.drop_column("media", "error_message")
    op.drop_column("media", "error_code")
    op.drop_column("media", "attempt_count")
    op.drop_column("media", "pipeline_version")
    op.drop_column("media", "content_sha256")
    op.drop_column("media", "client_upload_id")
    op.drop_column("media", "lifecycle_status")
    _lifecycle_enum.drop(op.get_bind(), checkfirst=True)
