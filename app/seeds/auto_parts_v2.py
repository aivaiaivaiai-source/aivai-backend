# -*- coding: utf-8 -*-
"""Transport → Автозапчасти V2 — leaf Create/Search SoT.

Parent ``transport-auto-parts`` (682) is picker-only.
Part identity = system leaf + structured ``part_name`` (not deep L3/L4).
Vehicle compatibility keys: ``vehicle_brand`` / ``vehicle_model`` (optional).

Free-text manufacturer / OEM are NOT live characteristics — sellers put
Bosch / Denso / OEM numbers in Description when needed.
Legacy keys ``part_manufacturer``, ``part_number``, ``oem_number`` stay
retired from Create/Search schemas.
"""
from __future__ import annotations

from typing import Any

from app.models.category_enums import CategoryFieldType, CategoryFilterType
from app.seeds.car_sale_v2 import CONTACT_METHOD_CHOICES, NEGOTIABLE_CHOICES

PARTS_PARENT_SLUG = "transport-auto-parts"
PARTS_PARENT_ID = 682
BODY_LEAF_ID = 702
BODY_LEAF_SLUG = "transport-auto-parts-kuzovnye-detali"
BODY_LEAF_LABEL = "Кузов"
OPTICS_LEAF_ID = 709
UNIVERSAL_INACTIVE_ID = 723
UNIVERSAL_INACTIVE_SLUG = "transport-auto-parts-universalnye-detali"

# ---------------------------------------------------------------------------
# Taxonomy
# ---------------------------------------------------------------------------

PASSENGER_SYSTEM_SLUGS: tuple[str, ...] = (
    "transport-auto-parts-dvigatel-i-navesnoe",
    "transport-auto-parts-korobka-peredach-i-transmissiya",
    "transport-auto-parts-hodovaya-i-podveska",
    "transport-auto-parts-rulevoe-upravlenie",
    "transport-auto-parts-tormoznaya-sistema",
    BODY_LEAF_SLUG,
    "transport-auto-parts-optika-fary-i-fonari",
    "transport-auto-parts-salon-i-interer",
    "transport-auto-parts-elektrika-i-elektronika",
    "transport-auto-parts-klimat-pechka-i-konditsioner",
    "transport-auto-parts-sistema-ohlazhdeniya",
    "transport-auto-parts-toplivnaya-sistema",
    "transport-auto-parts-vyhlopnaya-sistema",
    "transport-auto-parts-podshipniki",
    "transport-auto-parts-krepezh-rezinki-i-melkie-detali",
    "transport-auto-parts-masla-zhidkosti-i-rashodniki",
    "transport-auto-parts-drugoe",
)

PASSENGER_SYSTEM_LABELS: dict[str, str] = {
    "transport-auto-parts-dvigatel-i-navesnoe": "Двигатель и навесное",
    "transport-auto-parts-korobka-peredach-i-transmissiya": (
        "Коробка передач и трансмиссия"
    ),
    "transport-auto-parts-hodovaya-i-podveska": "Ходовая и подвеска",
    "transport-auto-parts-rulevoe-upravlenie": "Рулевое управление",
    "transport-auto-parts-tormoznaya-sistema": "Тормозная система",
    BODY_LEAF_SLUG: BODY_LEAF_LABEL,
    "transport-auto-parts-optika-fary-i-fonari": "Оптика, фары и фонари",
    "transport-auto-parts-salon-i-interer": "Салон и интерьер",
    "transport-auto-parts-elektrika-i-elektronika": "Электрика и электроника",
    "transport-auto-parts-klimat-pechka-i-konditsioner": (
        "Климат, печка и кондиционер"
    ),
    "transport-auto-parts-sistema-ohlazhdeniya": "Система охлаждения",
    "transport-auto-parts-toplivnaya-sistema": "Топливная система",
    "transport-auto-parts-vyhlopnaya-sistema": "Выхлопная система",
    "transport-auto-parts-podshipniki": "Подшипники",
    "transport-auto-parts-krepezh-rezinki-i-melkie-detali": (
        "Крепёж и мелкие детали"
    ),
    "transport-auto-parts-masla-zhidkosti-i-rashodniki": (
        "Масла, жидкости и расходники"
    ),
    "transport-auto-parts-drugoe": "Другое",
}

PASSENGER_SYSTEM_SORT: dict[str, int] = {
    "transport-auto-parts-dvigatel-i-navesnoe": 10,
    "transport-auto-parts-korobka-peredach-i-transmissiya": 20,
    "transport-auto-parts-hodovaya-i-podveska": 30,
    "transport-auto-parts-rulevoe-upravlenie": 40,
    "transport-auto-parts-tormoznaya-sistema": 50,
    BODY_LEAF_SLUG: 60,
    "transport-auto-parts-optika-fary-i-fonari": 70,
    "transport-auto-parts-salon-i-interer": 80,
    "transport-auto-parts-elektrika-i-elektronika": 90,
    "transport-auto-parts-klimat-pechka-i-konditsioner": 100,
    "transport-auto-parts-sistema-ohlazhdeniya": 110,
    "transport-auto-parts-toplivnaya-sistema": 120,
    "transport-auto-parts-vyhlopnaya-sistema": 130,
    "transport-auto-parts-podshipniki": 140,
    "transport-auto-parts-krepezh-rezinki-i-melkie-detali": 150,
    "transport-auto-parts-masla-zhidkosti-i-rashodniki": 160,
    "transport-auto-parts-drugoe": 170,
}

