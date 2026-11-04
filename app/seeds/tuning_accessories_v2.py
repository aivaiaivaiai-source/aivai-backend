# -*- coding: utf-8 -*-
"""Transport → Аксессуары и тюнинг V2 — flat sections + product_type SoT.

Parent ``transport-accessories-tuning`` (683) is picker-only.
Concrete products live in Backend ``product_type`` options (stable value + RU label).
Optional vehicle Brand/Model via Vehicle Catalog where applicable.
No free-text item_type / product Brand / product Model.
"""
from __future__ import annotations

from typing import Any

from app.models.category_enums import CategoryFieldType, CategoryFilterType
from app.seeds.car_sale_v2 import CONTACT_METHOD_CHOICES, NEGOTIABLE_CHOICES

PARENT_SLUG = "transport-accessories-tuning"
PARENT_ID = 683
PARENT_LABEL = "Аксессуары и тюнинг"

# ---------------------------------------------------------------------------
# Final 13 publishable sections (flat L2)
# ---------------------------------------------------------------------------

INTERIOR_ID = 728
INTERIOR_SLUG = "transport-accessories-tuning-aksessuary-salona"
INTERIOR_LABEL = "Салон и комфорт"

MULTIMEDIA_ID = 1682
MULTIMEDIA_SLUG = "transport-accessories-tuning-multimedia"
MULTIMEDIA_LABEL = "Мультимедиа"

AUDIO_ID = 725
AUDIO_SLUG = "transport-accessories-tuning-avtozvuk"
AUDIO_LEGACY_SLUG = "transport-accessories-tuning-avtozvuk-i-multimediya"
AUDIO_LABEL = "Автозвук"

SECURITY_ID = 1207
SECURITY_SLUG = "transport-accessories-tuning-signalizatsii-i-protivougonnye"
SECURITY_LABEL = "Охрана и противоугонные системы"

DASHCAM_ID = 1206
DASHCAM_SLUG = "transport-accessories-tuning-videoregistratory-kamery-parktroniki"
DASHCAM_LABEL = "Видеорегистраторы, камеры и парктроники"

EXTERIOR_ID = 1208
EXTERIOR_SLUG = "transport-accessories-tuning-vneshnie-aksessuary-i-dekor"
EXTERIOR_LABEL = "Внешний тюнинг и аксессуары"

LIGHTING_ID = 1683
LIGHTING_SLUG = "transport-accessories-tuning-svet-i-dopolnitelnoe-osveschenie"
LIGHTING_LABEL = "Свет и дополнительное освещение"

CARGO_ID = 730
CARGO_SLUG = "transport-accessories-tuning-bagazhniki-i-perevozka"
CARGO_LABEL = "Багажные системы"

OFFROAD_ID = 731
OFFROAD_SLUG = "transport-accessories-tuning-vnedorozhnyy-tyuning"
OFFROAD_LABEL = "Внедорожный тюнинг и защита"

TECHNICAL_ID = 732
TECHNICAL_SLUG = "transport-accessories-tuning-tehnicheskiy-tyuning"
TECHNICAL_LEGACY_SLUG = "transport-accessories-tuning-sportivnyy-tyuning"
TECHNICAL_LABEL = "Технический тюнинг"

FILMS_ID = 1684
FILMS_SLUG = "transport-accessories-tuning-plenki-i-materialy"
FILMS_LABEL = "Плёнки и материалы для авто"

CARE_ID = 1209
CARE_SLUG = "transport-accessories-tuning-uhod-i-avtohimiya"
CARE_LABEL = "Уход, автохимия и полезные принадлежности"

OTHER_ID = 734
OTHER_SLUG = "transport-accessories-tuning-drugoe"
OTHER_LABEL = "Другие аксессуары"

# Inactive / hidden (history kept, no DELETE)
OPTICS_LEGACY_ID = 726
OPTICS_LEGACY_SLUG = "transport-accessories-tuning-avtosvet-i-tyuning-optiki"
ELECTRONICS_LEGACY_ID = 727
ELECTRONICS_LEGACY_SLUG = "transport-accessories-tuning-elektronika-i-bezopasnost"
BODY_LEGACY_ID = 729
BODY_LEGACY_SLUG = "transport-accessories-tuning-aksessuary-kuzova"
TOOLS_LEGACY_ID = 733
TOOLS_LEGACY_SLUG = "transport-accessories-tuning-instrumenty-i-avtoaksessuary"
BELONGINGS_RETIRE_ID = 1210
BELONGINGS_RETIRE_SLUG = "transport-accessories-tuning-avtomobilnye-prinadlezhnosti"
MOTO_HIDE_ID = 1211
MOTO_HIDE_SLUG = "transport-accessories-tuning-ekipirovka-moto-velo"
WATER_HIDE_ID = 1212
WATER_HIDE_SLUG = "transport-accessories-tuning-vodnye-prinadlezhnosti"

