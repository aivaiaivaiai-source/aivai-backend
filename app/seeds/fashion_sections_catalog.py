# -*- coding: utf-8 -*-
"""Продажа «Одежда, обувь и аксессуары».

Вид — сама вещь. Детская одежда, обувь и школьная форма остаются в
«Детском мире». Строительные костюмы, каски и спецобувь — в ремонте.
Умные часы — в электронике. Украшения для пирсинга / косметички — Fashion
ownership (Beauty V2 removed them; exact Fashion kinds may be GAP until Fashion work).
Шырдаки и юрты — в хобби. Пряжа и рукоделие тоже остаются там.
Медицинская одежда — в медтоварах.
"""
from __future__ import annotations

from typing import Any


def _item(
    label: str,
    parent: str | None = None,
    kinds: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {"value": label, "label": label}
    if parent:
        row["parent"] = parent
    if kinds:
        row["for_kinds"] = list(kinds)
    return row


def _opts(*labels: str) -> list[dict[str, Any]]:
    return [_item(label) for label in labels]


def _group(
    label: str,
    options: tuple[str, ...] | list[dict[str, Any]],
    kinds: tuple[str, ...] | None = None,
    depends_on: str | None = None,
) -> dict[str, Any]:
    group: dict[str, Any] = {
        "label": label,
        "options": list(options) if options and isinstance(options[0], dict) else _opts(*options),  # type: ignore[index]
    }
    if kinds:
        group["applies_to"] = list(kinds)
    if depends_on:
        group["depends_on"] = depends_on
    return group


def _seller() -> dict[str, Any]:
    return _group("Продавец", ("Частное лицо", "Магазин", "Другой"))


def _condition() -> dict[str, Any]:
    return _group("Состояние", ("Новое", "Б/у"))


def _section(slug: str, label: str, kinds: tuple[str, ...], filters: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "category_slug": slug,
        "label": label,
        "question": "Какой товар?",
        "roles": _opts(*kinds),
        "filters": filters,
    }


_W_SIZE = ("40", "42", "44", "46", "48", "50", "52", "54", "56", "58", "60", "62", "64", "66")
_M_SIZE = ("46", "48", "50", "52", "54", "56", "58", "60", "62", "64", "66")
_SEASON = ("Лето", "Демисезон", "Зима")
_W_SHOE = ("35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46")
_M_SHOE = ("39", "40", "41", "42", "43", "44", "45", "46")

_W_CLOTHES = (
    "Платья",
    "Юбки",
    "Блузки и рубашки",
    "Футболки и топы",
    "Женские джинсы",
    "Женские брюки",
    "Кофты и кардиганы",
    "Женская верхняя одежда",
    "Женские костюмы",
)
_M_CLOTHES = (
    "Рубашки",
    "Футболки и поло",
    "Мужские джинсы",
    "Мужские брюки",
    "Пиджаки и костюмы",
    "Мужская верхняя одежда",
    "Свитеры и толстовки",
    "Шорты",
)

FASHION_SECTIONS: dict[str, dict[str, Any]] = {
    "women": _section(
        "fashion-zhenskaya-odezhda",
        "Женская одежда",
        (*_W_CLOTHES, "Другая женская одежда"),
        [
            _seller(),
            _condition(),
            _group("Размер", _W_SIZE),
            _group("Сезон", _SEASON, ("Женская верхняя одежда",)),
        ],
    ),
    "men": _section(
        "fashion-muzhskaya-odezhda",
        "Мужская одежда",
        (*_M_CLOTHES, "Другая мужская одежда"),
        [
            _seller(),
            _condition(),
            _group("Размер", _M_SIZE),
            _group("Сезон", _SEASON, ("Мужская верхняя одежда",)),
        ],
    ),
    "maternity": _section(
        "fashion-odezhda-dlya-beremennyh-kormyaschih",
        "Одежда для беременных/кормящих",
        (
            "Платья для беременных",
            "Брюки для беременных",
            "Бельё для кормления",
            "Кофты для беременных",
            "Другая одежда для беременных",
        ),
        [
            _seller(),
            _condition(),
            _group("Размер", _W_SIZE),
        ],
    ),
    "underwear": _section(
        "fashion-nizhnee-bele",
        "Нижнее бельё",
        (
            "Бюстгальтеры",
            "Трусы",
            "Комплекты белья",
            "Носки",
            "Колготки",
            "Боди",
            "Другое бельё",
        ),
        [
            _seller(),
            _condition(),
            _group("Пол", ("Женское", "Мужское"), ("Трусы", "Носки", "Комплекты белья")),
            _group("Размер", ("70B", "75B", "75C", "80B", "80C", "85C"), ("Бюстгальтеры",)),
            _group("Размер белья", _W_SIZE, ("Трусы", "Комплекты белья", "Носки", "Боди")),
        ],
    ),
    "homewear": _section(
        "fashion-domashnyaya-odezhda",
        "Домашняя одежда",
        ("Пижамы", "Домашние халаты", "Домашние костюмы", "Другая домашняя одежда"),
        [
            _seller(),
            _condition(),
            _group("Пол", ("Женская", "Мужская")),
            _group("Размер", _W_SIZE),
        ],
    ),
    "muslim": _section(
        "fashion-musulmanskaya-odezhda-aksessuary",
        "Мусульманская одежда/аксессуары",
        (
            "Хиджабы",
            "Абайи",
            "Платья для намаза",
            "Намазники",
            "Коврики для намаза",
            "Другие мусульманские товары",
        ),
        [
            _seller(),
            _condition(),
            _group("Размер", _W_SIZE, ("Абайи", "Платья для намаза", "Намазники")),
        ],
    ),
    "women-shoes": _section(
        "fashion-zhenskaya-obuv",
        "Женская обувь",
        (
            "Туфли",
            "Босоножки",
            "Балетки",
            "Сапоги",
            "Женские ботинки",
            "Женские кроссовки",
            "Женские кеды",
            "Лоферы",
            "Женские тапочки",
            "Другая женская обувь",
        ),
        [
            _seller(),
            _condition(),
            _group("Размер", _W_SHOE),
            _group("Сезон", _SEASON, ("Босоножки", "Сапоги", "Женские ботинки", "Женские кроссовки")),
        ],
    ),
    "men-shoes": _section(
        "fashion-muzhskaya-obuv",
        "Мужская обувь",
        (
            "Мужские туфли",
            "Мужские кроссовки",
            "Мужские ботинки",
            "Мужские кеды",
            "Сандалии",
            "Мужские тапочки",
            "Другая мужская обувь",
        ),
        [
            _seller(),
            _condition(),
            _group("Размер", _M_SHOE),
            _group("Сезон", _SEASON, ("Мужские ботинки", "Сандалии", "Мужские кроссовки")),
        ],
    ),
    "bags": _section(
        "fashion-sumki-i-chemodany",
        "Сумки и чемоданы",
        (
            "Женские сумки",
            "Клатчи",
            "Рюкзаки",
            "Чемоданы",
            "Дорожные сумки",
            "Кошельки",
            "Барсетки",
            "Другие сумки",
        ),
        [
            _seller(),
            _condition(),
            _group("Размер", ("Ручная кладь", "Средний", "Большой"), ("Чемоданы", "Дорожные сумки")),
        ],
    ),
    "jewelry": _section(
        "fashion-ukrasheniya-i-bizhuteriya",
        "Украшения и бижутерия",
        ("Кольца", "Серьги", "Цепочки", "Браслеты", "Подвески", "Бижутерия", "Другие украшения"),
        [
            _seller(),
            _condition(),
            _group(
                "Материал",
                ("Золото 585", "Серебро 925", "Сталь", "Бижутерный сплав"),
                ("Кольца", "Серьги", "Цепочки", "Браслеты", "Подвески"),
            ),
        ],
    ),
    "watches": _section(
        "fashion-chasy",
        "Часы",
        ("Мужские наручные часы", "Женские наручные часы", "Другие часы"),
        [
            _seller(),
            _condition(),
            _group("Механизм", ("Кварцевые", "Механические", "Электронные")),
        ],
    ),
    "accessories": _section(
        "fashion-aksessuary",
        "Аксессуары",
        (
            "Ремни",
            "Солнцезащитные очки",
            "Шарфы и платки",
            "Перчатки",
            "Шапки",
            "Кепки и бейсболки",
            "Галстуки",
            "Зонты",
            "Другие аксессуары",
        ),
        [
            _seller(),
            _condition(),
            _group("Пол", ("Женские", "Мужские"), ("Ремни", "Шапки", "Перчатки", "Шарфы и платки")),
            _group("Сезон", _SEASON, ("Шарфы и платки", "Перчатки", "Шапки")),
        ],
    ),
    "uniform": _section(
        "fashion-spetsodezhda-i-uniforma",
        "Спецодежда и униформа",
        (
            "Форма для общепита",
            "Форма охраны",
            "Форма для салонов",
            "Корпоративная форма",
            "Другая униформа",
        ),
        [
            _seller(),
            _condition(),
            _group("Размер", _W_SIZE),
            _group("Пол", ("Женская", "Мужская")),
        ],
    ),
    "national": _section(
        "fashion-natsionalnaya-odezhda",
        "Национальная одежда",
        ("Калпаки", "Элечек", "Чапаны", "Кёйнёки", "Бельдемчи", "Другая национальная одежда"),
        [
            _seller(),
            _condition(),
            _group("Размер", _W_SIZE, ("Элечек", "Чапаны", "Кёйнёки", "Бельдемчи")),
            _group("Для кого", ("Женская", "Мужская")),
        ],
    ),
    "wedding": _section(
        "fashion-svadebnaya-i-vechernyaya-odezhda",
        "Свадебная и вечерняя одежда",
        (
            "Свадебные платья",
            "Платья для подружек",
            "Вечерние платья",
            "Костюмы жениха",
            "Фата и аксессуары невесты",
            "Другая праздничная одежда",
        ),
        [
            _seller(),
            _condition(),
            _group("Размер", _W_SIZE, ("Свадебные платья", "Платья для подружек", "Вечерние платья")),
            _group("Размер костюма", _M_SIZE, ("Костюмы жениха",)),
        ],
    ),
    "sport": _section(
        "fashion-sportivnaya-odezhda-i-obuv",
        "Спортивная одежда и обувь",
        (
            "Спортивные костюмы",
            "Лосины и леггинсы",
            "Футбольная форма",
            "Ветровки для спорта",
            "Купальники",
            "Плавки",
            "Бутсы",
            "Кроссовки для бега",
            "Другая спортивная одежда",
        ),
        [
            _seller(),
            _condition(),
            _group("Размер одежды", _W_SIZE, ("Спортивные костюмы", "Лосины и леггинсы", "Футбольная форма", "Ветровки для спорта", "Купальники", "Плавки")),
            _group("Размер обуви", _W_SHOE, ("Бутсы", "Кроссовки для бега")),
            _group("Пол", ("Женская", "Мужская"), ("Спортивные костюмы", "Ветровки для спорта", "Бутсы", "Кроссовки для бега")),
        ],
    ),
    "other": _section(
        "fashion-prochee",
        "Прочее",
        ("Дождевики", "Жилеты", "Другие товары одежды"),
        [
            _seller(),
            _condition(),
            _group("Размер", _W_SIZE),
        ],
    ),
}


def build_fashion_section_catalog(section_key: str) -> dict[str, Any] | None:
    return FASHION_SECTIONS.get(section_key)