PASSENGER_SYSTEM_EXPECTED_IDS: dict[str, int] = {
    "transport-auto-parts-dvigatel-i-navesnoe": 697,
    "transport-auto-parts-korobka-peredach-i-transmissiya": 698,
    "transport-auto-parts-hodovaya-i-podveska": 699,
    "transport-auto-parts-rulevoe-upravlenie": 700,
    "transport-auto-parts-tormoznaya-sistema": 701,
    BODY_LEAF_SLUG: BODY_LEAF_ID,
    "transport-auto-parts-optika-fary-i-fonari": OPTICS_LEAF_ID,
    "transport-auto-parts-salon-i-interer": 714,
    "transport-auto-parts-elektrika-i-elektronika": 715,
    "transport-auto-parts-klimat-pechka-i-konditsioner": 716,
    "transport-auto-parts-sistema-ohlazhdeniya": 717,
    "transport-auto-parts-toplivnaya-sistema": 718,
    "transport-auto-parts-vyhlopnaya-sistema": 719,
    "transport-auto-parts-podshipniki": 720,
    "transport-auto-parts-krepezh-rezinki-i-melkie-detali": 721,
    "transport-auto-parts-masla-zhidkosti-i-rashodniki": 722,
    "transport-auto-parts-drugoe": 724,
}

# Body siblings retired into 702 (IDs preserved, inactive).
BODY_RETIRED: tuple[tuple[int, str, str], ...] = (
    (703, "transport-auto-parts-kabina-perednyaya-chast-nouskat", "Кабина / Нооскат"),
    (704, "transport-auto-parts-bampery-i-komplektuyuschie", "Бампер"),
    (705, "transport-auto-parts-dveri-i-komplektuyuschie", "Дверь"),
    (706, "transport-auto-parts-kapoty-i-kryshki-bagazhnika", "Капот / Крышка багажника"),
    (707, "transport-auto-parts-zerkala-i-komplektuyuschie", "Наружное зеркало"),
    (708, "transport-auto-parts-stekla-i-komplektuyuschie", "Стекло"),
    (710, "transport-auto-parts-reshetki-zhabo-i-naruzhnyy-plastik", "Решётка / Жабо"),
    (711, "transport-auto-parts-krylya-i-podkrylki", "Крыло / Подкрылок"),
    (712, "transport-auto-parts-bryzgoviki-i-zaschita-dnischa", "Брызговик / Защита днища"),
    (713, "transport-auto-parts-silovye-elementy-kuzova", "Силовой элемент"),
)

BODY_RETIRED_SLUGS: tuple[str, ...] = tuple(s for _, s, _ in BODY_RETIRED)
BODY_RETIRED_IDS: tuple[int, ...] = tuple(i for i, _, _ in BODY_RETIRED)

# Special applicability — active but NOT ordinary passenger Create/Search buttons.
SPECIAL_SYSTEM_SLUGS: tuple[str, ...] = (
    "transport-auto-parts-rabochaya-gidravlika-i-pnevmatika",
    "transport-auto-parts-rabochie-organy-i-detali-navesnogo",
    "transport-auto-parts-elektroprivod-i-tyagovye-batarei",
)

SPECIAL_SYSTEM_LABELS: dict[str, str] = {
    "transport-auto-parts-rabochaya-gidravlika-i-pnevmatika": (
        "Рабочая гидравлика и пневматика"
    ),
    "transport-auto-parts-rabochie-organy-i-detali-navesnogo": (
        "Рабочие органы и детали навесного оборудования"
    ),
    "transport-auto-parts-elektroprivod-i-tyagovye-batarei": (
        "Электропривод и тяговые батареи"
    ),
}

SPECIAL_SYSTEM_SORT: dict[str, int] = {
    "transport-auto-parts-rabochaya-gidravlika-i-pnevmatika": 200,
    "transport-auto-parts-rabochie-organy-i-detali-navesnogo": 210,
    "transport-auto-parts-elektroprivod-i-tyagovye-batarei": 220,
}

SPECIAL_SYSTEM_EXPECTED_IDS: dict[str, int] = {
    "transport-auto-parts-rabochaya-gidravlika-i-pnevmatika": 1203,
    "transport-auto-parts-rabochie-organy-i-detali-navesnogo": 1204,
    "transport-auto-parts-elektroprivod-i-tyagovye-batarei": 1205,
}

# applicability → vehicle_type / catalog context for Brand/Model pickers
SPECIAL_APPLICABILITY: dict[str, dict[str, str]] = {
    "transport-auto-parts-rabochaya-gidravlika-i-pnevmatika": {
        "applicability": "special_equipment",
        "vehicle_type": "special",
        "reason": "Hydraulics/pneumatics for trucks/special/farm — not passenger.",
    },
    "transport-auto-parts-rabochie-organy-i-detali-navesnogo": {
        "applicability": "farm_machinery",
        "vehicle_type": "agricultural",
        "reason": "Implement/attachment parts — farm/special machinery context.",
    },
    "transport-auto-parts-elektroprivod-i-tyagovye-batarei": {
        "applicability": "electric",
        "vehicle_type": "electric",
        "reason": "Traction battery / EV drive — not 12V starter battery.",
    },
}

