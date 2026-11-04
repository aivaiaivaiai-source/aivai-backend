# -*- coding: utf-8 -*-
"""Transport → Автоуслуги V2 — 10 sections + service_type SoT.

Parent ``transport-auto-services`` (685) is picker-only.
Concrete works live in Backend ``service_type`` (stable value + RU label).
Provider: ``provider_type`` private_master / service_center.
Price status: required ``service_price_type`` fixed / negotiable
(distinct from product ``negotiable`` — indicative vs final work cost).
Optional multi-select ``vehicle_class`` + optional ``with_visit``.
No product negotiable / condition / Brand / Model / service unit.
"""
from __future__ import annotations

from typing import Any

from app.models.category_enums import CategoryFieldType, CategoryFilterType
from app.seeds.car_sale_v2 import CONTACT_METHOD_CHOICES

PARENT_SLUG = "transport-auto-services"
PARENT_ID = 685
PARENT_LABEL = "Автоуслуги"

# ---------------------------------------------------------------------------
# Final 10 publishable sections (preserve IDs)
# ---------------------------------------------------------------------------

REPAIR_ID = 739
REPAIR_SLUG = "transport-auto-services-remont-i-obsluzhivanie"
REPAIR_LABEL = "Ремонт и обслуживание"

ELECTRICS_ID = 740
ELECTRICS_SLUG = "transport-auto-services-avtoelektrika"
ELECTRICS_LABEL = "Автоэлектрика и диагностика"

BODY_ID = 741
BODY_SLUG = "transport-auto-services-kuzovnoy-remont"
BODY_LABEL = "Кузовной ремонт и покраска"

DETAILING_ID = 742
DETAILING_SLUG = "transport-auto-services-deteyling-i-uhod"
DETAILING_LABEL = "Мойка, химчистка и детейлинг"

TIRES_SVC_ID = 743
TIRES_SVC_SLUG = "transport-auto-services-shinomontazh"
TIRES_SVC_LABEL = "Шиномонтаж и ремонт колёс"

TOWING_ID = 744
TOWING_SLUG = "transport-auto-services-evakuatsiya-i-pomosch-na-doroge"
TOWING_LABEL = "Эвакуация и помощь на дороге"

TUNING_SVC_ID = 745
TUNING_SVC_SLUG = "transport-auto-services-tyuning-i-doosnaschenie"
TUNING_SVC_LABEL = "Тюнинг и дооснащение"

GLASS_ID = 746
GLASS_SLUG = "transport-auto-services-avtostekla"
GLASS_LABEL = "Автостекла"

INSPECTION_ID = 748
INSPECTION_SLUG = "transport-auto-services-proverka-i-oformlenie"
INSPECTION_LABEL = "Автоподбор, проверка и оформление"

GBO_ID = 747
GBO_SLUG = "transport-auto-services-gbo-gazoballonnoe-oborudovanie"
GBO_LABEL = "ГБО"

# Preferred UX order: Inspection before GBO
LEAF_ORDER: tuple[tuple[int, str, str, int], ...] = (
    (REPAIR_ID, REPAIR_SLUG, REPAIR_LABEL, 10),
    (ELECTRICS_ID, ELECTRICS_SLUG, ELECTRICS_LABEL, 20),
    (BODY_ID, BODY_SLUG, BODY_LABEL, 30),
    (DETAILING_ID, DETAILING_SLUG, DETAILING_LABEL, 40),
    (TIRES_SVC_ID, TIRES_SVC_SLUG, TIRES_SVC_LABEL, 50),
    (TOWING_ID, TOWING_SLUG, TOWING_LABEL, 60),
    (TUNING_SVC_ID, TUNING_SVC_SLUG, TUNING_SVC_LABEL, 70),
    (GLASS_ID, GLASS_SLUG, GLASS_LABEL, 80),
    (INSPECTION_ID, INSPECTION_SLUG, INSPECTION_LABEL, 90),
    (GBO_ID, GBO_SLUG, GBO_LABEL, 100),
)

