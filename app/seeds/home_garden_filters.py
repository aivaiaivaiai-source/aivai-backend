"""Dependent filter schemas for Home & Garden leaf categories.

Category-specific only — no city/price/title/description (common listing fields).
Fields are optional by default (is_required=False) unless noted.
"""
from __future__ import annotations

from typing import Any

from app.models.category_enums import CategoryFieldType
from app.seeds.home_garden_catalog_final import HOME_GARDEN_LEAF_SLUGS

# (field_key, label, field_type, is_required, options|None, ai_hint|None)
FieldDef = tuple[str, str, CategoryFieldType, bool, dict[str, Any] | None, str | None]

_COND_OPTS = {
    "choices": [
        {"value": "new", "label": "Новое"},
        {"value": "used", "label": "Б/у"},
    ]
}
_YN = {
    "choices": [
        {"value": "yes", "label": "Да"},
        {"value": "no", "label": "Нет"},
    ]
}
_BED_SIZE = {
    "choices": [
        {"value": "single", "label": "Односпальное"},
        {"value": "one_half", "label": "Полуторное"},
        {"value": "double", "label": "Двуспальное"},
        {"value": "euro", "label": "Евро"},
        {"value": "family", "label": "Семейное"},
        {"value": "kids", "label": "Детское"},
    ]
}
_PLANT_SIZE = {
    "choices": [
        {"value": "small", "label": "Маленькое"},
        {"value": "medium", "label": "Среднее"},
        {"value": "large", "label": "Крупное"},
    ]
}
_FERT_FORM = {
    "choices": [
        {"value": "liquid", "label": "Жидкость"},
        {"value": "granules", "label": "Гранулы"},
        {"value": "powder", "label": "Порошок"},
        {"value": "other", "label": "Другое"},
    ]
}
_POWER_TYPE = {
    "choices": [
        {"value": "petrol", "label": "Бензин"},
        {"value": "electric", "label": "Электричество"},
        {"value": "battery", "label": "Аккумулятор"},
    ]
}
_FUEL_BBQ = {
    "choices": [
        {"value": "coal_wood", "label": "Уголь / дрова"},
        {"value": "gas", "label": "Газ"},
        {"value": "electric", "label": "Электричество"},
    ]
}
_FUEL_STOVE = {
    "choices": [
        {"value": "wood", "label": "Дрова"},
        {"value": "coal", "label": "Уголь"},
        {"value": "gas", "label": "Газ"},
        {"value": "electric", "label": "Электричество"},
        {"value": "other", "label": "Другое"},
    ]
}
_SAFE_PURPOSE = {
    "choices": [
        {"value": "money_documents", "label": "Для денег и документов"},
        {"value": "weapon", "label": "Оружейный"},
        {"value": "mini", "label": "Мини-сейф"},
        {"value": "other", "label": "Другое"},
    ]
}
_LOCK_TYPE = {
    "choices": [
        {"value": "key", "label": "Ключевой"},
        {"value": "mechanical_code", "label": "Кодовый"},
        {"value": "electronic", "label": "Электронный"},
        {"value": "other", "label": "Другой"},
    ]
}
_FURNITURE_PART = {
    "choices": [
        {"value": "countertop", "label": "Столешница"},
        {"value": "facade", "label": "Фасад"},
        {"value": "hardware", "label": "Фурнитура"},
        {"value": "legs", "label": "Ножки"},
        {"value": "handles", "label": "Ручки"},
        {"value": "wheels", "label": "Колёсики"},
        {"value": "other", "label": "Другое"},
    ]
}
_CONTAINER_MATERIAL = {
    "choices": [
        {"value": "plastic", "label": "Пластик"},
        {"value": "metal", "label": "Металл"},
        {"value": "stainless_steel", "label": "Нержавеющая сталь"},
        {"value": "other", "label": "Другое"},
    ]
}
_GAS_PURPOSE = {
    "choices": [
        {"value": "household", "label": "Бытовой"},
        {"value": "portable", "label": "Портативный"},
        {"value": "industrial", "label": "Промышленный"},
        {"value": "other", "label": "Другое"},
    ]
}
_FILL_STATE = {
    "choices": [
        {"value": "empty", "label": "Пустой"},
        {"value": "filled", "label": "Заправленный"},
    ]
}

_E = CategoryFieldType.enum
_N = CategoryFieldType.number
_D = CategoryFieldType.decimal
_S = CategoryFieldType.string
_B = CategoryFieldType.brand


