# -*- coding: utf-8 -*-
"""Transport → Сельхозтехника V2 — leaf Create/Search SoT.

Parent ``transport-farm-machinery`` is picker-only.
Final 7 active leaves: Tractor / Mini / Motoblock / Combine / Agri Drone /
Broad Implement (reuses id 839) / Other.
Implement L3 retire → ``equipment_type`` on broad leaf.
"""
from __future__ import annotations

from typing import Any

from app.models.category_enums import CategoryFieldType, CategoryFilterType
from app.seeds.car_sale_v2 import (
    CONDITION_V2_CHOICES,
    CONTACT_METHOD_CHOICES,
    EXCHANGE_CHOICES,
    INSTALLMENT_CHOICES,
    NEGOTIABLE_CHOICES,
    YES_NO_CHOICES,
)

FARM_PARENT_SLUG = "transport-farm-machinery"

# Reuse inactive 839 «Навесное оборудование» as broad implement leaf.
BROAD_IMPLEMENT_ID = 839
BROAD_IMPLEMENT_OLD_SLUG = "transport-farm-machinery-navesnoe-oborudovanie"
BROAD_IMPLEMENT_SLUG = (
    "transport-farm-machinery-navesnaya-i-pritsepnaya-selhoztehnika"
)
BROAD_IMPLEMENT_LABEL = "Навесная и прицепная сельхозтехника"

FARM_LEAF_SLUGS: tuple[str, ...] = (
    "transport-farm-machinery-traktory",
    "transport-farm-machinery-mini-traktory",
    "transport-farm-machinery-motobloki-i-motokultivatory",
    "transport-farm-machinery-kombayny",
    "transport-farm-machinery-agrodrony",
    BROAD_IMPLEMENT_SLUG,
    "transport-farm-machinery-drugaya-selhoztehnika",
)

FARM_LEAF_LABELS: dict[str, str] = {
    "transport-farm-machinery-traktory": "Тракторы",
    "transport-farm-machinery-mini-traktory": "Мини-тракторы",
    "transport-farm-machinery-motobloki-i-motokultivatory": (
        "Мотоблоки и мотокультиваторы"
    ),
    "transport-farm-machinery-kombayny": "Комбайны",
    "transport-farm-machinery-agrodrony": "Агродроны",
    BROAD_IMPLEMENT_SLUG: BROAD_IMPLEMENT_LABEL,
    "transport-farm-machinery-drugaya-selhoztehnika": "Другая сельхозтехника",
}

FARM_LEAF_SORT: dict[str, int] = {
    "transport-farm-machinery-traktory": 10,
    "transport-farm-machinery-mini-traktory": 20,
    "transport-farm-machinery-motobloki-i-motokultivatory": 30,
    "transport-farm-machinery-kombayny": 40,
    "transport-farm-machinery-agrodrony": 50,
    BROAD_IMPLEMENT_SLUG: 60,
    "transport-farm-machinery-drugaya-selhoztehnika": 70,
}

FARM_LEAF_EXPECTED_IDS: dict[str, int] = {
    "transport-farm-machinery-traktory": 833,
    "transport-farm-machinery-mini-traktory": 1653,
    "transport-farm-machinery-motobloki-i-motokultivatory": 1223,
    "transport-farm-machinery-kombayny": 834,
    "transport-farm-machinery-agrodrony": 1654,
    BROAD_IMPLEMENT_SLUG: BROAD_IMPLEMENT_ID,
    "transport-farm-machinery-drugaya-selhoztehnika": 1224,
}

FARM_LEAF_VEHICLE_TYPE: dict[str, str] = {
    "transport-farm-machinery-traktory": "tractor",
    "transport-farm-machinery-mini-traktory": "mini_tractor",
    "transport-farm-machinery-motobloki-i-motokultivatory": "walk_behind",
    "transport-farm-machinery-kombayny": "combine",
    "transport-farm-machinery-agrodrony": "agri_drone",
    BROAD_IMPLEMENT_SLUG: "farm_implement",
    "transport-farm-machinery-drugaya-selhoztehnika": "other_agri",
}