LEAF_SLUGS: tuple[str, ...] = tuple(s for _, s, _, _ in LEAF_ORDER)
LEAF_IDS: dict[str, int] = {s: i for i, s, _, _ in LEAF_ORDER}
LEAF_LABELS: dict[str, str] = {s: lab for _, s, lab, _ in LEAF_ORDER}
LEAF_SORT: dict[str, int] = {s: sort for _, s, _, sort in LEAF_ORDER}

# ---------------------------------------------------------------------------
# service_type options (stable, RU)
# ---------------------------------------------------------------------------

REPAIR_TYPES: tuple[tuple[str, str], ...] = (
    ("engine_repair", "Ремонт двигателя"),
    ("gearbox_repair", "Ремонт КПП"),
    ("clutch_replacement", "Замена сцепления"),
    ("suspension_repair", "Ремонт ходовой"),
    ("wheel_alignment", "Развал-схождение"),
    ("brake_system_repair", "Ремонт тормозной системы"),
    ("steering_repair", "Ремонт рулевого управления"),
    ("cooling_system_repair", "Ремонт системы охлаждения"),
    ("radiator_repair", "Ремонт радиатора"),
    ("fuel_system_repair", "Ремонт топливной системы"),
    ("injector_cleaning", "Промывка форсунок"),
    ("turbo_repair", "Ремонт турбины"),
    ("exhaust_system_repair", "Ремонт выхлопной системы"),
    ("oil_change", "Замена масла"),
    ("filter_change", "Замена фильтров"),
    ("belt_chain_replacement", "Замена ремня / цепи"),
    ("timing_belt_replacement", "Замена ГРМ"),
    ("maintenance", "Техническое обслуживание"),
    ("ac_repair", "Ремонт кондиционера"),
    ("ac_refill", "Заправка кондиционера"),
    ("other", "Другое"),
)

ELECTRICS_TYPES: tuple[tuple[str, str], ...] = (
    ("auto_electrician", "Автоэлектрик"),
    ("computer_diagnostics", "Компьютерная диагностика"),
    ("electrical_diagnostics", "Диагностика электрики"),
    ("starter_repair", "Ремонт стартера"),
    ("alternator_repair", "Ремонт генератора"),
    ("wiring_repair", "Ремонт проводки"),
    ("sensor_diagnostics", "Диагностика датчиков"),
    ("ecu_electronics_repair", "Ремонт электронных блоков"),
    ("car_key_making", "Изготовление автоключей"),
    ("car_key_programming", "Программирование автоключей"),
    ("other", "Другое"),
)

BODY_TYPES: tuple[tuple[str, str], ...] = (
    ("body_straightening", "Рихтовка"),
    ("car_painting", "Покраска автомобиля"),
    ("local_painting", "Локальная покраска"),
    ("body_welding", "Сварка кузова"),
    ("bumper_repair", "Ремонт бамперов"),
    ("dent_removal", "Удаление вмятин"),
    ("pdr", "PDR / удаление вмятин без покраски"),
    ("body_restoration", "Восстановление кузова"),
    ("other", "Другое"),
)

DETAILING_TYPES: tuple[tuple[str, str], ...] = (
    ("car_wash", "Автомойка"),
    ("interior_dry_cleaning", "Химчистка салона"),
    ("body_polishing", "Полировка кузова"),
    ("ceramic_coating", "Керамическое покрытие"),
    ("protective_coating", "Защитное покрытие"),
    ("headlight_polishing", "Полировка фар"),
    ("interior_detailing", "Детейлинг салона"),
    ("exterior_detailing", "Детейлинг кузова"),
    ("other", "Другое"),
)