def _f(
    key: str,
    label: str,
    ftype: CategoryFieldType,
    *,
    required: bool = False,
    options: dict[str, Any] | None = None,
    hint: str | None = None,
) -> FieldDef:
    return (key, label, ftype, required, options, hint)


CONDITION = _f("condition", "Состояние", _E, options=_COND_OPTS)
WIDTH = _f("width_cm", "Ширина", _N, hint="см")
HEIGHT = _f("height_cm", "Высота", _N, hint="см")
DEPTH = _f("depth_cm", "Глубина", _N, hint="см")
LENGTH = _f("length_cm", "Длина", _N, hint="см")
MATERIAL = _f("material", "Материал", _S)
SIZE = _f("size", "Размер", _S)
VOLUME = _f("volume", "Объём", _D)
CAPACITY = _f("capacity", "Объём", _D, hint="л")
WEIGHT = _f("weight", "Вес", _D)
QUANTITY = _f("quantity", "Количество", _N)
BRAND = _f("brand", "Бренд", _B)
POWER = _f("power", "Мощность", _S)
DIAMETER = _f("diameter_cm", "Диаметр", _N, hint="см")
CONTAINER_MATERIAL = _f("material", "Материал", _E, options=_CONTAINER_MATERIAL)


def _ends(slug: str, *suffixes: str) -> bool:
    return any(slug.endswith(s) or slug.endswith("-" + s) for s in suffixes)


