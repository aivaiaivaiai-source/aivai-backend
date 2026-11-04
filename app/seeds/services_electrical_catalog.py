# -*- coding: utf-8 -*-
"""Электрика.

Сантехника, отопление, подключение бытовой техники и охрана —
отдельные разделы Услуг, сюда не входят.
Вид услуги — сама работа, а не отдельный светильник или розетка.
"""
from __future__ import annotations

from typing import Any


def _opts(*labels: str) -> list[dict[str, str]]:
    return [{"value": label, "label": label} for label in labels]


_KINDS = (
    "Электрика под ключ",
    "Прокладка и замена проводки",
    "Электрощиты и автоматы",
    "Розетки и выключатели",
    "Освещение",
    "Счётчики электроэнергии",
    "Заземление и молниезащита",
    "Диагностика и ремонт электрики",
    "Стабилизаторы и генераторы",
    "Умный дом",
    "Наружное электроснабжение",
    "Другие электромонтажные работы",
)

_EXECUTORS = ("Частный мастер", "Бригада", "Компания", "Другой")


def build_electrical_services_catalog() -> dict[str, Any]:
    return {
        "category_slug": "services-elektrika",
        "label": "Электрика",
        "kinds": _opts(*_KINDS),
        "executors": _opts(*_EXECUTORS),
        "objects": [],
        "materials": [],
    }