# Old slug/id → equipment_type (Motokosilka merges into Косилка).
FARM_RETIRED_IMPLEMENT_MAP: dict[str, tuple[int, str]] = {
    "transport-farm-machinery-posevnaya-tehnika": (835, "Сеялка"),
    "transport-farm-machinery-kartofelesazhalki": (1655, "Картофелесажалка"),
    "transport-farm-machinery-plugi": (1656, "Плуг"),
    "transport-farm-machinery-borony": (1657, "Борона"),
    "transport-farm-machinery-kultivatory": (1658, "Культиватор"),
    "transport-farm-machinery-okuchniki": (1659, "Окучник"),
    "transport-farm-machinery-arychniki": (1660, "Арычник"),
    "transport-farm-machinery-mulchery": (1661, "Мульчер"),
    "transport-farm-machinery-kosilki": (1662, "Косилка"),
    "transport-farm-machinery-motokosilki": (1663, "Косилка"),
    "transport-farm-machinery-press-podborshchiki": (1664, "Пресс-подборщик"),
    "transport-farm-machinery-zhatki": (1665, "Жатка"),
    "transport-farm-machinery-grabli": (1666, "Грабли"),
    "transport-farm-machinery-kormorazdatchiki": (1667, "Кормораздатчик"),
    "transport-farm-machinery-opryskivateli": (838, "Опрыскиватель"),
    "transport-farm-machinery-razbrasyvateli-udobreniy": (
        1668,
        "Разбрасыватель удобрений",
    ),
    "transport-farm-machinery-navozorazbrasyvateli": (
        1669,
        "Навозоразбрасыватель",
    ),
    "transport-farm-machinery-kartofelekopalki": (1670, "Картофелекопалка"),
    "transport-farm-machinery-kuny": (1671, "КУН"),
    "transport-farm-machinery-drobilki": (1672, "Дробилка"),
    "transport-farm-machinery-zernometateli": (1673, "Зернометатель"),
    "transport-farm-machinery-zernoochistiteli": (1674, "Зерноочиститель"),
    "transport-farm-machinery-plenkoukladchiki": (
        1675,
        "Пленкоукладчик / грядообразователь",
    ),
    "transport-farm-machinery-bugoroobrazovateli": (1676, "Бугорообразователь"),
}

FARM_INACTIVE_LEGACY_SLUGS: tuple[str, ...] = (
    *tuple(FARM_RETIRED_IMPLEMENT_MAP.keys()),
    "transport-farm-machinery-pochvoobrabatyvayuschaya-tehnika",
    "transport-farm-machinery-tehnika-dlya-zagotovki-kormov",
    # old slug of broad leaf after rename still listed for safety
    BROAD_IMPLEMENT_OLD_SLUG,
    "transport-farm-machinery-pritsepy-dlya-selhoztehniki",
    "transport-farm-machinery-zapchasti-dlya-selhoztehniki",
    "transport-farm-machinery-remont-i-obsluzhivanie",
)

# Remaps: retired implements → broad; umbrellas → broad; trailer stays 1226.
FARM_REMAP_TARGETS: dict[str, str] = {
    **{src: BROAD_IMPLEMENT_SLUG for src in FARM_RETIRED_IMPLEMENT_MAP},
    "transport-farm-machinery-pochvoobrabatyvayuschaya-tehnika": (
        BROAD_IMPLEMENT_SLUG
    ),
    "transport-farm-machinery-tehnika-dlya-zagotovki-kormov": (
        BROAD_IMPLEMENT_SLUG
    ),
    "transport-farm-machinery-pritsepy-dlya-selhoztehniki": (
        "transport-trailers-pritsepy"
    ),
    "transport-farm-machinery-zapchasti-dlya-selhoztehniki": (
        "transport-auto-parts"
    ),
}

EQUIPMENT_TYPES: tuple[str, ...] = (
    "Сеялка",
    "Плуг",
    "Борона",
    "Культиватор",
    "Окучник",
    "Арычник",
    "Мульчер",
    "Косилка",
    "Пресс-подборщик",
    "Жатка",
    "Грабли",
    "Кормораздатчик",
    "Опрыскиватель",
    "Разбрасыватель удобрений",
    "Навозоразбрасыватель",
    "Картофелесажалка",
    "Картофелекопалка",
    "КУН",
    "Дробилка",
    "Зернометатель",
    "Зерноочиститель",
    "Пленкоукладчик / грядообразователь",
    "Бугорообразователь",
    "Другое",
)