TIRES_SVC_TYPES: tuple[tuple[str, str], ...] = (
    ("tire_fitting", "Шиномонтаж"),
    ("wheel_balancing", "Балансировка"),
    ("tire_repair", "Ремонт шин"),
    ("vulcanization", "Вулканизация"),
    ("seasonal_tire_change", "Сезонная переобувка"),
    ("rim_straightening", "Правка дисков"),
    ("rim_repair", "Ремонт дисков"),
    ("other", "Другое"),
)

TOWING_TYPES: tuple[tuple[str, str], ...] = (
    ("towing", "Эвакуатор"),
    ("tow_assist", "Буксировка"),
    ("jump_start", "Прикурить автомобиль"),
    ("roadside_tire_change", "Замена колеса на дороге"),
    ("fuel_delivery", "Подвоз топлива"),
    ("car_unlock", "Вскрытие автомобиля"),
    ("mobile_mechanic", "Выездной мастер"),
    ("other", "Другое"),
)

TUNING_SVC_TYPES: tuple[tuple[str, str], ...] = (
    ("alarm_installation", "Установка сигнализации"),
    ("head_unit_installation", "Установка магнитолы / мультимедиа"),
    ("camera_installation", "Установка камеры"),
    ("parktronic_installation", "Установка парктроника"),
    ("tow_hitch_installation", "Установка фаркопа"),
    ("extra_light_installation", "Установка дополнительного света"),
    ("car_tinting", "Тонировка автомобиля"),
    ("vinyl_ppf_wrapping", "Оклейка плёнкой / винилом / PPF"),
    ("soundproofing_work", "Шумоизоляция автомобиля"),
    ("body_kit_installation", "Установка обвеса"),
    ("chip_tuning", "Чип-тюнинг"),
    ("exhaust_tuning", "Тюнинг выхлопа"),
    ("suspension_tuning", "Тюнинг подвески"),
    ("other", "Другое"),
)

GLASS_TYPES: tuple[tuple[str, str], ...] = (
    ("windshield_replacement", "Замена лобового стекла"),
    ("side_glass_replacement", "Замена бокового стекла"),
    ("rear_glass_replacement", "Замена заднего стекла"),
    ("chip_repair", "Ремонт сколов"),
    ("crack_repair", "Ремонт трещин"),
    ("auto_glass_installation", "Установка автостекла"),
    ("other", "Другое"),
)

INSPECTION_TYPES: tuple[tuple[str, str], ...] = (
    ("pre_purchase_inspection", "Проверка авто перед покупкой"),
    ("car_selection", "Автоподбор"),
    ("onsite_pre_purchase_diagnostics", "Выездная диагностика перед покупкой"),
    ("document_check", "Проверка документов"),
    ("registration_help", "Помощь при оформлении"),
    ("reregistration_help", "Помощь при переоформлении"),
    ("other", "Другое"),
)

GBO_TYPES: tuple[tuple[str, str], ...] = (
    ("gbo_installation", "Установка ГБО"),
    ("gbo_tuning", "Настройка ГБО"),
    ("gbo_diagnostics", "Диагностика ГБО"),
    ("gbo_repair", "Ремонт ГБО"),
    ("gbo_maintenance", "Обслуживание ГБО"),
    ("other", "Другое"),
)

SERVICE_TYPES_BY_SLUG: dict[str, tuple[tuple[str, str], ...]] = {
    REPAIR_SLUG: REPAIR_TYPES,
    ELECTRICS_SLUG: ELECTRICS_TYPES,
    BODY_SLUG: BODY_TYPES,
    DETAILING_SLUG: DETAILING_TYPES,
    TIRES_SVC_SLUG: TIRES_SVC_TYPES,
    TOWING_SLUG: TOWING_TYPES,
    TUNING_SVC_SLUG: TUNING_SVC_TYPES,
    GLASS_SLUG: GLASS_TYPES,
    INSPECTION_SLUG: INSPECTION_TYPES,
    GBO_SLUG: GBO_TYPES,
}

