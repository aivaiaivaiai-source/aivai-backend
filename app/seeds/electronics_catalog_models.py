# -*- coding: utf-8 -*-
"""Electronics V2 marketplace brand→model catalog (Backend SoT fragment).

Depth: marketplace selection, not retailer SKU inventory.
No storage/RAM/color/region as model identity.
Checked against manufacturer catalogs / support lists (2026-11-08).
"""
from __future__ import annotations

from typing import Any

# Kind shortcuts
P = ("Смартфоны",)
B = ("Кнопочные телефоны",)
PB = ("Смартфоны", "Кнопочные телефоны")
TAB = ("Планшеты",)
EREAD = ("Электронные книги",)
NB = ("Ноутбуки",)
MONO = ("Моноблоки",)
MON = ("Мониторы",)
CPU = ("Процессоры",)
GPU = ("Видеокарты",)
RAM = ("Оперативная память",)
MB = ("Материнские платы",)
SSD = ("Накопители",)
PSU = ("Блоки питания",)
TV = ("Телевизоры",)
PROJ = ("Проекторы",)
HP = ("Наушники",)
SPK = ("Колонки",)
SB = ("Саундбары",)
CAM = ("Фотоаппараты",)
LENS = ("Объективы",)
VCAM = ("Видеокамеры",)
ACT = ("Экшн-камеры",)
DRONE = ("Квадрокоптеры",)
CONS = ("Игровые приставки",)
PAD = ("Геймпады",)
WATCH = ("Умные часы",)
BAND = ("Фитнес-браслеты",)
VR = ("VR-очки",)
RTR = ("Роутеры",)
UPS = ("ИБП",)
FRIDGE = ("Холодильники",)
WASH = ("Стиральные машины",)
DRY = ("Сушильные машины",)
VAC = ("Пылесосы",)
ROBOT = ("Роботы-пылесосы",)
AC = ("Кондиционеры",)
HEAT = ("Обогреватели",)
FAN = ("Вентиляторы",)
HUM = ("Увлажнители",)
AIR = ("Очистители воздуха",)
OVEN = ("Духовые шкафы",)
HOB = ("Варочные панели",)
DISH = ("Встраиваемые посудомойки",)
HOOD = ("Вытяжки",)
IFRIDGE = ("Встраиваемые холодильники",)
PRINT = ("Принтеры",)
MFP = ("МФУ",)
SCAN = ("Сканеры",)


def _b(label: str, kinds: tuple[str, ...] | None = None) -> tuple[str, tuple[str, ...] | None]:
    return (label, kinds)


def _m(brand: str, model: str, kinds: tuple[str, ...]) -> tuple[str, str, tuple[str, ...]]:
    return (brand, model, kinds)


# ---------------------------------------------------------------------------
# Phones — FULL
# Architecture: Xiaomi brand hosts Redmi/POCO model names (existing SoT).
# ---------------------------------------------------------------------------
PHONE_BRANDS: list[tuple[str, tuple[str, ...] | None]] = [
    _b("Apple", P),
    _b("Samsung", PB),
    _b("Xiaomi", P),
    _b("Honor", P),
    _b("Huawei", P),
    _b("Realme", P),
    _b("Oppo", P),
    _b("Vivo", P),
    _b("OnePlus", P),
    _b("Google", P),
    _b("Nothing", P),
    _b("Motorola", P),
    _b("Tecno", P),
    _b("Infinix", P),
    _b("Nokia", PB),
    _b("ZTE", P),
]