WALK_BEHIND_TYPES: tuple[str, ...] = ("Мотоблок", "Мотокультиватор")
HARVESTER_TYPES: tuple[str, ...] = (
    "Зерноуборочный",
    "Кормоуборочный",
    "Другой",
)
# Broad leaf = навесная/прицепная — no Самоходное.
MOUNT_TYPES: tuple[str, ...] = ("Навесное", "Прицепное", "Другое")
BALER_TYPES: tuple[str, ...] = ("Рулонный", "Тюковый", "Другой")
DRIVE_OPTIONS: tuple[str, ...] = ("2WD", "4WD")
FUEL_OPTIONS: tuple[str, ...] = (
    "Бензин",
    "Дизель",
    "Газ",
    "Электро",
    "Другое",
)
TRANSMISSION_OPTIONS: tuple[str, ...] = (
    "Механическая",
    "Гидростатическая",
    "Другая",
)

_SELLER = ("Частное лицо", "Компания", "Дилер")

WIDTH_TYPES = (
    "Сеялка",
    "Борона",
    "Культиватор",
    "Косилка",
    "Грабли",
    "Опрыскиватель",
    "Разбрасыватель удобрений",
    "Навозоразбрасыватель",
    "Пленкоукладчик / грядообразователь",
    "Картофелесажалка",
    "Мульчер",
    "Жатка",
)
ROW_TYPES = ("Сеялка", "Картофелесажалка")
SPRAYER_TYPES = ("Опрыскиватель",)
BALER_EQ_TYPES = ("Пресс-подборщик",)
MOUNT_SHOW_TYPES = (
    "Опрыскиватель",
    "Плуг",
    "Борона",
    "Культиватор",
    "Косилка",
    "Сеялка",
    "Пресс-подборщик",
    "Грабли",
    "КУН",
    "Картофелесажалка",
    "Картофелекопалка",
    "Разбрасыватель удобрений",
    "Навозоразбрасыватель",
    "Мульчер",
    "Жатка",
    "Другое",
)

FARM_OTHER_BRAND_TYPES: tuple[str, ...] = (
    "tractor",
    "mini_tractor",
    "walk_behind",
    "combine",
    "agri_drone",
    "farm_implement",
    "other_agri",
)

# Brands that must not appear as live manufacturers (pollution).
FARM_POLLUTED_BRAND_NAMES: frozenset[str] = frozenset(
    {
        "ДТ-75",
        "Т-40",
        "Т-25",
        "Т-16",
        "ПЛН",
        "БДТ",
        "КПШ",
        "ПР",
        "ОП",
        "ГВК",
        "Окучник",
        "Арычник",
        "Дробилка",
        "Пленкоукладчик",
        "Грядообразователь",
        "Бугорообразователь",
        "Зерномёт",
        "Зернометатель",
        "Hammer Mill",
        "Млын",
        "КСМ",
        "КТН",
        "РМУ",
        "ПРТ",
        "ПКУ",
        "ТУР",
        "ИСК",
        "ЗПС",
        "ПЗМ",
        "ЗАВ",
        "ОВС",
        "Агроном",
        "Плуг",
        "Борона",
        "Культиватор",
        "Сеялка",
        "Косилка",
        "Грабли",
        "Жатка",
        "КУН",
    }
)