PROVIDER_TYPE_CHOICES: tuple[tuple[str, str], ...] = (
    ("private_master", "Частный мастер"),
    ("service_center", "Автосервис"),
)

# Create picker labels (short). Card uses longer phrases via Flutter mapper.
SERVICE_PRICE_TYPE_CHOICES: tuple[tuple[str, str], ...] = (
    ("fixed", "Фиксированная"),
    ("negotiable", "Договорная"),
)

# Reuse Transport/Parts canonical stables; RU labels per Auto Services V2.
VEHICLE_CLASS_CHOICES: tuple[tuple[str, str], ...] = (
    ("passenger_cars", "Легковые"),
    ("cargo", "Грузовые"),
    ("buses", "Автобусы"),
    ("moto", "Мото"),
    ("special_equipment", "Спецтехника"),
    ("farm_machinery", "Сельхозтехника"),
)

WITH_VISIT_CHOICES: tuple[tuple[str, str], ...] = (
    ("yes", "Да"),
    ("no", "Нет"),
)

# ---------------------------------------------------------------------------
# Aliases
# ---------------------------------------------------------------------------

PARENT_ALIASES: dict[str, str] = {
    "автоуслуги": PARENT_SLUG,
    "автосервис услуги": PARENT_SLUG,
    "услуги для авто": PARENT_SLUG,
}

LEAF_ALIASES: dict[str, str] = {
    # Repair
    "ремонт двигателя": REPAIR_SLUG,
    "ремонт кпп": REPAIR_SLUG,
    "ремонт коробки": REPAIR_SLUG,
    "ремонт ходовой": REPAIR_SLUG,
    "ремонт тормозов": REPAIR_SLUG,
    "замена масла": REPAIR_SLUG,
    "техническое обслуживание": REPAIR_SLUG,
    "ремонт глушителя": REPAIR_SLUG,
    "заправка кондиционера авто": REPAIR_SLUG,
    "заправка автокондиционера": REPAIR_SLUG,
    "ремонт автокондиционера": REPAIR_SLUG,
    "ремонт турбины": REPAIR_SLUG,
    "ремонт турбин": REPAIR_SLUG,
    # Electrics
    "автоэлектрик": ELECTRICS_SLUG,
    "компьютерная диагностика": ELECTRICS_SLUG,
    "диагностика электрики": ELECTRICS_SLUG,
    "ремонт генератора": ELECTRICS_SLUG,
    "ремонт стартера": ELECTRICS_SLUG,
    "ремонт проводки": ELECTRICS_SLUG,
    "программирование автоключа": ELECTRICS_SLUG,
    "изготовление автоключа": ELECTRICS_SLUG,
    "ремонт ключа автомобиля": ELECTRICS_SLUG,
    # Body
    "покраска авто": BODY_SLUG,
    "покраска автомобиля": BODY_SLUG,
    "рихтовка": BODY_SLUG,
    "pdr": BODY_SLUG,
    "удаление вмятин": BODY_SLUG,
    "сварка кузова": BODY_SLUG,
    # Detailing
    "автомойка": DETAILING_SLUG,
    "химчистка салона": DETAILING_SLUG,
    "химчистка салона автомобиля": DETAILING_SLUG,
    "полировка авто": DETAILING_SLUG,
    "детейлинг": DETAILING_SLUG,
    # Tires service
    "шиномонтаж": TIRES_SVC_SLUG,
    "развал": REPAIR_SLUG,
    "развал-схождение": REPAIR_SLUG,
    "сход-развал": REPAIR_SLUG,
    "балансировка колёс": TIRES_SVC_SLUG,
    "балансировка колес": TIRES_SVC_SLUG,
    "вулканизация": TIRES_SVC_SLUG,
    "ремонт шин": TIRES_SVC_SLUG,
    "сезонная переобувка": TIRES_SVC_SLUG,
    # Towing / road
    "эвакуатор": TOWING_SLUG,
    "эвакуация": TOWING_SLUG,
    "эвакуация автомобиля": TOWING_SLUG,
    "нужен эвакуатор": TOWING_SLUG,
    "вызвать эвакуатор": TOWING_SLUG,
    "услуги эвакуатора": TOWING_SLUG,
    "буксировка": TOWING_SLUG,
    "прикурить машину": TOWING_SLUG,
    "прикурить автомобиль": TOWING_SLUG,
    "подвоз топлива": TOWING_SLUG,
    "замена колеса на дороге": TOWING_SLUG,
    "вскрытие автомобиля": TOWING_SLUG,
    "выездной мастер": TOWING_SLUG,
    # Tuning install
    "установка сигнализации": TUNING_SVC_SLUG,
    "установка магнитолы": TUNING_SVC_SLUG,
    "установка камеры": TUNING_SVC_SLUG,
    "установка парктроника": TUNING_SVC_SLUG,
    "установка фаркопа": TUNING_SVC_SLUG,
    "установка дополнительного света": TUNING_SVC_SLUG,
    "установка обвеса": TUNING_SVC_SLUG,
    "чип тюнинг": TUNING_SVC_SLUG,
    "чип-тюнинг": TUNING_SVC_SLUG,
    "тонировка авто": TUNING_SVC_SLUG,
    "тонировка автомобиля": TUNING_SVC_SLUG,
    "шумоизоляция автомобиля": TUNING_SVC_SLUG,
    # Glass
    "замена лобового стекла": GLASS_SLUG,
    "ремонт скола стекла": GLASS_SLUG,
    "ремонт трещины стекла": GLASS_SLUG,
    "установка автостекла": GLASS_SLUG,
    "ремонт стекла": GLASS_SLUG,
    # Inspection
    "автоподбор": INSPECTION_SLUG,
    "проверка авто перед покупкой": INSPECTION_SLUG,
    "выездная диагностика перед покупкой": INSPECTION_SLUG,
    "проверка документов автомобиля": INSPECTION_SLUG,
    # GBO
    "установка гбо": GBO_SLUG,
    "ремонт гбо": GBO_SLUG,
    "настройка гбо": GBO_SLUG,
    "диагностика гбо": GBO_SLUG,
    "обслуживание гбо": GBO_SLUG,
}