PHONE_MODELS: list[tuple[str, str, tuple[str, ...]]] = [
    # Apple — Apple Support identify-your-iPhone + used-market common gens
    _m("Apple", "iPhone 18 Pro", P),
    _m("Apple", "iPhone 18 Pro Max", P),
    _m("Apple", "iPhone Duo", P),
    _m("Apple", "iPhone 17", P),
    _m("Apple", "iPhone 17 Pro", P),
    _m("Apple", "iPhone 17 Pro Max", P),
    _m("Apple", "iPhone 17e", P),
    _m("Apple", "iPhone Air", P),
    _m("Apple", "iPhone 16", P),
    _m("Apple", "iPhone 16 Plus", P),
    _m("Apple", "iPhone 16 Pro", P),
    _m("Apple", "iPhone 16 Pro Max", P),
    _m("Apple", "iPhone 16e", P),
    _m("Apple", "iPhone 15", P),
    _m("Apple", "iPhone 15 Plus", P),
    _m("Apple", "iPhone 15 Pro", P),
    _m("Apple", "iPhone 15 Pro Max", P),
    _m("Apple", "iPhone 14", P),
    _m("Apple", "iPhone 14 Plus", P),
    _m("Apple", "iPhone 14 Pro", P),
    _m("Apple", "iPhone 14 Pro Max", P),
    _m("Apple", "iPhone 13", P),
    _m("Apple", "iPhone 13 mini", P),
    _m("Apple", "iPhone 13 Pro", P),
    _m("Apple", "iPhone 13 Pro Max", P),
    _m("Apple", "iPhone 12", P),
    _m("Apple", "iPhone 12 mini", P),
    _m("Apple", "iPhone 12 Pro", P),
    _m("Apple", "iPhone 12 Pro Max", P),
    _m("Apple", "iPhone 11", P),
    _m("Apple", "iPhone 11 Pro", P),
    _m("Apple", "iPhone 11 Pro Max", P),
    _m("Apple", "iPhone XS", P),
    _m("Apple", "iPhone XS Max", P),
    _m("Apple", "iPhone XR", P),
    _m("Apple", "iPhone X", P),
    _m("Apple", "iPhone SE (3rd generation)", P),
    _m("Apple", "iPhone SE (2nd generation)", P),
    _m("Apple", "iPhone SE", P),  # preserved Package A label
    _m("Apple", "iPhone 8", P),
    _m("Apple", "iPhone 8 Plus", P),
    _m("Apple", "iPhone 7", P),
    _m("Apple", "iPhone 7 Plus", P),
    # Samsung — S / Z / A / M + button
    _m("Samsung", "Galaxy S26 Ultra", P),
    _m("Samsung", "Galaxy S26+", P),
    _m("Samsung", "Galaxy S26", P),
    _m("Samsung", "Galaxy S26 FE", P),
    _m("Samsung", "Galaxy S25 Ultra", P),
    _m("Samsung", "Galaxy S25+", P),
    _m("Samsung", "Galaxy S25", P),
    _m("Samsung", "Galaxy S25 Edge", P),
    _m("Samsung", "Galaxy S25 FE", P),
    _m("Samsung", "Galaxy S24 Ultra", P),
    _m("Samsung", "Galaxy S24+", P),
    _m("Samsung", "Galaxy S24", P),
    _m("Samsung", "Galaxy S24 FE", P),
    _m("Samsung", "Galaxy S23 Ultra", P),
    _m("Samsung", "Galaxy S23+", P),
    _m("Samsung", "Galaxy S23", P),
    _m("Samsung", "Galaxy S23 FE", P),
    _m("Samsung", "Galaxy S22 Ultra", P),
    _m("Samsung", "Galaxy S22+", P),
    _m("Samsung", "Galaxy S22", P),
    _m("Samsung", "Galaxy S21 Ultra", P),
    _m("Samsung", "Galaxy S21", P),
    _m("Samsung", "Galaxy S21 FE", P),
    _m("Samsung", "Galaxy S20 FE", P),
    _m("Samsung", "Galaxy Z Fold7", P),
    _m("Samsung", "Galaxy Z Flip7", P),
    _m("Samsung", "Galaxy Z Flip7 FE", P),
    _m("Samsung", "Galaxy Z Fold6", P),
    _m("Samsung", "Galaxy Z Flip6", P),
    _m("Samsung", "Galaxy Z Fold5", P),
    _m("Samsung", "Galaxy Z Flip5", P),
    _m("Samsung", "Galaxy Z Fold4", P),
    _m("Samsung", "Galaxy Z Flip4", P),
    _m("Samsung", "Galaxy Z Flip", P),  # preserved Package A label
    _m("Samsung", "Galaxy A57", P),
    _m("Samsung", "Galaxy A56", P),
    _m("Samsung", "Galaxy A55", P),
    _m("Samsung", "Galaxy A54", P),
    _m("Samsung", "Galaxy A37", P),
    _m("Samsung", "Galaxy A36", P),
    _m("Samsung", "Galaxy A35", P),
    _m("Samsung", "Galaxy A34", P),
    _m("Samsung", "Galaxy A26", P),
    _m("Samsung", "Galaxy A25", P),
    _m("Samsung", "Galaxy A17", P),
    _m("Samsung", "Galaxy A16", P),
    _m("Samsung", "Galaxy A15", P),
    _m("Samsung", "Galaxy A14", P),
    _m("Samsung", "Galaxy A06", P),
    _m("Samsung", "Galaxy A05s", P),
    _m("Samsung", "Galaxy A05", P),
    _m("Samsung", "Galaxy M55", P),
    _m("Samsung", "Galaxy M35", P),
    _m("Samsung", "Galaxy M15", P),
    _m("Samsung", "Samsung Guru", B),
    # Xiaomi ecosystem under Brand=Xiaomi
    _m("Xiaomi", "Xiaomi 17 Ultra", P),
    _m("Xiaomi", "Xiaomi 17T", P),
    _m("Xiaomi", "Xiaomi 17", P),
    _m("Xiaomi", "Xiaomi 15 Ultra", P),
    _m("Xiaomi", "Xiaomi 15", P),
    _m("Xiaomi", "Xiaomi 14 Ultra", P),
    _m("Xiaomi", "Xiaomi 14", P),
    _m("Xiaomi", "Xiaomi 13T", P),
    _m("Xiaomi", "Xiaomi 13", P),
    _m("Xiaomi", "Redmi Note 17 Pro", P),
    _m("Xiaomi", "Redmi Note 17", P),
    _m("Xiaomi", "Redmi Note 15 Pro+", P),
    _m("Xiaomi", "Redmi Note 15 Pro", P),
    _m("Xiaomi", "Redmi Note 15", P),
    _m("Xiaomi", "Redmi Note 14 Pro+", P),
    _m("Xiaomi", "Redmi Note 14 Pro", P),
    _m("Xiaomi", "Redmi Note 14", P),
    _m("Xiaomi", "Redmi Note 13 Pro+", P),
    _m("Xiaomi", "Redmi Note 13 Pro", P),
    _m("Xiaomi", "Redmi Note 13", P),
    _m("Xiaomi", "Redmi Note 12", P),
    _m("Xiaomi", "Redmi 17", P),
    _m("Xiaomi", "Redmi 15", P),
    _m("Xiaomi", "Redmi 14C", P),
    _m("Xiaomi", "Redmi 13C", P),
    _m("Xiaomi", "Redmi A5", P),
    _m("Xiaomi", "POCO F9 Pro", P),
    _m("Xiaomi", "POCO F8 Ultra", P),
    _m("Xiaomi", "POCO F8 Pro", P),
    _m("Xiaomi", "POCO F6", P),
    _m("Xiaomi", "POCO F5", P),
    _m("Xiaomi", "POCO X8 Pro", P),
    _m("Xiaomi", "POCO X8", P),
    _m("Xiaomi", "POCO X7", P),
    _m("Xiaomi", "POCO X6 Pro", P),
    _m("Xiaomi", "POCO X6", P),
    _m("Xiaomi", "Poco X6", P),  # preserved Package A spelling
    _m("Xiaomi", "POCO M8", P),
    _m("Xiaomi", "POCO M6", P),
    # Honor / Huawei / Realme / Oppo / Vivo / OnePlus / Google / Nothing / Motorola
    _m("Honor", "Honor Magic7", P),
    _m("Honor", "Honor Magic6", P),
    _m("Honor", "Honor 200", P),
    _m("Honor", "Honor 200 Pro", P),
    _m("Honor", "Honor X9c", P),
    _m("Honor", "Honor X9b", P),
    _m("Honor", "Honor X9", P),
    _m("Honor", "Honor X8b", P),
    _m("Honor", "Honor X7c", P),
    _m("Huawei", "Pura 70 Ultra", P),
    _m("Huawei", "Pura 70 Pro", P),
    _m("Huawei", "Pura 70", P),
    _m("Huawei", "Pura 60", P),
    _m("Huawei", "Nova 13", P),
    _m("Huawei", "Nova 12", P),
    _m("Huawei", "Nova 11", P),
    _m("Huawei", "Mate 60", P),
    _m("Realme", "Realme GT 7", P),
    _m("Realme", "Realme 14", P),
    _m("Realme", "Realme 13", P),
    _m("Realme", "Realme 12", P),
    _m("Realme", "Realme Note 60", P),
    _m("Realme", "Realme Note 50", P),
    _m("Realme", "Realme C67", P),
    _m("Realme", "Realme C63", P),
    _m("Oppo", "Find X8", P),
    _m("Oppo", "Reno13", P),
    _m("Oppo", "Reno12", P),
    _m("Oppo", "A80", P),
    _m("Oppo", "A60", P),
    _m("Vivo", "V40", P),
    _m("Vivo", "V30", P),
    _m("Vivo", "Y36", P),
    _m("Vivo", "Y28", P),
    _m("Vivo", "Y18", P),
    _m("OnePlus", "OnePlus 13", P),
    _m("OnePlus", "OnePlus 12", P),
    _m("OnePlus", "OnePlus Nord 4", P),
    _m("OnePlus", "OnePlus Nord CE 4", P),
    _m("Google", "Pixel 9 Pro", P),
    _m("Google", "Pixel 9", P),
    _m("Google", "Pixel 9a", P),
    _m("Google", "Pixel 8 Pro", P),
    _m("Google", "Pixel 8", P),
    _m("Google", "Pixel 8a", P),
    _m("Google", "Pixel 7a", P),
    _m("Nothing", "Phone (3)", P),
    _m("Nothing", "Phone (2a)", P),
    _m("Nothing", "Phone (2)", P),
    _m("Motorola", "Edge 50", P),
    _m("Motorola", "G85", P),
    _m("Motorola", "G54", P),
    _m("Motorola", "G24", P),
    _m("Tecno", "Camon 40", P),
    _m("Tecno", "Camon 30", P),
    _m("Tecno", "Spark 30", P),
    _m("Tecno", "Spark 20", P),
    _m("Tecno", "Pova 6", P),
    _m("Infinix", "Note 40", P),
    _m("Infinix", "Note 30", P),
    _m("Infinix", "Hot 50", P),
    _m("Infinix", "Hot 40", P),
    _m("Infinix", "Zero 40", P),
    _m("Nokia", "Nokia G42", P),
    _m("Nokia", "Nokia C32", P),
    _m("Nokia", "Nokia 3210", B),
    _m("Nokia", "Nokia 2660 Flip", B),
    _m("Nokia", "Nokia 130", B),
    _m("Nokia", "Nokia 105", B),
    _m("ZTE", "Blade A55", P),
    _m("ZTE", "Blade V50", P),
]