CONDITION_EXEMPT_SLUGS: frozenset[str] = frozenset(
    {
        "transport-auto-parts-krepezh-rezinki-i-melkie-detali",
        "transport-auto-parts-masla-zhidkosti-i-rashodniki",
    }
)

# part_name required except thin self-identifying / catch-all
PART_NAME_OPTIONAL_SLUGS: frozenset[str] = frozenset(
    {
        "transport-auto-parts-podshipniki",
        "transport-auto-parts-drugoe",
    }
)

# ---------------------------------------------------------------------------
# Shared option vocabularies
# ---------------------------------------------------------------------------

PART_CONDITION_CHOICES = ("Новая", "Б/у", "Восстановленная")
PART_ORIGIN_CHOICES = ("Оригинал", "Аналог", "Не знаю")
SELLER_TYPE_CHOICES = ("Частное лицо", "Магазин", "Авторазбор")
SIDE_CHOICES = ("Левая", "Правая", "Комплект")
POSITION_CHOICES = ("Передняя", "Задняя")
TRANSMISSION_TYPE_CHOICES = ("АКПП", "МКПП", "Вариатор", "Робот")

ENGINE_PART_NAMES = (
    "Двигатель в сборе",
    "Блок цилиндров",
    "ГБЦ",
    "Клапанная крышка",
    "Поршни",
    "Поршневые кольца",
    "Шатуны",
    "Коленвал",
    "Распредвал",
    "Клапаны",
    "Прокладки двигателя",
    "Поддон",
    "Масляный насос",
    "Масляный радиатор",
    "Сальник",
    "Турбина / турбокомпрессор",
    "Интеркулер",
    "Дроссель",
    "Впускной коллектор",
    "Опора двигателя",
    "ГРМ / комплект ГРМ",
    "Ремень навесного оборудования",
    "Натяжитель / ролик",
    "Другое",
)

TRANSMISSION_PART_NAMES = (
    "КПП в сборе",
    "Раздатка",
    "Редуктор",
    "Дифференциал",
    "Кардан",
    "Полуось / привод",
    "ШРУС",
    "Пыльник ШРУСа",
    "Сцепление",
    "Комплект сцепления",
    "Выжимной подшипник",
    "Маховик",
    "Гидротрансформатор",
    "Кулиса / селектор",
    "Опора КПП",
    "Другое",
)

SUSPENSION_PART_NAMES = (
    "Амортизатор",
    "Стойка",
    "Пружина",
    "Рычаг",
    "Шаровая опора",
    "Сайлентблок",
    "Ступица",
    "Подшипник ступицы",
    "Поворотный кулак",
    "Стабилизатор",
    "Стойка стабилизатора",
    "Втулка стабилизатора",
    "Подрамник",
    "Реактивная тяга",
    "Пневмоподвеска / элемент пневмоподвески",
    "Другое",
)

STEERING_PART_NAMES = (
    "Рулевая рейка",
    "Рулевой редуктор",
    "Насос ГУР",
    "ЭУР",
    "Рулевая колонка",
    "Рулевая тяга",
    "Рулевой наконечник",
    "Бачок ГУР",
    "Шланг ГУР",
    "Другое",
)

BRAKE_PART_NAMES = (
    "Тормозные колодки",
    "Тормозной диск",
    "Тормозной барабан",
    "Суппорт",
    "Главный тормозной цилиндр",
    "Рабочий тормозной цилиндр",
    "Вакуумный усилитель",
    "Блок ABS",
    "Тормозной шланг / трубка",
    "Ручник / стояночный тормоз",
    "Другое",
)

BODY_PART_NAMES = (
    "Бампер",
    "Дверь",
    "Капот",
    "Крышка багажника",
    "Крыло",
    "Наружное зеркало",
    "Лобовое стекло",
    "Боковое стекло",
    "Заднее стекло",
    "Решётка радиатора",
    "Жабо",
    "Порог",
    "Крыша",
    "Кузов в сборе",
    "Кабина",
    "Нооскат / передняя часть",
    "Рама",
    "Лонжерон",
    "Подкрылок",
    "Брызговик",
    "Защита днища",
    "Ручка двери",
    "Замок двери",
    "Наружный пластик",
    "Другое",
)

OPTICS_PART_NAMES = (
    "Фара",
    "Задний фонарь",
    "Противотуманная фара",
    "Поворотник",
    "ДХО",
    "Лампа",
    "Блок розжига",
    "Корректор фары",
    "Другое",
)

INTERIOR_PART_NAMES = (
    "Сиденье",
    "Панель / торпедо",
    "Обшивка двери",
    "Центральная консоль",
    "Ремень безопасности",
    "Подушка безопасности",
    "Потолок",
    "Ковролин",
    "Подлокотник",
    "Руль",
    "Салонное зеркало",
    "Стеклоподъёмник / механизм",
    "Другое",
)

ELECTRICAL_PART_NAMES = (
    "Аккумулятор",
    "Стартер",
    "Генератор",
    "ЭБУ / ECU",
    "Блок управления",
    "Проводка",
    "Предохранитель",
    "Блок предохранителей",
    "Реле",
    "Датчик",
    "Лямбда-зонд",
    "Катушка зажигания",
    "Свеча зажигания",
    "Электромотор / моторчик",
    "Центральный замок / модуль",
    "Мотор стеклоподъёмника",
    "Другое",
)

