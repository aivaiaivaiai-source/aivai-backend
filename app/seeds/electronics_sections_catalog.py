# -*- coding: utf-8 -*-
"""Продажа «Техника и электроника».

Вид — тип техники. Марка и модель зависят друг от друга, как на Lalafo.
Не забирать: котлы, радиаторы, тёплый пол, вентиляционные системы,
водонагреватели, генераторы, кабель и розетки, детские часы, обычные часы,
промышленные швейные машины, кассовую технику.
"""
from __future__ import annotations

from typing import Any

from app.seeds.electronics_catalog_models import (
    ACCESSORY_BRANDS,
    ACCESSORY_MODELS,
    APPLIANCE_BRANDS,
    APPLIANCE_MODELS,
    AUDIO_BRANDS,
    AUDIO_MODELS,
    BUILTIN_BRANDS,
    BUILTIN_MODELS,
    CLIMATE_BRANDS,
    CLIMATE_MODELS,
    COMPUTER_BRANDS,
    COMPUTER_MODELS,
    CONSOLE_BRANDS,
    CONSOLE_MODELS,
    HOME_BRANDS,
    HOME_MODELS,
    KITCHEN_BRANDS,
    KITCHEN_MODELS,
    NETWORK_BRANDS,
    NETWORK_MODELS,
    OFFICE_GEAR_BRANDS,
    OFFICE_GEAR_MODELS,
    OFFICE_PRINT_BRANDS,
    OFFICE_PRINT_MODELS,
    OTHER_BRANDS,
    OTHER_MODELS,
    PARTS_BRANDS,
    PARTS_MODELS,
    PHONE_BRANDS,
    PHONE_MODELS,
    PHOTO_BRANDS,
    PHOTO_MODELS,
    TABLET_BRANDS,
    TABLET_MODELS,
    TV_BRANDS,
    TV_MODELS,
    WEARABLE_BRANDS,
    WEARABLE_MODELS,
)


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


OTHER_BRAND_VALUE = "other_brand"
OTHER_BRAND_LABEL = "Другая марка"
OTHER_MODEL_VALUE = "other_model"
OTHER_MODEL_LABEL = "Другая модель"


def _brands(rows: list[tuple[str, tuple[str, ...] | None]]) -> dict[str, Any]:
    options = [_item(name, kinds=kinds) for name, kinds in rows]
    # Trailing open-catalog fallback — always last, never alphabetical.
    options.append(
        {
            "value": OTHER_BRAND_VALUE,
            "label": OTHER_BRAND_LABEL,
        }
    )
    return {
        "label": "Марка",
        "options": options,
    }


def _models(rows: list[tuple[str, str, tuple[str, ...]]]) -> dict[str, Any]:
    options = [_item(model, parent=brand, kinds=kinds) for brand, model, kinds in rows]
    brand_kinds: dict[str, set[str]] = {}
    brand_order: list[str] = []
    for brand, _model, kinds in rows:
        if brand not in brand_kinds:
            brand_kinds[brand] = set()
            brand_order.append(brand)
        if kinds:
            brand_kinds[brand].update(kinds)
    for brand in brand_order:
        fk = sorted(brand_kinds[brand]) or None
        row: dict[str, Any] = {
            "value": OTHER_MODEL_VALUE,
            "label": OTHER_MODEL_LABEL,
            "parent": brand,
        }
        if fk:
            row["for_kinds"] = list(fk)
        options.append(row)
    return {
        "label": "Модель",
        "depends_on": "Марка",
        "options": options,
    }


def _section(slug: str, label: str, kinds: tuple[str, ...], filters: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "category_slug": slug,
        "label": label,
        "question": "Какой товар?",
        "roles": _opts(*kinds),
        "filters": filters,
    }


_PHONE = ("Смартфоны",)
_BUTTON = ("Кнопочные телефоны",)
_PHONE_ALL = ("Смартфоны", "Кнопочные телефоны")