# ---------------------------------------------------------------------------
# Tablets / e-readers — FULL tablets, FAMILY e-readers
# ---------------------------------------------------------------------------
TABLET_BRANDS = [
    _b("Apple", TAB),
    _b("Samsung", TAB),
    _b("Xiaomi", TAB),
    _b("Huawei", TAB),
    _b("Honor", TAB),
    _b("Lenovo", TAB),
    _b("Amazon", EREAD),
    _b("PocketBook", EREAD),
    _b("Onyx", EREAD),
    _b("Kobo", EREAD),
]

TABLET_MODELS = [
    _m("Apple", "iPad Pro 13-inch (M5)", TAB),
    _m("Apple", "iPad Pro 11-inch (M5)", TAB),
    _m("Apple", "iPad Pro 13-inch (M4)", TAB),
    _m("Apple", "iPad Pro 11-inch (M4)", TAB),
    _m("Apple", "iPad Air 13-inch (M4)", TAB),
    _m("Apple", "iPad Air 11-inch (M4)", TAB),
    _m("Apple", "iPad Air 13-inch (M3)", TAB),
    _m("Apple", "iPad Air 11-inch (M3)", TAB),
    _m("Apple", "iPad Air 13-inch (M2)", TAB),
    _m("Apple", "iPad Air 11-inch (M2)", TAB),
    _m("Apple", "iPad (A16)", TAB),
    _m("Apple", "iPad (10th generation)", TAB),
    _m("Apple", "iPad (9th generation)", TAB),
    _m("Apple", "iPad mini (A17 Pro)", TAB),
    _m("Apple", "iPad mini (6th generation)", TAB),
    # preserved Package A family labels
    _m("Apple", "iPad", TAB),
    _m("Apple", "iPad Air", TAB),
    _m("Apple", "iPad Pro", TAB),
    _m("Apple", "iPad mini", TAB),
    _m("Samsung", "Galaxy Tab S10 Ultra", TAB),
    _m("Samsung", "Galaxy Tab S10+", TAB),
    _m("Samsung", "Galaxy Tab S9 Ultra", TAB),
    _m("Samsung", "Galaxy Tab S9+", TAB),
    _m("Samsung", "Galaxy Tab S9", TAB),
    _m("Samsung", "Galaxy Tab S9 FE", TAB),
    _m("Samsung", "Galaxy Tab A9+", TAB),
    _m("Samsung", "Galaxy Tab A9", TAB),
    _m("Samsung", "Galaxy Tab A8", TAB),
    _m("Xiaomi", "Xiaomi Pad 8", TAB),
    _m("Xiaomi", "Xiaomi Pad 7 Pro", TAB),
    _m("Xiaomi", "Xiaomi Pad 7", TAB),
    _m("Xiaomi", "Xiaomi Pad 6", TAB),
    _m("Xiaomi", "Redmi Pad 2", TAB),
    _m("Xiaomi", "Redmi Pad SE", TAB),
    _m("Xiaomi", "Redmi Pad", TAB),
    _m("Xiaomi", "POCO Pad", TAB),
    _m("Huawei", "MatePad Pro", TAB),
    _m("Huawei", "MatePad 11.5", TAB),
    _m("Huawei", "MatePad SE", TAB),
    _m("Honor", "Honor Pad 9", TAB),
    _m("Honor", "Honor Pad X8", TAB),
    _m("Lenovo", "Tab P12", TAB),
    _m("Lenovo", "Tab M11", TAB),
    _m("Lenovo", "Tab M10", TAB),
    _m("Amazon", "Kindle Paperwhite", EREAD),
    _m("Amazon", "Kindle Oasis", EREAD),
    _m("Amazon", "Kindle", EREAD),
    _m("Amazon", "Kindle Scribe", EREAD),
    _m("PocketBook", "PocketBook Era", EREAD),
    _m("PocketBook", "PocketBook Verse", EREAD),
    _m("PocketBook", "PocketBook InkPad", EREAD),
    _m("Onyx", "Boox Note", EREAD),
    _m("Onyx", "Boox Palma", EREAD),
    _m("Onyx", "Boox Page", EREAD),
    _m("Kobo", "Kobo Clara", EREAD),
    _m("Kobo", "Kobo Libra", EREAD),
]

# ---------------------------------------------------------------------------
# Computers — FAMILY (chip/size generations; no RAM/SSD SKUs)
# ---------------------------------------------------------------------------
COMPUTER_BRANDS = [
    _b("Apple", ("Ноутбуки", "Моноблоки")),
    _b("Asus", ("Ноутбуки", "Мониторы")),
    _b("Acer", ("Ноутбуки", "Мониторы")),
    _b("Lenovo", ("Ноутбуки", "Моноблоки", "Мониторы")),
    _b("HP", ("Ноутбуки", "Моноблоки", "Мониторы")),
    _b("Dell", ("Ноутбуки", "Мониторы")),
    _b("MSI", ("Ноутбуки", "Мониторы")),
    _b("Huawei", NB),
    _b("Honor", NB),
    _b("Samsung", ("Ноутбуки", "Мониторы")),
    _b("Microsoft", NB),
    _b("LG", MON),
    _b("Gigabyte", MON),
]