# Clean manufacturers to seed under farm_implement (from existing catalogs).
FARM_IMPLEMENT_CLEAN_BRANDS: tuple[tuple[str, str, str | None], ...] = (
    ("amazone-fi", "Amazone", "Germany"),
    ("horsch-fi", "Horsch", "Germany"),
    ("john-deere-fi", "John Deere", "USA"),
    ("kinze-fi", "Kinze", "USA"),
    ("kuhn-fi", "Kuhn", "France"),
    ("vaderstad-fi", "Väderstad", "Sweden"),
    ("belotserkovmaz-fi", "БелоцерковМАЗ", "Ukraine"),
    ("gazmash-fi", "Газмаш", "Russia"),
    ("alpler-fi", "Alpler", "Turkey"),
    ("gregoire-besson-fi", "Grégoire-Besson", "France"),
    ("kverneland-fi", "Kverneland", "Norway"),
    ("lemken-fi", "Lemken", "Germany"),
    ("vogel-noot-fi", "Vogel & Noot", "Austria"),
    ("unlu-fi", "Ünlü", "Turkey"),
    ("akpil-fi", "Akpil", "Poland"),
    ("quivogne-fi", "Quivogne", "France"),
    ("wil-rich-fi", "Wil-Rich", "USA"),
    ("claas-fi", "CLAAS", "Germany"),
    ("krone-fi", "Krone", "Germany"),
    ("pottinger-fi", "Pöttinger", "Austria"),
    ("sipma-fi", "Sipma", "Poland"),
    ("rostselmash-fi", "Ростсельмаш", "Russia"),
    ("new-holland-fi", "New Holland", "Italy"),
    ("welger-fi", "Welger", "Germany"),
    ("hardi-fi", "Hardi", "Denmark"),
    ("hagie-fi", "Hagie", "USA"),
    ("rogator-fi", "RoGator", "USA"),
    ("tecnoma-fi", "Tecnoma", "France"),
    ("grimme-fi", "Grimme", "Germany"),
    ("hassia-fi", "Hassia", "Germany"),
    ("bolko-fi", "Болко", None),
    ("double-l-fi", "Double L", "USA"),
    ("baselier-fi", "Baselier", "Netherlands"),
    ("dondi-fi", "Dondi", "Italy"),
    ("berti-fi", "Berti", "Italy"),
    ("humus-fi", "Humus", "Germany"),
    ("orcsi-fi", "Orcsi", None),
    ("schulte-fi", "Schulte", "Canada"),
    ("capello-fi", "Capello", "Italy"),
    ("gomselmash-fi", "Гомсельмаш", "Belarus"),
    ("rmh-fi", "RMH", None),
    ("siolo-fi", "Siolo", None),
    ("trioliet-fi", "Trioliet", "Netherlands"),
    ("rauch-fi", "Rauch", "Germany"),
    ("sulky-fi", "Sulky", "France"),
    ("bergmann-fi", "Bergmann", "Germany"),
    ("rozmiesz-fi", "Rozmiesz", None),
    ("strautmann-fi", "Strautmann", "Germany"),
    ("metal-fach-fi", "Metal-Fach", "Poland"),
    ("quicke-fi", "Quicke", "Sweden"),
    ("stoll-fi", "Stoll", "Germany"),
    ("amkodor-fi", "Амкодор", "Belarus"),
    ("farmet-fi", "Farmet", "Czechia"),
    ("crippen-fi", "Crippen", "USA"),
    ("petkus-fi", "Petkus", "Germany"),
    ("hortitec-fi", "Hortitec", None),
)

FARM_YEAR_MIN = 1950
HOURS_MAX = 100_000
POWER_HP_MAX = 1000
WIDTH_M_MAX = 50
ROW_COUNT_MAX = 48
TANK_L_MAX = 20_000

FARM_LEAF_ALIASES: dict[str, str] = {
    "трактор": "transport-farm-machinery-traktory",
    "мини трактор": "transport-farm-machinery-mini-traktory",
    "минитрактор": "transport-farm-machinery-mini-traktory",
    "мотоблок": "transport-farm-machinery-motobloki-i-motokultivatory",
    "мотокультиватор": "transport-farm-machinery-motobloki-i-motokultivatory",
    "комбайн": "transport-farm-machinery-kombayny",
    "агродрон": "transport-farm-machinery-agrodrony",
    "сельхоздрон": "transport-farm-machinery-agrodrony",
    "плуг": BROAD_IMPLEMENT_SLUG,
    "борона": BROAD_IMPLEMENT_SLUG,
    "культиватор": BROAD_IMPLEMENT_SLUG,
    "сеялка": BROAD_IMPLEMENT_SLUG,
    "косилка": BROAD_IMPLEMENT_SLUG,
    "пресс подборщик": BROAD_IMPLEMENT_SLUG,
    "пресс-подборщик": BROAD_IMPLEMENT_SLUG,
    "опрыскиватель": BROAD_IMPLEMENT_SLUG,
    "кун": BROAD_IMPLEMENT_SLUG,
    "картофелесажалка": BROAD_IMPLEMENT_SLUG,
    "картофелекопалка": BROAD_IMPLEMENT_SLUG,
    "навесное оборудование": BROAD_IMPLEMENT_SLUG,
    "сельхознавесное": BROAD_IMPLEMENT_SLUG,
    "другая сельхозтехника": "transport-farm-machinery-drugaya-selhoztehnika",
    "сельхозприцеп": "transport-trailers-pritsepy",
    "прицеп сельскохозяйственный": "transport-trailers-pritsepy",
}

