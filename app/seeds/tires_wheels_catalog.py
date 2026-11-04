# -*- coding: utf-8 -*-
"""Шины и диски: фильтр как на f7.kz.

Ширина, высота, диаметр, сезонность, бренд и шипы зависят от направления.
Состояние и локация общие. Водного транспорта нет.
"""
from __future__ import annotations

from typing import Any


def _opts(*labels: str) -> list[dict[str, str]]:
    return [{"value": label, "label": label} for label in labels]


def _kind(
    value: str,
    label: str,
    *,
    widths: tuple[str, ...] = (),
    heights: tuple[str, ...] = (),
    diameters: tuple[str, ...] = (),
    seasons: tuple[str, ...] = (),
    brands: tuple[str, ...] = (),
    studs: tuple[str, ...] = (),
    accessory_types: tuple[str, ...] = (),
) -> dict[str, Any]:
    return {
        "value": value,
        "label": label,
        "widths": _opts(*widths),
        "heights": _opts(*heights),
        "diameters": _opts(*diameters),
        "seasons": _opts(*seasons),
        "brands": _opts(*brands),
        "studs": _opts(*studs),
        "accessory_types": _opts(*accessory_types),
    }


_SEASON_CAR = ("Летняя", "Зимняя", "Всесезонная")
_STUDS = ("шипованная", "нешипованная")
_SEASON_ALL = ("Всесезонная",)

_PASSENGER_W = (
    "155", "165", "175", "185", "195", "205", "215", "225", "235", "245",
    "255", "265", "275", "285", "295", "305", "315", "325",
)
_PASSENGER_H = ("30", "35", "40", "45", "50", "55", "60", "65", "70", "75", "80", "85")
_PASSENGER_D = (
    "R13", "R14", "R15", "R15C", "R16", "R16C", "R17", "R17C", "R18", "R19",
    "R20", "R21", "R22",
)
_PASSENGER_BRANDS = (
    "Ikon", "Bridgestone", "Continental", "Michelin", "Yokohama", "Roadx",
    "Hankook", "Kumho", "Nokian Tyres", "Pirelli", "Toyo", "Triangle",
    "Sailun", "Cordiant", "Matador", "Nexen", "BFGoodrich", "General Tire",
    "Haida", "Nitto", "Royal Black", "Sunny", "Autogreen", "Arivo", "Aplus",
    "Bars", "Farroad", "Zmax", "Roadx KZ", "Belshina", "Viatti", "KAMA",
)
_PASSENGER_RIM_W = ("5.5J", "6J", "6.5J", "7J", "7.5J", "8J", "8.5J", "9J", "9.5J", "10J")
_PASSENGER_RIM_BRANDS = (
    "Replay", "NZ", "SKAD", "КиК", "LS", "Alcasta", "Tech Line", "Cross Street",
    "Remain", "iFree",
)
_PASSENGER_ACC = (
    "Колпаки", "Болты и гайки", "Секретки", "Датчики давления",
    "Центровочные кольца", "Проставки", "Цепи противоскольжения",
    "Ниппели и вентили", "Грузики",
)

_TRUCK_W = (
    "7.50", "8.25", "9.00", "10.00", "11", "11.00", "12", "12.00",
    "215", "235", "245", "265", "275", "285", "295", "305", "315",
    "365", "385", "435", "445",
)
_TRUCK_H = ("00", "45", "50", "55", "60", "65", "70", "75", "80")
_TRUCK_D = ("R16", "R17.5", "R19.5", "R20", "R22.5")
_TRUCK_BRANDS = (
    "Advance", "Arisun", "ATTAR", "Bridgestone", "Double Coin", "Durun",
    "Forward Traction", "Hankook", "KAMA", "Kapsen", "Michelin", "Mirage",
    "Onyx", "Pirelli", "Roadx", "Torque", "Triangle", "Belshina", "Aeolus",
)
_TRUCK_RIM_W = ("6.00", "6.75", "7.50", "8.25", "9.00", "11.75")
_TRUCK_RIM_BRANDS = ("Hayes Lemmerz", "Maxion", "Accuride", "Jantsa", "Asterro")
_TRUCK_ACC = (
    "Удлинители вентилей", "Гайки крепления", "Датчики давления",
    "Цепи противоскольжения", "Камеры", "Ободные ленты", "Грузики",
)

