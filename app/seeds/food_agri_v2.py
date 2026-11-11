# -*- coding: utf-8 -*-
"""Products & Agri V2 — taxonomy + Package A Create + Package B Search SoT.

Taxonomy cleanup + Platform Coherence matrices + Backend Create builder.
Search filters = explicit short allowlist (Create ≠ Search).
"""
from __future__ import annotations

from typing import Any, Literal

from app.models.category_enums import (
    CategoryEntityType,
    CategoryFieldType,
    CategoryFilterType,
)
from app.seeds.shared_goods_create_contract import (
    CONTACT_METHOD_CHOICES,
    GOODS_NEGOTIABLE_CHOICES,
)

FOOD_AGRI_ROOT_SLUG = "food-agri"
FOOD_AGRI_ROOT_LABEL = "Продукты, сельхозтовары и фермерская продукция"
FOOD_AGRI_UI_LABEL = "Продукты и сельхозтовары"

# Canonical Animals destination for feed/hay (do not modify Animals behavior).
FOOD_AGRI_FEED_CANONICAL_ANIMALS_SLUG = "animals-seno-korma-i-kormovye-dobavki"
FOOD_AGRI_FEED_CANONICAL_ANIMALS_LABEL = "Сено, Корма и кормовые добавки"

# --- Retired (soft-inactive; rows preserved) ---

FOOD_AGRI_LEGACY_RETIRED_SLUGS: frozenset[str] = frozenset(
    {
        "food-agri-products",
        "food-agri-farm",
        "food-agri-feed",
    }
)

FOOD_AGRI_SALES_MODE_RETIRED_SLUGS: frozenset[str] = frozenset(
    {"food-agri-optovyy-otdel"}
)

FOOD_AGRI_ECO_RETIRED_SLUGS: frozenset[str] = frozenset(
    {"food-agri-ekoprodukty-i-fermerskie-tovary"}
)

FOOD_AGRI_TARA_RETIRED_SLUGS: frozenset[str] = frozenset(
    {"food-agri-tara-upakovka-dlya-produktsii"}
)

FOOD_AGRI_V2_RETIRED_SLUGS: frozenset[str] = (
    FOOD_AGRI_LEGACY_RETIRED_SLUGS
    | FOOD_AGRI_SALES_MODE_RETIRED_SLUGS
    | FOOD_AGRI_ECO_RETIRED_SLUGS
    | FOOD_AGRI_TARA_RETIRED_SLUGS
)

# Active edible L2 after cleanup (label, slug, sort).
FOOD_AGRI_V2_CANONICAL_LEAVES: tuple[tuple[str, str, int], ...] = (
    ("Овощи и фрукты", "food-agri-ovoschi-i-frukty", 10),
    ("Мясо и мясная продукция", "food-agri-myaso-i-myasnaya-produktsiya", 20),
    ("Молочная продукция", "food-agri-molochnaya-produktsiya", 30),
    ("Яйца", "food-agri-yaytsa", 40),
    ("Рыба и морепродукты", "food-agri-ryba-i-moreprodukty", 50),
    ("Мёд и продукты пчеловодства", "food-agri-med-i-produkty-pchelovodstva", 60),
    ("Орехи и сухофрукты", "food-agri-orehi-i-suhofrukty", 70),
    ("Крупы, мука/макаронные изделия", "food-agri-krupy-muka-makaronnye-izdeliya", 80),
    ("Масла и жиры", "food-agri-masla-i-zhiry", 90),
    ("Специи, приправы и пряности", "food-agri-spetsii-pripravy-i-pryanosti", 100),
    ("Бакалея и продукты питания", "food-agri-bakaleya-i-produkty-pitaniya", 110),
    ("Кондитерские изделия и сладости", "food-agri-konditerskie-izdeliya-i-sladosti", 120),
    ("Хлебобулочные изделия", "food-agri-hlebobulochnye-izdeliya", 130),
    ("Снеки и закуски", "food-agri-sneki-i-zakuski", 140),
    ("Полуфабрикаты", "food-agri-polufabrikaty", 150),
    ("Замороженные продукты", "food-agri-zamorozhennye-produkty", 160),
    ("Консервы и соленья", "food-agri-konservy-i-solenya", 170),
    ("Колбасные изделия и деликатесы", "food-agri-kolbasnye-izdeliya-i-delikatesy", 180),
    ("Готовая еда и кулинария", "food-agri-gotovaya-eda-i-kulinariya", 190),
    ("Чай и кофе", "food-agri-chay-i-kofe", 200),
    ("Напитки", "food-agri-napitki", 210),
    ("Зерно и зерновые культуры", "food-agri-zerno-i-zernovye-kultury", 220),
    ("Прочие продукты и сельхозтовары", "food-agri-prochie-produkty-i-selhoztovary", 260),
)

FOOD_AGRI_V2_CANONICAL_SLUGS: frozenset[str] = frozenset(
    slug for _label, slug, _sort in FOOD_AGRI_V2_CANONICAL_LEAVES
)

FOOD_AGRI_V2_EXPECTED_L2_COUNT = len(FOOD_AGRI_V2_CANONICAL_LEAVES)  # 23
FOOD_AGRI_V2_EXPECTED_KIND_COUNT = 158
FOOD_AGRI_V2_ENTITY_TYPE = CategoryEntityType.food