CLIMATE_PART_NAMES = (
    "Компрессор кондиционера",
    "Радиатор кондиционера / конденсер",
    "Испаритель",
    "Печка / радиатор печки",
    "Мотор печки",
    "Блок климата",
    "Трубка кондиционера",
    "Другое",
)

COOLING_PART_NAMES = (
    "Радиатор охлаждения",
    "Вентилятор",
    "Помпа",
    "Термостат",
    "Расширительный бачок",
    "Патрубок",
    "Другое",
)

FUEL_PART_NAMES = (
    "Топливный насос",
    "ТНВД",
    "Форсунка",
    "Топливная рампа",
    "Топливный бак",
    "Топливная трубка",
    "Карбюратор",
    "Другое",
)

EXHAUST_PART_NAMES = (
    "Глушитель",
    "Резонатор",
    "Катализатор",
    "Сажевый фильтр",
    "Выпускной коллектор",
    "Выхлопная труба",
    "Другое",
)

FASTENER_PART_NAMES = (
    "Болт",
    "Гайка",
    "Шпилька",
    "Клипса",
    "Пистон",
    "Крепление",
    "Резинка / уплотнитель",
    "Другое",
)

CONSUMABLE_PART_NAMES = (
    "Моторное масло",
    "Трансмиссионное масло",
    "Антифриз",
    "Тормозная жидкость",
    "Жидкость ГУР",
    "Омывающая жидкость",
    "Масляный фильтр",
    "Воздушный фильтр",
    "Салонный фильтр",
    "Топливный фильтр",
    "Щётки стеклоочистителя",
    "Другое",
)

HYDRAULICS_PART_NAMES = (
    "Гидронасос",
    "Гидромотор",
    "Гидроцилиндр",
    "Гидрораспределитель",
    "РВД / рукав высокого давления",
    "Пневмокомпонент",
    "Другое",
)

IMPLEMENT_PART_NAMES = (
    "Рабочий орган",
    "Режущий элемент",
    "Лемех / отвал",
    "Диск / лапа",
    "Крепление навесного",
    "Другое",
)

EV_DRIVE_PART_NAMES = (
    "Тяговая батарея",
    "Модуль батареи",
    "Инвертор",
    "Электродвигатель тяговый",
    "Зарядный порт / бортовое ЗУ",
    "Другое",
)

PART_NAMES_BY_SLUG: dict[str, tuple[str, ...]] = {
    "transport-auto-parts-dvigatel-i-navesnoe": ENGINE_PART_NAMES,
    "transport-auto-parts-korobka-peredach-i-transmissiya": TRANSMISSION_PART_NAMES,
    "transport-auto-parts-hodovaya-i-podveska": SUSPENSION_PART_NAMES,
    "transport-auto-parts-rulevoe-upravlenie": STEERING_PART_NAMES,
    "transport-auto-parts-tormoznaya-sistema": BRAKE_PART_NAMES,
    BODY_LEAF_SLUG: BODY_PART_NAMES,
    "transport-auto-parts-optika-fary-i-fonari": OPTICS_PART_NAMES,
    "transport-auto-parts-salon-i-interer": INTERIOR_PART_NAMES,
    "transport-auto-parts-elektrika-i-elektronika": ELECTRICAL_PART_NAMES,
    "transport-auto-parts-klimat-pechka-i-konditsioner": CLIMATE_PART_NAMES,
    "transport-auto-parts-sistema-ohlazhdeniya": COOLING_PART_NAMES,
    "transport-auto-parts-toplivnaya-sistema": FUEL_PART_NAMES,
    "transport-auto-parts-vyhlopnaya-sistema": EXHAUST_PART_NAMES,
    "transport-auto-parts-krepezh-rezinki-i-melkie-detali": FASTENER_PART_NAMES,
    "transport-auto-parts-masla-zhidkosti-i-rashodniki": CONSUMABLE_PART_NAMES,
    "transport-auto-parts-rabochaya-gidravlika-i-pnevmatika": HYDRAULICS_PART_NAMES,
    "transport-auto-parts-rabochie-organy-i-detali-navesnogo": IMPLEMENT_PART_NAMES,
    "transport-auto-parts-elektroprivod-i-tyagovye-batarei": EV_DRIVE_PART_NAMES,
}

# part_name → show side / position (depends_on values)
SIDE_PART_NAMES: frozenset[str] = frozenset(
    {
        "Дверь",
        "Крыло",
        "Наружное зеркало",
        "Боковое стекло",
        "Фара",
        "Задний фонарь",
        "Противотуманная фара",
        "Поворотник",
        "ДХО",
        "Амортизатор",
        "Стойка",
        "Рычаг",
        "Шаровая опора",
        "Ступица",
        "Поворотный кулак",
        "Стойка стабилизатора",
        "Рулевая тяга",
        "Рулевой наконечник",
        "Тормозные колодки",
        "Тормозной диск",
        "Суппорт",
        "Обшивка двери",
        "Подлокотник",
    }
)

