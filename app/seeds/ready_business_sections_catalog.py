# -*- coding: utf-8 -*-
"""Продажа «Готовый бизнес».

Вид — форма точки: магазин, бутик, островок, цех. Не ассортимент внутри неё.
Оборудование, витрины и станки остаются
в «Оборудовании для бизнеса». Лекарства остаются вне каталога: аптека здесь
это действующая точка с лицензией, а не полка препаратов.
"""
from __future__ import annotations

from typing import Any


def _item(label: str) -> dict[str, Any]:
    return {"value": label, "label": label}


def _opts(*labels: str) -> list[dict[str, Any]]:
    return [_item(label) for label in labels]


def _group(label: str, options: tuple[str, ...]) -> dict[str, Any]:
    return {"label": label, "options": _opts(*options)}


def _seller(options: tuple[str, ...] = ("Собственник", "Компания", "Агентство")) -> dict[str, Any]:
    return _group("Продавец", options)


def _premises() -> dict[str, Any]:
    return _group("Помещение", ("В собственности", "В аренде", "Без помещения"))


def _section(
    slug: str,
    label: str,
    kinds: tuple[str, ...],
    *,
    seller: tuple[str, ...] = ("Собственник", "Компания", "Агентство"),
    premises: bool = True,
) -> dict[str, Any]:
    filters = [_seller(seller)]
    if premises:
        filters.append(_premises())
    return {
        "category_slug": slug,
        "label": label,
        "question": "Какой бизнес?",
        "roles": _opts(*kinds),
        "filters": filters,
    }


READY_BUSINESS_SECTIONS: dict[str, dict[str, Any]] = {
    "shops": _section(
        "ready-business-magaziny-i-torgovye-tochki",
        "Магазины и торговые точки",
        (
            "Магазины",
            "Бутики",
            "Островки",
            "Киоски",
            "Павильоны",
            "Оптовые базы",
            "Другие торговые точки",
        ),
    ),
    "horeca": _section(
        "ready-business-kafe-restorany-i-obschepit",
        "Кафе, рестораны и общепит",
        (
            "Кафе",
            "Рестораны",
            "Фастфуд",
            "Фудтраки",
            "Столовые",
            "Другой общепит",
        ),
    ),
    "hotels": _section(
        "ready-business-gostinitsy-i-gostevye-doma",
        "Гостиницы и гостевые дома",
        (
            "Гостиницы",
            "Гостевые дома",
            "Хостелы",
            "Базы отдыха",
            "Другие объекты размещения",
        ),
    ),
    "salons": _section(
        "ready-business-salony-krasoty-i-barbershopy",
        "Салоны красоты и барбершопы",
        (
            "Салоны",
            "Барбершопы",
            "Студии",
            "Кабинеты",
            "СПА",
            "Другие салоны",
        ),
    ),
    "sewing": _section(
        "ready-business-shveynye-tseha-i-atele",
        "Швейные цеха и ателье",
        ("Цеха", "Ателье", "Мастерские", "Другие швейные бизнесы"),
    ),
    "production": _section(
        "ready-business-proizvodstvo-i-tseha",
        "Производство и цеха",
        (
            "Заводы",
            "Линии",
            "Другое производство",
        ),
    ),
    "auto": _section(
        "ready-business-avtomoyki-avtouslugi-i-sto",
        "Автомойки/автоуслуги и СТО",
        ("Автомойки", "СТО", "Боксы", "Другой автобизнес"),
    ),
    "medical": _section(
        "ready-business-meditsinskie-tsentry-i-apteki",
        "Медицинские центры и аптеки",
        (
            "Клиники",
            "Центры",
            "Аптеки",
            "Лаборатории",
            "Другие медицинские бизнесы",
        ),
    ),
    "education": _section(
        "ready-business-obrazovatelnye-tsentry",
        "Образовательные центры",
        (
            "Центры обучения",
            "Школы",
            "Детские сады",
            "Курсы",
            "Другие образовательные бизнесы",
        ),
    ),
    "online": _section(
        "ready-business-onlayn-magaziny",
        "Онлайн магазины",
        (
            "Интернет-магазины",
            "Витрины",
            "Маркетплейсы",
            "Другие онлайн-магазины",
        ),
        premises=False,
    ),
    "franchise": _section(
        "ready-business-franshizy",
        "Франшизы",
        (
            "Франшиза точки",
            "Региональная франшиза",
            "Мастер-франшиза",
            "Другие франшизы",
        ),
        seller=("Франчайзер", "Компания", "Агентство"),
        premises=False,
    ),
    "farm": _section(
        "ready-business-selskohozyaystvennyy-biznes",
        "Сельскохозяйственный бизнес",
        ("Хозяйства", "Тепличные хозяйства", "Другой сельхозбизнес"),
    ),
    "leisure": _section(
        "ready-business-razvlekatelnyy-biznes",
        "Развлекательный бизнес",
        (
            "Клубы",
            "Залы",
            "Аттракционы",
            "Площадки",
            "Другой развлекательный бизнес",
        ),
    ),
    "tourism": _section(
        "ready-business-turisticheskiy-biznes",
        "Туристический бизнес",
        (
            "Агентства",
            "Операторы",
            "Бюро",
            "Прокат",
            "Другой туристический бизнес",
        ),
    ),
    "finance": _section(
        "ready-business-finansovyy-investits-nyy-biznes",
        "Финансовый/инвестиц.ный бизнес",
        ("Ломбарды", "Обменные пункты", "Офисы", "Другой финансовый бизнес"),
    ),
    "crypto": _section(
        "ready-business-kriptobiznes-i-tsifrovye-aktivy",
        "Криптобизнес и цифровые активы",
        ("Майнинг-фермы", "Криптообменные точки", "Другой криптобизнес"),
    ),
    "shares": _section(
        "ready-business-dolya-v-biznese-i-investitsii",
        "Доля в бизнесе и инвестиции",
        (
            "Доля",
            "Пакет",
            "Партнёрство",
            "Другие доли и инвестиции",
        ),
        seller=("Собственник", "Компания"),
        premises=False,
    ),
    "turnkey": _section(
        "ready-business-biznes-pod-klyuch",
        "Бизнес под ключ",
        (
            "Точка под ключ",
            "Сеть под ключ",
            "Цех под ключ",
            "Офис под ключ",
            "Другой бизнес под ключ",
        ),
    ),
    "other": _section(
        "ready-business-prochiy-gotovyy-biznes",
        "Прочий готовый бизнес",
        ("Вендинг", "Готовые ОсОО", "Другой готовый бизнес"),
    ),
}


def build_ready_business_section_catalog(section_key: str) -> dict[str, Any] | None:
    return READY_BUSINESS_SECTIONS.get(section_key)