FOOD_AGRI_KIND_KEY = "food_kind"
FOOD_AGRI_KIND_LABEL = "Товар"
FOOD_AGRI_SELLER_KEY = "seller_type"
FOOD_AGRI_SELLER_LABEL = "Кто продаёт"

# Section key → slug (mirrors food_sections_catalog after cleanup).
FOOD_AGRI_V2_SECTION_SLUGS: dict[str, str] = {
    "produce": "food-agri-ovoschi-i-frukty",
    "meat": "food-agri-myaso-i-myasnaya-produktsiya",
    "dairy": "food-agri-molochnaya-produktsiya",
    "eggs": "food-agri-yaytsa",
    "fish": "food-agri-ryba-i-moreprodukty",
    "honey": "food-agri-med-i-produkty-pchelovodstva",
    "nuts": "food-agri-orehi-i-suhofrukty",
    "grains": "food-agri-krupy-muka-makaronnye-izdeliya",
    "oils": "food-agri-masla-i-zhiry",
    "spices": "food-agri-spetsii-pripravy-i-pryanosti",
    "grocery": "food-agri-bakaleya-i-produkty-pitaniya",
    "sweets": "food-agri-konditerskie-izdeliya-i-sladosti",
    "bakery": "food-agri-hlebobulochnye-izdeliya",
    "snacks": "food-agri-sneki-i-zakuski",
    "semi": "food-agri-polufabrikaty",
    "frozen": "food-agri-zamorozhennye-produkty",
    "canned": "food-agri-konservy-i-solenya",
    "sausage": "food-agri-kolbasnye-izdeliya-i-delikatesy",
    "ready": "food-agri-gotovaya-eda-i-kulinariya",
    "tea": "food-agri-chay-i-kofe",
    "drinks": "food-agri-napitki",
    "crops": "food-agri-zerno-i-zernovye-kultury",
    "other": "food-agri-prochie-produkty-i-selhoztovary",
}

# --- Tara ownership (retire from Food; no blind invent) ---
# decision: GAP | NEAREST_GAP | EQUIPMENT_NOT_GOODS
# Nearest Materials L2 exists but exact kind options do not — Archi may expand later.

FOOD_AGRI_TARA_KIND_OWNERSHIP: dict[str, tuple[str, str, str]] = {
    "Стеклянные банки": (
        "GAP",
        "materials-upakovochnye-materialy",
        "Materials packing has film/bags/cardboard — no «банки» kind",
    ),
    "Крышки": (
        "GAP",
        "materials-upakovochnye-materialy",
        "No lids kind under Materials or Business Equipment",
    ),
    "Пластиковые бутылки": (
        "GAP",
        "materials-upakovochnye-materialy",
        "No bottles kind; Materials has «Пакеты» only among close goods",
    ),
    "Ящики": (
        "GAP",
        "materials-upakovochnye-materialy",
        "No produce crates kind; HG storage boxes are household, not agri tara",
    ),
    "Мешки": (
        "GAP",
        "materials-upakovochnye-materialy",
        "No мешки kind; Business «Мешкозашивочные машины» is equipment not bags",
    ),
    "Контейнеры": (
        "GAP",
        "materials-upakovochnye-materialy",
        "No food-grade containers kind; Business «Торговые контейнеры» ≠ packaging tara",
    ),
    "Другая тара": (
        "GAP",
        "materials-upakovochnye-materialy",
        "Catch-all — no invent; Materials packing L2 is nearest root authority",
    ),
}

# Business packing L2 is machines (запайщики, датеры…) — not tara goods destination.
FOOD_AGRI_TARA_NOT_BUSINESS_EQUIPMENT_REASON = (
    "business-equipment-upakovka-i-markirovka owns packing *equipment*, not jars/bags"
)

# --- Grain ownership ---

GrainClass = Literal[
    "AGRICULTURAL_COMMODITY",
    "INDUSTRIAL_RAW_MATERIAL",
    "AMBIGUOUS",
]

FOOD_AGRI_GRAIN_KIND_OWNERSHIP: dict[str, tuple[GrainClass, str, str]] = {
    "Пшеница": (
        "AGRICULTURAL_COMMODITY",
        "food-agri-zerno-i-zernovye-kultury",
        "Farm-market grain — Food/Agri",
    ),
    "Ячмень": (
        "AGRICULTURAL_COMMODITY",
        "food-agri-zerno-i-zernovye-kultury",
        "Farm-market grain — Food/Agri",
    ),
    "Кукуруза": (
        "AGRICULTURAL_COMMODITY",
        "food-agri-zerno-i-zernovye-kultury",
        "Farm-market grain/crop — Food/Agri",
    ),
    "Овёс": (
        "AGRICULTURAL_COMMODITY",
        "food-agri-zerno-i-zernovye-kultury",
        "Farm-market grain — Food/Agri",
    ),
    "Подсолнечник": (
        "AGRICULTURAL_COMMODITY",
        "food-agri-zerno-i-zernovye-kultury",
        "Oilseed crop as agri produce — Food/Agri (not Materials oil)",
    ),
    "Нут": (
        "AGRICULTURAL_COMMODITY",
        "food-agri-zerno-i-zernovye-kultury",
        "Pulse crop — Food/Agri",
    ),
    "Другое зерно": (
        "AGRICULTURAL_COMMODITY",
        "food-agri-zerno-i-zernovye-kultury",
        "Open agri catch-all — Food/Agri",
    ),
}

