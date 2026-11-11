# -*- coding: utf-8 -*-
"""Продажа «Продукты и сельхозтовары» (Food/Agri V2 edible catalog).

Вид — сам продукт. Детские смеси, каши и пюре для прикорма остаются в
«Детском мире». Сено, комбикорм и живые животные — в «Животных».
Пчёлы и ульи — там же, мёд — здесь. Пищевое сырьё для производства —
в сырье. БАДы — в медтоварах.
Опт / эко / тара — не отдельные L2 (см. food_agri_v2 retired set).
"""
from __future__ import annotations

from typing import Any


def _item(
    label: str,
    kinds: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {"value": label, "label": label}
    if kinds:
        row["for_kinds"] = list(kinds)
    return row


def _opts(*labels: str) -> list[dict[str, Any]]:
    return [_item(label) for label in labels]


def _group(
    label: str,
    options: tuple[str, ...],
    kinds: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    group: dict[str, Any] = {"label": label, "options": _opts(*options)}
    if kinds:
        group["applies_to"] = list(kinds)
    return group


def _section(slug: str, label: str, kinds: tuple[str, ...], filters: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "category_slug": slug,
        "label": label,
        "question": "Какой товар?",
        "roles": _opts(*kinds),
        "filters": filters,
    }


def _seller() -> dict[str, Any]:
    """Package A approved Food seller override — one catalog for all sections."""
    return _group(
        "Кто продаёт",
        ("Частное лицо", "Фермер", "Магазин", "Другой"),
    )


FOOD_SECTIONS: dict[str, dict[str, Any]] = {
    "produce": _section(
        "food-agri-ovoschi-i-frukty",
        "Овощи и фрукты",
        (
            "Помидоры",
            "Огурцы",
            "Картофель",
            "Лук",
            "Морковь",
            "Капуста",
            "Болгарский перец",
            "Зелень",
            "Яблоки",
            "Виноград",
            "Арбузы и дыни",
            "Ягоды",
            "Другие овощи и фрукты",
        ),
        [_seller()],
    ),
    "meat": _section(
        "food-agri-myaso-i-myasnaya-produktsiya",
        "Мясо и мясная продукция",
        (
            "Говядина",
            "Баранина",
            "Конина",
            "Курица",
            "Индейка",
            "Свинина",
            "Фарш",
            "Субпродукты",
            "Другое мясо",
        ),
        [_seller()],
    ),
    "dairy": _section(
        "food-agri-molochnaya-produktsiya",
        "Молочная продукция",
        (
            "Молоко",
            "Кефир",
            "Сметана",
            "Творог",
            "Сыр",
            "Каймак",
            "Кумыс",
            "Чалап",
            "Другая молочная продукция",
        ),
        [_seller()],
    ),
    "eggs": _section(
        "food-agri-yaytsa",
        "Яйца",
        ("Куриные яйца", "Перепелиные яйца", "Индюшиные яйца", "Другие яйца"),
        [_seller()],
    ),
    "fish": _section(
        "food-agri-ryba-i-moreprodukty",
        "Рыба и морепродукты",
        ("Свежая рыба", "Копчёная рыба", "Солёная рыба", "Морепродукты", "Икра", "Другая рыба"),
        [_seller()],
    ),
    "honey": _section(
        "food-agri-med-i-produkty-pchelovodstva",
        "Мёд и продукты пчеловодства",
        ("Мёд", "Соты", "Перга", "Прополис", "Пыльца", "Другие продукты пчеловодства"),
        [_seller()],
    ),
    "nuts": _section(
        "food-agri-orehi-i-suhofrukty",
        "Орехи и сухофрукты",
        (
            "Грецкий орех",
            "Миндаль",
            "Фисташки",
            "Арахис",
            "Курага",
            "Изюм",
            "Чернослив",
            "Финики",
            "Другие орехи и сухофрукты",
        ),
        [_seller()],
    ),
    "grains": _section(
        "food-agri-krupy-muka-makaronnye-izdeliya",
        "Крупы, мука/макаронные изделия",
        ("Рис", "Гречка", "Овсянка", "Манка", "Пшено", "Мука", "Макароны", "Лапша", "Другие крупы"),
        [_seller()],
    ),
    "oils": _section(
        "food-agri-masla-i-zhiry",
        "Масла и жиры",
        (
            "Подсолнечное масло",
            "Оливковое масло",
            "Кукурузное масло",
            "Сливочное масло",
            "Топлёное масло",
            "Сало",
            "Другие масла и жиры",
        ),
        [_seller()],
    ),
    "spices": _section(
        "food-agri-spetsii-pripravy-i-pryanosti",
        "Специи, приправы и пряности",
        ("Чёрный перец", "Зира", "Лавровый лист", "Смеси приправ", "Соль", "Другие специи"),
        [_seller()],
    ),
    "grocery": _section(
        "food-agri-bakaleya-i-produkty-pitaniya",
        "Бакалея и продукты питания",
        ("Сахар", "Уксус", "Томатная паста", "Соусы", "Дрожжи", "Крахмал", "Другая бакалея"),
        [_seller()],
    ),
    "sweets": _section(
        "food-agri-konditerskie-izdeliya-i-sladosti",
        "Кондитерские изделия и сладости",
        ("Шоколад", "Конфеты", "Печенье", "Торты и пирожные", "Варенье", "Халва", "Другие сладости"),
        [_seller()],
    ),
    "bakery": _section(
        "food-agri-hlebobulochnye-izdeliya",
        "Хлебобулочные изделия",
        ("Хлеб", "Лепёшки", "Самса", "Булочки", "Лаваш", "Другая выпечка"),
        [_seller()],
    ),
    "snacks": _section(
        "food-agri-sneki-i-zakuski",
        "Снеки и закуски",
        ("Чипсы", "Сухарики", "Семечки", "Курт", "Другие снеки"),
        [_seller()],
    ),
    "semi": _section(
        "food-agri-polufabrikaty",
        "Полуфабрикаты",
        ("Пельмени", "Вареники", "Котлеты", "Голубцы", "Тесто", "Другие полуфабрикаты"),
        [_seller()],
    ),
    "frozen": _section(
        "food-agri-zamorozhennye-produkty",
        "Замороженные продукты",
        (
            "Замороженные овощи",
            "Замороженные ягоды",
            "Мороженое",
            "Замороженное тесто",
            "Другие замороженные продукты",
        ),
        [_seller()],
    ),
    "canned": _section(
        "food-agri-konservy-i-solenya",
        "Консервы и соленья",
        (
            "Овощные консервы",
            "Мясные консервы",
            "Рыбные консервы",
            "Соленья",
            "Домашние компоты",
            "Другие консервы",
        ),
        [_seller()],
    ),
    "sausage": _section(
        "food-agri-kolbasnye-izdeliya-i-delikatesy",
        "Колбасные изделия и деликатесы",
        (
            "Варёная колбаса",
            "Копчёная колбаса",
            "Сосиски и сардельки",
            "Ветчина",
            "Казы",
            "Другие деликатесы",
        ),
        [_seller()],
    ),
    "ready": _section(
        "food-agri-gotovaya-eda-i-kulinariya",
        "Готовая еда и кулинария",
        ("Плов", "Манты", "Салаты", "Первые блюда", "Вторые блюда", "Другая готовая еда"),
        [_seller()],
    ),
    "tea": _section(
        "food-agri-chay-i-kofe",
        "Чай и кофе",
        (
            "Листовой чай",
            "Чай в пакетиках",
            "Кофе в зёрнах",
            "Молотый кофе",
            "Растворимый кофе",
            "Какао",
            "Другой чай и кофе",
        ),
        [_seller()],
    ),
    "drinks": _section(
        "food-agri-napitki",
        "Напитки",
        (
            "Вода",
            "Соки",
            "Газированные напитки",
            "Энергетики",
            "Максым и жарма",
            "Пиво",
            "Вино",
            "Крепкий алкоголь",
            "Другие напитки",
        ),
        [_seller()],
    ),
    "crops": _section(
        "food-agri-zerno-i-zernovye-kultury",
        "Зерно и зерновые культуры",
        ("Пшеница", "Ячмень", "Кукуруза", "Овёс", "Подсолнечник", "Нут", "Другое зерно"),
        [_seller()],
    ),
    "other": _section(
        "food-agri-prochie-produkty-i-selhoztovary",
        "Прочие продукты и сельхозтовары",
        ("Пищевой лёд", "Сухое молоко", "Другие продукты"),
        [_seller()],
    ),
}


def build_food_section_catalog(section_key: str) -> dict[str, Any] | None:
    return FOOD_SECTIONS.get(section_key)