COMPUTER_MODELS = [
    _m("Apple", "MacBook Air 13-inch (M5)", NB),
    _m("Apple", "MacBook Air 15-inch (M5)", NB),
    _m("Apple", "MacBook Air 13-inch (M4)", NB),
    _m("Apple", "MacBook Air 15-inch (M4)", NB),
    _m("Apple", "MacBook Air 13-inch (M3)", NB),
    _m("Apple", "MacBook Air 15-inch (M3)", NB),
    _m("Apple", "MacBook Air 13-inch (M2)", NB),
    _m("Apple", "MacBook Air 15-inch (M2)", NB),
    _m("Apple", "MacBook Air 13-inch (M1)", NB),
    _m("Apple", "MacBook Pro 14-inch (M4)", NB),
    _m("Apple", "MacBook Pro 16-inch (M4)", NB),
    _m("Apple", "MacBook Pro 14-inch (M3)", NB),
    _m("Apple", "MacBook Pro 16-inch (M3)", NB),
    _m("Apple", "MacBook Pro 14-inch (M2)", NB),
    _m("Apple", "MacBook Pro 16-inch (M2)", NB),
    _m("Apple", "MacBook Pro 13-inch (M2)", NB),
    _m("Apple", "MacBook Air", NB),  # preserved Package A
    _m("Apple", "MacBook Pro", NB),  # preserved Package A
    _m("Apple", "iMac 24-inch (M4)", MONO),
    _m("Apple", "iMac 24-inch (M3)", MONO),
    _m("Apple", "iMac", MONO),  # preserved Package A
    _m("Apple", "Mac mini (M4)", ("Другие компьютеры",)),
    _m("Asus", "VivoBook", NB),  # preserved spelling
    _m("Asus", "Vivobook", NB),
    _m("Asus", "Zenbook", NB),
    _m("Asus", "TUF Gaming", NB),
    _m("Asus", "ROG Strix", NB),
    _m("Asus", "ROG Zephyrus", NB),
    _m("Asus", "ExpertBook", NB),
    _m("Asus", "TUF Gaming монитор", MON),
    _m("Asus", "ProArt Display", MON),
    _m("Acer", "Aspire", NB),
    _m("Acer", "Swift", NB),
    _m("Acer", "Nitro", NB),
    _m("Acer", "Predator", NB),
    _m("Lenovo", "IdeaPad", NB),
    _m("Lenovo", "Yoga", NB),
    _m("Lenovo", "ThinkPad", NB),
    _m("Lenovo", "ThinkBook", NB),
    _m("Lenovo", "Legion", NB),
    _m("Lenovo", "LOQ", NB),
    _m("Lenovo", "IdeaCentre", MONO),
    _m("HP", "Pavilion", NB),
    _m("HP", "Victus", NB),
    _m("HP", "OMEN", NB),
    _m("HP", "Envy", NB),
    _m("HP", "EliteBook", NB),
    _m("HP", "ProBook", NB),
    _m("Dell", "Inspiron", NB),
    _m("Dell", "XPS", NB),
    _m("Dell", "Latitude", NB),
    _m("Dell", "G Series", NB),
    _m("Dell", "Alienware", NB),
    _m("MSI", "Katana", NB),
    _m("MSI", "Thin", NB),
    _m("MSI", "Stealth", NB),
    _m("MSI", "Raider", NB),
    _m("Huawei", "MateBook D", NB),
    _m("Huawei", "MateBook 14", NB),
    _m("Huawei", "MateBook X Pro", NB),
    _m("Honor", "MagicBook", NB),
    _m("Samsung", "Galaxy Book4", NB),
    _m("Samsung", "Galaxy Book3", NB),
    _m("Samsung", "Odyssey G5", MON),
    _m("Samsung", "Odyssey G7", MON),
    _m("Microsoft", "Surface Laptop", NB),
    _m("Microsoft", "Surface Pro", NB),
    _m("LG", "UltraGear", MON),
    _m("LG", "UltraFine", MON),
    _m("Gigabyte", "G27", MON),
]

# ---------------------------------------------------------------------------
# PC parts — FAMILY
# ---------------------------------------------------------------------------
PARTS_BRANDS = [
    _b("Intel", CPU),
    _b("AMD", ("Процессоры", "Видеокарты")),
    _b("Nvidia", GPU),
    _b("Kingston", ("Оперативная память", "Накопители")),
    _b("Corsair", ("Оперативная память", "Блоки питания")),
    _b("G.Skill", RAM),
    _b("Samsung", SSD),
    _b("Western Digital", SSD),
    _b("Crucial", ("Оперативная память", "Накопители")),
    _b("Seagate", SSD),
    _b("Gigabyte", ("Материнские платы", "Видеокарты")),
    _b("MSI", ("Материнские платы", "Видеокарты")),
    _b("ASRock", MB),
    _b("ASUS", ("Материнские платы", "Видеокарты")),
    _b("be quiet!", PSU),
]

PARTS_MODELS = [
    _m("Intel", "Core Ultra 9", CPU),
    _m("Intel", "Core Ultra 7", CPU),
    _m("Intel", "Core Ultra 5", CPU),
    _m("Intel", "Core i9", CPU),
    _m("Intel", "Core i7", CPU),
    _m("Intel", "Core i5", CPU),
    _m("Intel", "Core i3", CPU),
    _m("AMD", "Ryzen 9", CPU),
    _m("AMD", "Ryzen 7", CPU),
    _m("AMD", "Ryzen 5", CPU),
    _m("AMD", "Ryzen 3", CPU),
    _m("AMD", "Radeon RX 7900", GPU),
    _m("AMD", "Radeon RX 7800", GPU),
    _m("AMD", "Radeon RX 7700", GPU),
    _m("AMD", "Radeon RX 7600", GPU),
    _m("Nvidia", "GeForce RTX 5090", GPU),
    _m("Nvidia", "GeForce RTX 5080", GPU),
    _m("Nvidia", "GeForce RTX 5070", GPU),
    _m("Nvidia", "GeForce RTX 4090", GPU),
    _m("Nvidia", "GeForce RTX 4080", GPU),
    _m("Nvidia", "GeForce RTX 4070 Ti", GPU),
    _m("Nvidia", "GeForce RTX 4070", GPU),
    _m("Nvidia", "GeForce RTX 4060 Ti", GPU),
    _m("Nvidia", "GeForce RTX 4060", GPU),
    _m("Nvidia", "GeForce RTX 3060", GPU),
    _m("Kingston", "Fury Beast", RAM),
    _m("Kingston", "Fury Renegade", RAM),
    _m("Kingston", "NV2", SSD),
    _m("Corsair", "Vengeance", RAM),
    _m("Corsair", "RM750", PSU),
    _m("Corsair", "RM850", PSU),
    _m("G.Skill", "Trident Z", RAM),
    _m("Samsung", "990 PRO", SSD),
    _m("Samsung", "990 EVO", SSD),
    _m("Samsung", "870 EVO", SSD),
    _m("Western Digital", "Black SN850X", SSD),
    _m("Western Digital", "Blue SN580", SSD),
    _m("Western Digital", "Blue", SSD),
    _m("Crucial", "T500", SSD),
    _m("Crucial", "MX500", SSD),
    _m("Seagate", "FireCuda", SSD),
    _m("Gigabyte", "B650", MB),
    _m("Gigabyte", "B760", MB),
    _m("MSI", "B650", MB),
    _m("MSI", "B760", MB),
    _m("ASRock", "B650", MB),
    _m("ASUS", "ROG Strix B650", MB),
    _m("ASUS", "TUF Gaming B760", MB),
    _m("be quiet!", "Pure Power", PSU),
]

# ---------------------------------------------------------------------------
# Office print — FAMILY
# ---------------------------------------------------------------------------
OFFICE_PRINT_BRANDS = [
    _b("HP", None),
    _b("Canon", None),
    _b("Epson", None),
    _b("Brother", None),
    _b("Kyocera", None),
    _b("Xerox", None),
    _b("Pantum", None),
]

OFFICE_PRINT_MODELS = [
    _m("HP", "LaserJet", ("Принтеры", "МФУ")),
    _m("HP", "DeskJet", ("Принтеры", "МФУ")),
    _m("HP", "OfficeJet", ("Принтеры", "МФУ")),
    _m("Canon", "PIXMA", ("Принтеры", "МФУ")),
    _m("Canon", "imageCLASS", ("Принтеры", "МФУ")),
    _m("Epson", "EcoTank", ("Принтеры", "МФУ")),
    _m("Epson", "L-series", ("Принтеры", "МФУ")),
    _m("Brother", "DCP", MFP),
    _m("Brother", "MFC", MFP),
    _m("Brother", "HL", PRINT),
    _m("Kyocera", "ECOSYS", ("Принтеры", "МФУ")),
    _m("Xerox", "WorkCentre", MFP),
    _m("Pantum", "Pantum P2500", PRINT),
    _m("Pantum", "Pantum M6500", MFP),
]