# Materials industrial food ingredients must stay out of Food crops/kinds.
FOOD_AGRI_MATERIALS_FOOD_RAW_SLUG = "materials-pischevoe-syre-i-ingredienty"
FOOD_AGRI_BANNED_INDUSTRIAL_RAW_KINDS: frozenset[str] = frozenset(
    {
        "Сухое молоко",  # also appears in Food «other» as retail leftover — PRODUCT_DECISION later
        "Сыворотка",
        "Патока",
        "Солод",
        "Желатин",
        "Ароматизаторы",
        "Пищевые добавки",
        "Какао-бобы",
        "Пищевое сырьё",
    }
)

# --- Condition: default OFF for all edible Food/Agri kinds ---

FOOD_AGRI_CONDITION_DEFAULT = "OFF"
FOOD_AGRI_CONDITION_APPROVED_KINDS: frozenset[str] = frozenset()  # empty = none

# --- Price semantics (audit only; not implemented) ---

PriceClass = Literal["ITEM_PRICE", "UNIT_PRICE_REQUIRED", "PRODUCT_DECISION"]

# kind → (class, rationale)
FOOD_AGRI_PRICE_SEMANTICS: dict[str, tuple[PriceClass, str]] = {
    # produce — usually sold by weight
    "Помидоры": ("UNIT_PRICE_REQUIRED", "Typically sold by kg"),
    "Огурцы": ("UNIT_PRICE_REQUIRED", "Typically sold by kg"),
    "Картофель": ("UNIT_PRICE_REQUIRED", "Typically sold by kg / мешок"),
    "Лук": ("UNIT_PRICE_REQUIRED", "Typically sold by kg"),
    "Морковь": ("UNIT_PRICE_REQUIRED", "Typically sold by kg"),
    "Капуста": ("PRODUCT_DECISION", "May be per head (шт) or kg"),
    "Болгарский перец": ("UNIT_PRICE_REQUIRED", "Typically sold by kg"),
    "Зелень": ("PRODUCT_DECISION", "Bunch (шт) vs weight varies"),
    "Яблоки": ("UNIT_PRICE_REQUIRED", "Typically sold by kg"),
    "Виноград": ("UNIT_PRICE_REQUIRED", "Typically sold by kg"),
    "Арбузы и дыни": ("PRODUCT_DECISION", "Often per piece; sometimes kg"),
    "Ягоды": ("UNIT_PRICE_REQUIRED", "Typically sold by kg / л"),
    "Другие овощи и фрукты": ("PRODUCT_DECISION", "Open set"),
    # meat
    "Говядина": ("UNIT_PRICE_REQUIRED", "Sold by kg"),
    "Баранина": ("UNIT_PRICE_REQUIRED", "Sold by kg"),
    "Конина": ("UNIT_PRICE_REQUIRED", "Sold by kg"),
    "Курица": ("PRODUCT_DECISION", "Whole bird (шт) vs cuts by kg"),
    "Индейка": ("PRODUCT_DECISION", "Whole vs cuts"),
    "Свинина": ("UNIT_PRICE_REQUIRED", "Sold by kg"),
    "Фарш": ("UNIT_PRICE_REQUIRED", "Sold by kg"),
    "Субпродукты": ("UNIT_PRICE_REQUIRED", "Sold by kg"),
    "Другое мясо": ("PRODUCT_DECISION", "Open set"),
    # dairy
    "Молоко": ("UNIT_PRICE_REQUIRED", "Usually per л / bottle size in title"),
    "Кефир": ("UNIT_PRICE_REQUIRED", "Usually per л / pack"),
    "Сметана": ("UNIT_PRICE_REQUIRED", "Usually per кг / pack weight"),
    "Творог": ("UNIT_PRICE_REQUIRED", "Usually per кг"),
    "Сыр": ("PRODUCT_DECISION", "Wheel/piece vs kg"),
    "Каймак": ("UNIT_PRICE_REQUIRED", "Usually per кг"),
    "Кумыс": ("UNIT_PRICE_REQUIRED", "Usually per л"),
    "Чалап": ("UNIT_PRICE_REQUIRED", "Usually per л"),
    "Другая молочная продукция": ("PRODUCT_DECISION", "Open set"),
    # eggs
    "Куриные яйца": ("PRODUCT_DECISION", "Per шт / dozen / tray"),
    "Перепелиные яйца": ("PRODUCT_DECISION", "Per шт / pack"),
    "Индюшиные яйца": ("PRODUCT_DECISION", "Per шт / pack"),
    "Другие яйца": ("PRODUCT_DECISION", "Open set"),
    # fish — form already in kind; price still often by kg
    "Свежая рыба": ("UNIT_PRICE_REQUIRED", "Typically by kg"),
    "Копчёная рыба": ("PRODUCT_DECISION", "Piece vs kg"),
    "Солёная рыба": ("PRODUCT_DECISION", "Piece vs kg"),
    "Морепродукты": ("UNIT_PRICE_REQUIRED", "Typically by kg"),
    "Икра": ("UNIT_PRICE_REQUIRED", "Typically by г / кг"),
    "Другая рыба": ("PRODUCT_DECISION", "Open set"),
    # honey
    "Мёд": ("UNIT_PRICE_REQUIRED", "Typically by кг / л"),
    "Соты": ("PRODUCT_DECISION", "Frame/piece vs weight"),
    "Перга": ("UNIT_PRICE_REQUIRED", "Typically by кг / г"),
    "Прополис": ("PRODUCT_DECISION", "Small piece vs weight"),
    "Пыльца": ("UNIT_PRICE_REQUIRED", "Typically by кг / г"),
    "Другие продукты пчеловодства": ("PRODUCT_DECISION", "Open set"),
    # nuts
    "Грецкий орех": ("UNIT_PRICE_REQUIRED", "Typically by кг"),
    "Миндаль": ("UNIT_PRICE_REQUIRED", "Typically by кг"),
    "Фисташки": ("UNIT_PRICE_REQUIRED", "Typically by кг"),
    "Арахис": ("UNIT_PRICE_REQUIRED", "Typically by кг"),
    "Курага": ("UNIT_PRICE_REQUIRED", "Typically by кг"),
    "Изюм": ("UNIT_PRICE_REQUIRED", "Typically by кг"),
    "Чернослив": ("UNIT_PRICE_REQUIRED", "Typically by кг"),
    "Финики": ("UNIT_PRICE_REQUIRED", "Typically by кг"),
    "Другие орехи и сухофрукты": ("PRODUCT_DECISION", "Open set"),
    # grocery grains/pasta — often packaged (ITEM) but bulk exists
    "Рис": ("PRODUCT_DECISION", "Pack vs bulk kg"),
    "Гречка": ("PRODUCT_DECISION", "Pack vs bulk kg"),
    "Овсянка": ("ITEM_PRICE", "Usually branded pack"),
    "Манка": ("ITEM_PRICE", "Usually branded pack"),
    "Пшено": ("PRODUCT_DECISION", "Pack vs bulk"),
    "Мука": ("PRODUCT_DECISION", "Pack vs мешок"),
    "Макароны": ("ITEM_PRICE", "Usually pack"),
    "Лапша": ("ITEM_PRICE", "Usually pack"),
    "Другие крупы": ("PRODUCT_DECISION", "Open set"),
    # oils
    "Подсолнечное масло": ("PRODUCT_DECISION", "Bottle (ITEM) vs bulk л"),
    "Оливковое масло": ("ITEM_PRICE", "Usually bottle"),
    "Кукурузное масло": ("ITEM_PRICE", "Usually bottle"),
    "Сливочное масло": ("UNIT_PRICE_REQUIRED", "Often by кг / pack weight"),
    "Топлёное масло": ("UNIT_PRICE_REQUIRED", "Often by кг"),
    "Сало": ("UNIT_PRICE_REQUIRED", "Often by кг"),
    "Другие масла и жиры": ("PRODUCT_DECISION", "Open set"),
    # spices — small packs usually ITEM
    "Чёрный перец": ("ITEM_PRICE", "Small pack / jar"),
    "Зира": ("PRODUCT_DECISION", "Pack vs bulk г/кг"),
    "Лавровый лист": ("ITEM_PRICE", "Small pack"),
    "Смеси приправ": ("ITEM_PRICE", "Pack"),
    "Соль": ("ITEM_PRICE", "Pack"),
    "Другие специи": ("PRODUCT_DECISION", "Open set"),
    # grocery
    "Сахар": ("PRODUCT_DECISION", "Pack vs мешок"),
    "Уксус": ("ITEM_PRICE", "Bottle"),
    "Томатная паста": ("ITEM_PRICE", "Jar/pack"),
    "Соусы": ("ITEM_PRICE", "Bottle/jar"),
    "Дрожжи": ("ITEM_PRICE", "Pack"),
    "Крахмал": ("ITEM_PRICE", "Pack"),
    "Другая бакалея": ("PRODUCT_DECISION", "Open set"),
    # sweets
    "Шоколад": ("ITEM_PRICE", "Bar/pack"),
    "Конфеты": ("PRODUCT_DECISION", "Box (ITEM) vs кг"),
    "Печенье": ("ITEM_PRICE", "Pack"),
    "Торты и пирожные": ("ITEM_PRICE", "Piece / cake"),
    "Варенье": ("ITEM_PRICE", "Jar"),
    "Халва": ("PRODUCT_DECISION", "Piece vs кг"),
    "Другие сладости": ("PRODUCT_DECISION", "Open set"),
    # bakery
    "Хлеб": ("ITEM_PRICE", "Loaf"),
    "Лепёшки": ("ITEM_PRICE", "Piece"),
    "Самса": ("ITEM_PRICE", "Piece / portion"),
    "Булочки": ("ITEM_PRICE", "Piece"),
    "Лаваш": ("ITEM_PRICE", "Piece / pack"),
    "Другая выпечка": ("ITEM_PRICE", "Piece / pack"),
    # snacks
    "Чипсы": ("ITEM_PRICE", "Pack"),
    "Сухарики": ("ITEM_PRICE", "Pack"),
    "Семечки": ("PRODUCT_DECISION", "Pack vs кг"),
    "Курт": ("PRODUCT_DECISION", "Pack vs кг"),
    "Другие снеки": ("PRODUCT_DECISION", "Open set"),
    # semi / frozen / canned / sausage — usually packaged
    "Пельмени": ("ITEM_PRICE", "Pack"),
    "Вареники": ("ITEM_PRICE", "Pack"),
    "Котлеты": ("ITEM_PRICE", "Pack / portion"),
    "Голубцы": ("ITEM_PRICE", "Pack / portion"),
    "Тесто": ("ITEM_PRICE", "Pack"),
    "Другие полуфабрикаты": ("ITEM_PRICE", "Pack"),
    "Замороженные овощи": ("ITEM_PRICE", "Pack"),
    "Замороженные ягоды": ("ITEM_PRICE", "Pack"),
    "Мороженое": ("ITEM_PRICE", "Pack / portion"),
    "Замороженное тесто": ("ITEM_PRICE", "Pack"),
    "Другие замороженные продукты": ("ITEM_PRICE", "Pack"),
    "Овощные консервы": ("ITEM_PRICE", "Jar/can"),
    "Мясные консервы": ("ITEM_PRICE", "Can"),
    "Рыбные консервы": ("ITEM_PRICE", "Can"),
    "Соленья": ("ITEM_PRICE", "Jar"),
    "Домашние компоты": ("ITEM_PRICE", "Jar"),
    "Другие консервы": ("ITEM_PRICE", "Jar/can"),
    "Варёная колбаса": ("PRODUCT_DECISION", "Stick (ITEM) vs кг"),
    "Копчёная колбаса": ("PRODUCT_DECISION", "Stick vs кг"),
    "Сосиски и сардельки": ("ITEM_PRICE", "Pack"),
    "Ветчина": ("PRODUCT_DECISION", "Piece vs кг"),
    "Казы": ("PRODUCT_DECISION", "Piece vs кг"),
    "Другие деликатесы": ("PRODUCT_DECISION", "Open set"),
    # ready food
    "Плов": ("ITEM_PRICE", "Portion / container"),
    "Манты": ("ITEM_PRICE", "Portion"),
    "Салаты": ("ITEM_PRICE", "Container / portion"),
    "Первые блюда": ("ITEM_PRICE", "Portion"),
    "Вторые блюда": ("ITEM_PRICE", "Portion"),
    "Другая готовая еда": ("ITEM_PRICE", "Portion"),
    # tea/coffee
    "Листовой чай": ("ITEM_PRICE", "Pack"),
    "Чай в пакетиках": ("ITEM_PRICE", "Pack"),
    "Кофе в зёрнах": ("PRODUCT_DECISION", "Pack vs кг"),
    "Молотый кофе": ("ITEM_PRICE", "Pack"),
    "Растворимый кофе": ("ITEM_PRICE", "Jar/pack"),
    "Какао": ("ITEM_PRICE", "Pack"),
    "Другой чай и кофе": ("PRODUCT_DECISION", "Open set"),
    # drinks
    "Вода": ("ITEM_PRICE", "Bottle"),
    "Соки": ("ITEM_PRICE", "Bottle/pack"),
    "Газированные напитки": ("ITEM_PRICE", "Bottle"),
    "Энергетики": ("ITEM_PRICE", "Can"),
    "Максым и жарма": ("PRODUCT_DECISION", "Bottle vs л bulk"),
    "Пиво": ("ITEM_PRICE", "Bottle/can"),
    "Вино": ("ITEM_PRICE", "Bottle"),
    "Крепкий алкоголь": ("ITEM_PRICE", "Bottle"),
    "Другие напитки": ("PRODUCT_DECISION", "Open set"),
    # crops — agri commodity
    "Пшеница": ("UNIT_PRICE_REQUIRED", "Commodity by кг / тонна / мешок"),
    "Ячмень": ("UNIT_PRICE_REQUIRED", "Commodity by кг / тонна / мешок"),
    "Кукуруза": ("UNIT_PRICE_REQUIRED", "Commodity by кг / тонна"),
    "Овёс": ("UNIT_PRICE_REQUIRED", "Commodity by кг / тонна"),
    "Подсолнечник": ("UNIT_PRICE_REQUIRED", "Commodity by кг / тонна"),
    "Нут": ("UNIT_PRICE_REQUIRED", "Commodity by кг / мешок"),
    "Другое зерно": ("UNIT_PRICE_REQUIRED", "Commodity unit needed"),
    # other
    "Пищевой лёд": ("PRODUCT_DECISION", "Bag vs кг"),
    "Сухое молоко": ("PRODUCT_DECISION", "Retail pack vs industrial — Materials overlap risk"),
    "Другие продукты": ("PRODUCT_DECISION", "Open set"),
}