LEAF_SLUGS: tuple[str, ...] = (
    INTERIOR_SLUG,
    MULTIMEDIA_SLUG,
    AUDIO_SLUG,
    SECURITY_SLUG,
    DASHCAM_SLUG,
    EXTERIOR_SLUG,
    LIGHTING_SLUG,
    CARGO_SLUG,
    OFFROAD_SLUG,
    TECHNICAL_SLUG,
    FILMS_SLUG,
    CARE_SLUG,
    OTHER_SLUG,
)

LEAF_LABELS: dict[str, str] = {
    INTERIOR_SLUG: INTERIOR_LABEL,
    MULTIMEDIA_SLUG: MULTIMEDIA_LABEL,
    AUDIO_SLUG: AUDIO_LABEL,
    SECURITY_SLUG: SECURITY_LABEL,
    DASHCAM_SLUG: DASHCAM_LABEL,
    EXTERIOR_SLUG: EXTERIOR_LABEL,
    LIGHTING_SLUG: LIGHTING_LABEL,
    CARGO_SLUG: CARGO_LABEL,
    OFFROAD_SLUG: OFFROAD_LABEL,
    TECHNICAL_SLUG: TECHNICAL_LABEL,
    FILMS_SLUG: FILMS_LABEL,
    CARE_SLUG: CARE_LABEL,
    OTHER_SLUG: OTHER_LABEL,
}

LEAF_IDS: dict[str, int] = {
    INTERIOR_SLUG: INTERIOR_ID,
    MULTIMEDIA_SLUG: MULTIMEDIA_ID,
    AUDIO_SLUG: AUDIO_ID,
    SECURITY_SLUG: SECURITY_ID,
    DASHCAM_SLUG: DASHCAM_ID,
    EXTERIOR_SLUG: EXTERIOR_ID,
    LIGHTING_SLUG: LIGHTING_ID,
    CARGO_SLUG: CARGO_ID,
    OFFROAD_SLUG: OFFROAD_ID,
    TECHNICAL_SLUG: TECHNICAL_ID,
    FILMS_SLUG: FILMS_ID,
    CARE_SLUG: CARE_ID,
    OTHER_SLUG: OTHER_ID,
}

LEAF_SORT: dict[str, int] = {
    INTERIOR_SLUG: 10,
    MULTIMEDIA_SLUG: 20,
    AUDIO_SLUG: 30,
    SECURITY_SLUG: 40,
    DASHCAM_SLUG: 50,
    EXTERIOR_SLUG: 60,
    LIGHTING_SLUG: 70,
    CARGO_SLUG: 80,
    OFFROAD_SLUG: 90,
    TECHNICAL_SLUG: 100,
    FILMS_SLUG: 110,
    CARE_SLUG: 120,
    OTHER_SLUG: 130,
}

RETIRE_OR_HIDE_IDS: tuple[int, ...] = (
    OPTICS_LEGACY_ID,
    ELECTRONICS_LEGACY_ID,
    BODY_LEGACY_ID,
    TOOLS_LEGACY_ID,
    BELONGINGS_RETIRE_ID,
    MOTO_HIDE_ID,
    WATER_HIDE_ID,
)

CONDITION_CHOICES = ("Новое", "Б/у")
SELLER_TYPE_CHOICES = ("Частное лицо", "Магазин")

# ---------------------------------------------------------------------------
# product_type starter sets (stable → RU)
# ---------------------------------------------------------------------------

