# -*- coding: utf-8 -*-
"""Бытовые услуги.

Вид — работа мастерской, а не модель обуви, тип ключа или вид ножа.
Уборка, химчистка, пошив одежды, ремонт техники, аварийное вскрытие,
фото и видео, полиграфия и сад — отдельные разделы Услуг.
"""
from __future__ import annotations

from typing import Any


def _opts(*labels: str) -> list[dict[str, str]]:
    return [{"value": label, "label": label} for label in labels]


_KINDS = (
    "Ремонт обуви, сумок и чемоданов",
    "Изготовление ключей и ремонт замков",
    "Заточка ножей и инструмента",
    "Ремонт часов",
    "Ремонт ювелирных изделий",
    "Ремонт очков",
    "Другие бытовые услуги",
)

_EXECUTORS = ("Частный мастер", "Мастерская", "Другой")


def build_household_services_catalog() -> dict[str, Any]:
    return {
        "category_slug": "services-bytovye-uslugi",
        "label": "Бытовые услуги",
        "kinds": _opts(*_KINDS),
        "executor_label": "Исполнитель",
        "executors": _opts(*_EXECUTORS),
        "objects": [],
        "materials": [],
    }