# ---------------------------------------------------------------------------
# TV / projectors — FAMILY
# ---------------------------------------------------------------------------
TV_BRANDS = [
    _b("Samsung", TV),
    _b("LG", TV),
    _b("Sony", TV),
    _b("Xiaomi", ("Телевизоры", "Проекторы")),
    _b("Hisense", TV),
    _b("TCL", TV),
    _b("Philips", TV),
    _b("Epson", PROJ),
    _b("BenQ", PROJ),
    _b("XGIMI", PROJ),
]

TV_MODELS = [
    _m("Samsung", "Crystal UHD", TV),
    _m("Samsung", "QLED", TV),
    _m("Samsung", "Neo QLED", TV),
    _m("Samsung", "OLED", TV),
    _m("Samsung", "The Frame", TV),
    _m("LG", "OLED", TV),
    _m("LG", "QNED", TV),
    _m("LG", "NanoCell", TV),
    _m("LG", "UQ", TV),
    _m("Sony", "Bravia", TV),
    _m("Xiaomi", "Xiaomi TV A", TV),
    _m("Xiaomi", "Xiaomi TV S", TV),
    _m("Xiaomi", "Mi TV", TV),
    _m("Xiaomi", "Mi Smart Projector", PROJ),
    _m("Hisense", "ULED", TV),
    _m("Hisense", "U7", TV),
    _m("Hisense", "A6", TV),
    _m("TCL", "C855", TV),
    _m("TCL", "C645", TV),
    _m("TCL", "P755", TV),
    _m("Philips", "Ambilight", TV),
    _m("Epson", "EH-TW", PROJ),
    _m("Epson", "CO-W", PROJ),
    _m("BenQ", "TH", PROJ),
    _m("XGIMI", "Horizon", PROJ),
]

# ---------------------------------------------------------------------------
# Audio — FAMILY
# ---------------------------------------------------------------------------
AUDIO_BRANDS = [
    _b("Apple", HP),
    _b("Samsung", ("Наушники", "Саундбары")),
    _b("Sony", ("Наушники", "Колонки")),
    _b("JBL", ("Колонки", "Наушники")),
    _b("Marshall", SPK),
    _b("Bose", ("Наушники", "Колонки")),
    _b("Xiaomi", ("Наушники", "Колонки")),
    _b("Anker", ("Наушники", "Колонки")),
    _b("Edifier", SPK),
    _b("Sennheiser", HP),
    _b("Beats", HP),
]

AUDIO_MODELS = [
    _m("Apple", "AirPods Pro 2", HP),
    _m("Apple", "AirPods Pro", HP),
    _m("Apple", "AirPods 4", HP),
    _m("Apple", "AirPods 3", HP),
    _m("Apple", "AirPods Max", HP),
    _m("Samsung", "Galaxy Buds3 Pro", HP),
    _m("Samsung", "Galaxy Buds3", HP),
    _m("Samsung", "Galaxy Buds2 Pro", HP),
    _m("Samsung", "Galaxy Buds FE", HP),
    _m("Samsung", "Galaxy Buds", HP),
    _m("Samsung", "HW-Q", SB),
    _m("Sony", "WH-1000XM5", HP),
    _m("Sony", "WH-1000XM4", HP),
    _m("Sony", "WF-1000XM5", HP),
    _m("Sony", "WH-CH720N", HP),
    _m("Sony", "SRS-XB", SPK),
    _m("JBL", "Flip 6", SPK),
    _m("JBL", "Flip 7", SPK),
    _m("JBL", "Charge 5", SPK),
    _m("JBL", "Charge 6", SPK),
    _m("JBL", "Tune 770NC", HP),
    _m("JBL", "Tune 520BT", HP),
    _m("Marshall", "Emberton II", SPK),
    _m("Marshall", "Emberton III", SPK),
    _m("Marshall", "Acton III", SPK),
    _m("Bose", "QuietComfort Ultra", HP),
    _m("Bose", "QuietComfort", HP),
    _m("Bose", "SoundLink Flex", SPK),
    _m("Xiaomi", "Redmi Buds", HP),
    _m("Xiaomi", "Buds 5", HP),
    _m("Anker", "Soundcore Life Q30", HP),
    _m("Anker", "Soundcore Motion", SPK),
    _m("Edifier", "R1280DB", SPK),
    _m("Edifier", "MR4", SPK),
    _m("Sennheiser", "Momentum 4", HP),
    _m("Beats", "Studio Buds", HP),
    _m("Beats", "Solo", HP),
]

# ---------------------------------------------------------------------------
# Photo — FAMILY
# ---------------------------------------------------------------------------
PHOTO_BRANDS = [
    _b("Canon", ("Фотоаппараты", "Объективы")),
    _b("Nikon", ("Фотоаппараты", "Объективы")),
    _b("Sony", ("Фотоаппараты", "Объективы", "Видеокамеры")),
    _b("Fujifilm", CAM),
    _b("Panasonic", ("Фотоаппараты", "Видеокамеры")),
    _b("GoPro", ACT),
    _b("DJI", ("Квадрокоптеры", "Экшн-камеры")),
    _b("Insta360", ACT),
]

PHOTO_MODELS = [
    _m("Canon", "EOS R50", CAM),
    _m("Canon", "EOS R10", CAM),
    _m("Canon", "EOS R8", CAM),
    _m("Canon", "EOS R6 Mark II", CAM),
    _m("Canon", "EOS 2000D", CAM),
    _m("Canon", "RF 24-105mm", LENS),
    _m("Nikon", "Z50", CAM),
    _m("Nikon", "Z30", CAM),
    _m("Nikon", "Z6 III", CAM),
    _m("Nikon", "D3500", CAM),
    _m("Sony", "Alpha 7 IV", CAM),
    _m("Sony", "Alpha 7C II", CAM),
    _m("Sony", "Alpha 6400", CAM),
    _m("Sony", "ZV-E10", VCAM),
    _m("Sony", "FX30", VCAM),
    _m("Fujifilm", "X-T50", CAM),
    _m("Fujifilm", "X-T30 II", CAM),
    _m("Fujifilm", "X-S20", CAM),
    _m("Panasonic", "Lumix G9 II", CAM),
    _m("Panasonic", "Lumix S5 II", CAM),
    _m("GoPro", "Hero 13 Black", ACT),
    _m("GoPro", "Hero 12 Black", ACT),
    _m("GoPro", "Hero 11 Black", ACT),
    _m("DJI", "Mini 4 Pro", DRONE),
    _m("DJI", "Mini 3", DRONE),
    _m("DJI", "Air 3", DRONE),
    _m("DJI", "Osmo Action 5 Pro", ACT),
    _m("DJI", "Osmo Action 4", ACT),
    _m("Insta360", "X4", ACT),
    _m("Insta360", "X3", ACT),
    _m("Insta360", "GO 3S", ACT),
]