INTERIOR_TYPES: tuple[tuple[str, str], ...] = (
    ("floor_mats", "Коврики"),
    ("seat_covers", "Чехлы на сиденья"),
    ("seat_capes", "Накидки на сиденья"),
    ("seat_heater", "Подогрев сидений"),
    ("steering_wheel_cover", "Оплётка руля"),
    ("organizer", "Органайзер"),
    ("sun_shades", "Шторки / солнцезащитные экраны"),
    ("phone_holder", "Держатель телефона"),
    ("armrest_accessory", "Подлокотник аксессуар"),
    ("pedal_covers", "Накладки на педали"),
    ("interior_ambient_light", "Декоративная подсветка салона"),
    ("trunk_accessories", "Аксессуары багажника"),
    ("air_freshener", "Ароматизатор"),
    ("other", "Другое"),
)

MULTIMEDIA_TYPES: tuple[tuple[str, str], ...] = (
    ("head_unit", "Магнитола / головное устройство"),
    ("android_monitor", "Android-монитор"),
    ("carplay_adapter", "CarPlay / Android Auto адаптер"),
    ("car_monitor", "Автомобильный монитор"),
    ("fm_transmitter", "FM-трансмиттер"),
    ("usb_charger", "USB / зарядное устройство"),
    ("inverter", "Инвертор"),
    ("hud", "HUD"),
    ("other", "Другое"),
)

AUDIO_TYPES: tuple[tuple[str, str], ...] = (
    ("speakers", "Динамики"),
    ("subwoofer", "Сабвуфер"),
    ("amplifier", "Усилитель"),
    ("tweeter", "Твитер"),
    ("audio_processor", "Аудиопроцессор"),
    ("speaker_system", "Акустическая система"),
    ("audio_wiring_kit", "Комплект проводов для аудио"),
    ("other", "Другое"),
)

SECURITY_TYPES: tuple[tuple[str, str], ...] = (
    ("alarm", "Сигнализация"),
    ("immobilizer", "Иммобилайзер"),
    ("gps_tracker", "GPS-трекер"),
    ("remote_start", "Автозапуск"),
    ("anti_theft", "Противоугонное устройство"),
    ("central_lock_kit", "Комплект центрального замка"),
    ("other", "Другое"),
)

DASHCAM_TYPES: tuple[tuple[str, str], ...] = (
    ("dashcam", "Видеорегистратор"),
    ("rear_camera", "Камера заднего вида"),
    ("surround_camera_kit", "Камера кругового обзора / комплект"),
    ("parking_sensors", "Парктроник"),
    ("other", "Другое"),
)

EXTERIOR_TYPES: tuple[tuple[str, str], ...] = (
    ("body_kit", "Обвес"),
    ("spoiler", "Спойлер"),
    ("diffuser", "Диффузор"),
    ("bumper_lip", "Накладка на бампер"),
    ("fender_flares", "Расширители арок"),
    ("tuning_grille", "Тюнинг-решётка"),
    ("window_deflectors", "Дефлекторы окон / ветровики"),
    ("hood_deflector", "Дефлектор капота"),
    ("mirror_covers", "Накладки на зеркала"),
    ("moldings", "Молдинги"),
    ("door_sill_plates", "Накладки на пороги"),
    ("headlight_eyebrows", "Реснички"),
    ("license_plate_frame", "Рамка номера"),
    ("antenna", "Антенна"),
    ("other", "Другое"),
)

LIGHTING_TYPES: tuple[tuple[str, str], ...] = (
    ("led_bar", "LED-балка"),
    ("aux_light", "Дополнительная фара"),
    ("aux_fog_light", "Дополнительный противотуманный свет"),
    ("work_light", "Рабочий свет"),
    ("decorative_led", "Декоративная LED-подсветка"),
    ("underbody_light", "Подсветка днища"),
    ("tuning_light_kit", "Тюнинг-комплект света"),
    ("other", "Другое"),
)

CARGO_TYPES: tuple[tuple[str, str], ...] = (
    ("roof_rack", "Багажник на крышу"),
    ("crossbars", "Поперечины"),
    ("aftermarket_rails", "Рейлинги aftermarket"),
    ("roof_box", "Автобокс"),
    ("bike_carrier", "Крепление для велосипеда"),
    ("ski_carrier", "Крепление для лыж / сноуборда"),
    ("expedition_rack", "Экспедиционный багажник"),
    ("tow_hitch", "Фаркоп"),
    ("other", "Другое"),
)

