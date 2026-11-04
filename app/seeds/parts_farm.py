# -*- coding: utf-8 -*-
"""Farm machinery parts catalogs — per subtype.

API: farm_machinery (+ optional equipment_type matching sale vehicle_types).
Keys match Flutter FarmMachinerySubcategoriesData.
"""
from __future__ import annotations

from typing import Any

APPLICABILITY = "farm_machinery"

_Item = tuple[str, str] | tuple[str, str, list[tuple[str, str]]]
_Section = tuple[str, str, list[_Item]]


def _items(*pairs: _Item) -> list[_Item]:
    return list(pairs)


def _section(value: str, label: str, *pairs: _Item) -> _Section:
    return (value, label, _items(*pairs))


_ENGINE = _section(
    "engine",
    "Двигатель",
    ("engine_assembly", "Двигатель в сборе"),
    ("turbo", "Турбина"),
    ("injectors", "Форсунки"),
    ("fuel_pump", "ТНВД / топливный насос"),
    ("alternator", "Генератор"),
    ("starter", "Стартер"),
    ("radiator", "Радиатор"),
    ("air_filter", "Воздушный фильтр"),
    ("other", "Другое"),
)

_TRANSMISSION = _section(
    "transmission",
    "КПП и трансмиссия",
    ("gearbox", "Коробка передач"),
    ("clutch", "Сцепление"),
    ("pto", "ВОМ / кардан ВОМ"),
    ("differential", "Редуктор / дифференциал"),
    ("final_drive", "Бортовой редуктор"),
    ("other", "Другое"),
)

_HYDRAULICS = _section(
    "hydraulics",
    "Гидравлика",
    ("hydraulic_pump", "Гидронасос"),
    ("hydraulic_cylinder", "Гидроцилиндр"),
    ("distributor", "Распределитель"),
    ("hoses", "РВД / шланги"),
    ("other", "Другое"),
)

_CHASSIS = _section(
    "chassis",
    "Ходовая",
    ("tracks", "Гусеницы"),
    ("bearings", "Подшипники"),
    ("axle", "Мост / ось"),
    ("other", "Другое"),
)

_SUPPORT_WHEELS = _section(
    "support_wheels",
    "Опорные колёса",
    ("wheels", "Колёса"),
    ("bearings", "Подшипники"),
    ("other", "Другое"),
)

_WALK_WHEELS = _section(
    "wheel_bearings",
    "Подшипники колёс",
    ("bearings", "Подшипники"),
    ("other", "Другое"),
)

_BRAKES = _section(
    "brakes",
    "Тормоза",
    ("brake_pads", "Колодки"),
    ("brake_discs", "Диски"),
    ("brake_drums", "Барабаны"),
    ("other", "Другое"),
)

_ELECTRICAL = _section(
    "electrical",
    "Электрика",
    ("battery", "АКБ"),
    ("wiring", "Проводка"),
    ("lights", "Фары / фонари"),
    ("sensors", "Датчики"),
    ("other", "Другое"),
)

_CABIN = _section(
    "cabin",
    "Кабина",
    ("glass", "Стёкла"),
    ("seat", "Сиденье"),
    ("mirrors", "Зеркала"),
    ("hvac", "Отопитель / кондиционер"),
    ("other", "Другое"),
)

_COOLING = _section(
    "cooling",
    "Охлаждение",
    ("radiator", "Радиатор"),
    ("water_pump", "Помпа"),
    ("thermostat", "Термостат"),
    ("fan", "Вентилятор"),
    ("hoses", "Патрубки"),
    ("other", "Другое"),
)

_CONSUMABLES = _section(
    "consumables",
    "Расходники",
    ("filters", "Фильтры"),
    ("fluids", "Жидкости / масла"),
    ("belts", "Ремни"),
    ("other", "Другое"),
)

_OTHER = _section("other", "Другое", ("other", "Другое"))

_TRACTOR_EXTRA = _section(
    "tractor_equipment",
    "Навесное / сцепка",
    ("three_point", "Трёхточечная навеска"),
    ("drawbar", "Прицепное устройство"),
    ("front_loader", "КУН / фронтальный погрузчик"),
    ("weights", "Утяжелители"),
    ("other", "Другое"),
)