# ---------------------------------------------------------------------------
# Consoles — FULL gens; Games → BRAND_ONLY (no game title catalog)
# ---------------------------------------------------------------------------
CONSOLE_BRANDS = [
    _b("Sony", ("Игровые приставки", "Геймпады")),
    _b("Microsoft", ("Игровые приставки", "Геймпады")),
    _b("Nintendo", ("Игровые приставки",)),
]

CONSOLE_MODELS = [
    _m("Sony", "PlayStation 5", CONS),
    _m("Sony", "PlayStation 5 Slim", CONS),
    _m("Sony", "PlayStation 5 Pro", CONS),
    _m("Sony", "PlayStation 4", CONS),
    _m("Sony", "PlayStation 4 Pro", CONS),
    _m("Sony", "DualSense", PAD),
    _m("Sony", "DualShock 4", PAD),
    _m("Microsoft", "Xbox Series X", CONS),
    _m("Microsoft", "Xbox Series S", CONS),
    _m("Microsoft", "Xbox One", CONS),
    _m("Microsoft", "Xbox One S", CONS),
    _m("Microsoft", "Xbox Wireless Controller", PAD),
    _m("Nintendo", "Switch 2", CONS),
    _m("Nintendo", "Switch OLED", CONS),
    _m("Nintendo", "Switch", CONS),
    _m("Nintendo", "Switch Lite", CONS),
]

# ---------------------------------------------------------------------------
# Wearables — FULL / FAMILY
# ---------------------------------------------------------------------------
WEARABLE_BRANDS = [
    _b("Apple", WATCH),
    _b("Samsung", ("Умные часы", "Фитнес-браслеты")),
    _b("Xiaomi", ("Умные часы", "Фитнес-браслеты")),
    _b("Huawei", ("Умные часы", "Фитнес-браслеты")),
    _b("Garmin", WATCH),
    _b("Amazfit", ("Умные часы", "Фитнес-браслеты")),
    _b("Meta", VR),
    _b("PlayStation", VR),
]

WEARABLE_MODELS = [
    _m("Apple", "Apple Watch Series 11", WATCH),
    _m("Apple", "Apple Watch Series 10", WATCH),
    _m("Apple", "Apple Watch Series 9", WATCH),
    _m("Apple", "Apple Watch Series 8", WATCH),
    _m("Apple", "Apple Watch SE (2nd generation)", WATCH),
    _m("Apple", "Apple Watch Ultra 2", WATCH),
    _m("Apple", "Apple Watch Ultra", WATCH),
    _m("Samsung", "Galaxy Watch Ultra", WATCH),
    _m("Samsung", "Galaxy Watch 7", WATCH),
    _m("Samsung", "Galaxy Watch 6", WATCH),
    _m("Samsung", "Galaxy Watch FE", WATCH),
    _m("Samsung", "Galaxy Fit3", BAND),
    _m("Xiaomi", "Xiaomi Watch S3", WATCH),
    _m("Xiaomi", "Redmi Watch 5", WATCH),
    _m("Xiaomi", "Redmi Watch 4", WATCH),
    _m("Xiaomi", "Smart Band 9", BAND),
    _m("Xiaomi", "Smart Band 8", BAND),
    _m("Huawei", "Watch GT 5", WATCH),
    _m("Huawei", "Watch GT 4", WATCH),
    _m("Huawei", "Band 9", BAND),
    _m("Garmin", "Forerunner 265", WATCH),
    _m("Garmin", "Forerunner 55", WATCH),
    _m("Garmin", "Venu 3", WATCH),
    _m("Amazfit", "Bip 5", WATCH),
    _m("Amazfit", "GTR 4", WATCH),
    _m("Amazfit", "Band 7", BAND),
    _m("Meta", "Quest 3S", VR),
    _m("Meta", "Quest 3", VR),
    _m("Meta", "Quest 2", VR),
    _m("PlayStation", "PlayStation VR2", VR),
]

# ---------------------------------------------------------------------------
# Network — FAMILY
# ---------------------------------------------------------------------------
NETWORK_BRANDS = [
    _b("TP-Link", None),
    _b("Keenetic", RTR),
    _b("MikroTik", ("Роутеры", "Коммутаторы")),
    _b("Xiaomi", RTR),
    _b("Huawei", RTR),
    _b("Asus", RTR),
    _b("Ubiquiti", ("Роутеры", "Коммутаторы")),
    _b("Mercusys", ("Роутеры", "Усилители сигнала")),
]

NETWORK_MODELS = [
    _m("TP-Link", "Archer AX55", RTR),
    _m("TP-Link", "Archer AX73", RTR),
    _m("TP-Link", "Archer C6", RTR),
    _m("TP-Link", "Deco X55", RTR),
    _m("TP-Link", "Deco M5", RTR),
    _m("Keenetic", "Hero", RTR),
    _m("Keenetic", "Giga", RTR),
    _m("Keenetic", "Extra", RTR),
    _m("Keenetic", "Hopper", RTR),
    _m("MikroTik", "hAP ax3", RTR),
    _m("MikroTik", "hAP ax2", RTR),
    _m("MikroTik", "RB4011", RTR),
    _m("Xiaomi", "Router AX3000", RTR),
    _m("Xiaomi", "Router AX6000", RTR),
    _m("Huawei", "WiFi AX3", RTR),
    _m("Asus", "RT-AX86U", RTR),
    _m("Asus", "RT-AX58U", RTR),
    _m("Ubiquiti", "UniFi Dream Machine", RTR),
    _m("Ubiquiti", "UniFi AP", ("Усилители сигнала",)),
    _m("Mercusys", "MR50G", RTR),
    _m("Mercusys", "MW306R", RTR),
]

# ---------------------------------------------------------------------------
# Office gear — FAMILY UPS; BRAND_ONLY shredders
# ---------------------------------------------------------------------------
OFFICE_GEAR_BRANDS = [
    _b("APC", UPS),
    _b("Ippon", UPS),
    _b("CyberPower", UPS),
    _b("Powercom", UPS),
    _b("Fellowes", ("Шредеры",)),
]

OFFICE_GEAR_MODELS = [
    _m("APC", "Back-UPS 650", UPS),
    _m("APC", "Back-UPS 850", UPS),
    _m("APC", "Back-UPS 1100", UPS),
    _m("APC", "Smart-UPS", UPS),
    _m("Ippon", "Back Basic 650", UPS),
    _m("Ippon", "Back Basic 850", UPS),
    _m("Ippon", "Smart Power Pro", UPS),
    _m("CyberPower", "UT650EG", UPS),
    _m("CyberPower", "UT850EG", UPS),
    _m("Powercom", "RPT-600A", UPS),
    _m("Powercom", "RPT-800A", UPS),
    _m("Fellowes", "Powershred", ("Шредеры",)),
]

# ---------------------------------------------------------------------------
# Appliances — FAMILY
# ---------------------------------------------------------------------------
APPLIANCE_BRANDS = [
    _b("Samsung", None),
    _b("LG", None),
    _b("Bosch", None),
    _b("Beko", None),
    _b("Haier", None),
    _b("Artel", None),
    _b("Midea", None),
    _b("Indesit", None),
    _b("Gorenje", None),
    _b("Hisense", None),
    _b("Xiaomi", ("Роботы-пылесосы", "Пылесосы")),
    _b("Dyson", ("Пылесосы",)),
    _b("Philips", ("Пылесосы",)),
    _b("Roborock", ROBOT),
]

