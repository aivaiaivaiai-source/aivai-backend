"""Media P0 — supersede duplicate category-scoped queued jobs.

Revision ID: e1f2a3b4c5d6mediajob
Revises: d0e1f2a3b4c5repairv2a
Create Date: 2026-11-07

Data maintenance only: mark extra queued/failed media_jobs dead (SUPERSEDED)
so one media has at most one actionable job for its listing's current category.
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "e1f2a3b4c5d6mediajob"
down_revision = "d0e1f2a3b4c5repairv2a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    # For each media_id with multiple actionable jobs, keep the one matching
    # listing.category_id when possible; otherwise keep the newest id.
    rows = bind.execute(
        text(
            """
            SELECT m.id AS media_id, l.category_id
            FROM media m
            JOIN listings l ON l.id = m.listing_id
            WHERE EXISTS (
              SELECT 1 FROM media_jobs j
              WHERE j.media_id = m.id
                AND j.status IN ('queued', 'failed')
              GROUP BY j.media_id
              HAVING count(*) > 1
            )
            """
        )
    ).fetchall()

    for media_id, category_id in rows:
        keep_id = None
        if category_id is not None:
            keep = bind.execute(
                text(
                    """
                    SELECT id FROM media_jobs
                    WHERE media_id = :mid
                      AND status IN ('queued', 'failed')
                      AND idempotency_key LIKE :pat
                    ORDER BY id DESC
                    LIMIT 1
                    """
                ),
                {"mid": int(media_id), "pat": f"%:cat:{int(category_id)}"},
            ).fetchone()
            if keep is not None:
                keep_id = int(keep[0])
        if keep_id is None:
            newest = bind.execute(
                text(
                    """
                    SELECT id FROM media_jobs
                    WHERE media_id = :mid AND status IN ('queued', 'failed')
                    ORDER BY id DESC
                    LIMIT 1
                    """
                ),
                {"mid": int(media_id)},
            ).fetchone()
            if newest is None:
                continue
            keep_id = int(newest[0])

        bind.execute(
            text(
                """
                UPDATE media_jobs
                SET status = 'dead',
                    completed_at = now(),
                    lease_owner = NULL,
                    lease_until = NULL,
                    last_error_code = 'SUPERSEDED',
                    last_error_message = 'Superseded by media job idempotency cleanup',
                    updated_at = now()
                WHERE media_id = :mid
                  AND status IN ('queued', 'failed')
                  AND id <> :keep
                """
            ),
            {"mid": int(media_id), "keep": keep_id},
        )

    # Restore ready when variants exist but lifecycle left queued with no
    # remaining actionable jobs (publish wait hole).
    bind.execute(
        text(
            """
            UPDATE media m
            SET lifecycle_status = 'ready',
                error_code = NULL,
                error_message = NULL,
                updated_at = now()
            WHERE m.lifecycle_status = 'queued'
              AND (
                m.display_storage_key IS NOT NULL
                OR m.display_url IS NOT NULL
                OR m.feed_storage_key IS NOT NULL
                OR m.thumb_storage_key IS NOT NULL
              )
              AND NOT EXISTS (
                SELECT 1 FROM media_jobs j
                WHERE j.media_id = m.id
                  AND j.status IN ('queued', 'leased', 'failed')
              )
              AND EXISTS (
                SELECT 1 FROM media_jobs j
                WHERE j.media_id = m.id AND j.status = 'succeeded'
              )
            """
        )
    )


def downgrade() -> None:
    pass