# Smallest unit sets proposed ONLY for UNIT_PRICE_REQUIRED (not implemented).
FOOD_AGRI_UNIT_NEED: dict[str, tuple[str, ...]] = {
    # produce / meat / dairy / fish / honey / nuts / oils / crops defaults
    "Помидоры": ("кг",),
    "Огурцы": ("кг",),
    "Картофель": ("кг", "мешок"),
    "Лук": ("кг", "мешок"),
    "Морковь": ("кг",),
    "Болгарский перец": ("кг",),
    "Яблоки": ("кг",),
    "Виноград": ("кг",),
    "Ягоды": ("кг",),
    "Говядина": ("кг",),
    "Баранина": ("кг",),
    "Конина": ("кг",),
    "Свинина": ("кг",),
    "Фарш": ("кг",),
    "Субпродукты": ("кг",),
    "Молоко": ("л",),
    "Кефир": ("л",),
    "Сметана": ("кг",),
    "Творог": ("кг",),
    "Каймак": ("кг",),
    "Кумыс": ("л",),
    "Чалап": ("л",),
    "Свежая рыба": ("кг",),
    "Морепродукты": ("кг",),
    "Икра": ("г", "кг"),
    "Мёд": ("кг", "л"),
    "Перга": ("г", "кг"),
    "Пыльца": ("г", "кг"),
    "Грецкий орех": ("кг",),
    "Миндаль": ("кг",),
    "Фисташки": ("кг",),
    "Арахис": ("кг",),
    "Курага": ("кг",),
    "Изюм": ("кг",),
    "Чернослив": ("кг",),
    "Финики": ("кг",),
    "Сливочное масло": ("кг",),
    "Топлёное масло": ("кг",),
    "Сало": ("кг",),
    "Пшеница": ("кг", "мешок", "тонна"),
    "Ячмень": ("кг", "мешок", "тонна"),
    "Кукуруза": ("кг", "мешок", "тонна"),
    "Овёс": ("кг", "мешок", "тонна"),
    "Подсолнечник": ("кг", "мешок", "тонна"),
    "Нут": ("кг", "мешок"),
    "Другое зерно": ("кг", "мешок", "тонна"),
}