_MINI_TRACTOR_EXTRA = _section(
    "mini_tractor_equipment",
    "Оборудование мини-трактора",
    ("three_point", "Навеска"),
    ("mower_deck", "Косилка / дека"),
    ("front_loader", "КУН"),
    ("rotavator", "Фреза"),
    ("other", "Другое"),
)

_WALK_BEHIND_EXTRA = _section(
    "walk_behind_equipment",
    "Оборудование мотоблока",
    ("cutters", "Фрезы / культиватор"),
    ("plow", "Плуг"),
    ("hiller", "Окучник"),
    ("wheels_weights", "Грунтозацепы / утяжелители"),
    ("trailer_hitch", "Прицеп / сцепка"),
    ("other", "Другое"),
)

_COMBINE_EXTRA = _section(
    "combine_equipment",
    "Оборудование комбайна",
    ("header", "Жатка"),
    ("threshing", "Молотильный барабан"),
    ("sieves", "Решета"),
    ("elevator", "Элеватор / шнек"),
    ("straw_chopper", "Измельчитель соломы"),
    ("other", "Другое"),
)

_SEEDER_EXTRA = _section(
    "seeder_equipment",
    "Оборудование сеялки",
    ("seed_units", "Высевающие аппараты"),
    ("coulters", "Сошники"),
    ("seed_tank", "Бункер семян"),
    ("fertilizer_tank", "Бункер удобрений"),
    ("markers", "Маркеры"),
    ("other", "Другое"),
)

_TILLAGE_EXTRA = _section(
    "working_parts",
    "Рабочие органы",
    ("shares", "Лемеха / отвалы"),
    ("discs", "Диски"),
    ("tines", "Стойки / лапы"),
    ("knives", "Ножи / сегменты"),
    ("points", "Наконечники"),
    ("rollers", "Катки"),
    ("other", "Другое"),
)

_FORAGE_EXTRA = _section(
    "forage_equipment",
    "Оборудование кормозаготовки",
    ("knives", "Ножи / сегменты"),
    ("baler_twine", "Шпагат / сетка"),
    ("pickup", "Подборщик"),
    ("conditioner", "Кондиционер / плющилка"),
    ("other", "Другое"),
)

_SPRAYER_EXTRA = _section(
    "sprayer_equipment",
    "Оборудование опрыскивателя",
    ("boom", "Штанга"),
    ("nozzles", "Форсунки / распылители"),
    ("pump", "Насос"),
    ("tank", "Бак"),
    ("filters", "Фильтры раствора"),
    ("other", "Другое"),
)

_DRONE_EXTRA = _section(
    "drone_equipment",
    "Оборудование агродрона",
    ("propellers", "Пропеллеры"),
    ("battery", "Аккумулятор"),
    ("spray_tank", "Бак / распылитель"),
    ("motors", "Моторы"),
    ("remote", "Пульт / RC"),
    ("gps", "GPS / RTK"),
    ("other", "Другое"),
)

_OTHER_AGRI_EXTRA = _section(
    "other_agri_equipment",
    "Спецоборудование",
    ("working_parts", "Рабочие органы"),
    ("drive", "Привод"),
    ("other", "Другое"),
)

_HITCH = _section(
    "hitch",
    "Навеска / сцепка",
    ("three_point", "Трёхточечная навеска"),
    ("pins", "Пальцы / шплинты"),
    ("drawbar", "Прицепное"),
    ("other", "Другое"),
)

_WORKING_PARTS = _section(
    "working_parts",
    "Рабочие органы",
    ("shares", "Лемеха / отвалы"),
    ("discs", "Диски"),
    ("tines", "Стойки / лапы"),
    ("knives", "Ножи / сегменты"),
    ("points", "Наконечники"),
    ("other", "Другое"),
)

_KUN_EXTRA = _section(
    "kun_equipment",
    "Оборудование КУНа",
    ("bucket", "Ковш"),
    ("forks", "Вилы"),
    ("boom", "Стрела"),
    ("cylinders", "Гидроцилиндры"),
    ("other", "Другое"),
)