def fields_for_leaf(slug: str) -> list[FieldDef]:
    """Return dependent product characteristics for a leaf category slug."""
    # --- Furniture ---
    if slug.endswith("-seyfy"):
        return [
            _f("safe_purpose", "Назначение", _E, options=_SAFE_PURPOSE),
            _f("lock_type", "Тип замка", _E, options=_LOCK_TYPE),
            CONDITION,
        ]
    if "komplektuyuschie-dlya-mebeli" in slug:
        return [
            _f("furniture_part_type", "Тип комплектующей", _E, options=_FURNITURE_PART),
            CONDITION,
        ]
    if slug.endswith("-divany"):
        return [CONDITION, WIDTH, HEIGHT, DEPTH, MATERIAL, _f("foldable", "Раскладной", _E, options=_YN)]
    if slug.endswith("-krovati") or slug.endswith("-matrasy"):
        return [
            CONDITION,
            WIDTH,
            HEIGHT,
            DEPTH,
            MATERIAL,
            _f("sleeping_place_size", "Размер спального места", _E, options=_BED_SIZE),
        ]
    if slug.endswith("-shkafy") or "ofisnye-shkafy" in slug:
        return [
            CONDITION,
            WIDTH,
            HEIGHT,
            DEPTH,
            MATERIAL,
            _f("door_count", "Количество дверей", _N),
        ]
    if "mebel" in slug and any(
        x in slug
        for x in (
            "kresla",
            "komody",
            "tumby",
            "stoly",
            "stulya",
            "pufy",
            "polki",
            "sunduki",
            "garnitury",
            "komplekty",
            "banketki",
            "skameyki",
            "lezaki",
            "stoiki",
            "tualetnye-stoliki",
            "shirmy-i-peregorodki",
            "drugaya-mebel",
            "drugie-garnitury",
            "drugie-komplekty",
            "drugaya-ofisnaya",
            "drugaya-sadovaya",
        )
    ):
        return [CONDITION, WIDTH, HEIGHT, DEPTH, MATERIAL]

    # --- Carpets ---
    if slug.startswith("home-garden-tekstil-i-kovry-"):
        fields = [CONDITION, LENGTH, WIDTH, MATERIAL]
        if any(x in slug for x in ("kovry", "kovriki", "palasy", "detskie")):
            fields.append(_f("shape", "Форма", _S))
        return fields

    # --- Sleep ---
    if "postelnoe-bele" in slug and "postelnoe-bele-i-pledy-postelnoe" in slug:
        return [
            CONDITION,
            _f("bedding_size", "Размер", _E, options=_BED_SIZE),
            MATERIAL,
        ]
    if slug.startswith("home-garden-postelnoe-bele-i-pledy-"):
        if any(x in slug for x in ("podushki", "odeyala")):
            return [CONDITION, SIZE, _f("filler", "Наполнитель", _S)]
        return [CONDITION, SIZE, MATERIAL]

    # --- Curtains ---
    if slug.startswith("home-garden-shtory-zhalyuzi-i-karnizy-"):
        if "karnizy" in slug and slug.endswith("-karnizy"):
            return [CONDITION, LENGTH, MATERIAL]
        return [CONDITION, WIDTH, HEIGHT, MATERIAL]

    # --- Dishware ---
    if slug.startswith("home-garden-posuda-kuhonnye-prinadlezhnosti-"):
        fields = [CONDITION, MATERIAL]
        if any(
            x in slug
            for x in ("kastryuli", "skovorody", "kazany", "chayniki", "termosy", "konteynery")
        ):
            fields.append(VOLUME)
        if "servizy" in slug or "nabory" in slug:
            fields.append(_f("item_count", "Количество предметов", _N))
        return fields

    # --- Household chemicals ---
    if slug.startswith("home-garden-bytovaya-himiya-i-hoz-tovary-"):
        if any(
            x in slug
            for x in (
                "sredstva-dlya-stirki",
                "sredstva-dlya-mytya",
                "sredstva-dlya-uborki",
                "sredstva-dlya-vannoy",
                "osvezhiteli",
            )
        ):
            return [VOLUME, WEIGHT]
        if any(
            x in slug
            for x in (
                "vedra",
                "shvabry",
                "sushilki",
                "gladilnye",
                "musornye",
                "perchatki",
                "gubki",
            )
        ):
            return [CONDITION]
        return [CONDITION]

    # --- Bathroom ---
    if slug.startswith("home-garden-tovary-dlya-vannoy-"):
        return [CONDITION, SIZE, MATERIAL]

    # --- Storage ---
    if slug.startswith("home-garden-hranenie-i-organizatsiya-"):
        return [CONDITION, SIZE, MATERIAL, QUANTITY]

    # --- Decor ---
    if slug.startswith("home-garden-dekor-i-interer-"):
        return [CONDITION, SIZE, MATERIAL]

    # --- Mirrors ---
    if slug.startswith("home-garden-zerkala-"):
        return [CONDITION, WIDTH, HEIGHT, _f("shape", "Форма", _S)]

    # --- Live plants ---
    if slug.startswith("home-garden-komnatnye-rasteniya-i-tsvety-"):
        return [
            _f("plant_size", "Размер растения", _E, options=_PLANT_SIZE),
            _f("with_pot", "С горшком", _E, options=_YN),
        ]

    # --- Artificial plants ---
    if slug.startswith("home-garden-iskusstvennye-tsvety-i-rasteniya-"):
        return [CONDITION, SIZE, QUANTITY]

    # --- Seedlings ---
    if slug.startswith("home-garden-sazhentsy-i-rassada-"):
        return [
            _f("plant_name", "Название растения", _S),
            _f("seedling_age", "Возраст саженца", _S),
            QUANTITY,
        ]

    # --- Seeds ---
    if slug.startswith("home-garden-semena-i-posadochnyy-material-"):
        return [_f("plant_name", "Название растения", _S), WEIGHT, QUANTITY]

    # --- Pots / soil ---
    if slug.startswith("home-garden-gorshki-kashpo-i-grunty-"):
        if any(x in slug for x in ("gorshki", "kashpo", "vazony", "poddony")):
            return [CONDITION, DIAMETER, VOLUME, MATERIAL]
        if any(x in slug for x in ("grunt", "substraty", "drenazh")):
            return [WEIGHT, VOLUME]
        return [CONDITION, SIZE]

    # --- Fertilizers ---
    if slug.startswith("home-garden-udobreniya-dlya-rasteniy-"):
        return [_f("form", "Форма", _E, options=_FERT_FORM), WEIGHT, VOLUME]

    # --- Plant protection ---
    if slug.startswith("home-garden-sredstva-zaschity-rasteniy-"):
        if "zaschitnye-setki" in slug:
            return [CONDITION, SIZE, MATERIAL]
        return [_f("form", "Форма выпуска", _S), WEIGHT, VOLUME]

    # --- Greenhouses ---
    if slug.startswith("home-garden-teplitsy-i-parniki-"):
        if "zatenyayuschie-setki" in slug:
            return [CONDITION, SIZE, MATERIAL]
        if any(x in slug for x in ("teplitsy", "parniki")) and "dugi" not in slug and "plenka" not in slug and "polikarbonat" not in slug and "komplektuyuschie" not in slug:
            return [CONDITION, LENGTH, WIDTH, HEIGHT, _f("cover_material", "Материал покрытия", _S)]
        if "plenka" in slug or "polikarbonat" in slug:
            return [CONDITION, LENGTH, WIDTH, SIZE]
        return [CONDITION]

    # --- Irrigation ---
    if slug.startswith("home-garden-poliv-i-oroshenie-"):
        if slug.endswith("-shlangi"):
            return [CONDITION, LENGTH, DIAMETER]
        if "opryskivateli" in slug or "motopompy" in slug or "nasosy" in slug:
            return [CONDITION, BRAND, POWER, _f("throughput", "Производительность", _S)]
        return [CONDITION]

    # --- Containers / reservoirs ---
    if slug.startswith("home-garden-emkosti-i-rezervuary-") or slug == "home-garden-emkosti-i-rezervuary":
        return [CAPACITY, CONTAINER_MATERIAL, CONDITION]

    # --- Firewood / coal ---
    if slug.startswith("home-garden-drova-i-ugol-") or slug == "home-garden-drova-i-ugol":
        return [WEIGHT, VOLUME, QUANTITY]

    # --- Gas cylinders (L2 leaf) ---
    if slug == "home-garden-gazovye-ballony":
        return [
            _f("gas_cylinder_purpose", "Назначение", _E, options=_GAS_PURPOSE),
            CAPACITY,
            CONDITION,
            _f("fill_state", "Заправка", _E, options=_FILL_STATE),
        ]

    # --- Holiday goods ---
    if slug.startswith("home-garden-tovary-dlya-prazdnikov-"):
        if "vozdushnye-shary" in slug and "nasosy" not in slug and "stoyki" not in slug and "aksessuary" not in slug:
            return [QUANTITY, SIZE, MATERIAL]
        return [CONDITION, SIZE, QUANTITY]

    # --- Garden tools ---
    if slug.startswith("home-garden-sadovyy-inventar-"):
        if "tachki" in slug:
            return [CONDITION, _f("wheel_count", "Количество колёс", _N)]
        return [CONDITION]

    # --- Garden machinery ---
    if slug.startswith("home-garden-sadovaya-tehnika-"):
        fields = [CONDITION, BRAND, _f("power_type", "Тип питания", _E, options=_POWER_TYPE), POWER]
        if "gazonokosilki" in slug:
            fields.extend(
                [
                    _f("cutting_width", "Ширина скашивания", _N),
                    _f("self_propelled", "Самоходная", _E, options=_YN),
                ]
            )
        if "benzopily" in slug:
            fields.append(_f("bar_length", "Длина шины", _N))
        if "moyki" in slug:
            fields.append(_f("pressure", "Давление", _S))
        return fields

    # --- Gazebo / dacha ---
    if slug.startswith("home-garden-besedki-navesy-i-tovary-dlya-dachi-"):
        return [CONDITION, SIZE, MATERIAL]

    # --- BBQ ---
    if slug.startswith("home-garden-mangaly-barbekyu-tandyr-grili-"):
        fields = [CONDITION]
        if any(x in slug for x in ("mangaly", "barbekyu", "grili", "tandyr", "koptilni", "kazany")):
            fields.extend(
                [
                    _f("fuel_type", "Тип топлива", _E, options=_FUEL_BBQ),
                    SIZE,
                    MATERIAL,
                ]
            )
        else:
            fields.append(MATERIAL)
        return fields

    # --- Pools ---
    if slug.startswith("home-garden-basseyny-i-tovary-dlya-otdyha-"):
        if any(x in slug for x in ("karkasnye", "naduvnye", "detskie-basseyny", "sbornye")):
            return [
                CONDITION,
                _f("length_or_diameter", "Длина / диаметр", _N),
                WIDTH,
                _f("depth_cm", "Высота / глубина", _N),
                VOLUME,
            ]
        if "filtry-i-nasosy" in slug:
            return [CONDITION, _f("throughput", "Производительность", _S)]
        if "sredstva-dlya-uhoda" in slug:
            return [VOLUME, WEIGHT]
        return [CONDITION]

    # --- Swings ---
    if slug.startswith("home-garden-sadovye-kacheli-i-gamaki-"):
        return [
            CONDITION,
            _f("seat_count", "Количество мест", _N),
            _f("max_load", "Максимальная нагрузка", _S),
            SIZE,
        ]

    # --- Bath / sauna goods ---
    if slug.startswith("home-garden-tovary-dlya-bani-i-sauny-"):
        if "veniki" in slug or "kamni" in slug:
            return [MATERIAL, SIZE]
        return [CONDITION, MATERIAL, VOLUME, SIZE]

    # --- Fireplaces / stoves ---
    if slug.startswith("home-garden-kaminy-pechi-i-aksessuary-"):
        if any(
            x in slug
            for x in ("kaminy", "pechi", "burzhuyki", "kaminnye-topki")
        ) and "dymohody" not in slug and "dvertsy" not in slug and "aksessuary" not in slug:
            return [
                CONDITION,
                _f("fuel_type", "Тип топлива", _E, options=_FUEL_STOVE),
                POWER,
            ]
        return [CONDITION]

    # --- Prochee leaf = L2 itself ---
    if slug == "home-garden-prochee-dlya-doma-i-sada":
        return [CONDITION]

    # Fallback minimal
    return [CONDITION]