FARM_PARENT_ALIASES: dict[str, str] = {
    "сельхозтехника": FARM_PARENT_SLUG,
    "сельхоз техника": FARM_PARENT_SLUG,
}


def _choices(*labels: str) -> dict[str, Any]:
    items = [{"value": x, "label": x} for x in labels]
    return {"choices": items, "values": items}


def _opt_cfg(*labels: str, **extra: Any) -> dict[str, Any]:
    cfg: dict[str, Any] = {
        "options": [{"value": o, "label": o} for o in labels],
    }
    cfg.update(extra)
    return cfg


def _field(
    key: str,
    label: str,
    ftype: CategoryFieldType,
    required: bool,
    sort: int,
    options: dict[str, Any] | None = None,
    hint: str | None = None,
) -> tuple[str, str, CategoryFieldType, bool, int, dict[str, Any] | None, str | None]:
    return (key, label, ftype, required, sort, options, hint)


def _filt(
    key: str,
    label: str,
    ftype: CategoryFilterType,
    sort: int,
    config: dict[str, Any] | None,
) -> tuple[str, str, CategoryFilterType, int, dict[str, Any] | None]:
    return (key, label, ftype, sort, config)


def _geo_head() -> list:
    return [
        _field("region", "Регион", CategoryFieldType.string, True, 0),
        _field("city", "Город", CategoryFieldType.city, True, 1),
    ]


def _brand_model(sort: int = 10) -> list:
    return [
        _field("brand", "Марка", CategoryFieldType.brand, False, sort),
        _field("model", "Модель", CategoryFieldType.model, False, sort + 5),
    ]


def _year(sort: int) -> list:
    return [
        _field(
            "year",
            "Год выпуска",
            CategoryFieldType.year,
            False,
            sort,
            {"min": FARM_YEAR_MIN, "max_offset_years": 1},
        ),
    ]


def _condition_block(sort: int) -> list:
    return [
        _field(
            "condition",
            "Состояние",
            CategoryFieldType.enum,
            True,
            sort,
            _choices(*CONDITION_V2_CHOICES),
        ),
        _field(
            "needs_investment",
            "Требует вложений",
            CategoryFieldType.enum,
            False,
            sort + 5,
            _choices(*YES_NO_CHOICES),
        ),
    ]


def _commerce(sort: int) -> list:
    return [
        _field("price", "Цена", CategoryFieldType.price, True, sort),
        _field(
            "negotiable",
            "Возможность торга",
            CategoryFieldType.enum,
            True,
            sort + 10,
            _choices(*NEGOTIABLE_CHOICES),
        ),
        _field(
            "exchange",
            "Возможность обмена",
            CategoryFieldType.enum,
            False,
            sort + 20,
            _choices(*EXCHANGE_CHOICES),
        ),
        _field(
            "installment",
            "Возможность рассрочки",
            CategoryFieldType.enum,
            False,
            sort + 30,
            _choices(*INSTALLMENT_CHOICES),
        ),
        _field(
            "seller_type",
            "Кто продаёт",
            CategoryFieldType.enum,
            True,
            sort + 40,
            _choices(*_SELLER),
        ),
        _field(
            "contact_methods",
            "Способы связи",
            CategoryFieldType.enum,
            True,
            sort + 50,
            _choices(*CONTACT_METHOD_CHOICES),
        ),
    ]


def _operating_hours(sort: int) -> list:
    return [
        _field(
            "operating_hours",
            "Моточасы",
            CategoryFieldType.number,
            False,
            sort,
            {"min": 0, "max": HOURS_MAX, "unit": "ч", "integer": True},
            "Наработка в моточасах",
        ),
    ]


def _engine_power(sort: int) -> list:
    return [
        _field(
            "engine_power_hp",
            "Мощность двигателя",
            CategoryFieldType.number,
            False,
            sort,
            {"min": 0, "max": POWER_HP_MAX, "unit": "л.с.", "integer": True},
            "Мощность в лошадиных силах",
        ),
    ]