_BALER_EXTRA = _section(
    "baler_equipment",
    "Оборудование пресс-подборщика",
    ("pickup", "Подборщик"),
    ("twine", "Шпагат / сетка"),
    ("knives", "Ножи"),
    ("rollers", "Валики / камеры"),
    ("other", "Другое"),
)

_DIGGER_EXTRA = _section(
    "digger_equipment",
    "Оборудование копалки",
    ("shares", "Лемеха"),
    ("elevator", "Элеватор / транспортер"),
    ("separator", "Сепаратор"),
    ("other", "Другое"),
)


def _powered(*extra: _Section) -> list[_Section]:
    return [
        _ENGINE,
        _TRANSMISSION,
        _HYDRAULICS,
        *extra,
        _CHASSIS,
        _BRAKES,
        _COOLING,
        _ELECTRICAL,
        _CABIN,
        _CONSUMABLES,
        _OTHER,
    ]


def _implement(*extra: _Section, working_parts: bool = True) -> list[_Section]:
    """Implements without full powertrain (seeders, plows, etc.)."""
    sections: list[_Section] = [_HITCH, _HYDRAULICS]
    if working_parts:
        sections.append(_WORKING_PARTS)
    sections.extend(extra)
    sections.extend([_SUPPORT_WHEELS, _ELECTRICAL, _CONSUMABLES, _OTHER])
    return sections


TYPE_LABELS: dict[str, str] = {
    "tractor": "Тракторы",
    "mini_tractor": "Мини-тракторы",
    "walk_behind": "Мотоблоки и мотокультиваторы",
    "combine": "Комбайны",
    "seeder": "Сеялки",
    "potato_planter": "Картофелесажалки",
    "tillage": "Почвообрабатывающая техника",
    "forage": "Техника для заготовки кормов",
    "plow": "Плуги",
    "harrow": "Бороны",
    "cultivator": "Культиваторы",
    "hiller": "Окучники",
    "ditcher": "Арычники",
    "mulcher": "Мульчеры",
    "mower": "Косилки",
    "walk_behind_mower": "Мотокосилки",
    "baler": "Пресс-подборщики",
    "header": "Жатки",
    "rake": "Грабли",
    "feed_mixer": "Кормораздатчики",
    "sprayer": "Опрыскиватели",
    "fertilizer_spreader": "Разбрасыватели удобрений",
    "manure_spreader": "Навозоразбрасыватели",
    "potato_digger": "Картофелекопалки",
    "kun": "КУНы",
    "farm_crusher": "Дробилки",
    "grain_thrower": "Зернометатели",
    "grain_cleaner": "Зерноочистители",
    "film_layer": "Пленкоукладчики и грядообразователи",
    "ridge_former": "Бугорообразователи",
    "agri_drone": "Агродроны",
    "other_agri": "Другая сельхозтехника",
}

TYPE_SECTIONS: dict[str, list[_Section]] = {
    "tractor": _powered(_TRACTOR_EXTRA),
    "mini_tractor": _powered(_MINI_TRACTOR_EXTRA),
    "walk_behind": [
        _ENGINE,
        _TRANSMISSION,
        _WALK_BEHIND_EXTRA,
        _WALK_WHEELS,
        _ELECTRICAL,
        _CONSUMABLES,
        _OTHER,
    ],
    "combine": _powered(_COMBINE_EXTRA),
    "seeder": _implement(_SEEDER_EXTRA),
    "potato_planter": _implement(_SEEDER_EXTRA),
    "tillage": _implement(_TILLAGE_EXTRA, working_parts=False),
    "forage": _powered(_FORAGE_EXTRA),
    "plow": _implement(_TILLAGE_EXTRA, working_parts=False),
    "harrow": _implement(_TILLAGE_EXTRA, working_parts=False),
    "cultivator": _implement(_TILLAGE_EXTRA, working_parts=False),
    "hiller": _implement(_TILLAGE_EXTRA, working_parts=False),
    "ditcher": _implement(_TILLAGE_EXTRA, working_parts=False),
    "mulcher": _implement(_FORAGE_EXTRA),
    "mower": _implement(_FORAGE_EXTRA),
    "walk_behind_mower": _powered(_FORAGE_EXTRA),
    "baler": _implement(_BALER_EXTRA),
    "header": _implement(_COMBINE_EXTRA),
    "rake": _implement(_FORAGE_EXTRA),
    "feed_mixer": _implement(_FORAGE_EXTRA),
    "sprayer": _powered(_SPRAYER_EXTRA),
    "fertilizer_spreader": _implement(_SPRAYER_EXTRA),
    "manure_spreader": _implement(_SPRAYER_EXTRA),
    "potato_digger": _implement(_DIGGER_EXTRA),
    "kun": _implement(_KUN_EXTRA),
    "farm_crusher": _implement(_OTHER_AGRI_EXTRA),
    "grain_thrower": _implement(_OTHER_AGRI_EXTRA),
    "grain_cleaner": _implement(_OTHER_AGRI_EXTRA),
    "film_layer": _implement(_OTHER_AGRI_EXTRA),
    "ridge_former": _implement(_TILLAGE_EXTRA, working_parts=False),
    "agri_drone": [
        _DRONE_EXTRA,
        _ELECTRICAL,
        _CONSUMABLES,
        _OTHER,
    ],
    "other_agri": _powered(_OTHER_AGRI_EXTRA),
}

