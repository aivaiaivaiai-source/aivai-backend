# -*- coding: utf-8 -*-
"""Отопление и климат.

Сантехника, электрика, подключение бытовой техники и проектирование —
отдельные разделы Услуг, сюда не входят.
Вид услуги — сама работа, а не модель котла или тип сплит-системы.
"""
from __future__ import annotations

from typing import Any


def _opts(*labels: str) -> list[dict[str, str]]:
    return [{"value": label, "label": label} for label in labels]


_KINDS = (
    "Услуги отопления под ключ",
    "Установка котлов",
    "Установка радиаторов и полотенцесушителей",
    "Установка тёплого пола",
    "Услуги газификации",
    "Установка печей и каминов",
    "Установка вентиляции",
    "Установка кондиционеров",
    "Обслуживание и ремонт кондиционеров",
    "Другие работы по отоплению и климату",
)

_EXECUTORS = ("Частный мастер", "Бригада", "Компания", "Другой")


def build_climate_services_catalog() -> dict[str, Any]:
    return {
        "category_slug": "services-otoplenie-i-klimat",
        "label": "Отопление и климат",
        "kinds": _opts(*_KINDS),
        "executors": _opts(*_EXECUTORS),
        "objects": [],
        "materials": [],
    }