# Package A — Price Basis (optional for ALL kinds; visibility not gated by audit matrix).
FOOD_AGRI_PRICE_BASIS_FIELD_KEY = "price_basis"
FOOD_AGRI_PRICE_BASIS_FIELD_LABEL = "Цена за"
FOOD_AGRI_PRICE_BASIS_FIELD_TYPE = "enum"
FOOD_AGRI_PRICE_BASIS_REQUIRED = False
# Stable values == display labels (AiVai goods enum convention).
FOOD_AGRI_PRICE_BASIS_OPTIONS: tuple[str, ...] = (
    "кг",
    "г",
    "л",
    "мл",
    "шт.",
    "упаковку",
    "мешок",
    "ящик",
    "тонну",
    "Другое",
)
# Legacy audit alias (not production visibility authority).
FOOD_AGRI_PRICE_BASIS_OPTIONS_CLOSED = FOOD_AGRI_PRICE_BASIS_OPTIONS

FOOD_AGRI_RECOMMENDED_PRICE_MODEL = "B"

# Approved Food domain seller override (single catalog, all 23 L2 / 158 kinds).
FOOD_AGRI_SELLER_CHOICES: tuple[str, ...] = (
    "Частное лицо",
    "Фермер",
    "Магазин",
    "Другой",
)
FOOD_AGRI_SELLER_STANDARD_GOODS: tuple[str, ...] = (
    "Частное лицо",
    "Магазин",
    "Другой",
)
FOOD_AGRI_SELLER_RECOMMENDED_OVERRIDE = FOOD_AGRI_SELLER_CHOICES
FOOD_AGRI_SELLER_RECOMMENDATION = "FOOD_DOMAIN_OVERRIDE"
FOOD_AGRI_SELLER_DROP_SECTION_ROLES: frozenset[str] = frozenset(
    {"Пекарня", "Кафе", "Оптовик", "Производитель"}
)