APPLIANCE_MODELS = [
    _m("Samsung", "RB37", FRIDGE),
    _m("Samsung", "RB34", FRIDGE),
    _m("Samsung", "RB", FRIDGE),  # preserved Package A
    _m("Samsung", "RT", FRIDGE),
    _m("Samsung", "WW80", WASH),
    _m("Samsung", "WW90", WASH),
    _m("Samsung", "WW", WASH),  # preserved Package A
    _m("Samsung", "DV90", DRY),
    _m("Samsung", "VS20", VAC),
    _m("LG", "GC-B", FRIDGE),
    _m("LG", "GA-B", FRIDGE),
    _m("LG", "GC", FRIDGE),  # preserved Package A
    _m("LG", "F2V5", WASH),
    _m("LG", "F4V5", WASH),
    _m("LG", "F2", WASH),  # preserved Package A
    _m("LG", "RC90", DRY),
    _m("LG", "CordZero", VAC),
    _m("Bosch", "Serie 4 KGN", FRIDGE),
    _m("Bosch", "Serie 6 KGN", FRIDGE),
    _m("Bosch", "Serie 4 WAN", WASH),
    _m("Bosch", "Serie 6 WAU", WASH),
    _m("Bosch", "Serie 4", ("Холодильники", "Стиральные машины")),  # preserved
    _m("Beko", "RCNK", FRIDGE),
    _m("Beko", "WUE", WASH),
    _m("Haier", "C2F", FRIDGE),
    _m("Haier", "HW", WASH),
    _m("Haier", "Haier CE", WASH),  # preserved Package A
    _m("Artel", "Artel HD", FRIDGE),
    _m("Artel", "Artel HS", FRIDGE),  # preserved Package A
    _m("Artel", "Artel WF", WASH),
    _m("Midea", "MDRB", FRIDGE),
    _m("Midea", "MF100", WASH),
    _m("Midea", "Midea Robot", ROBOT),  # preserved Package A
    _m("Indesit", "ITF", FRIDGE),
    _m("Indesit", "BWSA", WASH),
    _m("Gorenje", "NRK", FRIDGE),
    _m("Gorenje", "WEI", WASH),
    _m("Hisense", "RB", FRIDGE),
    _m("Hisense", "WF", WASH),
    _m("Xiaomi", "Robot Vacuum S20", ROBOT),
    _m("Xiaomi", "Robot Vacuum X20", ROBOT),
    _m("Xiaomi", "Robot Vacuum", ROBOT),
    _m("Dyson", "V15 Detect", VAC),
    _m("Dyson", "V12 Detect Slim", VAC),
    _m("Dyson", "V8", VAC),
    _m("Philips", "Series 3000", VAC),
    _m("Roborock", "S8", ROBOT),
    _m("Roborock", "Q Revo", ROBOT),
    _m("Roborock", "Q5", ROBOT),
]

# ---------------------------------------------------------------------------
# Climate — FAMILY
# ---------------------------------------------------------------------------
CLIMATE_BRANDS = [
    _b("Midea", AC),
    _b("Gree", AC),
    _b("Haier", AC),
    _b("Samsung", AC),
    _b("LG", AC),
    _b("Artel", AC),
    _b("TCL", AC),
    _b("Daikin", AC),
    _b("Ballu", ("Обогреватели", "Вентиляторы", "Увлажнители")),
    _b("Electrolux", ("Обогреватели", "Увлажнители")),
    _b("Xiaomi", ("Очистители воздуха", "Увлажнители")),
]

CLIMATE_MODELS = [
    _m("Midea", "Blanc", AC),
    _m("Midea", "Mission", AC),
    _m("Gree", "Bora", AC),
    _m("Gree", "Lomo", AC),
    _m("Haier", "Coral", AC),
    _m("Haier", "Flexis", AC),
    _m("Samsung", "WindFree", AC),
    _m("Samsung", "AR", AC),
    _m("LG", "DualCool", AC),
    _m("Artel", "Artel Shahrisabz", AC),
    _m("TCL", "TAC", AC),
    _m("Daikin", "Sensira", AC),
    _m("Ballu", "Ballu BIH", HEAT),
    _m("Ballu", "Ballu BOH", HEAT),
    _m("Ballu", "Ballu BF", FAN),
    _m("Electrolux", "EOH", HEAT),
    _m("Electrolux", "EHU", HUM),
    _m("Xiaomi", "Mi Air Purifier 4", AIR),
    _m("Xiaomi", "Mi Air Purifier", AIR),
    _m("Xiaomi", "Smart Humidifier 2", HUM),
]

# ---------------------------------------------------------------------------
# Built-in — FAMILY
# ---------------------------------------------------------------------------
BUILTIN_BRANDS = [
    _b("Bosch", None),
    _b("Samsung", None),
    _b("Electrolux", None),
    _b("Gefest", None),
    _b("Gorenje", None),
    _b("Maunfeld", HOOD),
    _b("Krona", HOOD),
    _b("Weissgauff", None),
]

BUILTIN_MODELS = [
    _m("Bosch", "Serie 4 HBA", OVEN),
    _m("Bosch", "Serie 6 HBG", OVEN),
    _m("Bosch", "Serie 4 PKE", HOB),
    _m("Bosch", "Serie 6 PIX", HOB),
    _m("Bosch", "Serie 4 SMV", DISH),
    _m("Samsung", "NV75", OVEN),
    _m("Samsung", "NZ64", HOB),
    _m("Samsung", "DW60", DISH),
    _m("Electrolux", "EOE", OVEN),
    _m("Electrolux", "EIV", HOB),
    _m("Electrolux", "ESL", DISH),
    _m("Gefest", "Gefest ДА", OVEN),
    _m("Gefest", "Gefest СВН", HOB),
    _m("Gorenje", "BO", OVEN),
    _m("Gorenje", "IT", HOB),
    _m("Maunfeld", "Maunfeld Tower", HOOD),
    _m("Maunfeld", "Maunfeld Crosby", HOOD),
    _m("Krona", "Krona Kamilla", HOOD),
    _m("Weissgauff", "EOM", OVEN),
    _m("Weissgauff", "HV", HOOD),
]

# ---------------------------------------------------------------------------
# Kitchen — FAMILY / pragmatic
# ---------------------------------------------------------------------------
KITCHEN_BRANDS = [
    _b("Redmond", ("Мультиварки", "Блендеры", "Электрочайники")),
    _b("Philips", ("Блендеры", "Кофемашины")),
    _b("Bosch", ("Мясорубки", "Плиты")),
    _b("Tefal", ("Мультиварки", "Электрочайники", "Блендеры")),
    _b("DeLonghi", ("Кофемашины",)),
    _b("Artel", ("Плиты", "Микроволновые печи")),
    _b("Samsung", ("Микроволновые печи",)),
    _b("LG", ("Микроволновые печи",)),
    _b("Gefest", ("Плиты",)),
    _b("Moulinex", ("Блендеры", "Мясорубки")),
    _b("Kitfort", ("Мультиварки", "Блендеры", "Электрочайники")),
]