def build_home_garden_core_fields() -> dict[str, list[FieldDef]]:
    return {slug: fields_for_leaf(slug) for slug in HOME_GARDEN_LEAF_SLUGS}


# Search filter: (filter_key, label, CategoryFilterType value, config|None)
SearchFilterDef = tuple[str, str, str, dict[str, Any] | None]


def _filter_config_from_core(field: FieldDef) -> dict[str, Any] | None:
    _key, _label, ftype, _req, options, _hint = field
    if options:
        return dict(options)
    ftv = ftype.value if hasattr(ftype, "value") else str(ftype)
    if ftv in {"number", "decimal"}:
        return {"mode": "range"}
    return None


def _core_type_to_filter_type(field: FieldDef) -> str:
    ftype = field[2]
    ftv = ftype.value if hasattr(ftype, "value") else str(ftype)
    if ftv == "enum":
        return "select"
    if ftv == "boolean":
        return "boolean"
    if ftv in {"number", "decimal"}:
        return "range"
    if ftv == "brand":
        return "text"
    return "text"


def _wanted_search_keys(slug: str) -> list[str]:
    """Approved searchable keys per leaf (subset of core_fields)."""
    if slug.endswith("-seyfy"):
        return ["safe_purpose", "lock_type", "condition"]
    if slug.endswith("-divany"):
        return ["condition", "width_cm", "depth_cm", "foldable"]
    if slug.endswith("-matrasy"):
        return ["sleeping_place_size", "condition"]
    if slug.startswith("home-garden-tekstil-i-kovry-"):
        return ["length_cm", "width_cm", "shape", "condition"]
    if slug.startswith("home-garden-emkosti-i-rezervuary-") or slug == "home-garden-emkosti-i-rezervuary":
        return ["capacity", "material", "condition"]
    if "gazonokosilki" in slug:
        return ["brand", "power_type", "condition", "self_propelled"]
    if slug == "home-garden-gazovye-ballony":
        return ["gas_cylinder_purpose", "capacity", "condition", "fill_state"]
    if slug.startswith("home-garden-drova-i-ugol-"):
        return ["weight", "volume", "quantity"]
    if slug.endswith("-toshoki"):
        return ["condition", "size"]
    # Other garden tech with useful enums
    if slug.startswith("home-garden-sadovaya-tehnika-"):
        return ["brand", "power_type", "condition"]
    # Generic furniture leaves with condition
    if "mebel-dlya-doma" in slug and any(
        x in slug
        for x in (
            "kresla",
            "krovati",
            "shkafy",
            "komody",
            "tumby",
            "stoly",
            "stulya",
            "pufy",
            "sunduki",
            "tualetnye",
            "shirmy",
            "komplektuyuschie",
        )
    ):
        return ["condition", "material"]
    return []


