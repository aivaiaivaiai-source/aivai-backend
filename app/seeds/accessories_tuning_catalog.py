# -*- coding: utf-8 -*-
"""Аксессуары и тюнинг: у каждого направления свой набор и свои бренды.

Сначала направление, затем фильтр: тип, бренд, состояние, локация.
Состояние и локация общие и задаются на клиенте.
"""
from __future__ import annotations

from typing import Any


def _opts(*labels: str) -> list[dict[str, str]]:
    return [{"value": label, "label": label} for label in labels]


_PASSENGER_TYPES = (
    "Автозвук и мультимедиа",
    "Видеорегистраторы, камеры и парктроники",
    "Сигнализации и противоугонные устройства",
    "Аксессуары салона",
    "Багажники и перевозка багажа",
    "Внешние аксессуары и декор",
    "Автосвет и тюнинг оптики",
    "Внедорожный тюнинг",
    "Спортивный тюнинг",
    "Уход и автохимия",
    "Автомобильные принадлежности",
    "Другие аксессуары",
)
_PASSENGER_BRANDS = (
    "Pioneer", "Alpine", "Sony", "Kenwood", "JBL", "Bosch", "HELLA",
    "Osram", "Thule", "StarLine", "Pandora", "Sho-Me", "Liqui Moly",
)

_CARGO_TYPES = (
    "Видеорегистраторы и камеры",
    "Тахографы",
    "Сигнализации и замки",
    "Аксессуары кабины",
    "Крепления и стяжки груза",
    "Тенты и дуги",
    "Зеркала и козырьки",
    "Автосвет",
    "Уход и химия",
    "Инструмент",
    "Другие аксессуары",
)
_CARGO_BRANDS = ("VDO", "Hella", "Bosch", "Daken", "JOST", "BPW", "Edscha", "Continental")

_BUS_TYPES = (
    "Видеонаблюдение салона",
    "Информационные табло",
    "Автозвук",
    "Сигнализации",
    "Аксессуары салона",
    "Багажные системы",
    "Автосвет",
    "Уход и химия",
    "Другие аксессуары",
)
_BUS_BRANDS = ("Actia", "Bosch", "Hella", "Continental", "Streamax")

_SPECIAL_TYPES = (
    "Проблесковые маяки",
    "Рабочее освещение",
    "Камеры",
    "Аксессуары кабины",
    "Защита и накладки",
    "Инструмент",
    "Другие аксессуары",
)
_SPECIAL_BRANDS = ("Hella", "Federal Signal", "Whelen", "Bosch", "Brigade")

_FARM_TYPES = (
    "Рабочее освещение",
    "Проблесковые маяки",
    "Камеры",
    "Зеркала и козырьки",
    "Аксессуары кабины",
    "Инструмент",
    "Уход",
    "Другие аксессуары",
)
_FARM_BRANDS = ("Hella", "Cobo", "Bosch", "John Deere", "Granit")

_MOTO_TYPES = (
    "Шлемы",
    "Куртки и штаны",
    "Перчатки",
    "Ботинки",
    "Защита",
    "Кофры и сумки",
    "Дуги и слайдеры",
    "Ветровые стекла",
    "Сигнализации и замки",
    "Уход",
    "Другие аксессуары",
)
_MOTO_BRANDS = (
    "Shoei", "Arai", "HJC", "LS2", "Alpinestars", "Dainese",
    "GIVI", "SHAD", "SW-Motech",
)

_ELECTRIC_TYPES = (
    "Шлемы",
    "Замки",
    "Сумки и крепления",
    "Фонари",
    "Крылья",
    "Чехлы",
    "Зеркала",
    "Держатели телефона",
    "Другие аксессуары",
)
_ELECTRIC_BRANDS = ("Xiaomi", "Ninebot", "Segway", "ABUS", "Rockbros")

_BIKE_TYPES = (
    "Шлемы",
    "Перчатки и защита",
    "Велозамки",
    "Фонари",
    "Сумки и багажники",
    "Крылья",
    "Фляги и держатели",
    "Велокомпьютеры",
    "Насосы",
    "Другие аксессуары",
)
_BIKE_BRANDS = ("Abus", "Kryptonite", "Garmin", "Cateye", "Giro", "Bell", "Topeak", "Ortlieb")

_WATER_TYPES = (
    "Спасательные жилеты",
    "Якоря и швартовка",
    "Вёсла",
    "Тенты",
    "Эхолоты и навигация",
    "Насосы",
    "Сиденья и чехлы",
    "Уход",
    "Другие аксессуары",
)
_WATER_BRANDS = ("Garmin", "Lowrance", "Humminbird", "Attwood", "Plastimo", "Osculati")

_TRAILER_TYPES = (
    "Тенты",
    "Противооткатные упоры",
    "Замки сцепки",
    "Освещение и проводка",
    "Крепления груза",
    "Опорные стойки",
    "Чехлы",
    "Другие аксессуары",
)
_TRAILER_BRANDS = ("Knott", "AL-KO", "Winterhoff", "Thule", "Hella")


def _catalog(types: tuple[str, ...], brands: tuple[str, ...]) -> dict[str, Any]:
    return {
        "types": _opts(*types),
        "brands": _opts(*brands),
    }


_CATALOGS: dict[str, tuple[str, dict[str, Any]]] = {
    "passenger_cars": ("Легковые автомобили", _catalog(_PASSENGER_TYPES, _PASSENGER_BRANDS)),
    "cargo": ("Грузовой транспорт", _catalog(_CARGO_TYPES, _CARGO_BRANDS)),
    "buses": ("Автобусы", _catalog(_BUS_TYPES, _BUS_BRANDS)),
    "special_equipment": ("Спецтехника", _catalog(_SPECIAL_TYPES, _SPECIAL_BRANDS)),
    "farm_machinery": ("Сельхозтехника", _catalog(_FARM_TYPES, _FARM_BRANDS)),
    "moto": ("Мототехника", _catalog(_MOTO_TYPES, _MOTO_BRANDS)),
    "electric": ("Электротранспорт", _catalog(_ELECTRIC_TYPES, _ELECTRIC_BRANDS)),
    "bicycles": ("Велосипеды", _catalog(_BIKE_TYPES, _BIKE_BRANDS)),
    "watercraft": ("Водный транспорт", _catalog(_WATER_TYPES, _WATER_BRANDS)),
    "trailers": ("Прицепы", _catalog(_TRAILER_TYPES, _TRAILER_BRANDS)),
}

ACCESSORIES_DIRECTIONS: list[tuple[str, str]] = [
    (key, label) for key, (label, _catalog_body) in _CATALOGS.items()
]


def accessories_directions() -> list[dict[str, str]]:
    return [{"value": value, "label": label} for value, label in ACCESSORIES_DIRECTIONS]


def build_accessories_catalog(applicability: str) -> dict[str, Any] | None:
    key = (applicability or "").strip().lower()
    found = _CATALOGS.get(key)
    if found is None:
        return None
    label, body = found
    return {
        "applicability": key,
        "applicability_label": label,
        "category_slug": "transport-accessories-tuning",
        "types": body["types"],
        "brands": body["brands"],
    }