_OTR_W = ("10.00", "12.00", "14.00", "15.5", "16.9", "17.5", "18.4", "20.5", "23.5", "26.5")
_OTR_H = ("65", "70", "80", "85")
_OTR_D = ("R20", "R24", "R25", "R26", "R28")
_OTR_BRANDS = (
    "BKT", "Bridgestone", "Continental", "Maxam", "Deestone", "Advance",
    "Sailun", "Triangle", "Michelin", "Nexen",
)
_OTR_ACC = ("Камеры", "Ободные ленты", "Вентили", "Защитные кольца обода", "Цепи противоскольжения")

# Metric / decimal widths only. Legacy dash sizes like 23.1-26 need a
# dedicated representation (architecture blocker — do not fake as profile).
_FARM_W = (
    "6.50", "7.50", "8.3", "9.5", "11.2", "12.4", "13.6", "14.9", "15.5",
    "16.9", "18.4", "420", "460", "480", "520", "600",
)
_FARM_H = ("70", "80", "85", "00")
_FARM_D = ("R16", "R20", "R24", "R26", "R28", "R30", "R34", "R38", "R42")
_FARM_BRANDS = (
    "BKT", "Alliance", "Mitas", "Rosava", "Voltyre", "Belshina", "Petlas",
    "Trelleborg", "Michelin", "Cultor", "Ozka",
)
_FARM_ACC = (
    "Камеры", "Ободные ленты", "Вентили", "Грузы колёс",
    "Удлинители вентилей", "Проставки для спарки",
)

_MOTO_W = ("90", "100", "110", "120", "130", "140", "150", "160", "180", "190", "3.00", "3.50")
_MOTO_H = ("50", "55", "60", "70", "80", "90")
_MOTO_D = ("R12", "R13", "R14", "R17", "R18", "R19", "R21")
_MOTO_BRANDS = (
    "Michelin", "Pirelli", "Metzeler", "Bridgestone", "Dunlop", "Continental",
    "Heidenau", "IRC", "Mitas", "Kenda", "Shinko",
)
_MOTO_ACC = ("Камеры", "Ободные ленты", "Ниппели", "Грузики", "Бескамерный герметик", "Золотники")

_E_W = ("8", "8.5", "10", "12", "200", "255")
_E_H = ("2", "2.125", "2.5", "3", "50", "80")
_E_D = ("8\"", "8.5\"", "10\"", "12\"")
_E_BRANDS = ("CST", "Kenda", "Chaoyang", "Innova", "Wanda", "Deli")
_E_ACC = ("Камеры", "Ободные ленты", "Ниппели", "Бескамерный герметик")

_BIKE_W = ("1.75", "1.95", "2.1", "2.25", "2.4", "23", "25", "28", "32", "35")
_BIKE_H = ("23", "25", "28", "32", "35", "38")
_BIKE_D = ("16\"", "20\"", "24\"", "26\"", "27.5\"", "29\"", "700C")
_BIKE_BRANDS = ("Schwalbe", "Continental", "Maxxis", "Kenda", "CST", "Michelin", "Vittoria", "Chaoyang")
_BIKE_ACC = ("Камеры", "Ободные ленты", "Ниппели", "Бескамерный набор", "Герметик", "Флиппер")

_TRAILER_W = ("155", "165", "185", "195", "215", "235", "385")
_TRAILER_H = ("65", "70", "75", "80")
_TRAILER_D = ("R13", "R13C", "R14C", "R15C", "R17.5", "R22.5")
_TRAILER_BRANDS = ("KAMA", "Rosava", "Cordiant", "Triangle", "Roadx", "Michelin", "Hankook", "Matador")
_TRAILER_ACC = ("Камеры", "Колпаки", "Гайки", "Удлинители вентилей", "Крышки ступиц")


def _catalog(
    widths: tuple[str, ...],
    heights: tuple[str, ...],
    diameters: tuple[str, ...],
    seasons: tuple[str, ...],
    brands: tuple[str, ...],
    studs: tuple[str, ...],
    rim_widths: tuple[str, ...],
    rim_diameters: tuple[str, ...],
    rim_brands: tuple[str, ...],
    accessories: tuple[str, ...],
) -> list[dict[str, Any]]:
    tire = _kind(
        "tires",
        "Шины",
        widths=widths,
        heights=heights,
        diameters=diameters,
        seasons=seasons,
        brands=brands,
        studs=studs,
    )
    wheels = _kind(
        "wheel_assy",
        "Колёса в сборе",
        widths=widths,
        heights=heights,
        diameters=diameters,
        seasons=seasons,
        brands=brands,
        studs=studs,
    )
    rims = _kind(
        "rims",
        "Диски",
        widths=rim_widths,
        diameters=rim_diameters,
        brands=rim_brands,
    )
    acc = _kind(
        "accessories",
        "Аксессуары для шин и дисков",
        diameters=diameters,
        brands=brands,
        accessory_types=accessories,
    )
    return [tire, rims, wheels, acc]