def _drive(sort: int) -> list:
    return [
        _field(
            "drive",
            "Привод",
            CategoryFieldType.enum,
            False,
            sort,
            _choices(*DRIVE_OPTIONS),
        ),
    ]


def _fuel(sort: int) -> list:
    return [
        _field(
            "fuel",
            "Топливо",
            CategoryFieldType.enum,
            False,
            sort,
            _choices(*FUEL_OPTIONS),
        ),
    ]


def _transmission(sort: int) -> list:
    return [
        _field(
            "transmission",
            "Коробка передач",
            CategoryFieldType.enum,
            False,
            sort,
            _choices(*TRANSMISSION_OPTIONS),
        ),
    ]


def _depends(field: str, values: tuple[str, ...]) -> dict[str, Any]:
    return {"depends_on": {"field": field, "values": list(values)}}


def _tractor_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(10),
        *_year(25),
        *_operating_hours(30),
        *_engine_power(40),
        *_drive(50),
        *_fuel(60),
        *_transmission(70),
        *_condition_block(100),
        *_commerce(120),
    ]


def _mini_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(10),
        *_year(25),
        *_operating_hours(30),
        *_engine_power(40),
        *_drive(50),
        *_fuel(60),
        *_transmission(70),
        *_condition_block(100),
        *_commerce(120),
    ]


def _motoblock_fields() -> list:
    return [
        *_geo_head(),
        _field(
            "walk_behind_type",
            "Тип техники",
            CategoryFieldType.enum,
            True,
            8,
            _choices(*WALK_BEHIND_TYPES),
        ),
        *_brand_model(10),
        *_year(25),
        *_engine_power(40),
        *_fuel(60),
        *_condition_block(100),
        *_commerce(120),
    ]


def _combine_fields() -> list:
    return [
        *_geo_head(),
        _field(
            "harvester_type",
            "Тип комбайна",
            CategoryFieldType.enum,
            False,
            8,
            _choices(*HARVESTER_TYPES),
        ),
        *_brand_model(10),
        *_year(25),
        *_operating_hours(30),
        *_engine_power(40),
        *_fuel(60),
        *_transmission(70),
        *_condition_block(100),
        *_commerce(120),
    ]


def _drone_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(10),
        *_year(25),
        *_condition_block(100),
        *_commerce(120),
    ]


def _implement_fields() -> list:
    width_opts = {
        "min": 0,
        "max": WIDTH_M_MAX,
        "unit": "m",
        **_depends("equipment_type", WIDTH_TYPES),
    }
    row_opts = {
        "min": 1,
        "max": ROW_COUNT_MAX,
        "integer": True,
        **_depends("equipment_type", ROW_TYPES),
    }
    tank_opts = {
        "min": 0,
        "max": TANK_L_MAX,
        "unit": "L",
        "integer": True,
        **_depends("equipment_type", SPRAYER_TYPES),
    }
    baler_opts = {
        **_choices(*BALER_TYPES),
        **_depends("equipment_type", BALER_EQ_TYPES),
    }
    mount_opts = {
        **_choices(*MOUNT_TYPES),
        **_depends("equipment_type", MOUNT_SHOW_TYPES),
    }
    return [
        *_geo_head(),
        _field(
            "equipment_type",
            "Тип техники",
            CategoryFieldType.enum,
            True,
            8,
            _choices(*EQUIPMENT_TYPES),
        ),
        *_brand_model(10),
        *_year(25),
        _field(
            "mount_type",
            "Способ установки",
            CategoryFieldType.enum,
            False,
            35,
            mount_opts,
        ),
        _field(
            "working_width_m",
            "Ширина захвата",
            CategoryFieldType.decimal,
            False,
            40,
            width_opts,
            "Ширина захвата в метрах",
        ),
        _field(
            "row_count",
            "Количество рядов",
            CategoryFieldType.number,
            False,
            45,
            row_opts,
        ),
        _field(
            "tank_capacity_l",
            "Объём бака",
            CategoryFieldType.number,
            False,
            50,
            tank_opts,
            "Объём бака в литрах",
        ),
        _field(
            "baler_type",
            "Тип пресс-подборщика",
            CategoryFieldType.enum,
            False,
            55,
            baler_opts,
        ),
        *_condition_block(100),
        *_commerce(120),
    ]