OFFROAD_TYPES: tuple[tuple[str, str], ...] = (
    ("winch", "Лебёдка"),
    ("snorkel", "Шноркель"),
    ("steel_bumper", "Силовой бампер"),
    ("bull_bar", "Кенгурятник / защитная дуга"),
    ("rock_sliders", "Силовые пороги"),
    ("engine_skid_plate", "Защита двигателя / картера"),
    ("headlight_guards", "Защита фар"),
    ("recovery_gear", "Такелаж / recovery"),
    ("hi_lift_jack", "Хайджек"),
    ("other", "Другое"),
)

TECHNICAL_TYPES: tuple[tuple[str, str], ...] = (
    ("coilovers", "Койловеры"),
    ("lowering_springs", "Заниженные пружины"),
    ("lift_kit", "Лифт-комплект"),
    ("suspension_tuning_kit", "Тюнинг подвески / комплект"),
    ("sport_exhaust", "Спортивный выхлоп"),
    ("straight_pipe", "Прямоток"),
    ("exhaust_tip", "Насадка на выхлоп"),
    ("intake_kit", "Впуск / комплект впуска"),
    ("intercooler_upgrade", "Интеркулер (тюнинг)"),
    ("turbo_upgrade_kit", "Турбокит"),
    ("tuning_box", "Чип / tuning box"),
    ("performance_brake_kit", "Тюнинг тормозов"),
    ("gbo_kit", "Комплект ГБО"),
    ("other", "Другое"),
)

FILMS_TYPES: tuple[tuple[str, str], ...] = (
    ("tint_film", "Тонировочная плёнка"),
    ("vinyl_wrap", "Автовинил"),
    ("ppf", "PPF / защитная плёнка"),
    ("sound_deadening", "Шумоизоляционный материал"),
    ("vibration_damping", "Виброизоляционный материал"),
    ("soundproofing_kit", "Комплект шумоизоляции"),
    ("other_material", "Другой материал"),
)

CARE_PHYSICAL_TYPES: tuple[tuple[str, str], ...] = (
    ("microfiber", "Микрофибра"),
    ("brush_scraper", "Щётка / скребок"),
    ("car_compressor", "Автомобильный компрессор"),
    ("jumper_cables", "Провода прикуривания"),
    ("tow_rope", "Буксировочный трос"),
    ("warning_triangle", "Аварийный знак"),
    ("fire_extinguisher", "Огнетушитель"),
    ("first_aid_kit", "Аптечка"),
    ("jack", "Домкрат"),
    ("other", "Другое"),
)

CARE_CONSUMABLE_TYPES: tuple[tuple[str, str], ...] = (
    ("car_shampoo", "Автошампунь"),
    ("polish", "Полироль"),
    ("wax", "Воск"),
    ("cleaner", "Очиститель"),
    ("interior_cleaner", "Средство для салона"),
    ("anti_rain", "Антидождь"),
)

CARE_TYPES: tuple[tuple[str, str], ...] = CARE_CONSUMABLE_TYPES + CARE_PHYSICAL_TYPES

PRODUCT_TYPES_BY_SLUG: dict[str, tuple[tuple[str, str], ...]] = {
    INTERIOR_SLUG: INTERIOR_TYPES,
    MULTIMEDIA_SLUG: MULTIMEDIA_TYPES,
    AUDIO_SLUG: AUDIO_TYPES,
    SECURITY_SLUG: SECURITY_TYPES,
    DASHCAM_SLUG: DASHCAM_TYPES,
    EXTERIOR_SLUG: EXTERIOR_TYPES,
    LIGHTING_SLUG: LIGHTING_TYPES,
    CARGO_SLUG: CARGO_TYPES,
    OFFROAD_SLUG: OFFROAD_TYPES,
    TECHNICAL_SLUG: TECHNICAL_TYPES,
    FILMS_SLUG: FILMS_TYPES,
    CARE_SLUG: CARE_TYPES,
}

