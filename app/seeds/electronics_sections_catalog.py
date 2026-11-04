# -*- coding: utf-8 -*-
"""Продажа «Техника и электроника».

Вид — тип техники. Марка и модель зависят друг от друга, как на Lalafo.
Не забирать: котлы, радиаторы, тёплый пол, вентиляционные системы,
водонагреватели, генераторы, кабель и розетки, детские часы, обычные часы,
промышленные швейные машины, кассовую технику.
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


def _brands(rows: list[tuple[str, tuple[str, ...] | None]]) -> dict[str, Any]:
    return {
        "label": "Марка",
        "options": [_item(name, kinds=kinds) for name, kinds in rows],
    }


def _models(rows: list[tuple[str, str, tuple[str, ...]]]) -> dict[str, Any]:
    return {
        "label": "Модель",
        "depends_on": "Марка",
        "options": [_item(model, parent=brand, kinds=kinds) for brand, model, kinds in rows],
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
        "electronics-telefony",
        "Смартфоны и телефоны",
        ("Смартфоны", "Кнопочные телефоны", "Другие телефоны"),
        [
            _seller(),
            _condition(),
            _brands([
                ("Apple", _PHONE),
                ("Samsung", _PHONE_ALL),
                ("Xiaomi", _PHONE),
                ("Honor", _PHONE),
                ("Huawei", _PHONE),
                ("Realme", _PHONE),
                ("Tecno", _PHONE),
                ("Infinix", _PHONE),
                ("Nokia", _BUTTON),
            ]),
            _models([
                ("Apple", "iPhone 13", _PHONE),
                ("Apple", "iPhone 14", _PHONE),
                ("Apple", "iPhone 15", _PHONE),
                ("Apple", "iPhone 16", _PHONE),
                ("Apple", "iPhone SE", _PHONE),
                ("Samsung", "Galaxy A15", _PHONE),
                ("Samsung", "Galaxy A35", _PHONE),
                ("Samsung", "Galaxy A55", _PHONE),
                ("Samsung", "Galaxy S24", _PHONE),
                ("Samsung", "Galaxy S25", _PHONE),
                ("Samsung", "Galaxy Z Flip", _PHONE),
                ("Xiaomi", "Redmi Note 13", _PHONE),
                ("Xiaomi", "Redmi Note 14", _PHONE),
                ("Xiaomi", "Poco X6", _PHONE),
                ("Xiaomi", "Xiaomi 14", _PHONE),
                ("Honor", "Honor X9", _PHONE),
                ("Honor", "Honor 200", _PHONE),
                ("Huawei", "Nova 12", _PHONE),
                ("Huawei", "Pura 70", _PHONE),
                ("Realme", "Realme 12", _PHONE),
                ("Realme", "Realme Note 50", _PHONE),
                ("Tecno", "Spark 20", _PHONE),
                ("Tecno", "Camon 30", _PHONE),
                ("Infinix", "Hot 40", _PHONE),
                ("Infinix", "Note 40", _PHONE),
                ("Nokia", "Nokia 105", _BUTTON),
                ("Nokia", "Nokia 130", _BUTTON),
                ("Samsung", "Samsung Guru", _BUTTON),
            ]),
            _group("Память", ("64 ГБ", "128 ГБ", "256 ГБ", "512 ГБ", "1 ТБ"), _PHONE),
            _group("ОЗУ", ("4 ГБ", "6 ГБ", "8 ГБ", "12 ГБ"), _PHONE),
        ],
    ),
    "tablets": _section(
        "electronics-planshety",
        "Планшеты и электронные книги",
        ("Планшеты", "Электронные книги", "Другие планшеты и книги"),
        [
            _seller(),
            _condition(),
            _brands([
                ("Apple", ("Планшеты",)),
                ("Samsung", ("Планшеты",)),
                ("Xiaomi", ("Планшеты",)),
                ("Huawei", ("Планшеты",)),
                ("Lenovo", ("Планшеты",)),
                ("PocketBook", ("Электронные книги",)),
                ("Amazon", ("Электронные книги",)),
            ]),
            _models([
                ("Apple", "iPad", ("Планшеты",)),
                ("Apple", "iPad Air", ("Планшеты",)),
                ("Apple", "iPad Pro", ("Планшеты",)),
                ("Apple", "iPad mini", ("Планшеты",)),
                ("Samsung", "Galaxy Tab A9", ("Планшеты",)),
                ("Samsung", "Galaxy Tab S9", ("Планшеты",)),
                ("Xiaomi", "Redmi Pad", ("Планшеты",)),
                ("Xiaomi", "Xiaomi Pad 6", ("Планшеты",)),
                ("Huawei", "MatePad", ("Планшеты",)),
                ("Lenovo", "Tab M11", ("Планшеты",)),
                ("PocketBook", "PocketBook Verse", ("Электронные книги",)),
                ("PocketBook", "PocketBook Era", ("Электронные книги",)),
                ("Amazon", "Kindle", ("Электронные книги",)),
                ("Amazon", "Kindle Paperwhite", ("Электронные книги",)),
            ]),
            _group("Экран", ('8"', '10"', '11"', '12.9"'), ("Планшеты",)),
            _group("Память", ("64 ГБ", "128 ГБ", "256 ГБ", "512 ГБ"), ("Планшеты",)),
        ],
    ),
    "computers": _section(
        "electronics-kompyutery",
        "Ноутбуки и компьютеры",
        ("Ноутбуки", "Моноблоки", "Системные блоки", "Мониторы", "Другие компьютеры"),
        [
            _seller(),
            _condition(),
            _brands([
                ("Apple", ("Ноутбуки", "Моноблоки")),
                ("Asus", ("Ноутбуки", "Мониторы")),
                ("Acer", ("Ноутбуки", "Мониторы")),
                ("Lenovo", ("Ноутбуки", "Моноблоки")),
                ("HP", ("Ноутбуки",)),
                ("Dell", ("Ноутбуки", "Мониторы")),
                ("MSI", ("Ноутбуки",)),
                ("Samsung", ("Мониторы",)),
                ("LG", ("Мониторы",)),
            ]),
            _models([
                ("Apple", "MacBook Air", ("Ноутбуки",)),
                ("Apple", "MacBook Pro", ("Ноутбуки",)),
                ("Apple", "iMac", ("Моноблоки",)),
                ("Asus", "VivoBook", ("Ноутбуки",)),
                ("Asus", "TUF Gaming", ("Ноутбуки",)),
                ("Asus", "ROG", ("Ноутбуки",)),
                ("Acer", "Aspire", ("Ноутбуки",)),
                ("Acer", "Nitro", ("Ноутбуки",)),
                ("Lenovo", "IdeaPad", ("Ноутбуки",)),
                ("Lenovo", "ThinkPad", ("Ноутбуки",)),
                ("Lenovo", "Legion", ("Ноутбуки",)),
                ("HP", "Pavilion", ("Ноутбуки",)),
                ("HP", "Victus", ("Ноутбуки",)),
                ("Dell", "Inspiron", ("Ноутбуки",)),
                ("Dell", "XPS", ("Ноутбуки",)),
                ("MSI", "Katana", ("Ноутбуки",)),
                ("Samsung", "Odyssey", ("Мониторы",)),
                ("LG", "UltraGear", ("Мониторы",)),
                ("Asus", "TUF Gaming монитор", ("Мониторы",)),
            ]),
            _group("ОЗУ", ("8 ГБ", "16 ГБ", "32 ГБ"), ("Ноутбуки", "Моноблоки", "Системные блоки")),
            _group("Накопитель", ("256 ГБ", "512 ГБ", "1 ТБ"), ("Ноутбуки", "Моноблоки", "Системные блоки")),
            _group("Диагональ", ('14"', '15.6"', '16"', '24"', '27"')),
        ],
    ),
    "parts": _section(
        "electronics-komplektuyushchie",
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
            _brands([
                ("Intel", ("Процессоры",)),
                ("AMD", ("Процессоры", "Видеокарты")),
                ("Nvidia", ("Видеокарты",)),
                ("Kingston", ("Оперативная память", "Накопители")),
                ("Samsung", ("Накопители",)),
                ("Western Digital", ("Накопители",)),
                ("Gigabyte", ("Материнские платы", "Видеокарты")),
                ("MSI", ("Материнские платы", "Видеокарты")),
                ("ASRock", ("Материнские платы",)),
                ("Corsair", ("Блоки питания", "Оперативная память")),
            ]),
            _models([
                ("Intel", "Core i5", ("Процессоры",)),
                ("Intel", "Core i7", ("Процессоры",)),
                ("Intel", "Core i9", ("Процессоры",)),
                ("AMD", "Ryzen 5", ("Процессоры",)),
                ("AMD", "Ryzen 7", ("Процессоры",)),
                ("AMD", "Radeon RX 7600", ("Видеокарты",)),
                ("Nvidia", "GeForce RTX 4060", ("Видеокарты",)),
                ("Nvidia", "GeForce RTX 4070", ("Видеокарты",)),
                ("Kingston", "Fury", ("Оперативная память",)),
                ("Samsung", "990 EVO", ("Накопители",)),
                ("Western Digital", "Blue", ("Накопители",)),
                ("Corsair", "RM750", ("Блоки питания",)),
            ]),
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
            _brands([
                ("HP", None),
                ("Canon", None),
                ("Epson", None),
                ("Brother", None),
                ("Pantum", None),
            ]),
            _models([
                ("HP", "LaserJet", ("Принтеры", "МФУ")),
                ("Canon", "PIXMA", ("Принтеры", "МФУ")),
                ("Epson", "EcoTank", ("Принтеры", "МФУ")),
                ("Brother", "DCP", ("МФУ",)),
                ("Pantum", "Pantum P2500", ("Принтеры",)),
            ]),
            _group("Печать", ("Лазерная", "Струйная"), ("Принтеры", "МФУ")),
        ],
    ),
    "tv": _section(
        "electronics-televizory",
        "Телевизоры и проекторы",
        ("Телевизоры", "Проекторы", "ТВ-приставки", "Другие экраны"),
        [
            _seller(),
            _condition(),
            _brands([
                ("Samsung", ("Телевизоры",)),
                ("LG", ("Телевизоры",)),
                ("Xiaomi", ("Телевизоры", "Проекторы")),
                ("Hisense", ("Телевизоры",)),
                ("TCL", ("Телевизоры",)),
                ("Sony", ("Телевизоры",)),
                ("Epson", ("Проекторы",)),
            ]),
            _models([
                ("Samsung", "Crystal UHD", ("Телевизоры",)),
                ("Samsung", "QLED", ("Телевизоры",)),
                ("LG", "OLED", ("Телевизоры",)),
                ("LG", "NanoCell", ("Телевизоры",)),
                ("Xiaomi", "Mi TV", ("Телевизоры",)),
                ("Hisense", "ULED", ("Телевизоры",)),
                ("TCL", "C645", ("Телевизоры",)),
                ("Sony", "Bravia", ("Телевизоры",)),
                ("Epson", "EH-TW", ("Проекторы",)),
                ("Xiaomi", "Mi Smart Projector", ("Проекторы",)),
            ]),
            _group("Диагональ", ('32"', '43"', '50"', '55"', '65"', '75"'), ("Телевизоры",)),
            _group("Разрешение", ("HD", "Full HD", "4K"), ("Телевизоры", "Проекторы")),
        ],
    ),
    "audio": _section(
        "electronics-audio",
        "Аудиотехника",
        ("Колонки", "Наушники", "Саундбары", "Музыкальные центры", "Микрофоны", "Другая аудиотехника"),
        [
            _seller(),
            _condition(),
            _brands([
                ("JBL", ("Колонки", "Наушники")),
                ("Sony", ("Наушники", "Колонки")),
                ("Apple", ("Наушники",)),
                ("Samsung", ("Наушники", "Саундбары")),
                ("Xiaomi", ("Наушники", "Колонки")),
                ("Marshall", ("Колонки",)),
                ("Edifier", ("Колонки",)),
            ]),
            _models([
                ("JBL", "Flip", ("Колонки",)),
                ("JBL", "Charge", ("Колонки",)),
                ("JBL", "Tune", ("Наушники",)),
                ("Sony", "WH-1000XM", ("Наушники",)),
                ("Apple", "AirPods", ("Наушники",)),
                ("Apple", "AirPods Pro", ("Наушники",)),
                ("Samsung", "Galaxy Buds", ("Наушники",)),
                ("Marshall", "Emberton", ("Колонки",)),
                ("Edifier", "R1280", ("Колонки",)),
            ]),
            _group("Подключение", ("Проводные", "Bluetooth"), ("Колонки", "Наушники")),
        ],
    ),
    "photo": _section(
        "electronics-foto",
        "Фото и видеотехника",
        ("Фотоаппараты", "Объективы", "Видеокамеры", "Экшн-камеры", "Квадрокоптеры", "Другая фототехника"),
        [
            _seller(),
            _condition(),
            _brands([
                ("Canon", ("Фотоаппараты", "Объективы")),
                ("Nikon", ("Фотоаппараты", "Объективы")),
                ("Sony", ("Фотоаппараты", "Объективы", "Видеокамеры")),
                ("Fujifilm", ("Фотоаппараты",)),
                ("GoPro", ("Экшн-камеры",)),
                ("DJI", ("Квадрокоптеры", "Экшн-камеры")),
            ]),
            _models([
                ("Canon", "EOS R50", ("Фотоаппараты",)),
                ("Canon", "EOS 2000D", ("Фотоаппараты",)),
                ("Nikon", "Z50", ("Фотоаппараты",)),
                ("Sony", "Alpha 7", ("Фотоаппараты",)),
                ("Sony", "ZV-E10", ("Видеокамеры",)),
                ("Fujifilm", "X-T30", ("Фотоаппараты",)),
                ("GoPro", "Hero 12", ("Экшн-камеры",)),
                ("DJI", "Mini 4", ("Квадрокоптеры",)),
                ("DJI", "Osmo Action", ("Экшн-камеры",)),
            ]),
        ],
    ),
    "consoles": _section(
        "electronics-pristavki",
        "Игровые приставки и аксессуары",
        ("Игровые приставки", "Геймпады", "Игры", "Другие игровые товары"),
        [
            _seller(),
            _condition(),
            _brands([
                ("Sony", ("Игровые приставки", "Геймпады", "Игры")),
                ("Microsoft", ("Игровые приставки", "Геймпады", "Игры")),
                ("Nintendo", ("Игровые приставки", "Игры")),
            ]),
            _models([
                ("Sony", "PlayStation 4", ("Игровые приставки",)),
                ("Sony", "PlayStation 5", ("Игровые приставки",)),
                ("Sony", "DualSense", ("Геймпады",)),
                ("Microsoft", "Xbox Series S", ("Игровые приставки",)),
                ("Microsoft", "Xbox Series X", ("Игровые приставки",)),
                ("Nintendo", "Switch", ("Игровые приставки",)),
                ("Nintendo", "Switch OLED", ("Игровые приставки",)),
            ]),
        ],
    ),
    "wearables": _section(
        "electronics-gadzhety",
        "Умные часы и гаджеты",
        ("Умные часы", "Фитнес-браслеты", "VR-очки", "Другие гаджеты"),
        [
            _seller(),
            _condition(),
            _brands([
                ("Apple", ("Умные часы",)),
                ("Samsung", ("Умные часы", "Фитнес-браслеты")),
                ("Xiaomi", ("Умные часы", "Фитнес-браслеты")),
                ("Huawei", ("Умные часы", "Фитнес-браслеты")),
                ("Garmin", ("Умные часы",)),
                ("Amazfit", ("Умные часы", "Фитнес-браслеты")),
                ("Meta", ("VR-очки",)),
            ]),
            _models([
                ("Apple", "Apple Watch SE", ("Умные часы",)),
                ("Apple", "Apple Watch Series 10", ("Умные часы",)),
                ("Apple", "Apple Watch Ultra", ("Умные часы",)),
                ("Samsung", "Galaxy Watch 7", ("Умные часы",)),
                ("Samsung", "Galaxy Fit", ("Фитнес-браслеты",)),
                ("Xiaomi", "Redmi Watch", ("Умные часы",)),
                ("Xiaomi", "Smart Band 9", ("Фитнес-браслеты",)),
                ("Huawei", "Watch GT", ("Умные часы",)),
                ("Garmin", "Forerunner", ("Умные часы",)),
                ("Amazfit", "Bip", ("Умные часы",)),
                ("Meta", "Quest 3", ("VR-очки",)),
            ]),
        ],
    ),
    "network": _section(
        "electronics-seti",
        "Сетевое оборудование",
        ("Роутеры", "Усилители сигнала", "Коммутаторы", "Модемы", "Другое сетевое оборудование"),
        [
            _seller(),
            _condition(),
            _brands([
                ("TP-Link", None),
                ("Xiaomi", ("Роутеры",)),
                ("Keenetic", ("Роутеры",)),
                ("Asus", ("Роутеры",)),
                ("Mercusys", ("Роутеры", "Усилители сигнала")),
            ]),
            _models([
                ("TP-Link", "Archer", ("Роутеры",)),
                ("TP-Link", "Deco", ("Роутеры",)),
                ("Xiaomi", "Mi Router", ("Роутеры",)),
                ("Keenetic", "Giga", ("Роутеры",)),
                ("Asus", "RT-AX", ("Роутеры",)),
                ("Mercusys", "MW", ("Роутеры",)),
            ]),
            _group("Диапазон", ("2.4 ГГц", "5 ГГц", "Двухдиапазонный"), ("Роутеры", "Усилители сигнала")),
        ],
    ),
    "office-gear": _section(
        "electronics-ofisnaya-tehnika",
        "Техника для офиса",
        ("ИБП", "Шредеры", "Брошюровщики", "Другая офисная техника"),
        [
            _seller(),
            _condition(),
            _brands([
                ("APC", ("ИБП",)),
                ("CyberPower", ("ИБП",)),
                ("Powercom", ("ИБП",)),
                ("Fellowes", ("Шредеры",)),
            ]),
            _models([
                ("APC", "Back-UPS 650", ("ИБП",)),
                ("APC", "Back-UPS 1100", ("ИБП",)),
                ("CyberPower", "UT650", ("ИБП",)),
                ("Powercom", "RPT-600", ("ИБП",)),
                ("Fellowes", "Powershred", ("Шредеры",)),
            ]),
        ],
    ),
    "appliances": _section(
        "electronics-bytovaya",
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
            _brands([
                ("Samsung", None),
                ("LG", None),
                ("Bosch", None),
                ("Beko", None),
                ("Haier", None),
                ("Artel", None),
                ("Midea", None),
                ("Indesit", None),
                ("Xiaomi", ("Роботы-пылесосы",)),
            ]),
            _models([
                ("Samsung", "RB", ("Холодильники",)),
                ("Samsung", "WW", ("Стиральные машины",)),
                ("LG", "GC", ("Холодильники",)),
                ("LG", "F2", ("Стиральные машины",)),
                ("Bosch", "Serie 4", ("Холодильники", "Стиральные машины")),
                ("Artel", "Artel HS", ("Холодильники",)),
                ("Haier", "Haier CE", ("Стиральные машины",)),
                ("Midea", "Midea Robot", ("Роботы-пылесосы",)),
                ("Xiaomi", "Robot Vacuum", ("Роботы-пылесосы",)),
            ]),
            _group("Объём", ("До 250 л", "250-350 л", "Более 350 л"), ("Холодильники",)),
            _group("Загрузка", ("5 кг", "6 кг", "7 кг", "8 кг", "9 кг"), ("Стиральные машины", "Сушильные машины")),
        ],
    ),
    "climate": _section(
        "electronics-klimat",
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
            _brands([
                ("Midea", ("Кондиционеры",)),
                ("Gree", ("Кондиционеры",)),
                ("Haier", ("Кондиционеры",)),
                ("Samsung", ("Кондиционеры",)),
                ("LG", ("Кондиционеры",)),
                ("Artel", ("Кондиционеры",)),
                ("TCL", ("Кондиционеры",)),
                ("Ballu", ("Обогреватели", "Вентиляторы")),
                ("Electrolux", ("Обогреватели", "Увлажнители")),
                ("Xiaomi", ("Очистители воздуха", "Увлажнители")),
            ]),
            _models([
                ("Midea", "Blanc", ("Кондиционеры",)),
                ("Gree", "Bora", ("Кондиционеры",)),
                ("Haier", "Coral", ("Кондиционеры",)),
                ("Samsung", "WindFree", ("Кондиционеры",)),
                ("LG", "DualCool", ("Кондиционеры",)),
                ("Artel", "Artel Shahrisabz", ("Кондиционеры",)),
                ("TCL", "TAC", ("Кондиционеры",)),
                ("Ballu", "Ballu BIH", ("Обогреватели",)),
                ("Xiaomi", "Mi Air Purifier", ("Очистители воздуха",)),
            ]),
            _group("Тип", ("Инвертор", "Обычный"), ("Кондиционеры",)),
            _group("Мощность", ("7", "9", "12", "18", "24"), ("Кондиционеры",)),
        ],
    ),
    "built-in": _section(
        "electronics-vstraivaemaya",
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
            _brands([
                ("Bosch", None),
                ("Samsung", None),
                ("Electrolux", None),
                ("Gefest", None),
                ("Maunfeld", ("Вытяжки",)),
                ("Krona", ("Вытяжки",)),
            ]),
            _models([
                ("Bosch", "Serie 4", ("Духовые шкафы", "Варочные панели")),
                ("Samsung", "NV", ("Духовые шкафы",)),
                ("Electrolux", "EOB", ("Духовые шкафы",)),
                ("Gefest", "Gefest ДА", ("Духовые шкафы",)),
                ("Maunfeld", "Maunfeld Tower", ("Вытяжки",)),
                ("Krona", "Krona Kamilla", ("Вытяжки",)),
            ]),
            _group("Ширина", ("45 см", "60 см", "90 см"), ("Духовые шкафы", "Варочные панели", "Вытяжки")),
        ],
    ),
    "kitchen": _section(
        "electronics-kuhnya",
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
            _brands([
                ("Redmond", ("Мультиварки", "Блендеры", "Электрочайники")),
                ("Philips", ("Блендеры", "Кофемашины")),
                ("Bosch", ("Мясорубки", "Плиты")),
                ("Tefal", ("Мультиварки", "Электрочайники")),
                ("DeLonghi", ("Кофемашины",)),
                ("Artel", ("Плиты", "Микроволновые печи")),
                ("Samsung", ("Микроволновые печи",)),
                ("Gefest", ("Плиты",)),
            ]),
            _models([
                ("Redmond", "RMC", ("Мультиварки",)),
                ("Philips", "HR", ("Блендеры",)),
                ("DeLonghi", "Magnifica", ("Кофемашины",)),
                ("Artel", "Artel плита", ("Плиты",)),
                ("Gefest", "Gefest 3200", ("Плиты",)),
                ("Samsung", "MS", ("Микроволновые печи",)),
                ("Bosch", "MFW", ("Мясорубки",)),
            ]),
        ],
    ),
    "home": _section(
        "electronics-dlya-doma",
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
            _brands([
                ("Philips", ("Утюги и отпариватели",)),
                ("Tefal", ("Утюги и отпариватели",)),
                ("Braun", ("Утюги и отпариватели",)),
                ("Janome", ("Бытовые швейные машины",)),
                ("Brother", ("Бытовые швейные машины",)),
                ("Singer", ("Бытовые швейные машины",)),
                ("Xiaomi", ("Напольные весы",)),
            ]),
            _models([
                ("Philips", "Azur", ("Утюги и отпариватели",)),
                ("Tefal", "Ultimate", ("Утюги и отпариватели",)),
                ("Janome", "Janome Sewist", ("Бытовые швейные машины",)),
                ("Brother", "Brother Universal", ("Бытовые швейные машины",)),
                ("Xiaomi", "Mi Smart Scale", ("Напольные весы",)),
            ]),
        ],
    ),
    "accessories": _section(
        "electronics-aksessuary",
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
            _brands([
                ("Apple", ("Чехлы", "Защитные стёкла", "Зарядные устройства")),
                ("Samsung", ("Чехлы", "Защитные стёкла", "Зарядные устройства")),
                ("Xiaomi", ("Чехлы", "Защитные стёкла", "Зарядные устройства")),
                ("Baseus", ("Зарядные устройства", "Кабели", "Внешние аккумуляторы")),
                ("Anker", ("Зарядные устройства", "Внешние аккумуляторы")),
            ]),
            _models([
                ("Apple", "для iPhone 14", ("Чехлы", "Защитные стёкла")),
                ("Apple", "для iPhone 15", ("Чехлы", "Защитные стёкла")),
                ("Apple", "для iPhone 16", ("Чехлы", "Защитные стёкла")),
                ("Samsung", "для Galaxy A55", ("Чехлы", "Защитные стёкла")),
                ("Samsung", "для Galaxy S24", ("Чехлы", "Защитные стёкла")),
                ("Xiaomi", "для Redmi Note 13", ("Чехлы", "Защитные стёкла")),
                ("Baseus", "GaN", ("Зарядные устройства",)),
                ("Anker", "Nano", ("Зарядные устройства", "Внешние аккумуляторы")),
            ]),
        ],
    ),
    "other": _section(
        "electronics-prochee",
        "Прочая техника и электроника",
        ("Стабилизаторы напряжения", "Сетевые фильтры", "Другая техника"),
        [
            _seller(),
            _condition(),
            _brands([
                ("Resanta", ("Стабилизаторы напряжения",)),
                ("Sven", ("Стабилизаторы напряжения", "Сетевые фильтры")),
                ("Powercom", ("Стабилизаторы напряжения",)),
            ]),
            _models([
                ("Resanta", "АСН", ("Стабилизаторы напряжения",)),
                ("Sven", "AVR", ("Стабилизаторы напряжения",)),
                ("Powercom", "TCA", ("Стабилизаторы напряжения",)),
            ]),
        ],
    ),
}


def build_electronics_section_catalog(section_key: str) -> dict[str, Any] | None:
    return ELECTRONICS_SECTIONS.get(section_key)
