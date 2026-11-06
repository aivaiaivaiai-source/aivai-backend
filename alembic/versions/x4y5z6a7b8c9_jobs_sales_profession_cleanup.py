"""Drop three overlapping sales professions from the Jobs catalog.

Revision ID: x4y5z6a7b8c9jobssales
Revises: w3x4y5z6a7b8commdep
Create Date: 2026-11-06

Canonical metadata only. Does not delete listing_field_values.
Fresh installs pick up the same roles from JOB_SECTIONS via the seed loader.
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

revision = "x4y5z6a7b8c9jobssales"
down_revision = "w3x4y5z6a7b8commdep"
branch_labels = None
depends_on = None

_SLUG = "jobs-prodazhi-i-torgovlya"

_PREVIOUS = (
    "Продавец",
    "Продавец-консультант",
    "Продавец-кассир",
    "Кассир",
    "Торговый агент",
    "Торговый представитель",
    "Менеджер по продажам",
    "Менеджер интернет-магазина",
    "Мерчандайзер",
    "Супервайзер",
    "Заведующий магазином",
    "Руководитель отдела продаж",
    "Другие профессии продаж и торговли",
)


def _choices(labels: tuple[str, ...]) -> str:
    return json.dumps(
        {"choices": [{"value": label, "label": label} for label in labels]},
        ensure_ascii=False,
    )


def _current_labels() -> tuple[str, ...]:
    from app.seeds.jobs_sections_catalog import JOB_SECTIONS

    for section in JOB_SECTIONS.values():
        if section["category_slug"] == _SLUG:
            return tuple(role["value"] for role in section["roles"])
    raise RuntimeError(f"missing section {_SLUG}")


def _write(labels: tuple[str, ...]) -> None:
    from app.models.job_create_intent import HIRING, JOB_SEEKING

    bind = op.get_bind()
    category_id = bind.execute(
        text("SELECT id FROM categories WHERE slug = :slug"),
        {"slug": _SLUG},
    ).scalar()
    if category_id is None:
        return
    payload = _choices(labels)
    for intent in (HIRING, JOB_SEEKING):
        bind.execute(
            text(
                """
                UPDATE category_core_fields
                SET options = CAST(:options AS jsonb)
                WHERE category_id = :category_id
                  AND field_key = 'job_role'
                  AND create_intent = :intent
                """
            ),
            {
                "options": payload,
                "category_id": category_id,
                "intent": intent,
            },
        )


def upgrade() -> None:
    _write(_current_labels())


def downgrade() -> None:
    _write(_PREVIOUS)