def search_filters_for_leaf(slug: str) -> list[SearchFilterDef]:
    wanted = _wanted_search_keys(slug)
    if not wanted:
        return []
    by_key = {f[0]: f for f in fields_for_leaf(slug)}
    out: list[SearchFilterDef] = []
    for key in wanted:
        field = by_key.get(key)
        if field is None:
            continue
        _k, label, _t, _r, _o, _h = field
        out.append(
            (
                key,
                label,
                _core_type_to_filter_type(field),
                _filter_config_from_core(field),
            )
        )
    return out


def build_home_garden_search_filters() -> dict[str, list[SearchFilterDef]]:
    return {slug: search_filters_for_leaf(slug) for slug in HOME_GARDEN_LEAF_SLUGS}


# Explicit old shallow L3 → TARGET leaf (MERGE / MOVE / CROSS_L1).
LEGACY_L3_REMAP: dict[str, str] = {
    # Furniture
    "home-garden-mebel-dlya-doma-divany": "home-garden-mebel-dlya-doma-divany",
    "home-garden-mebel-dlya-doma-kresla": "home-garden-mebel-dlya-doma-kresla",
    "home-garden-mebel-dlya-doma-krovati": "home-garden-mebel-dlya-doma-krovati",
    "home-garden-mebel-dlya-doma-shkafy": "home-garden-mebel-dlya-doma-shkafy",
    "home-garden-mebel-dlya-doma-komody-i-tumby": "home-garden-mebel-dlya-doma-komody",
    "home-garden-mebel-dlya-doma-stoly": "home-garden-mebel-dlya-doma-stoly",
    "home-garden-mebel-dlya-doma-stulya-i-taburety": "home-garden-mebel-dlya-doma-stulya-i-taburety",
    "home-garden-mebel-dlya-doma-polki-i-stellazhi": "home-garden-mebel-dlya-doma-polki-i-stellazhi",
    "home-garden-mebel-dlya-doma-kuhonnye-garnitury": "home-garden-mebel-dlya-doma-mebelnye-garnitury-kuhonnye-garnitury",
    "home-garden-mebel-dlya-doma-matrasy-i-osnovaniya": "home-garden-mebel-dlya-doma-matrasy",
    "home-garden-mebel-dlya-doma-sadovaya-mebel": "home-garden-mebel-dlya-doma-sadovaya-mebel",
    "home-garden-mebel-dlya-doma-drugaya-mebel": "home-garden-mebel-dlya-doma-drugaya-mebel",
    # Kids furniture → Kids L1 (canonical)
    "home-garden-mebel-dlya-doma-detskaya-mebel": "kids-detskaya-mebel",
    "home-garden-mebel-dlya-doma-detskaya-mebel-detskie-krovatki": "kids-detskaya-mebel",
    "home-garden-mebel-dlya-doma-detskaya-mebel-detskie-stoly-i-stulya": "kids-detskaya-mebel",
    "home-garden-mebel-dlya-doma-detskaya-mebel-detskie-shkafy": "kids-detskaya-mebel",
    "home-garden-mebel-dlya-doma-detskaya-mebel-detskie-komody": "kids-detskaya-mebel",
    "home-garden-mebel-dlya-doma-detskaya-mebel-party": "kids-detskaya-mebel",
    "home-garden-mebel-dlya-doma-detskaya-mebel-drugaya-detskaya-mebel": "kids-detskaya-mebel",
    "home-garden-mebel-dlya-doma-mebelnye-garnitury-detskie-garnitury": "kids-detskaya-mebel",
    # Carpets
    "home-garden-tekstil-i-kovry-kovry": "home-garden-tekstil-i-kovry-kovry",
    "home-garden-tekstil-i-kovry-kovrovye-dorozhki": "home-garden-tekstil-i-kovry-kovrovye-dorozhki",
    "home-garden-tekstil-i-kovry-kovriki": "home-garden-tekstil-i-kovry-kovriki",
    "home-garden-tekstil-i-kovry-kovrolin": "home-garden-tekstil-i-kovry-kovrolin",
    # Sleep — no mattress here
    "home-garden-postelnoe-bele-i-pledy-podushki": "home-garden-postelnoe-bele-i-pledy-podushki",
    "home-garden-postelnoe-bele-i-pledy-odeyala": "home-garden-postelnoe-bele-i-pledy-odeyala",
    "home-garden-postelnoe-bele-i-pledy-pledy": "home-garden-postelnoe-bele-i-pledy-pledy",
    "home-garden-postelnoe-bele-i-pledy-postelnoe-bele": "home-garden-postelnoe-bele-i-pledy-postelnoe-bele",
    "home-garden-postelnoe-bele-i-pledy-namatrasniki": "home-garden-postelnoe-bele-i-pledy-namatrasniki",
    "home-garden-postelnoe-bele-i-pledy-chehly-i-zaschita": "home-garden-postelnoe-bele-i-pledy-drugie-tovary-dlya-sna",
    # Curtains
    "home-garden-shtory-zhalyuzi-i-karnizy-shtory": "home-garden-shtory-zhalyuzi-i-karnizy-shtory",
    "home-garden-shtory-zhalyuzi-i-karnizy-tyul": "home-garden-shtory-zhalyuzi-i-karnizy-tyul",
    "home-garden-shtory-zhalyuzi-i-karnizy-zhalyuzi": "home-garden-shtory-zhalyuzi-i-karnizy-zhalyuzi",
    "home-garden-shtory-zhalyuzi-i-karnizy-rolshtory": "home-garden-shtory-zhalyuzi-i-karnizy-rulonnye-shtory",
    "home-garden-shtory-zhalyuzi-i-karnizy-rimskie-shtory": "home-garden-shtory-zhalyuzi-i-karnizy-rimskie-shtory",
    "home-garden-shtory-zhalyuzi-i-karnizy-karnizy": "home-garden-shtory-zhalyuzi-i-karnizy-karnizy",
    # Dacha duplicates → garden furniture
    "home-garden-besedki-navesy-i-tovary-dlya-dachi-shezlongi": "home-garden-mebel-dlya-doma-sadovaya-mebel-lezaki-i-shezlongi",
    "home-garden-besedki-navesy-i-tovary-dlya-dachi-skameyki-dlya-dachi": "home-garden-mebel-dlya-doma-sadovaya-mebel-sadovye-skameyki",
    # Irrigation tanks → containers L2 (generic leaf when subtype unknown)
    "home-garden-poliv-i-oroshenie-emkosti-dlya-poliva": "home-garden-emkosti-i-rezervuary-drugie-emkosti",
}