# product_type values that benefit from vehicle Brand/Model
COMPAT_BY_SLUG: dict[str, tuple[str, ...]] = {
    INTERIOR_SLUG: (
        "floor_mats",
        "seat_covers",
        "seat_capes",
        "armrest_accessory",
        "pedal_covers",
        "trunk_accessories",
        "steering_wheel_cover",
        "sun_shades",
    ),
    EXTERIOR_SLUG: (
        "body_kit",
        "spoiler",
        "diffuser",
        "bumper_lip",
        "fender_flares",
        "tuning_grille",
        "window_deflectors",
        "hood_deflector",
        "mirror_covers",
        "moldings",
        "door_sill_plates",
        "headlight_eyebrows",
    ),
    CARGO_SLUG: (
        "roof_rack",
        "crossbars",
        "aftermarket_rails",
        "roof_box",
        "bike_carrier",
        "ski_carrier",
        "expedition_rack",
        "tow_hitch",
    ),
    OFFROAD_SLUG: (
        "winch",
        "snorkel",
        "steel_bumper",
        "bull_bar",
        "rock_sliders",
        "engine_skid_plate",
        "headlight_guards",
    ),
    TECHNICAL_SLUG: (
        "coilovers",
        "lowering_springs",
        "lift_kit",
        "suspension_tuning_kit",
        "sport_exhaust",
        "straight_pipe",
        "intake_kit",
        "intercooler_upgrade",
        "turbo_upgrade_kit",
        "tuning_box",
        "performance_brake_kit",
        "gbo_kit",
    ),
    MULTIMEDIA_SLUG: ("head_unit", "android_monitor", "car_monitor"),
    LIGHTING_SLUG: ("tuning_light_kit",),
}

# Sections where condition is always required (all types reusable)
ALWAYS_CONDITION_SLUGS: frozenset[str] = frozenset(
    {
        INTERIOR_SLUG,
        MULTIMEDIA_SLUG,
        AUDIO_SLUG,
        SECURITY_SLUG,
        DASHCAM_SLUG,
        EXTERIOR_SLUG,
        LIGHTING_SLUG,
        CARGO_SLUG,
        OFFROAD_SLUG,
        TECHNICAL_SLUG,
    }
)

# Films: no condition. Care: condition only for physical types.
NO_CONDITION_SLUGS: frozenset[str] = frozenset({FILMS_SLUG, OTHER_SLUG})

CARE_CONDITION_TYPES: tuple[str, ...] = tuple(v for v, _ in CARE_PHYSICAL_TYPES)

# ---------------------------------------------------------------------------
# Aliases
# ---------------------------------------------------------------------------

LEAF_ALIASES: dict[str, str] = {
    # Interior
    "чехлы": INTERIOR_SLUG,
    "чехлы на сиденья": INTERIOR_SLUG,
    "авточехлы": INTERIOR_SLUG,
    "коврики для машины": INTERIOR_SLUG,
    "автоковрики": INTERIOR_SLUG,
    "автоковрик": INTERIOR_SLUG,
    "коврики в салон": INTERIOR_SLUG,
    "оплётка руля": INTERIOR_SLUG,
    "оплетка руля": INTERIOR_SLUG,
    # Multimedia / audio
    "магнитола": MULTIMEDIA_SLUG,
    "головное устройство": MULTIMEDIA_SLUG,
    "android монитор": MULTIMEDIA_SLUG,
    "автозвук": AUDIO_SLUG,
    "сабвуфер": AUDIO_SLUG,
    "динамики авто": AUDIO_SLUG,
    "усилитель автозвук": AUDIO_SLUG,
    # Security
    "сигнализация": SECURITY_SLUG,
    "продам сигнализацию": SECURITY_SLUG,
    "иммобилайзер": SECURITY_SLUG,
    "gps трекер": SECURITY_SLUG,
    # Dashcam
    "видеорегистратор": DASHCAM_SLUG,
    "регистратор": DASHCAM_SLUG,
    "камера заднего вида": DASHCAM_SLUG,
    "парктроник": DASHCAM_SLUG,
    # Exterior
    "спойлер": EXTERIOR_SLUG,
    "обвес": EXTERIOR_SLUG,
    "дефлекторы": EXTERIOR_SLUG,
    "ветровики": EXTERIOR_SLUG,
    # Lighting (aftermarket)
    "led балка": LIGHTING_SLUG,
    "led-балка": LIGHTING_SLUG,
    "ledbar": LIGHTING_SLUG,
    "дополнительный свет": LIGHTING_SLUG,
    "подсветка днища": LIGHTING_SLUG,
    "рабочий свет авто": LIGHTING_SLUG,
    # Cargo / hitch
    "фаркоп": CARGO_SLUG,
    "багажник на крышу": CARGO_SLUG,
    "автобокс": CARGO_SLUG,
    "поперечины": CARGO_SLUG,
    # Off-road
    "лебёдка": OFFROAD_SLUG,
    "лебедка": OFFROAD_SLUG,
    "шноркель": OFFROAD_SLUG,
    "кенгурятник": OFFROAD_SLUG,
    # Technical
    "прямоток": TECHNICAL_SLUG,
    "спортивный глушитель": TECHNICAL_SLUG,
    "койловеры": TECHNICAL_SLUG,
    "койловер": TECHNICAL_SLUG,
    "лифт комплект": TECHNICAL_SLUG,
    "lift kit": TECHNICAL_SLUG,
    "комплект гбо": TECHNICAL_SLUG,
    "гбо комплект": TECHNICAL_SLUG,
    "продам гбо комплект": TECHNICAL_SLUG,
    "чип бокс": TECHNICAL_SLUG,
    "тюнинг бокс": TECHNICAL_SLUG,
    # Films / materials
    "тонировочная пленка": FILMS_SLUG,
    "тонировочная плёнка": FILMS_SLUG,
    "пленка для тонировки": FILMS_SLUG,
    "автовинил": FILMS_SLUG,
    "ppf": FILMS_SLUG,
    "защитная пленка ppf": FILMS_SLUG,
    "шумоизоляционный материал": FILMS_SLUG,
    "материал шумоизоляции": FILMS_SLUG,
    # Care
    "автошампунь": CARE_SLUG,
    "автомобильный компрессор": CARE_SLUG,
    "провода прикуривания": CARE_SLUG,
}