FARM_SECTIONS: list[_Section] = TYPE_SECTIONS["tractor"]

FARM_PARTS_SEARCH_ALIASES: dict[str, tuple[str, str] | tuple[str, str, str]] = {
    "вом": ("transmission", "pto"),
    "кун": ("tractor_equipment", "front_loader"),
    "жатка": ("combine_equipment", "header"),
    "форсунки": ("engine", "injectors"),
    "акб": ("electrical", "battery"),
    "пропеллеры": ("drone_equipment", "propellers"),
}

LISTING_FIELDS: list[dict[str, Any]] = [
    {
        "field_key": "brand",
        "label": "Марка",
        "field_type": "brand",
        "is_required": True,
        "sort_order": 10,
    },
    {
        "field_key": "model",
        "label": "Модель",
        "field_type": "model",
        "is_required": True,
        "sort_order": 20,
    },
    {
        "field_key": "year",
        "label": "Год",
        "field_type": "year",
        "is_required": False,
        "sort_order": 30,
    },
    {
        "field_key": "condition",
        "label": "Состояние",
        "field_type": "enum",
        "is_required": True,
        "sort_order": 40,
        "options": {
            "values": [
                {"value": "new", "label": "Новое"},
                {"value": "used", "label": "Б/у"},
            ]
        },
    },
    {
        "field_key": "city",
        "label": "Город",
        "field_type": "city",
        "is_required": True,
        "sort_order": 50,
    },
]

PATH_FIELDS: tuple[str, ...] = (
    "vehicle_applicability",
    "part_section",
    "part_name",
    "part_subtype",
)


def _serialize_item(item: _Item) -> dict[str, Any]:
    if len(item) == 3:
        value, label, children = item  # type: ignore[misc]
        return {
            "value": value,
            "label": label,
            "children": [{"value": c[0], "label": c[1]} for c in children],
        }
    value, label = item  # type: ignore[misc]
    return {"value": value, "label": label}


def build_farm_catalog(*, equipment_type: str | None = None) -> dict[str, Any]:
    key = (equipment_type or "").strip().lower() or None
    if key and key not in TYPE_SECTIONS:
        key = None
    sections_src = TYPE_SECTIONS[key] if key else FARM_SECTIONS
    label = TYPE_LABELS.get(key or "", "Сельхозтехника")
    sections = [
        {
            "value": value,
            "label": section_label,
            "items": [_serialize_item(i) for i in items],
        }
        for value, section_label, items in sections_src
    ]
    return {
        "applicability": APPLICABILITY,
        "applicability_label": label,
        "category_slug": "transport-auto-parts",
        "sections": sections,
        "listing_fields": LISTING_FIELDS,
        "path_fields": list(PATH_FIELDS),
        "search_aliases": {
            k: {
                "part_section": v[0],
                "part_name": v[1],
                **({"part_subtype": v[2]} if len(v) == 3 else {}),
            }
            for k, v in FARM_PARTS_SEARCH_ALIASES.items()
        },
    }