def _other_fields() -> list:
    return [
        *_geo_head(),
        *_brand_model(10),
        *_year(25),
        *_operating_hours(30),
        *_engine_power(40),
        *_condition_block(100),
        *_commerce(120),
    ]


FARM_CORE_FIELDS_BY_SLUG: dict[str, list] = {
    "transport-farm-machinery-traktory": _tractor_fields(),
    "transport-farm-machinery-mini-traktory": _mini_fields(),
    "transport-farm-machinery-motobloki-i-motokultivatory": _motoblock_fields(),
    "transport-farm-machinery-kombayny": _combine_fields(),
    "transport-farm-machinery-agrodrony": _drone_fields(),
    BROAD_IMPLEMENT_SLUG: _implement_fields(),
    "transport-farm-machinery-drugaya-selhoztehnika": _other_fields(),
}


def _common_search_head(*, sort: int = 10) -> list:
    return [
        _filt("brand", "Марка", CategoryFilterType.select, sort, {}),
        _filt("model", "Модель", CategoryFilterType.select, sort + 10, {}),
        _filt("price", "Цена", CategoryFilterType.range, sort + 20, {"unit": "KGS"}),
        _filt("year", "Год выпуска", CategoryFilterType.range, sort + 30, {}),
        _filt("region", "Регион", CategoryFilterType.select, sort + 40, {}),
        _filt("city", "Город", CategoryFilterType.select, sort + 50, {}),
    ]


def _condition_seller_sort(sort: int) -> list:
    return [
        _filt(
            "condition",
            "Состояние",
            CategoryFilterType.multi_select,
            sort,
            _opt_cfg(*CONDITION_V2_CHOICES),
        ),
        _filt(
            "seller_type",
            "Кто продаёт",
            CategoryFilterType.multi_select,
            sort + 10,
            _opt_cfg(*_SELLER),
        ),
        _filt(
            "sort",
            "Сортировка",
            CategoryFilterType.select,
            sort + 20,
            {
                "options": [
                    {"value": "newest", "label": "Сначала новые"},
                    {"value": "price_asc", "label": "Сначала дешевле"},
                    {"value": "price_desc", "label": "Сначала дороже"},
                ]
            },
        ),
    ]


def _self_propelled_advanced(sort: int = 200, *, with_drive: bool = True) -> list:
    out = [
        _filt(
            "operating_hours",
            "Моточасы",
            CategoryFilterType.range,
            sort,
            {"unit": "ч", "mode": "max"},
        ),
        _filt(
            "engine_power_hp",
            "Мощность двигателя",
            CategoryFilterType.range,
            sort + 10,
            {"unit": "л.с.", "mode": "min"},
        ),
    ]
    if with_drive:
        out.append(
            _filt(
                "drive",
                "Привод",
                CategoryFilterType.multi_select,
                sort + 20,
                _opt_cfg(*DRIVE_OPTIONS),
            )
        )
    out.append(
        _filt(
            "fuel",
            "Топливо",
            CategoryFilterType.multi_select,
            sort + 30,
            _opt_cfg(*FUEL_OPTIONS),
        )
    )
    out.append(
        _filt(
            "transmission",
            "Коробка передач",
            CategoryFilterType.multi_select,
            sort + 40,
            _opt_cfg(*TRANSMISSION_OPTIONS),
        )
    )
    return out


def _tractor_search() -> list:
    return [
        *_common_search_head(),
        *_condition_seller_sort(100),
        *_self_propelled_advanced(200, with_drive=True),
    ]


def _mini_search() -> list:
    return _tractor_search()


def _motoblock_search() -> list:
    return [
        _filt(
            "walk_behind_type",
            "Тип техники",
            CategoryFilterType.multi_select,
            5,
            _opt_cfg(*WALK_BEHIND_TYPES),
        ),
        *_common_search_head(sort=10),
        *_condition_seller_sort(100),
        _filt(
            "engine_power_hp",
            "Мощность двигателя",
            CategoryFilterType.range,
            200,
            {"unit": "л.с.", "mode": "min"},
        ),
        _filt(
            "fuel",
            "Топливо",
            CategoryFilterType.multi_select,
            210,
            _opt_cfg(*FUEL_OPTIONS),
        ),
    ]