# Alias text → TARGET leaf slug (resolver / search).
HOME_GARDEN_FINAL_ALIAS_REMAP: dict[str, str] = {
    "кухонный гарнитур": "home-garden-mebel-dlya-doma-mebelnye-garnitury-kuhonnye-garnitury",
    "кухонные гарнитуры": "home-garden-mebel-dlya-doma-mebelnye-garnitury-kuhonnye-garnitury",
    "стол и стулья": "home-garden-mebel-dlya-doma-komplekty-mebeli-stol-i-stulya",
    "стол со стульями": "home-garden-mebel-dlya-doma-komplekty-mebeli-stol-i-stulya",
    "матрас": "home-garden-mebel-dlya-doma-matrasy",
    "матрасы": "home-garden-mebel-dlya-doma-matrasy",
    "диван": "home-garden-mebel-dlya-doma-divany",
    "кровать": "home-garden-mebel-dlya-doma-krovati",
    "шкаф": "home-garden-mebel-dlya-doma-shkafy",
    "сундук": "home-garden-mebel-dlya-doma-sunduki",
    "сейф": "home-garden-mebel-dlya-doma-seyfy",
    "бинбэг": "home-garden-mebel-dlya-doma-kresla",
    "бинбег": "home-garden-mebel-dlya-doma-kresla",
    "кресло-мешок": "home-garden-mebel-dlya-doma-kresla",
    "кресло мешок": "home-garden-mebel-dlya-doma-kresla",
    "bean bag": "home-garden-mebel-dlya-doma-kresla",
    "игровое кресло": "home-garden-mebel-dlya-doma-kresla",
    "постельное бельё": "home-garden-postelnoe-bele-i-pledy-postelnoe-bele",
    "постельное белье": "home-garden-postelnoe-bele-i-pledy-postelnoe-bele",
    "тошок": "home-garden-postelnoe-bele-i-pledy-toshoki",
    "тошоки": "home-garden-postelnoe-bele-i-pledy-toshoki",
    "төшөк": "home-garden-postelnoe-bele-i-pledy-toshoki",
    "төшөктөр": "home-garden-postelnoe-bele-i-pledy-toshoki",
    "шырдак": "home-garden-tekstil-i-kovry-shyrdaki",
    "шырдаки": "home-garden-tekstil-i-kovry-shyrdaki",
    "жайнамаз": "home-garden-tekstil-i-kovry-zhaynamazy",
    "жайнамазы": "home-garden-tekstil-i-kovry-zhaynamazy",
    "мантышница": "home-garden-posuda-kuhonnye-prinadlezhnosti-mantyshnitsy",
    "мантышницы": "home-garden-posuda-kuhonnye-prinadlezhnosti-mantyshnitsy",
    "манты казан": "home-garden-posuda-kuhonnye-prinadlezhnosti-mantyshnitsy",
    "манты-казан": "home-garden-posuda-kuhonnye-prinadlezhnosti-mantyshnitsy",
    "мантоварка": "home-garden-posuda-kuhonnye-prinadlezhnosti-mantyshnitsy",
    "газонокосилка": "home-garden-sadovaya-tehnika-gazonokosilki",
    "газонокосилка бензиновая": "home-garden-sadovaya-tehnika-gazonokosilki",
    "садовая качеля": "home-garden-sadovye-kacheli-i-gamaki-sadovye-kacheli",
    "садовые качели": "home-garden-sadovye-kacheli-i-gamaki-sadovye-kacheli",
    "гамак": "home-garden-sadovye-kacheli-i-gamaki-gamaki",
    "кресло кокон": "home-garden-sadovye-kacheli-i-gamaki-kacheli-kokony",
    "печь для бани": "home-garden-kaminy-pechi-i-aksessuary-pechi-dlya-bani-i-sauny",
    "банная печь": "home-garden-kaminy-pechi-i-aksessuary-pechi-dlya-bani-i-sauny",
    "веник для бани": "home-garden-tovary-dlya-bani-i-sauny-veniki",
    "веник": "home-garden-tovary-dlya-bani-i-sauny-veniki",
    "зеркало": "home-garden-zerkala-nastennye-zerkala",
    "ковёр": "home-garden-tekstil-i-kovry-kovry",
    "ковер": "home-garden-tekstil-i-kovry-kovry",
    "еврокуб": "home-garden-emkosti-i-rezervuary-evrokuby",
    "еврокубы": "home-garden-emkosti-i-rezervuary-evrokuby",
    "ibc": "home-garden-emkosti-i-rezervuary-evrokuby",
    "ibc контейнер": "home-garden-emkosti-i-rezervuary-evrokuby",
    "ibc-контейнер": "home-garden-emkosti-i-rezervuary-evrokuby",
    "кубовая ёмкость": "home-garden-emkosti-i-rezervuary-evrokuby",
    "кубовая емкость": "home-garden-emkosti-i-rezervuary-evrokuby",
    "бочка": "home-garden-emkosti-i-rezervuary-bochki",
    "бочки": "home-garden-emkosti-i-rezervuary-bochki",
    "дрова": "home-garden-drova-i-ugol-drova",
    "уголь": "home-garden-drova-i-ugol-ugol",
    "кара-кече": "home-garden-drova-i-ugol-ugol",
    "кара кече": "home-garden-drova-i-ugol-ugol",
    "шабыркуль": "home-garden-drova-i-ugol-ugol",
    "древесный уголь": "home-garden-drova-i-ugol-drevesnyy-ugol",
    "уголь для мангала": "home-garden-drova-i-ugol-drevesnyy-ugol",
    "газовый баллон": "home-garden-gazovye-ballony",
    "газовые баллоны": "home-garden-gazovye-ballony",
    "навоз": "home-garden-udobreniya-dlya-rasteniy-organicheskie-udobreniya",
    "перегной": "home-garden-udobreniya-dlya-rasteniy-organicheskie-udobreniya",
    "компост": "home-garden-udobreniya-dlya-rasteniy-organicheskie-udobreniya",
    "рулонный газон": "home-garden-sazhentsy-i-rassada-rulonnyy-i-gotovyy-gazon",
    "готовый газон": "home-garden-sazhentsy-i-rassada-rulonnyy-i-gotovyy-gazon",
    "садовый умывальник": "home-garden-besedki-navesy-i-tovary-dlya-dachi-dachnye-umyvalniki",
    "сетка от птиц": "home-garden-sredstva-zaschity-rasteniy-zaschitnye-setki",
    "сетка для защиты растений": "home-garden-sredstva-zaschity-rasteniy-zaschitnye-setki",
    "сетка для защиты урожая": "home-garden-sredstva-zaschity-rasteniy-zaschitnye-setki",
    "затеняющая сетка": "home-garden-teplitsy-i-parniki-zatenyayuschie-setki",
    "сетка для тени": "home-garden-teplitsy-i-parniki-zatenyayuschie-setki",
    "сетка для теплицы от солнца": "home-garden-teplitsy-i-parniki-zatenyayuschie-setki",
    "садовая фигура": "home-garden-dekor-i-interer-sadovye-figury",
    "садовые фигуры": "home-garden-dekor-i-interer-sadovye-figury",
    "садовый фонтан": "home-garden-dekor-i-interer-sadovye-fontany",
    "садовые фонтаны": "home-garden-dekor-i-interer-sadovye-fontany",
    "опрыскиватель": "home-garden-poliv-i-oroshenie-opryskivateli",
    "мотопомпа": "home-garden-poliv-i-oroshenie-motopompy",
    "ёлочные игрушки": "home-garden-tovary-dlya-prazdnikov-novogodnie-tovary-elochnye-igrushki-i-ukrasheniya",
    "воздушные шары": "home-garden-tovary-dlya-prazdnikov-vozdushnye-shary-i-aksessuary-vozdushnye-shary",
    "органайзер для косметики": "home-garden-hranenie-i-organizatsiya-organayzery",
}