PARENT_ALIASES: dict[str, str] = {
    "аксессуары для авто": PARENT_SLUG,
    "автоаксессуары": PARENT_SLUG,
    "тюнинг": PARENT_SLUG,
    "тюнинг авто": PARENT_SLUG,
}

SERVICE_BOUNDARY_ALIASES: dict[str, str] = {
    "установка сигнализации": "transport-auto-services-tyuning-i-doosnaschenie",
    "установка магнитолы": "transport-auto-services-tyuning-i-doosnaschenie",
    "установка фаркопа": "transport-auto-services-tyuning-i-doosnaschenie",
    "установка гбо": "transport-auto-services-gbo-gazoballonnoe-oborudovanie",
    "ремонт гбо": "transport-auto-services-gbo-gazoballonnoe-oborudovanie",
    "тонировка автомобиля": "transport-auto-services-tyuning-i-doosnaschenie",
    "тонировка авто": "transport-auto-services-tyuning-i-doosnaschenie",
    "шумоизоляция автомобиля": "transport-auto-services-tyuning-i-doosnaschenie",
    "ремонт глушителя": "transport-auto-services-remont-i-obsluzhivanie",
    "чип тюнинг": "transport-auto-services-tyuning-i-doosnaschenie",
    "установка обвеса": "transport-auto-services-tyuning-i-doosnaschenie",
}

# Parts boundary phrases (keep/strengthen OEM routing)
PARTS_BOUNDARY_ALIASES: dict[str, str] = {
    "фара": "transport-auto-parts-optika-fary-i-fonari",
    "штатная фара": "transport-auto-parts-optika-fary-i-fonari",
    "бампер": "transport-auto-parts-kuzovnye-detali",
    "глушитель": "transport-auto-parts-vyhlopnaya-sistema",
    "катализатор": "transport-auto-parts-vyhlopnaya-sistema",
    "амортизатор": "transport-auto-parts-hodovaya-i-podveska",
    "пружина подвески": "transport-auto-parts-hodovaya-i-podveska",
}

KIDS_BOUNDARY_ALIASES: dict[str, str] = {
    "детское автокресло": "kids-avtokresla-i-perenoski",
    "автокресло детское": "kids-avtokresla-i-perenoski",
    "бустер автокресло": "kids-avtokresla-i-perenoski",
}


# ---------------------------------------------------------------------------
# Field helpers
# ---------------------------------------------------------------------------


def _choices_labeled(pairs: tuple[tuple[str, str], ...]) -> dict[str, Any]:
    items = [{"value": v, "label": lab} for v, lab in pairs]
    return {"choices": items, "values": items}


def _choices(*labels: str) -> dict[str, Any]:
    items = [{"value": x, "label": x} for x in labels]
    return {"choices": items, "values": items}


def _depends(field: str, *values: str) -> dict[str, Any]:
    return {"depends_on": {"field": field, "values": list(values)}}


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


def _geo() -> list:
    return [
        _field("region", "Регион", CategoryFieldType.string, True, 0),
        _field("city", "Город", CategoryFieldType.city, True, 1),
    ]