POSITION_PART_NAMES: frozenset[str] = frozenset(
    {
        "Дверь",
        "Крыло",
        "Боковое стекло",
        "Амортизатор",
        "Стойка",
        "Рычаг",
        "Шаровая опора",
        "Ступица",
        "Стойка стабилизатора",
        "Тормозные колодки",
        "Тормозной диск",
        "Суппорт",
        "Бампер",
    }
)

# ---------------------------------------------------------------------------
# Aliases / resolver
# ---------------------------------------------------------------------------

PARTS_LEAF_ALIASES: dict[str, str] = {
    "двигатель": "transport-auto-parts-dvigatel-i-navesnoe",
    "турбина": "transport-auto-parts-dvigatel-i-navesnoe",
    "гбц": "transport-auto-parts-dvigatel-i-navesnoe",
    "коробка": "transport-auto-parts-korobka-peredach-i-transmissiya",
    "кпп": "transport-auto-parts-korobka-peredach-i-transmissiya",
    "граната": "transport-auto-parts-korobka-peredach-i-transmissiya",
    "шрус": "transport-auto-parts-korobka-peredach-i-transmissiya",
    "амортизатор": "transport-auto-parts-hodovaya-i-podveska",
    "шаровая": "transport-auto-parts-hodovaya-i-podveska",
    "рейка": "transport-auto-parts-rulevoe-upravlenie",
    "колодки": "transport-auto-parts-tormoznaya-sistema",
    "бампер": BODY_LEAF_SLUG,
    "дверь": BODY_LEAF_SLUG,
    "капот": BODY_LEAF_SLUG,
    "зеркало": BODY_LEAF_SLUG,
    "стекло": BODY_LEAF_SLUG,
    "фара": "transport-auto-parts-optika-fary-i-fonari",
    "фонарь": "transport-auto-parts-optika-fary-i-fonari",
    "оптика": "transport-auto-parts-optika-fary-i-fonari",
    "сиденье": "transport-auto-parts-salon-i-interer",
    "руль": "transport-auto-parts-salon-i-interer",
    "подушка безопасности": "transport-auto-parts-salon-i-interer",
    "аккумулятор": "transport-auto-parts-elektrika-i-elektronika",
    "стартер": "transport-auto-parts-elektrika-i-elektronika",
    "генератор": "transport-auto-parts-elektrika-i-elektronika",
    "мозги": "transport-auto-parts-elektrika-i-elektronika",
    "эбу": "transport-auto-parts-elektrika-i-elektronika",
    "лямбда": "transport-auto-parts-elektrika-i-elektronika",
    "свеча": "transport-auto-parts-elektrika-i-elektronika",
    "печка": "transport-auto-parts-klimat-pechka-i-konditsioner",
    "кондиционер": "transport-auto-parts-klimat-pechka-i-konditsioner",
    "радиатор": "transport-auto-parts-sistema-ohlazhdeniya",
    "бензонасос": "transport-auto-parts-toplivnaya-sistema",
    "форсунка": "transport-auto-parts-toplivnaya-sistema",
    "глушитель": "transport-auto-parts-vyhlopnaya-sistema",
    "фильтр": "transport-auto-parts-masla-zhidkosti-i-rashodniki",
    "масло": "transport-auto-parts-masla-zhidkosti-i-rashodniki",
    "щётки": "transport-auto-parts-masla-zhidkosti-i-rashodniki",
    "запчасти": PARTS_PARENT_SLUG,
    "автозапчасти": PARTS_PARENT_SLUG,
}

# Alias → (system_slug, part_name label) for resolver enrichment tests
PARTS_PART_NAME_ALIASES: dict[str, tuple[str, str]] = {
    "граната": (
        "transport-auto-parts-korobka-peredach-i-transmissiya",
        "ШРУС",
    ),
    "шрус": (
        "transport-auto-parts-korobka-peredach-i-transmissiya",
        "ШРУС",
    ),
    "рейка": (
        "transport-auto-parts-rulevoe-upravlenie",
        "Рулевая рейка",
    ),
    "шаровая": (
        "transport-auto-parts-hodovaya-i-podveska",
        "Шаровая опора",
    ),
    "мозги": (
        "transport-auto-parts-elektrika-i-elektronika",
        "ЭБУ / ECU",
    ),
    "эбу": (
        "transport-auto-parts-elektrika-i-elektronika",
        "ЭБУ / ECU",
    ),
    "турбина": (
        "transport-auto-parts-dvigatel-i-navesnoe",
        "Турбина / турбокомпрессор",
    ),
    "стартер": (
        "transport-auto-parts-elektrika-i-elektronika",
        "Стартер",
    ),
    "генератор": (
        "transport-auto-parts-elektrika-i-elektronika",
        "Генератор",
    ),
    "печка": (
        "transport-auto-parts-klimat-pechka-i-konditsioner",
        "Печка / радиатор печки",
    ),
    "бензонасос": (
        "transport-auto-parts-toplivnaya-sistema",
        "Топливный насос",
    ),
    "форсунка": (
        "transport-auto-parts-toplivnaya-sistema",
        "Форсунка",
    ),
    "лямбда": (
        "transport-auto-parts-elektrika-i-elektronika",
        "Датчик",
    ),
    "фара": (
        "transport-auto-parts-optika-fary-i-fonari",
        "Фара",
    ),
    "колодки": (
        "transport-auto-parts-tormoznaya-sistema",
        "Тормозные колодки",
    ),
}

