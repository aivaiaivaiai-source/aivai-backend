"""media jobs + transactional outbox (Stage 3/7)

Revision ID: l3b4c5d6e7f8
Revises: k2a3b4c5d6e7
Create Date: 2026-08-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "l3b4c5d6e7f8"
down_revision: Union[str, None] = "k2a3b4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_job_status = postgresql.ENUM(
    "queued",
    "leased",
    "succeeded",
    "failed",
    "dead",
    name="media_job_status_enum",
    create_type=False,
)
_outbox_status = postgresql.ENUM(
    "pending",
    "dispatched",
    name="media_outbox_status_enum",
    create_type=False,
)


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE media_job_status_enum AS ENUM (
                'queued', 'leased', 'succeeded', 'failed', 'dead'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
        """
    )
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE media_outbox_status_enum AS ENUM ('pending', 'dispatched');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
        """
    )

    job_status = _job_status
    outbox_status = _outbox_status

    op.create_table(
        "media_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("media_id", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=256), nullable=False),
        sa.Column("pipeline_version", sa.String(length=32), nullable=False),
        sa.Column("status", job_status, nullable=False, server_default="queued"),
        sa.Column("lease_owner", sa.String(length=128), nullable=True),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error_code", sa.String(length=64), nullable=True),
        sa.Column("last_error_message", sa.String(length=512), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["media_id"], ["media.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_media_jobs_idempotency_key"),
    )
    op.create_index(op.f("ix_media_jobs_media_id"), "media_jobs", ["media_id"])
    op.create_index(op.f("ix_media_jobs_status"), "media_jobs", ["status"])
    op.create_index(
        "ix_media_jobs_dispatch",
        "media_jobs",
        ["status", "available_at"],
        unique=False,
    )

    op.create_table(
        "media_outbox",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("dedupe_key", sa.String(length=256), nullable=False),
        sa.Column("status", outbox_status, nullable=False, server_default="pending"),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.UniqueConstraint("dedupe_key", name="uq_media_outbox_dedupe_key"),
    )
    op.create_index(op.f("ix_media_outbox_job_id"), "media_outbox", ["job_id"])
    op.create_index(op.f("ix_media_outbox_status"), "media_outbox", ["status"])


def downgrade() -> None:
    op.drop_index(op.f("ix_media_outbox_status"), table_name="media_outbox")
    op.drop_index(op.f("ix_media_outbox_job_id"), table_name="media_outbox")
    op.drop_table("media_outbox")
    op.drop_index("ix_media_jobs_dispatch", table_name="media_jobs")
    op.drop_index(op.f("ix_media_jobs_status"), table_name="media_jobs")
    op.drop_index(op.f("ix_media_jobs_media_id"), table_name="media_jobs")
    op.drop_table("media_jobs")
    _outbox_status.drop(op.get_bind(), checkfirst=True)
    _job_status.drop(op.get_bind(), checkfirst=True)