# Sale evacuator stays Cargo (do not steal).
CARGO_EVACUATOR_ALIASES: dict[str, str] = {
    "продам эвакуатор": "transport-cargo-evakuatory",
    "продажа эвакуатора": "transport-cargo-evakuatory",
    "эвакуатор продам": "transport-cargo-evakuatory",
    "эвакуатор продаётся": "transport-cargo-evakuatory",
}

# ---------------------------------------------------------------------------
# Field / filter helpers
# ---------------------------------------------------------------------------


def _choices_labeled(pairs: tuple[tuple[str, str], ...]) -> dict[str, Any]:
    items = [{"value": v, "label": lab} for v, lab in pairs]
    return {"choices": items, "values": items}


def _choices(*labels: str) -> dict[str, Any]:
    items = [{"value": x, "label": x} for x in labels]
    return {"choices": items, "values": items}


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


def _common_service_fields(slug: str) -> list:
    types = SERVICE_TYPES_BY_SLUG[slug]
    return [
        *_geo(),
        _field(
            "service_type",
            "Вид услуги",
            CategoryFieldType.enum,
            True,
            20,
            _choices_labeled(types),
            hint="Какую услугу оказываете?",
        ),
        _field(
            "vehicle_class",
            "Работаю с транспортом",
            CategoryFieldType.multi_select,
            False,
            40,
            _choices_labeled(VEHICLE_CLASS_CHOICES),
        ),
        _field(
            "with_visit",
            "С выездом",
            CategoryFieldType.enum,
            False,
            50,
            _choices_labeled(WITH_VISIT_CHOICES),
        ),
        _field("price", "Цена", CategoryFieldType.price, True, 200),
        _field(
            "service_price_type",
            "Условия цены",
            CategoryFieldType.enum,
            True,
            205,
            _choices_labeled(SERVICE_PRICE_TYPE_CHOICES),
            hint="Фиксированная сумма или договорная (ориентир)",
        ),
        _field(
            "provider_type",
            "Кто оказывает услугу",
            CategoryFieldType.enum,
            True,
            210,
            _choices_labeled(PROVIDER_TYPE_CHOICES),
        ),
        _field(
            "contact_methods",
            "Способы связи",
            CategoryFieldType.enum,
            True,
            220,
            _choices(*CONTACT_METHOD_CHOICES),
        ),
    ]