PARTS_PARENT_ALIASES: dict[str, str] = {
    "автозапчасти": PARTS_PARENT_SLUG,
    "запчасти": PARTS_PARENT_SLUG,
}

# Services boundary — keep weight high so repair phrases do not resolve to Parts.
PARTS_SERVICE_BOUNDARY_ALIASES: dict[str, str] = {
    "ремонт коробки": "transport-auto-services-remont-i-obsluzhivanie",
    "ремонт кпп": "transport-auto-services-remont-i-obsluzhivanie",
    "ремонт турбины": "transport-auto-services-remont-i-obsluzhivanie",
    "ремонт турбин": "transport-auto-services-remont-i-obsluzhivanie",
    "ремонт двигателя": "transport-auto-services-remont-i-obsluzhivanie",
    "установка сигнализации": "transport-auto-services-tyuning-i-doosnaschenie",
}

# LED: do not blind-route decorative LED to OEM Optics (prefer Accessories).
# Safe: keep фара/оптика → Optics; leave generic «led» on Accessories lighting if present.
LED_ACCESSORIES_SLUG = (
    "transport-accessories-tuning-svet-i-dopolnitelnoe-osveschenie"
)

# ---------------------------------------------------------------------------
# Field helpers
# ---------------------------------------------------------------------------


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


def _vehicle_compat(sort: int = 30) -> list:
    return [
        _field(
            "vehicle_brand",
            "Марка автомобиля",
            CategoryFieldType.brand,
            False,
            sort,
            hint="Для какого автомобиля деталь?",
        ),
        _field(
            "vehicle_model",
            "Модель автомобиля",
            CategoryFieldType.model,
            False,
            sort + 5,
            hint="Модель автомобиля",
        ),
    ]


