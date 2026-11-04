# -*- coding: utf-8 -*-
"""Сантехника.

Электрика, отопление и климат, подключение бытовой техники —
отдельные разделы Услуг, сюда не входят.
Вид услуги — сама работа. Помещение выбирается в фильтре «Объект».
"""
from __future__ import annotations

from typing import Any


def _opts(*labels: str) -> list[dict[str, str]]:
    return [{"value": label, "label": label} for label in labels]


_KINDS = (
    "Водоснабжение и разводка труб",
    "Канализация",
    "Прочистка засоров",
    "Устранение протечек",
    "Установка и замена сантехники",
    "Реставрация ванн",
    "Счётчики воды",
    "Фильтры для воды",
    "Насосы",
    "Септики и откачка",
    "Другие сантехнические работы",
)

_EXECUTORS = ("Частный мастер", "Бригада", "Компания", "Другой")
_OBJECTS = (
    "Квартира",
    "Дом и коттедж",
    "Новостройка",
    "Офис",
    "Коммерческое помещение",
    "Баня",
    "Участок",
    "Другое",
)
_MATERIALS = ("С материалом", "Без материала", "Частично с материалом")


def build_plumbing_services_catalog() -> dict[str, Any]:
    return {
        "category_slug": "services-santehnika",
        "label": "Сантехника",
        "kinds": _opts(*_KINDS),
        "executors": _opts(*_EXECUTORS),
        "objects": _opts(*_OBJECTS),
        "materials": _opts(*_MATERIALS),
    }