FOOD_AGRI_CONTACT_MUST_MATCH_SHARED = True
FOOD_AGRI_NEGOTIABLE_MUST_MATCH_SHARED = True

FOOD_AGRI_CREATE_FORBIDDEN: frozenset[str] = frozenset(
    {
        "condition",
        "quantity",
        "weight",
        "volume",
        "packaging",
        "brand",
        "origin",
        "producer",
        "organic",
        "eco",
        "expiry",
        "freshness",
        "wholesale",
        "min_order",
        "minimum_order",
        "unit",
        "amount",
    }
)

_ALWAYS_CREATE: frozenset[str] = frozenset(
    {
        FOOD_AGRI_KIND_KEY,
        FOOD_AGRI_SELLER_KEY,
        "price",
        FOOD_AGRI_PRICE_BASIS_FIELD_KEY,
        "negotiable",
        "contact_methods",
    }
)

# --- Package B Search SoT (Create ≠ Search) ---
# Geo region/city = shared Search UX (not leaf EAV CategoryFilter rows).
FOOD_AGRI_V2_SEARCH_ALLOWLIST: frozenset[str] = frozenset(
    {
        FOOD_AGRI_KIND_KEY,
        FOOD_AGRI_SELLER_KEY,
        "region",
        "city",
    }
)

FOOD_AGRI_V2_SEARCH_EAV_KEYS: frozenset[str] = frozenset(
    {
        FOOD_AGRI_KIND_KEY,
        FOOD_AGRI_SELLER_KEY,
    }
)

FOOD_AGRI_V2_SEARCH_EXCLUDE: frozenset[str] = frozenset(
    set(FOOD_AGRI_CREATE_FORBIDDEN)
    | {
        "price",
        FOOD_AGRI_PRICE_BASIS_FIELD_KEY,
        "negotiable",
        "contact_methods",
        "currency",
        "title",
        "description",
        "photos",
        "opt",
        "wholesale_price",
    }
)

# Legacy alias kept for Package A tests / docs (geo = shared region+city UX).
FOOD_AGRI_V2_SEARCH_POLICY_PREP: frozenset[str] = frozenset(
    {FOOD_AGRI_KIND_KEY, FOOD_AGRI_SELLER_KEY, "geo"}
)


def _choices(*labels: str) -> dict[str, Any]:
    return {"choices": [{"value": label, "label": label} for label in labels]}


def _dep_field(
    key: str,
    label: str,
    ftype: CategoryFieldType,
    required: bool,
    sort: int,
    options: dict[str, Any] | None,
    hint: str | None = None,
) -> tuple:
    return (key, label, ftype, required, sort, options, hint)