def _commerce(sort: int = 200, *, with_negotiable: bool = True) -> list:
    fields = [
        _field("price", "Цена", CategoryFieldType.price, True, sort),
    ]
    if with_negotiable:
        fields.append(
            _field(
                "negotiable",
                "Торг",
                CategoryFieldType.enum,
                False,
                sort + 5,
                _choices(*NEGOTIABLE_CHOICES),
            )
        )
    fields.extend(
        [
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
    )
    return fields


def _origin_field(sort: int = 80) -> list:
    return [
        _field(
            "part_origin_type",
            "Тип запчасти",
            CategoryFieldType.enum,
            False,
            sort,
            _choices(*PART_ORIGIN_CHOICES),
        ),
    ]


def _part_name_field(
    names: tuple[str, ...],
    *,
    required: bool,
    sort: int = 20,
) -> tuple:
    return _field(
        "part_name",
        "Название детали",
        CategoryFieldType.enum,
        required,
        sort,
        _choices(*names),
        hint="Что именно продаёте?",
    )


def _condition_field(sort: int = 70) -> tuple:
    return _field(
        "part_condition",
        "Состояние",
        CategoryFieldType.enum,
        True,
        sort,
        _choices(*PART_CONDITION_CHOICES),
    )


def _side_position_fields(sort: int = 100) -> list:
    side_vals = sorted(SIDE_PART_NAMES)
    pos_vals = sorted(POSITION_PART_NAMES)
    side_opts = _choices(*SIDE_CHOICES)
    side_opts.update(_depends("part_name", *side_vals))
    pos_opts = _choices(*POSITION_CHOICES)
    pos_opts.update(_depends("part_name", *pos_vals))
    return [
        _field(
            "side",
            "Сторона",
            CategoryFieldType.enum,
            False,
            sort,
            side_opts,
        ),
        _field(
            "position",
            "Расположение",
            CategoryFieldType.enum,
            False,
            sort + 5,
            pos_opts,
        ),
    ]


def _physical_schema(
    names: tuple[str, ...] | None,
    *,
    with_side_position: bool = False,
    with_transmission: bool = False,
    part_name_required: bool = True,
) -> list:
    fields: list = [*_geo()]
    if names is not None:
        fields.append(_part_name_field(names, required=part_name_required))
    fields.extend(_vehicle_compat(40))
    fields.append(_condition_field(70))
    fields.extend(_origin_field(80))
    if with_side_position:
        fields.extend(_side_position_fields(100))
    if with_transmission:
        fields.append(
            _field(
                "transmission_type",
                "Тип КПП",
                CategoryFieldType.enum,
                False,
                110,
                _choices(*TRANSMISSION_TYPE_CHOICES),
            )
        )
    fields.extend(_commerce(200))
    return fields


def _consumable_schema(names: tuple[str, ...]) -> list:
    return [
        *_geo(),
        _part_name_field(names, required=True),
        *_vehicle_compat(40),
        *_origin_field(80),
        *_commerce(200),
    ]


def _fastener_schema(names: tuple[str, ...]) -> list:
    return [
        *_geo(),
        _part_name_field(names, required=True),
        *_vehicle_compat(40),
        *_commerce(200),
    ]


def _bearings_schema() -> list:
    # Leaf itself identifies product family — no forced part_name.
    return [
        *_geo(),
        *_vehicle_compat(40),
        _condition_field(70),
        *_origin_field(80),
        *_commerce(200),
    ]


def _other_schema() -> list:
    return [
        *_geo(),
        *_vehicle_compat(40),
        _condition_field(70),
        *_origin_field(80),
        *_commerce(200),
    ]


def _special_schema(names: tuple[str, ...]) -> list:
    return _physical_schema(names, part_name_required=True)


def _search_filters_for(
    slug: str,
    *,
    with_part_name: bool,
    with_condition: bool,
    with_side_position: bool = False,
    with_transmission: bool = False,
) -> list:
    filters: list = [
        _filt("region", "Регион", CategoryFilterType.text, 10, {}),
        _filt("city", "Город", CategoryFilterType.text, 20, {}),
        _filt(
            "vehicle_brand",
            "Марка автомобиля",
            CategoryFilterType.text,
            30,
            {},
        ),
        _filt(
            "vehicle_model",
            "Модель автомобиля",
            CategoryFilterType.text,
            40,
            {},
        ),
    ]
    if with_part_name and slug in PART_NAMES_BY_SLUG:
        filters.append(
            _filt(
                "part_name",
                "Название детали",
                CategoryFilterType.select,
                50,
                _choices(*PART_NAMES_BY_SLUG[slug]),
            )
        )
    if with_condition:
        filters.append(
            _filt(
                "part_condition",
                "Состояние",
                CategoryFilterType.select,
                60,
                _choices(*PART_CONDITION_CHOICES),
            )
        )
    filters.append(
        _filt(
            "part_origin_type",
            "Тип запчасти",
            CategoryFilterType.select,
            70,
            _choices(*PART_ORIGIN_CHOICES),
        )
    )
    filters.append(
        _filt(
            "seller_type",
            "Кто продаёт",
            CategoryFilterType.select,
            80,
            _choices(*SELLER_TYPE_CHOICES),
        )
    )
    if with_side_position:
        filters.append(
            _filt("side", "Сторона", CategoryFilterType.select, 110, _choices(*SIDE_CHOICES))
        )
        filters.append(
            _filt(
                "position",
                "Расположение",
                CategoryFilterType.select,
                120,
                _choices(*POSITION_CHOICES),
            )
        )
    if with_transmission:
        filters.append(
            _filt(
                "transmission_type",
                "Тип КПП",
                CategoryFilterType.select,
                130,
                _choices(*TRANSMISSION_TYPE_CHOICES),
            )
        )
    filters.append(_filt("price", "Цена", CategoryFilterType.range, 200, {}))
    filters.append(
        _filt(
            "sort",
            "Сортировка",
            CategoryFilterType.select,
            300,
            {
                "choices": [
                    {"value": "newest", "label": "Сначала новые"},
                    {"value": "price_asc", "label": "Сначала дешевле"},
                    {"value": "price_desc", "label": "Сначала дороже"},
                ]
            },
        )
    )
    return filters


def _build_core_and_filters() -> tuple[dict[str, list], dict[str, list]]:
    cores: dict[str, list] = {}
    filters: dict[str, list] = {}

    cores["transport-auto-parts-dvigatel-i-navesnoe"] = _physical_schema(
        ENGINE_PART_NAMES
    )
    filters["transport-auto-parts-dvigatel-i-navesnoe"] = _search_filters_for(
        "transport-auto-parts-dvigatel-i-navesnoe",
        with_part_name=True,
        with_condition=True,
    )

    cores["transport-auto-parts-korobka-peredach-i-transmissiya"] = (
        _physical_schema(TRANSMISSION_PART_NAMES, with_transmission=True)
    )
    filters["transport-auto-parts-korobka-peredach-i-transmissiya"] = (
        _search_filters_for(
            "transport-auto-parts-korobka-peredach-i-transmissiya",
            with_part_name=True,
            with_condition=True,
            with_transmission=True,
        )
    )

    cores["transport-auto-parts-hodovaya-i-podveska"] = _physical_schema(
        SUSPENSION_PART_NAMES, with_side_position=True
    )
    filters["transport-auto-parts-hodovaya-i-podveska"] = _search_filters_for(
        "transport-auto-parts-hodovaya-i-podveska",
        with_part_name=True,
        with_condition=True,
        with_side_position=True,
    )

    cores["transport-auto-parts-rulevoe-upravlenie"] = _physical_schema(
        STEERING_PART_NAMES, with_side_position=True
    )
    filters["transport-auto-parts-rulevoe-upravlenie"] = _search_filters_for(
        "transport-auto-parts-rulevoe-upravlenie",
        with_part_name=True,
        with_condition=True,
        with_side_position=True,
    )

    cores["transport-auto-parts-tormoznaya-sistema"] = _physical_schema(
        BRAKE_PART_NAMES, with_side_position=True
    )
    filters["transport-auto-parts-tormoznaya-sistema"] = _search_filters_for(
        "transport-auto-parts-tormoznaya-sistema",
        with_part_name=True,
        with_condition=True,
        with_side_position=True,
    )

    cores[BODY_LEAF_SLUG] = _physical_schema(
        BODY_PART_NAMES, with_side_position=True
    )
    filters[BODY_LEAF_SLUG] = _search_filters_for(
        BODY_LEAF_SLUG,
        with_part_name=True,
        with_condition=True,
        with_side_position=True,
    )

    cores["transport-auto-parts-optika-fary-i-fonari"] = _physical_schema(
        OPTICS_PART_NAMES, with_side_position=True
    )
    filters["transport-auto-parts-optika-fary-i-fonari"] = _search_filters_for(
        "transport-auto-parts-optika-fary-i-fonari",
        with_part_name=True,
        with_condition=True,
        with_side_position=True,
    )

    cores["transport-auto-parts-salon-i-interer"] = _physical_schema(
        INTERIOR_PART_NAMES, with_side_position=True
    )
    filters["transport-auto-parts-salon-i-interer"] = _search_filters_for(
        "transport-auto-parts-salon-i-interer",
        with_part_name=True,
        with_condition=True,
        with_side_position=True,
    )

    cores["transport-auto-parts-elektrika-i-elektronika"] = _physical_schema(
        ELECTRICAL_PART_NAMES
    )
    filters["transport-auto-parts-elektrika-i-elektronika"] = _search_filters_for(
        "transport-auto-parts-elektrika-i-elektronika",
        with_part_name=True,
        with_condition=True,
    )

    cores["transport-auto-parts-klimat-pechka-i-konditsioner"] = _physical_schema(
        CLIMATE_PART_NAMES
    )
    filters["transport-auto-parts-klimat-pechka-i-konditsioner"] = (
        _search_filters_for(
            "transport-auto-parts-klimat-pechka-i-konditsioner",
            with_part_name=True,
            with_condition=True,
        )
    )

    cores["transport-auto-parts-sistema-ohlazhdeniya"] = _physical_schema(
        COOLING_PART_NAMES
    )
    filters["transport-auto-parts-sistema-ohlazhdeniya"] = _search_filters_for(
        "transport-auto-parts-sistema-ohlazhdeniya",
        with_part_name=True,
        with_condition=True,
    )

    cores["transport-auto-parts-toplivnaya-sistema"] = _physical_schema(
        FUEL_PART_NAMES
    )
    filters["transport-auto-parts-toplivnaya-sistema"] = _search_filters_for(
        "transport-auto-parts-toplivnaya-sistema",
        with_part_name=True,
        with_condition=True,
    )

    cores["transport-auto-parts-vyhlopnaya-sistema"] = _physical_schema(
        EXHAUST_PART_NAMES
    )
    filters["transport-auto-parts-vyhlopnaya-sistema"] = _search_filters_for(
        "transport-auto-parts-vyhlopnaya-sistema",
        with_part_name=True,
        with_condition=True,
    )

    cores["transport-auto-parts-podshipniki"] = _bearings_schema()
    filters["transport-auto-parts-podshipniki"] = _search_filters_for(
        "transport-auto-parts-podshipniki",
        with_part_name=False,
        with_condition=True,
    )

    cores["transport-auto-parts-krepezh-rezinki-i-melkie-detali"] = (
        _fastener_schema(FASTENER_PART_NAMES)
    )
    filters["transport-auto-parts-krepezh-rezinki-i-melkie-detali"] = (
        _search_filters_for(
            "transport-auto-parts-krepezh-rezinki-i-melkie-detali",
            with_part_name=True,
            with_condition=False,
        )
    )

    cores["transport-auto-parts-masla-zhidkosti-i-rashodniki"] = (
        _consumable_schema(CONSUMABLE_PART_NAMES)
    )
    filters["transport-auto-parts-masla-zhidkosti-i-rashodniki"] = (
        _search_filters_for(
            "transport-auto-parts-masla-zhidkosti-i-rashodniki",
            with_part_name=True,
            with_condition=False,
        )
    )

    cores["transport-auto-parts-drugoe"] = _other_schema()
    filters["transport-auto-parts-drugoe"] = _search_filters_for(
        "transport-auto-parts-drugoe",
        with_part_name=False,
        with_condition=True,
    )

    for slug in SPECIAL_SYSTEM_SLUGS:
        cores[slug] = _special_schema(PART_NAMES_BY_SLUG[slug])
        filters[slug] = _search_filters_for(
            slug, with_part_name=True, with_condition=True
        )

    # Parent: empty live Create/Search SoT (picker only).
    cores[PARTS_PARENT_SLUG] = []
    filters[PARTS_PARENT_SLUG] = []

    return cores, filters


PARTS_CORE_FIELDS_BY_SLUG, PARTS_SEARCH_FILTERS_BY_SLUG = _build_core_and_filters()


def normalize_part_number(raw: str) -> str:
    """Casefold + trim; strip spaces/hyphens for Search matching.

    Display value is preserved as entered; this is lookup-only.
    ``90915-YZZD2`` / ``90915 YZZD2`` / ``90915-yzzd2`` → same needle.
    """
    s = (raw or "").strip().casefold()
    s = " ".join(s.split())
    return s.replace(" ", "").replace("-", "")


def is_passenger_system_slug(slug: str) -> bool:
    return slug in PASSENGER_SYSTEM_SLUGS


def is_special_system_slug(slug: str) -> bool:
    return slug in SPECIAL_SYSTEM_SLUGS


def is_auto_parts_leaf_slug(slug: str | None) -> bool:
    if not slug:
        return False
    return slug in PASSENGER_SYSTEM_SLUGS or slug in SPECIAL_SYSTEM_SLUGS