ELECTRONICS_SECTIONS: dict[str, dict[str, Any]] = {
    "phones": _section(
        "electronics-smartfony-i-telefony",
        "Смартфоны и телефоны",
        ("Смартфоны", "Кнопочные телефоны", "Другие телефоны"),
        [
            _seller(),
            _condition(),
            _brands(PHONE_BRANDS),
            _models(PHONE_MODELS),
            _group("Память", ("64 ГБ", "128 ГБ", "256 ГБ", "512 ГБ", "1 ТБ"), _PHONE),
            _group("ОЗУ", ("4 ГБ", "6 ГБ", "8 ГБ", "12 ГБ"), _PHONE),
        ],
    ),
    "tablets": _section(
        "electronics-planshety-i-elektronnye-knigi",
        "Планшеты и электронные книги",
        ("Планшеты", "Электронные книги", "Другие планшеты и книги"),
        [
            _seller(),
            _condition(),
            _brands(TABLET_BRANDS),
            _models(TABLET_MODELS),
            _group("Экран", ('8"', '10"', '11"', '12.9"'), ("Планшеты",)),
            _group("Память", ("64 ГБ", "128 ГБ", "256 ГБ", "512 ГБ"), ("Планшеты",)),
        ],
    ),
    "computers": _section(
        "electronics-noutbuki-i-kompyutery",
        "Ноутбуки и компьютеры",
        ("Ноутбуки", "Моноблоки", "Системные блоки", "Мониторы", "Другие компьютеры"),
        [
            _seller(),
            _condition(),
            _brands(COMPUTER_BRANDS),
            _models(COMPUTER_MODELS),
            _group("ОЗУ", ("8 ГБ", "16 ГБ", "32 ГБ"), ("Ноутбуки", "Моноблоки", "Системные блоки")),
            _group("Накопитель", ("256 ГБ", "512 ГБ", "1 ТБ"), ("Ноутбуки", "Моноблоки", "Системные блоки")),
            _group("Диагональ", ('14"', '15.6"', '16"', '24"', '27"')),
        ],
    ),
    "parts": _section(
        "electronics-komplektuyuschie-dlya-kompyuterov",
        "Комплектующие для компьютеров",
        (
            "Процессоры",
            "Видеокарты",
            "Оперативная память",
            "Материнские платы",
            "Накопители",
            "Блоки питания",
            "Корпуса",
            "Другие комплектующие",
        ),
        [
            _seller(),
            _condition(),
            _brands(PARTS_BRANDS),
            _models(PARTS_MODELS),
            _group("Объём", ("8 ГБ", "16 ГБ", "32 ГБ", "512 ГБ", "1 ТБ", "2 ТБ"), ("Оперативная память", "Накопители")),
        ],
    ),
    "office-print": _section(
        "electronics-orgtehnika",
        "Оргтехника",
        ("Принтеры", "Сканеры", "МФУ", "Другая оргтехника"),
        [
            _seller(),
            _condition(),
            _brands(OFFICE_PRINT_BRANDS),
            _models(OFFICE_PRINT_MODELS),
            _group("Печать", ("Лазерная", "Струйная"), ("Принтеры", "МФУ")),
        ],
    ),
    "tv": _section(
        "electronics-televizory-i-proektory",
        "Телевизоры и проекторы",
        ("Телевизоры", "Проекторы", "ТВ-приставки", "Другие экраны"),
        [
            _seller(),
            _condition(),
            _brands(TV_BRANDS),
            _models(TV_MODELS),
            _group("Диагональ", ('32"', '43"', '50"', '55"', '65"', '75"'), ("Телевизоры",)),
            _group("Разрешение", ("HD", "Full HD", "4K"), ("Телевизоры", "Проекторы")),
        ],
    ),
    "audio": _section(
        "electronics-audiotehnika",
        "Аудиотехника",
        ("Колонки", "Наушники", "Саундбары", "Музыкальные центры", "Микрофоны", "Другая аудиотехника"),
        [
            _seller(),
            _condition(),
            _brands(AUDIO_BRANDS),
            _models(AUDIO_MODELS),
            _group("Подключение", ("Проводные", "Bluetooth"), ("Колонки", "Наушники")),
        ],
    ),
    "photo": _section(
        "electronics-foto-i-videotehnika",
        "Фото и видеотехника",
        ("Фотоаппараты", "Объективы", "Видеокамеры", "Экшн-камеры", "Квадрокоптеры", "Другая фототехника"),
        [
            _seller(),
            _condition(),
            _brands(PHOTO_BRANDS),
            _models(PHOTO_MODELS),
        ],
    ),
    "consoles": _section(
        "electronics-igrovye-pristavki-i-aksessuary",
        "Игровые приставки и аксессуары",
        ("Игровые приставки", "Геймпады", "Игры", "Другие игровые товары"),
        [
            _seller(),
            _condition(),
            _brands(CONSOLE_BRANDS),
            _models(CONSOLE_MODELS),
        ],
    ),
    "wearables": _section(
        "electronics-umnye-chasy-i-gadzhety",
        "Умные часы и гаджеты",
        ("Умные часы", "Фитнес-браслеты", "VR-очки", "Другие гаджеты"),
        [
            _seller(),
            _condition(),
            _brands(WEARABLE_BRANDS),
            _models(WEARABLE_MODELS),
        ],
    ),
    "network": _section(
        "electronics-setevoe-oborudovanie",
        "Сетевое оборудование",
        ("Роутеры", "Усилители сигнала", "Коммутаторы", "Модемы", "Другое сетевое оборудование"),
        [
            _seller(),
            _condition(),
            _brands(NETWORK_BRANDS),
            _models(NETWORK_MODELS),
            _group("Диапазон", ("2.4 ГГц", "5 ГГц", "Двухдиапазонный"), ("Роутеры", "Усилители сигнала")),
        ],
    ),
    "office-gear": _section(
        "electronics-tehnika-dlya-ofisa",
        "Техника для офиса",
        ("ИБП", "Шредеры", "Брошюровщики", "Другая офисная техника"),
        [
            _seller(),
            _condition(),
            _brands(OFFICE_GEAR_BRANDS),
            _models(OFFICE_GEAR_MODELS),
        ],
    ),
    "appliances": _section(
        "electronics-bytovaya-tehnika",
        "Бытовая техника",
        (
            "Холодильники",
            "Стиральные машины",
            "Сушильные машины",
            "Пылесосы",
            "Роботы-пылесосы",
            "Другая бытовая техника",
        ),
        [
            _seller(),
            _condition(),
            _brands(APPLIANCE_BRANDS),
            _models(APPLIANCE_MODELS),
            _group("Объём", ("До 250 л", "250-350 л", "Более 350 л"), ("Холодильники",)),
            _group("Загрузка", ("5 кг", "6 кг", "7 кг", "8 кг", "9 кг"), ("Стиральные машины", "Сушильные машины")),
        ],
    ),
    "climate": _section(
        "electronics-klimaticheskaya-tehnika",
        "Климатическая техника",
        (
            "Кондиционеры",
            "Обогреватели",
            "Вентиляторы",
            "Увлажнители",
            "Очистители воздуха",
            "Другая климатическая техника",
        ),
        [
            _seller(),
            _condition(),
            _brands(CLIMATE_BRANDS),
            _models(CLIMATE_MODELS),
            _group("Тип", ("Инвертор", "Обычный"), ("Кондиционеры",)),
            _group("Мощность", ("7", "9", "12", "18", "24"), ("Кондиционеры",)),
        ],
    ),
    "built-in": _section(
        "electronics-vstraivaemaya-tehnika",
        "Встраиваемая техника",
        (
            "Духовые шкафы",
            "Варочные панели",
            "Встраиваемые посудомойки",
            "Вытяжки",
            "Встраиваемые холодильники",
            "Другая встраиваемая техника",
        ),
        [
            _seller(),
            _condition(),
            _brands(BUILTIN_BRANDS),
            _models(BUILTIN_MODELS),
            _group("Ширина", ("45 см", "60 см", "90 см"), ("Духовые шкафы", "Варочные панели", "Вытяжки")),
        ],
    ),
    "kitchen": _section(
        "electronics-kuhonnaya-tehnika",
        "Кухонная техника",
        (
            "Плиты",
            "Микроволновые печи",
            "Отдельностоящие посудомойки",
            "Мультиварки",
            "Блендеры",
            "Кофемашины",
            "Электрочайники",
            "Мясорубки",
            "Другая кухонная техника",
        ),
        [
            _seller(),
            _condition(),
            _brands(KITCHEN_BRANDS),
            _models(KITCHEN_MODELS),
        ],
    ),
    "home": _section(
        "electronics-tehnika-dlya-doma",
        "Техника для дома",
        (
            "Утюги и отпариватели",
            "Бытовые швейные машины",
            "Напольные весы",
            "Другая техника для дома",
        ),
        [
            _seller(),
            _condition(),
            _brands(HOME_BRANDS),
            _models(HOME_MODELS),
        ],
    ),
    "accessories": _section(
        "electronics-zapchasti-i-aksessuary",
        "Запчасти и аксессуары",
        (
            "Чехлы",
            "Защитные стёкла",
            "Зарядные устройства",
            "Кабели",
            "Внешние аккумуляторы",
            "Запчасти для техники",
            "Другие аксессуары",
        ),
        [
            _seller(),
            _condition(),
            _brands(ACCESSORY_BRANDS),
            _models(ACCESSORY_MODELS),
        ],
    ),
    "other": _section(
        "electronics-prochaya-tehnika-i-elektronika",
        "Прочая техника и электроника",
        ("Стабилизаторы напряжения", "Сетевые фильтры", "Другая техника"),
        [
            _seller(),
            _condition(),
            _brands(OTHER_BRANDS),
            _models(OTHER_MODELS),
        ],
    ),
}


def build_electronics_section_catalog(section_key: str) -> dict[str, Any] | None:
    return ELECTRONICS_SECTIONS.get(section_key)
