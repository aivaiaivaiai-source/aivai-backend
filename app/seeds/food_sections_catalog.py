# -*- coding: utf-8 -*-
"""Продажа «Продукты и сельхозтовары».

Вид — сам продукт. Детские смеси, каши и пюре для прикорма остаются в
«Детском мире». Сено, комбикорм и живые животные — в «Животных».
Пчёлы и ульи — там же, мёд — здесь. Пищевое сырьё для производства —
в сырье. БАДы — в медтоварах.
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


def _farmer() -> dict[str, Any]:
    return _group("Продавец", ("Частное лицо", "Фермер", "Магазин"))


def _shop() -> dict[str, Any]:
    return _group("Продавец", ("Частное лицо", "Магазин", "Другой"))


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
        [_farmer()],
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
        [_farmer()],
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
        [_farmer()],
    ),
    "eggs": _section(
        "food-agri-yaytsa",
        "Яйца",
        ("Куриные яйца", "Перепелиные яйца", "Индюшиные яйца", "Другие яйца"),
        [_farmer()],
    ),
    "fish": _section(
        "food-agri-ryba-i-moreprodukty",
        "Рыба и морепродукты",
        ("Свежая рыба", "Копчёная рыба", "Солёная рыба", "Морепродукты", "Икра", "Другая рыба"),
        [_shop()],
    ),
    "honey": _section(
        "food-agri-med-i-produkty-pchelovodstva",
        "Мёд и продукты пчеловодства",
        ("Мёд", "Соты", "Перга", "Прополис", "Пыльца", "Другие продукты пчеловодства"),
        [_farmer()],
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
        [_farmer()],
    ),
    "grains": _section(
        "food-agri-krupy-muka-makaronnye-izdeliya",
        "Крупы, мука/макаронные изделия",
        ("Рис", "Гречка", "Овсянка", "Манка", "Пшено", "Мука", "Макароны", "Лапша", "Другие крупы"),
        [_shop()],
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
        [_shop()],
    ),
    "spices": _section(
        "food-agri-spetsii-pripravy-i-pryanosti",
        "Специи, приправы и пряности",
        ("Чёрный перец", "Зира", "Лавровый лист", "Смеси приправ", "Соль", "Другие специи"),
        [_shop()],
    ),
    "grocery": _section(
        "food-agri-bakaleya-i-produkty-pitaniya",
        "Бакалея и продукты питания",
        ("Сахар", "Уксус", "Томатная паста", "Соусы", "Дрожжи", "Крахмал", "Другая бакалея"),
        [_shop()],
    ),
    "sweets": _section(
        "food-agri-konditerskie-izdeliya-i-sladosti",
        "Кондитерские изделия и сладости",
        ("Шоколад", "Конфеты", "Печенье", "Торты и пирожные", "Варенье", "Халва", "Другие сладости"),
        [_shop()],
    ),
    "bakery": _section(
        "food-agri-hlebobulochnye-izdeliya",
        "Хлебобулочные изделия",
        ("Хлеб", "Лепёшки", "Самса", "Булочки", "Лаваш", "Другая выпечка"),
        [_group("Продавец", ("Частное лицо", "Пекарня", "Магазин"))],
    ),
    "snacks": _section(
        "food-agri-sneki-i-zakuski",
        "Снеки и закуски",
        ("Чипсы", "Сухарики", "Семечки", "Курт", "Другие снеки"),
        [_shop()],
    ),
    "semi": _section(
        "food-agri-polufabrikaty",
        "Полуфабрикаты",
        ("Пельмени", "Вареники", "Котлеты", "Голубцы", "Тесто", "Другие полуфабрикаты"),
        [_shop()],
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
        [_shop()],
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
        [_shop()],
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
        [_shop()],
    ),
    "ready": _section(
        "food-agri-gotovaya-eda-i-kulinariya",
        "Готовая еда и кулинария",
        ("Плов", "Манты", "Салаты", "Первые блюда", "Вторые блюда", "Другая готовая еда"),
        [_group("Продавец", ("Частное лицо", "Кафе", "Магазин"))],
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
        [_shop()],
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
        [_shop()],
    ),
    "crops": _section(
        "food-agri-zerno-i-zernovye-kultury",
        "Зерно и зерновые культуры",
        ("Пшеница", "Ячмень", "Кукуруза", "Овёс", "Подсолнечник", "Нут", "Другое зерно"),
        [_farmer()],
    ),
    "wholesale": _section(
        "food-agri-optovyy-otdel",
        "Оптовый отдел",
        (
            "Овощи оптом",
            "Фрукты оптом",
            "Мясо оптом",
            "Молочная продукция оптом",
            "Бакалея оптом",
            "Напитки оптом",
            "Другой опт",
        ),
        [_group("Продавец", ("Оптовик", "Фермер", "Магазин"))],
    ),
    "packaging": _section(
        "food-agri-tara-upakovka-dlya-produktsii",
        "Тара/упаковка для продукции",
        (
            "Стеклянные банки",
            "Крышки",
            "Пластиковые бутылки",
            "Ящики",
            "Мешки",
            "Контейнеры",
            "Другая тара",
        ),
        [_group("Продавец", ("Магазин", "Производитель", "Частное лицо"))],
    ),
    "eco": _section(
        "food-agri-ekoprodukty-i-fermerskie-tovary",
        "Экопродукты и фермерские товары",
        ("Фермерские наборы", "Органические наборы", "Другие фермерские товары"),
        [_farmer()],
    ),
    "other": _section(
        "food-agri-prochie-produkty-i-selhoztovary",
        "Прочие продукты и сельхозтовары",
        ("Пищевой лёд", "Сухое молоко", "Другие продукты"),
        [_shop()],
    ),
}


def build_food_section_catalog(section_key: str) -> dict[str, Any] | None:
    return FOOD_SECTIONS.get(section_key)