KITCHEN_MODELS = [
    _m("Redmond", "RMC-M", ("Мультиварки",)),
    _m("Redmond", "RHB", ("Блендеры",)),
    _m("Philips", "Series 5000", ("Блендеры",)),
    _m("Philips", "LatteGo", ("Кофемашины",)),
    _m("DeLonghi", "Magnifica S", ("Кофемашины",)),
    _m("DeLonghi", "Magnifica Evo", ("Кофемашины",)),
    _m("DeLonghi", "Dinamica", ("Кофемашины",)),
    _m("Artel", "Artel газовая плита", ("Плиты",)),
    _m("Artel", "Artel СВЧ", ("Микроволновые печи",)),
    _m("Gefest", "Gefest 3200", ("Плиты",)),
    _m("Gefest", "Gefest 5100", ("Плиты",)),
    _m("Samsung", "MS23K", ("Микроволновые печи",)),
    _m("Samsung", "ME83X", ("Микроволновые печи",)),
    _m("LG", "MS20", ("Микроволновые печи",)),
    _m("Bosch", "MFW3", ("Мясорубки",)),
    _m("Bosch", "HGA", ("Плиты",)),
    _m("Tefal", "Cook4me", ("Мультиварки",)),
    _m("Tefal", "KO", ("Электрочайники",)),
    _m("Moulinex", "DD55", ("Блендеры",)),
    _m("Kitfort", "KT", ("Мультиварки", "Блендеры", "Электрочайники")),
]

# ---------------------------------------------------------------------------
# Home — FAMILY
# ---------------------------------------------------------------------------
HOME_BRANDS = [
    _b("Philips", ("Утюги и отпариватели",)),
    _b("Tefal", ("Утюги и отпариватели",)),
    _b("Braun", ("Утюги и отпариватели",)),
    _b("Janome", ("Бытовые швейные машины",)),
    _b("Brother", ("Бытовые швейные машины",)),
    _b("Singer", ("Бытовые швейные машины",)),
    _b("Xiaomi", ("Напольные весы",)),
]

HOME_MODELS = [
    _m("Philips", "Azur", ("Утюги и отпариватели",)),
    _m("Philips", "PerfectCare", ("Утюги и отпариватели",)),
    _m("Tefal", "Ultimate Pure", ("Утюги и отпариватели",)),
    _m("Tefal", "Easygliss", ("Утюги и отпариватели",)),
    _m("Braun", "TexStyle", ("Утюги и отпариватели",)),
    _m("Janome", "Janome Sewist", ("Бытовые швейные машины",)),
    _m("Janome", "Janome Decor", ("Бытовые швейные машины",)),
    _m("Brother", "Brother Innov-is", ("Бытовые швейные машины",)),
    _m("Singer", "Singer Talent", ("Бытовые швейные машины",)),
    _m("Xiaomi", "Mi Body Composition Scale 2", ("Напольные весы",)),
    _m("Xiaomi", "Mi Smart Scale 2", ("Напольные весы",)),
]

# ---------------------------------------------------------------------------
# Accessories — BRAND_ONLY / compatibility labels for cases only (pragmatic)
# ---------------------------------------------------------------------------
ACCESSORY_BRANDS = [
    _b("Apple", ("Чехлы", "Защитные стёкла", "Зарядные устройства")),
    _b("Samsung", ("Чехлы", "Защитные стёкла", "Зарядные устройства")),
    _b("Xiaomi", ("Чехлы", "Защитные стёкла", "Зарядные устройства")),
    _b("Baseus", ("Зарядные устройства", "Кабели", "Внешние аккумуляторы")),
    _b("Anker", ("Зарядные устройства", "Внешние аккумуляторы", "Кабели")),
    _b("Ugreen", ("Кабели", "Зарядные устройства")),
]

ACCESSORY_MODELS = [
    # Compatibility targets — not device SKUs; kept as compatibility selectors
    _m("Apple", "для iPhone 17", ("Чехлы", "Защитные стёкла")),
    _m("Apple", "для iPhone 16", ("Чехлы", "Защитные стёкла")),
    _m("Apple", "для iPhone 15", ("Чехлы", "Защитные стёкла")),
    _m("Apple", "для iPhone 14", ("Чехлы", "Защитные стёкла")),
    _m("Samsung", "для Galaxy S25", ("Чехлы", "Защитные стёкла")),
    _m("Samsung", "для Galaxy S24", ("Чехлы", "Защитные стёкла")),
    _m("Samsung", "для Galaxy A55", ("Чехлы", "Защитные стёкла")),
    _m("Xiaomi", "для Redmi Note 14", ("Чехлы", "Защитные стёкла")),
    _m("Xiaomi", "для Redmi Note 13", ("Чехлы", "Защитные стёкла")),
    _m("Baseus", "GaN", ("Зарядные устройства",)),
    _m("Anker", "Nano", ("Зарядные устройства", "Внешние аккумуляторы")),
    _m("Ugreen", "USB-C", ("Кабели",)),
]

# ---------------------------------------------------------------------------
# Other — BRAND_ONLY / light FAMILY
# ---------------------------------------------------------------------------
OTHER_BRANDS = [
    _b("Resanta", ("Стабилизаторы напряжения",)),
    _b("Sven", ("Стабилизаторы напряжения", "Сетевые фильтры")),
    _b("Powercom", ("Стабилизаторы напряжения",)),
]

OTHER_MODELS = [
    _m("Resanta", "АСН", ("Стабилизаторы напряжения",)),
    _m("Sven", "AVR", ("Стабилизаторы напряжения",)),
    _m("Powercom", "TCA", ("Стабилизаторы напряжения",)),
]


# Source authority notes (developer audit; not user-facing labels)
CATALOG_SOURCE_NOTES: list[dict[str, Any]] = [
    {
        "kind_scope": "Смартфоны/Apple",
        "authority": "Apple Support Identify your iPhone model (support.apple.com/108044); apple.com/iphone",
        "checked": "2026-11-08",
    },
    {
        "kind_scope": "Смартфоны/Samsung",
        "authority": "Samsung official smartphone catalogs (samsung.com AU/US/UK); regional general catalog PDF",
        "checked": "2026-11-08",
    },
    {
        "kind_scope": "Смартфоны/Xiaomi+Redmi+POCO",
        "authority": "mi.com/global/mobile official product list",
        "checked": "2026-11-08",
        "architecture": "Brand=Xiaomi; Redmi/POCO as model labels (preserved Package A SoT)",
    },
    {
        "kind_scope": "Планшеты/Apple",
        "authority": "Apple Support Identify your iPad; apple.com/ipad/compare",
        "checked": "2026-11-08",
    },
    {
        "kind_scope": "Ноутбуки/Apple",
        "authority": "Apple Support MacBook Air/Pro identify pages; apple.com/mac/compare",
        "checked": "2026-11-08",
        "rule": "Size+chip generation is model; RAM/SSD are separate fields",
    },
    {
        "kind_scope": "Бытовая техника",
        "authority": "Manufacturer family lines (Samsung/LG/Bosch/Haier/Artel/Xiaomi/Roborock) — FAMILY depth",
        "checked": "2026-11-08",
    },
]