def _combine_search() -> list:
    return [
        _filt(
            "harvester_type",
            "Тип комбайна",
            CategoryFilterType.multi_select,
            5,
            _opt_cfg(*HARVESTER_TYPES),
        ),
        *_common_search_head(sort=10),
        *_condition_seller_sort(100),
        *_self_propelled_advanced(200, with_drive=False),
    ]


def _drone_search() -> list:
    return [
        *_common_search_head(),
        *_condition_seller_sort(100),
    ]


def _implement_search() -> list:
    return [
        _filt(
            "equipment_type",
            "Тип техники",
            CategoryFilterType.multi_select,
            5,
            _opt_cfg(*EQUIPMENT_TYPES),
        ),
        _filt("price", "Цена", CategoryFilterType.range, 20, {"unit": "KGS"}),
        _filt("region", "Регион", CategoryFilterType.select, 40, {}),
        _filt("city", "Город", CategoryFilterType.select, 50, {}),
        *_condition_seller_sort(100),
        _filt("brand", "Марка", CategoryFilterType.select, 200, {}),
        _filt(
            "working_width_m",
            "Ширина захвата",
            CategoryFilterType.range,
            210,
            {
                "unit": "m",
                "depends_on": {
                    "field": "equipment_type",
                    "values": list(WIDTH_TYPES),
                },
            },
        ),
        _filt(
            "mount_type",
            "Способ установки",
            CategoryFilterType.multi_select,
            220,
            {
                **_opt_cfg(*MOUNT_TYPES),
                "depends_on": {
                    "field": "equipment_type",
                    "values": list(MOUNT_SHOW_TYPES),
                },
            },
        ),
        _filt(
            "row_count",
            "Количество рядов",
            CategoryFilterType.range,
            230,
            {
                "mode": "min",
                "depends_on": {
                    "field": "equipment_type",
                    "values": list(ROW_TYPES),
                },
            },
        ),
        _filt(
            "tank_capacity_l",
            "Объём бака",
            CategoryFilterType.range,
            240,
            {
                "unit": "L",
                "mode": "min",
                "depends_on": {
                    "field": "equipment_type",
                    "values": list(SPRAYER_TYPES),
                },
            },
        ),
        _filt(
            "baler_type",
            "Тип пресс-подборщика",
            CategoryFilterType.multi_select,
            250,
            {
                **_opt_cfg(*BALER_TYPES),
                "depends_on": {
                    "field": "equipment_type",
                    "values": list(BALER_EQ_TYPES),
                },
            },
        ),
    ]


def _other_search() -> list:
    return [
        *_common_search_head(),
        *_condition_seller_sort(100),
        _filt(
            "operating_hours",
            "Моточасы",
            CategoryFilterType.range,
            200,
            {"unit": "ч", "mode": "max"},
        ),
        _filt(
            "engine_power_hp",
            "Мощность двигателя",
            CategoryFilterType.range,
            210,
            {"unit": "л.с.", "mode": "min"},
        ),
    ]


FARM_SEARCH_FILTERS_BY_SLUG: dict[str, list] = {
    "transport-farm-machinery-traktory": _tractor_search(),
    "transport-farm-machinery-mini-traktory": _mini_search(),
    "transport-farm-machinery-motobloki-i-motokultivatory": _motoblock_search(),
    "transport-farm-machinery-kombayny": _combine_search(),
    "transport-farm-machinery-agrodrony": _drone_search(),
    BROAD_IMPLEMENT_SLUG: _implement_search(),
    "transport-farm-machinery-drugaya-selhoztehnika": _other_search(),
}


def farm_other_brands() -> list[tuple[str, str, str | None, str]]:
    out: list[tuple[str, str, str | None, str]] = []
    for vt in FARM_OTHER_BRAND_TYPES:
        out.append((f"other-{vt.replace('_', '-')}", "Другая марка", None, vt))
    return out


def farm_other_models() -> dict[str, list[tuple[str, str]]]:
    return {
        f"other-{vt.replace('_', '-')}": [
            (f"other-{vt.replace('_', '-')}-model", "Другая модель")
        ]
        for vt in FARM_OTHER_BRAND_TYPES
    }


def farm_implement_brands() -> list[tuple[str, str, str | None, str]]:
    return [
        (slug, name, country, "farm_implement")
        for slug, name, country in FARM_IMPLEMENT_CLEAN_BRANDS
    ]