_CATALOGS: dict[str, tuple[str, list[dict[str, Any]]]] = {
    "passenger_cars": (
        "Легковые автомобили",
        _catalog(
            _PASSENGER_W, _PASSENGER_H, _PASSENGER_D, _SEASON_CAR,
            _PASSENGER_BRANDS, _STUDS, _PASSENGER_RIM_W, _PASSENGER_D,
            _PASSENGER_RIM_BRANDS, _PASSENGER_ACC,
        ),
    ),
    "cargo": (
        "Грузовой транспорт",
        _catalog(
            _TRUCK_W, _TRUCK_H, _TRUCK_D, _SEASON_ALL, _TRUCK_BRANDS, _STUDS,
            _TRUCK_RIM_W, _TRUCK_D, _TRUCK_RIM_BRANDS, _TRUCK_ACC,
        ),
    ),
    "buses": (
        "Автобусы",
        _catalog(
            _TRUCK_W, _TRUCK_H, _TRUCK_D, _SEASON_ALL, _TRUCK_BRANDS, _STUDS,
            _TRUCK_RIM_W, _TRUCK_D, _TRUCK_RIM_BRANDS,
            _TRUCK_ACC + ("Колпаки ступиц",),
        ),
    ),
    "special_equipment": (
        "Спецтехника",
        _catalog(
            _OTR_W, _OTR_H, _OTR_D, _SEASON_ALL, _OTR_BRANDS, ("нешипованная",),
            ("8.00", "10.00", "14.00", "17.00", "19.50"), _OTR_D, _OTR_BRANDS,
            _OTR_ACC,
        ),
    ),
    "farm_machinery": (
        "Сельхозтехника",
        _catalog(
            _FARM_W, _FARM_H, _FARM_D, _SEASON_ALL, _FARM_BRANDS, ("нешипованная",),
            ("W8", "W10", "W12", "DW15", "DW16", "DW18"), _FARM_D, _FARM_BRANDS,
            _FARM_ACC,
        ),
    ),
    "moto": (
        "Мототехника",
        _catalog(
            _MOTO_W, _MOTO_H, _MOTO_D, _SEASON_CAR, _MOTO_BRANDS, _STUDS,
            ("1.85", "2.15", "2.50", "3.00", "3.50", "4.00", "5.50"), _MOTO_D,
            ("Excel", "DID", "Morad", "Takasago"), _MOTO_ACC,
        ),
    ),
    "electric": (
        "Электротранспорт",
        _catalog(
            _E_W, _E_H, _E_D, _SEASON_ALL, _E_BRANDS, ("нешипованная",),
            ("1.75", "2.15", "2.50"), _E_D, _E_BRANDS, _E_ACC,
        ),
    ),
    "bicycles": (
        "Велосипеды",
        _catalog(
            _BIKE_W, _BIKE_H, _BIKE_D, _SEASON_ALL, _BIKE_BRANDS, ("нешипованная",),
            ("19 мм", "21 мм", "23 мм", "25 мм", "30 мм"), _BIKE_D,
            ("Alexrims", "DT Swiss", "Mavic", "Weinmann"), _BIKE_ACC,
        ),
    ),
    "trailers": (
        "Прицепы",
        _catalog(
            _TRAILER_W, _TRAILER_H, _TRAILER_D, ("Всесезонная", "Летняя"),
            _TRAILER_BRANDS, ("нешипованная",),
            ("4.5J", "5J", "5.5J", "6.00", "11.75"), _TRAILER_D,
            _TRAILER_BRANDS, _TRAILER_ACC,
        ),
    ),
}

TIRES_DIRECTIONS: list[tuple[str, str]] = [
    (key, label) for key, (label, _kinds) in _CATALOGS.items()
]


def tires_directions() -> list[dict[str, str]]:
    return [{"value": value, "label": label} for value, label in TIRES_DIRECTIONS]


def build_tires_catalog(applicability: str) -> dict[str, Any] | None:
    key = (applicability or "").strip().lower()
    found = _CATALOGS.get(key)
    if found is None:
        return None
    label, kinds = found
    return {
        "applicability": key,
        "applicability_label": label,
        "category_slug": "transport-tires-wheels",
        "kinds": kinds,
    }
