# -*- coding: utf-8 -*-
"""Stable create-listing intents for L1 «Работа» (not category tree nodes)."""
from __future__ import annotations

from enum import StrEnum


class JobCreateIntent(StrEnum):
    hiring = "hiring"
    job_seeking = "job_seeking"


HIRING = JobCreateIntent.hiring.value
JOB_SEEKING = JobCreateIntent.job_seeking.value

VALID_JOB_CREATE_INTENTS = frozenset({HIRING, JOB_SEEKING})

# UI labels — presentation only; never use as API/DB identity.
JOB_INTENT_UI_LABELS: dict[str, str] = {
    HIRING: "Ищу сотрудника",
    JOB_SEEKING: "Ищу работу",
}