def _food_sections() -> dict[str, dict[str, Any]]:
    from app.seeds.food_sections_catalog import FOOD_SECTIONS

    return FOOD_SECTIONS


def food_agri_v2_kind_count() -> int:
    sections = _food_sections()
    return sum(len(cat["roles"]) for cat in sections.values())


def food_agri_v2_all_kinds() -> list[str]:
    out: list[str] = []
    for cat in _food_sections().values():
        for role in cat["roles"]:
            out.append(str(role["label"]))
    return out


def food_agri_v2_assert_contracts() -> None:
    sections = _food_sections()
    if len(sections) != FOOD_AGRI_V2_EXPECTED_L2_COUNT:
        raise RuntimeError(
            f"Food/Agri expected {FOOD_AGRI_V2_EXPECTED_L2_COUNT} sections, "
            f"got {len(sections)}"
        )
    catalog_slugs = {cat["category_slug"] for cat in sections.values()}
    if catalog_slugs != FOOD_AGRI_V2_CANONICAL_SLUGS:
        raise RuntimeError("Food/Agri catalog slugs ≠ canonical L2 set")
    if catalog_slugs & FOOD_AGRI_V2_RETIRED_SLUGS:
        raise RuntimeError("Food/Agri catalog resurrects retired slugs")
    kinds = food_agri_v2_all_kinds()
    if len(kinds) != FOOD_AGRI_V2_EXPECTED_KIND_COUNT:
        raise RuntimeError(
            f"Food/Agri expected {FOOD_AGRI_V2_EXPECTED_KIND_COUNT} kinds, "
            f"got {len(kinds)}"
        )
    if len(kinds) != len(set(kinds)):
        raise RuntimeError("Food/Agri duplicate kinds across sections")
    if FOOD_AGRI_CONDITION_APPROVED_KINDS:
        raise RuntimeError("Food/Agri Condition must stay absent (empty allowlist)")
    banned_sellers = FOOD_AGRI_SELLER_DROP_SECTION_ROLES
    for cat in sections.values():
        for group in cat.get("filters") or []:
            if group.get("label") not in {"Продавец", "Кто продаёт"}:
                continue
            for opt in group.get("options") or []:
                label = str(opt.get("label") or opt.get("value") or "")
                if label in banned_sellers:
                    raise RuntimeError(
                        f"Food/Agri section catalog still has banned seller {label}"
                    )


def build_food_agri_v2_core_fields() -> dict[str, list]:
    """Create cores for all 23 canonical Food/Agri L2 (Package A SoT)."""
    food_agri_v2_assert_contracts()
    sections = _food_sections()
    out: dict[str, list] = {}

    for section_key, slug in FOOD_AGRI_V2_SECTION_SLUGS.items():
        catalog = sections[section_key]
        kinds = [str(r["label"]) for r in catalog["roles"]]
        fields: list = [
            _dep_field(
                FOOD_AGRI_KIND_KEY,
                FOOD_AGRI_KIND_LABEL,
                CategoryFieldType.enum,
                True,
                10,
                _choices(*kinds),
                hint=str(catalog.get("question") or "Какой товар?"),
            ),
            _dep_field(
                FOOD_AGRI_SELLER_KEY,
                FOOD_AGRI_SELLER_LABEL,
                CategoryFieldType.enum,
                True,
                20,
                _choices(*FOOD_AGRI_SELLER_CHOICES),
            ),
            (
                "price",
                "Цена",
                CategoryFieldType.price,
                True,
                30,
                None,
                "Цена товара (СОМ / KGS)",
            ),
            _dep_field(
                FOOD_AGRI_PRICE_BASIS_FIELD_KEY,
                FOOD_AGRI_PRICE_BASIS_FIELD_LABEL,
                CategoryFieldType.enum,
                False,
                40,
                _choices(*FOOD_AGRI_PRICE_BASIS_OPTIONS),
                hint="Необязательно. Другое → уточните в описании",
            ),
            _dep_field(
                "negotiable",
                "Торг",
                CategoryFieldType.enum,
                False,
                50,
                _choices(*GOODS_NEGOTIABLE_CHOICES),
            ),
            _dep_field(
                "contact_methods",
                "Способы связи",
                CategoryFieldType.enum,
                True,
                60,
                _choices(*CONTACT_METHOD_CHOICES),
            ),
        ]

        for row in fields:
            key = row[0]
            if key in FOOD_AGRI_CREATE_FORBIDDEN:
                raise RuntimeError(f"forbidden Create field {slug}.{key}")
            if key not in _ALWAYS_CREATE:
                raise RuntimeError(f"unapproved Create field {slug}.{key}")
            opts = row[5]
            if opts and opts.get("choices") is not None and len(opts["choices"]) == 0:
                raise RuntimeError(f"empty picker {slug}.{key}")

        out[slug] = fields
    return out