def _commerce(sort: int = 200) -> list:
    return [
        _field("price", "Цена", CategoryFieldType.price, True, sort),
        _field(
            "negotiable",
            "Торг",
            CategoryFieldType.enum,
            False,
            sort + 5,
            _choices(*NEGOTIABLE_CHOICES),
        ),
        _field(
            "seller_type",
            "Кто продаёт",
            CategoryFieldType.enum,
            True,
            sort + 10,
            _choices(*SELLER_TYPE_CHOICES),
        ),
        _field(
            "contact_methods",
            "Способы связи",
            CategoryFieldType.enum,
            True,
            sort + 20,
            _choices(*CONTACT_METHOD_CHOICES),
        ),
    ]


def _product_type_field(
    types: tuple[tuple[str, str], ...],
    *,
    required: bool = True,
    sort: int = 20,
) -> tuple:
    return _field(
        "product_type",
        "Тип товара",
        CategoryFieldType.enum,
        required,
        sort,
        _choices_labeled(types),
        hint="Что именно продаёте?",
    )


def _vehicle_compat(
    *,
    product_types: tuple[str, ...] | None,
    sort: int = 40,
) -> list:
    brand_opts: dict[str, Any] | None = None
    model_opts: dict[str, Any] | None = None
    if product_types:
        brand_opts = _depends("product_type", *product_types)
        model_opts = _depends("product_type", *product_types)
    return [
        _field(
            "vehicle_brand",
            "Марка автомобиля",
            CategoryFieldType.brand,
            False,
            sort,
            brand_opts,
            hint="Для какого автомобиля?",
        ),
        _field(
            "vehicle_model",
            "Модель автомобиля",
            CategoryFieldType.model,
            False,
            sort + 5,
            model_opts,
            hint="Модель автомобиля",
        ),
    ]


def _condition_field(
    *,
    sort: int = 70,
    required: bool = True,
    depends_types: tuple[str, ...] | None = None,
) -> tuple:
    opts = _choices(*CONDITION_CHOICES)
    if depends_types:
        opts.update(_depends("product_type", *depends_types))
    return _field(
        "product_condition",
        "Состояние",
        CategoryFieldType.enum,
        required,
        sort,
        opts,
    )


def _schema_for(
    slug: str,
    *,
    with_product_type: bool = True,
    with_condition: bool = True,
    condition_depends: tuple[str, ...] | None = None,
) -> list:
    fields: list = [*_geo()]
    types = PRODUCT_TYPES_BY_SLUG.get(slug)
    if with_product_type and types:
        fields.append(_product_type_field(types, required=True))
    compat = COMPAT_BY_SLUG.get(slug)
    if compat:
        fields.extend(_vehicle_compat(product_types=compat, sort=40))
    if with_condition:
        fields.append(
            _condition_field(
                sort=70,
                required=True,
                depends_types=condition_depends,
            )
        )
    fields.extend(_commerce(200))
    return fields


def _other_schema() -> list:
    # Catch-all: no redundant product_type=Другое
    return [*_geo(), *_commerce(200)]


def _films_schema() -> list:
    return _schema_for(FILMS_SLUG, with_condition=False)


def _care_schema() -> list:
    return _schema_for(
        CARE_SLUG,
        with_condition=True,
        condition_depends=CARE_CONDITION_TYPES,
    )


TUNING_CORE_FIELDS_BY_SLUG: dict[str, list] = {
    INTERIOR_SLUG: _schema_for(INTERIOR_SLUG),
    MULTIMEDIA_SLUG: _schema_for(MULTIMEDIA_SLUG),
    AUDIO_SLUG: _schema_for(AUDIO_SLUG),
    SECURITY_SLUG: _schema_for(SECURITY_SLUG),
    DASHCAM_SLUG: _schema_for(DASHCAM_SLUG),
    EXTERIOR_SLUG: _schema_for(EXTERIOR_SLUG),
    LIGHTING_SLUG: _schema_for(LIGHTING_SLUG),
    CARGO_SLUG: _schema_for(CARGO_SLUG),
    OFFROAD_SLUG: _schema_for(OFFROAD_SLUG),
    TECHNICAL_SLUG: _schema_for(TECHNICAL_SLUG),
    FILMS_SLUG: _films_schema(),
    CARE_SLUG: _care_schema(),
    OTHER_SLUG: _other_schema(),
}


