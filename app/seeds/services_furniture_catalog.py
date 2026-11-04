# -*- coding: utf-8 -*-
"""Мебель и интерьер.

Вид услуги — сама работа, а не шкаф, кухня или диван.
Дизайн, химчистка, перевозка, двери, полы и потолки — отдельные разделы.
"""
from __future__ import annotations

from typing import Any


def _opts(*labels: str) -> list[dict[str, str]]:
    return [{"value": label, "label": label} for label in labels]


_KINDS = (
    "Сборка и разборка мебели",
    "Изготовление мебели на заказ",
    "Ремонт и реставрация мебели",
    "Перетяжка мягкой мебели",
    "Услуги по шторам, карнизам и жалюзи",
    "Другие работы по мебели и интерьеру",
)

_EXECUTORS = ("Частный мастер", "Бригада", "Компания", "Другой")


def build_furniture_services_catalog() -> dict[str, Any]:
    return {
        "category_slug": "services-mebel-i-interer",
        "label": "Мебель и интерьер",
        "kinds": _opts(*_KINDS),
        "executors": _opts(*_EXECUTORS),
        "objects": [],
        "materials": [],
    }