def food_agri_v2_all_kind_audit() -> list[dict[str, Any]]:
    """Programmatic all-kind audit for Package A (independent of Flutter)."""
    cores = build_food_agri_v2_core_fields()
    rows: list[dict[str, Any]] = []
    sections = _food_sections()
    for section_key, slug in FOOD_AGRI_V2_SECTION_SLUGS.items():
        catalog = sections[section_key]
        fields = cores[slug]
        keys = [r[0] for r in fields]
        kind_row = next(r for r in fields if r[0] == FOOD_AGRI_KIND_KEY)
        seller_row = next(r for r in fields if r[0] == FOOD_AGRI_SELLER_KEY)
        basis_row = next(r for r in fields if r[0] == FOOD_AGRI_PRICE_BASIS_FIELD_KEY)
        kind_opts = [c["value"] for c in kind_row[5]["choices"]]
        seller_opts = [c["value"] for c in seller_row[5]["choices"]]
        basis_opts = [c["value"] for c in basis_row[5]["choices"]]
        for role in catalog["roles"]:
            kind = str(role["label"])
            rows.append(
                {
                    "kind": kind,
                    "section": section_key,
                    "slug": slug,
                    "food_kind_valid": kind in kind_opts,
                    "seller": seller_opts,
                    "price": "price" in keys,
                    "price_basis": FOOD_AGRI_PRICE_BASIS_FIELD_KEY in keys,
                    "price_basis_options": basis_opts,
                    "condition": "condition" in keys,
                    "forbidden": sorted(set(keys) & FOOD_AGRI_CREATE_FORBIDDEN),
                    "components": {
                        FOOD_AGRI_KIND_KEY: "enum",
                        FOOD_AGRI_SELLER_KEY: "enum",
                        "price": "price",
                        FOOD_AGRI_PRICE_BASIS_FIELD_KEY: "enum",
                        "negotiable": "enum",
                        "contact_methods": "enum",
                    },
                }
            )
    return rows


def food_agri_v2_search_policy_prep() -> dict[str, Any]:
    """Explicit Search allowlist (Package B)."""
    return {
        "allow": sorted(FOOD_AGRI_V2_SEARCH_ALLOWLIST),
        "eav": sorted(FOOD_AGRI_V2_SEARCH_EAV_KEYS),
        "exclude": sorted(FOOD_AGRI_V2_SEARCH_EXCLUDE),
        "legacy_prep": sorted(FOOD_AGRI_V2_SEARCH_POLICY_PREP),
    }


def food_agri_v2_complexity_histogram() -> dict[str, int]:
    """Specials over shared base: food_kind + optional price_basis → bucket 2."""
    kinds = food_agri_v2_all_kinds()
    return {"0": 0, "1": 0, "2": len(kinds), "3": 0, "4": 0, "5+": 0}


def _search_filter(
    key: str,
    label: str,
    ftype: CategoryFilterType,
    sort: int,
    config: dict[str, Any] | None,
) -> tuple:
    return (key, label, ftype, sort, config)


def build_food_agri_v2_search_filters() -> dict[str, list]:
    """Package B Search SoT per canonical Food/Agri L2.

    Explicit allowlist only: food_kind + seller_type.
    price_basis / price / negotiable / contacts / forbidden never Search.
    Geo is shared Search UX, not CategoryFilter rows.
    """
    cores = build_food_agri_v2_core_fields()
    out: dict[str, list] = {}
    for slug, fields in cores.items():
        filters: list = []
        for key, label, _ftype, _required, sort, options, _hint in fields:
            if key not in FOOD_AGRI_V2_SEARCH_EAV_KEYS:
                continue
            if key in FOOD_AGRI_V2_SEARCH_EXCLUDE:
                continue
            if key not in FOOD_AGRI_V2_SEARCH_ALLOWLIST:
                continue
            cfg: dict[str, Any] | None = None
            if options:
                cfg = dict(options)
                if "choices" in cfg and "options" not in cfg:
                    cfg["options"] = list(cfg["choices"])
            filters.append(
                _search_filter(
                    key,
                    label,
                    CategoryFilterType.multi_select,
                    int(sort),
                    cfg,
                )
            )
        out[slug] = filters
    if set(out) != FOOD_AGRI_V2_CANONICAL_SLUGS:
        raise RuntimeError(
            "Food Search filter map != canonical L2 slugs: "
            f"extra={sorted(set(out) - FOOD_AGRI_V2_CANONICAL_SLUGS)} "
            f"missing={sorted(FOOD_AGRI_V2_CANONICAL_SLUGS - set(out))}"
        )
    return out


def food_agri_v2_search_kind_audit_row(slug: str, kind: str) -> dict[str, Any]:
    """All-kind Search audit row (independent of Create visible_components)."""
    return {
        "l2": slug,
        "kind": kind,
        "search_food_kind": "YES",
        "search_seller": "YES",
        "search_price_basis": "NO",
        "search_condition": "NO",
        "search_quantity": "NO",
        "retired_resurrected": slug in FOOD_AGRI_V2_RETIRED_SLUGS,
        "visible_search_keys": [
            FOOD_AGRI_KIND_KEY,
            FOOD_AGRI_SELLER_KEY,
        ],
    }


def food_agri_v2_all_search_kind_audit() -> list[dict[str, Any]]:
    return [
        food_agri_v2_search_kind_audit_row(slug, kind)
        for slug in sorted(FOOD_AGRI_V2_CANONICAL_SLUGS)
        for kind in food_agri_v2_section_kinds(slug)
    ]


def food_agri_v2_section_kinds(slug: str) -> list[str]:
    """Kinds for a canonical L2 slug (from FOOD_SECTIONS)."""
    sections = _food_sections()
    for section_key, section_slug in FOOD_AGRI_V2_SECTION_SLUGS.items():
        if section_slug != slug:
            continue
        catalog = sections[section_key]
        return [str(role["label"]) for role in catalog["roles"]]
    return []