def _search_filters_for(
    slug: str,
    *,
    with_product_type: bool,
    with_condition: bool,
    with_compat: bool,
) -> list:
    filters: list = [
        _filt("region", "Регион", CategoryFilterType.text, 10, {}),
        _filt("city", "Город", CategoryFilterType.text, 20, {}),
    ]
    if with_product_type and slug in PRODUCT_TYPES_BY_SLUG:
        filters.append(
            _filt(
                "product_type",
                "Тип товара",
                CategoryFilterType.select,
                30,
                _choices_labeled(PRODUCT_TYPES_BY_SLUG[slug]),
            )
        )
    if with_compat and slug in COMPAT_BY_SLUG:
        filters.append(
            _filt(
                "vehicle_brand",
                "Марка автомобиля",
                CategoryFilterType.text,
                40,
                {},
            )
        )
        filters.append(
            _filt(
                "vehicle_model",
                "Модель автомобиля",
                CategoryFilterType.text,
                45,
                {},
            )
        )
    if with_condition:
        cfg = _choices(*CONDITION_CHOICES)
        if slug == CARE_SLUG:
            cfg.update(_depends("product_type", *CARE_CONDITION_TYPES))
        filters.append(
            _filt(
                "product_condition",
                "Состояние",
                CategoryFilterType.select,
                50,
                cfg,
            )
        )
    filters.extend(
        [
            _filt("price", "Цена", CategoryFilterType.range, 60, {}),
            _filt(
                "seller_type",
                "Кто продаёт",
                CategoryFilterType.select,
                70,
                _choices(*SELLER_TYPE_CHOICES),
            ),
            _filt(
                "sort",
                "Сортировка",
                CategoryFilterType.select,
                90,
                _choices(
                    "Сначала новые",
                    "Сначала дешевле",
                    "Сначала дороже",
                ),
            ),
        ]
    )
    return filters


TUNING_SEARCH_FILTERS_BY_SLUG: dict[str, list] = {
    INTERIOR_SLUG: _search_filters_for(
        INTERIOR_SLUG, with_product_type=True, with_condition=True, with_compat=True
    ),
    MULTIMEDIA_SLUG: _search_filters_for(
        MULTIMEDIA_SLUG, with_product_type=True, with_condition=True, with_compat=True
    ),
    AUDIO_SLUG: _search_filters_for(
        AUDIO_SLUG, with_product_type=True, with_condition=True, with_compat=False
    ),
    SECURITY_SLUG: _search_filters_for(
        SECURITY_SLUG, with_product_type=True, with_condition=True, with_compat=False
    ),
    DASHCAM_SLUG: _search_filters_for(
        DASHCAM_SLUG, with_product_type=True, with_condition=True, with_compat=False
    ),
    EXTERIOR_SLUG: _search_filters_for(
        EXTERIOR_SLUG, with_product_type=True, with_condition=True, with_compat=True
    ),
    LIGHTING_SLUG: _search_filters_for(
        LIGHTING_SLUG, with_product_type=True, with_condition=True, with_compat=True
    ),
    CARGO_SLUG: _search_filters_for(
        CARGO_SLUG, with_product_type=True, with_condition=True, with_compat=True
    ),
    OFFROAD_SLUG: _search_filters_for(
        OFFROAD_SLUG, with_product_type=True, with_condition=True, with_compat=True
    ),
    TECHNICAL_SLUG: _search_filters_for(
        TECHNICAL_SLUG, with_product_type=True, with_condition=True, with_compat=True
    ),
    FILMS_SLUG: _search_filters_for(
        FILMS_SLUG, with_product_type=True, with_condition=False, with_compat=False
    ),
    CARE_SLUG: _search_filters_for(
        CARE_SLUG, with_product_type=True, with_condition=True, with_compat=False
    ),
    OTHER_SLUG: _search_filters_for(
        OTHER_SLUG, with_product_type=False, with_condition=False, with_compat=False
    ),
}


def product_type_label(value: str) -> str:
    for pairs in PRODUCT_TYPES_BY_SLUG.values():
        for v, lab in pairs:
            if v == value:
                return lab
    return value


def all_product_type_labels() -> dict[str, str]:
    out: dict[str, str] = {}
    for pairs in PRODUCT_TYPES_BY_SLUG.values():
        for v, lab in pairs:
            out[v] = lab
    return out