def _search_filters(slug: str) -> list:
    types = SERVICE_TYPES_BY_SLUG[slug]
    return [
        _filt("region", "Регион", CategoryFilterType.text, 10, {}),
        _filt("city", "Город", CategoryFilterType.text, 20, {}),
        _filt(
            "service_type",
            "Вид услуги",
            CategoryFilterType.select,
            30,
            _choices_labeled(types),
        ),
        _filt(
            "provider_type",
            "Кто оказывает услугу",
            CategoryFilterType.select,
            40,
            _choices_labeled(PROVIDER_TYPE_CHOICES),
        ),
        _filt(
            "vehicle_class",
            "Работаю с транспортом",
            CategoryFilterType.multi_select,
            50,
            _choices_labeled(VEHICLE_CLASS_CHOICES),
        ),
        _filt(
            "with_visit",
            "С выездом",
            CategoryFilterType.select,
            60,
            _choices_labeled(WITH_VISIT_CHOICES),
        ),
        _filt("price", "Цена", CategoryFilterType.range, 70, {}),
        _filt(
            "service_price_type",
            "Условия цены",
            CategoryFilterType.select,
            75,
            _choices_labeled(SERVICE_PRICE_TYPE_CHOICES),
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


AUTO_SERVICES_CORE_FIELDS_BY_SLUG: dict[str, list] = {
    slug: _common_service_fields(slug) for slug in LEAF_SLUGS
}

AUTO_SERVICES_SEARCH_FILTERS_BY_SLUG: dict[str, list] = {
    slug: _search_filters(slug) for slug in LEAF_SLUGS
}


def service_type_label(value: str) -> str:
    for pairs in SERVICE_TYPES_BY_SLUG.values():
        for v, lab in pairs:
            if v == value:
                return lab
    return value


def provider_type_label(value: str) -> str:
    for v, lab in PROVIDER_TYPE_CHOICES:
        if v == value:
            return lab
    return value


def service_price_type_label(value: str) -> str:
    """Create/Detail short label (Фиксированная / Договорная)."""
    for v, lab in SERVICE_PRICE_TYPE_CHOICES:
        if v == value:
            return lab
    return value


def service_price_type_card_label(value: str) -> str:
    """Compact Card Line 3 — self-explanatory without field label."""
    if value == "fixed":
        return "Фиксированная цена"
    if value == "negotiable":
        return "Цена договорная"
    return ""


def vehicle_class_label(value: str) -> str:
    for v, lab in VEHICLE_CLASS_CHOICES:
        if v == value:
            return lab
    return value


def with_visit_label(value: str) -> str:
    for v, lab in WITH_VISIT_CHOICES:
        if v == value:
            return lab
    return value


def all_service_type_labels() -> dict[str, str]:
    out: dict[str, str] = {}
    for pairs in SERVICE_TYPES_BY_SLUG.values():
        for v, lab in pairs:
            out[v] = lab
    return out


def service_type_counts() -> dict[str, int]:
    return {slug: len(pairs) for slug, pairs in SERVICE_TYPES_BY_SLUG.items()}
