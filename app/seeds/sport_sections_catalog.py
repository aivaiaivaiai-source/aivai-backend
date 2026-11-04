# -*- coding: utf-8 -*-
"""Продажа «Спорт, отдых и хобби».

Вид — сам товар. Одежда, обувь, рюкзаки и перчатки остаются в одежде.
Детские велосипеды и самокаты — в детском мире, взрослые велосипеды — в транспорте.
Бильярд, игровые автоматы и тренажёры для залов — в оборудовании для бизнеса.
Приставки и наушники — в технике. Краски, ноты и книги — в канцтоварах.
Пряжа и ткани — в сырье. Лошади — в животных, амуниция — здесь.
Лекарства и витаминные комплексы — в медтоварах.
"""
from __future__ import annotations

from typing import Any


def _item(label: str) -> dict[str, Any]:
    return {"value": label, "label": label}


def _opts(*labels: str) -> list[dict[str, Any]]:
    return [_item(label) for label in labels]


def _group(label: str, options: tuple[str, ...]) -> dict[str, Any]:
    return {"label": label, "options": _opts(*options)}


def _seller(*labels: str) -> dict[str, Any]:
    return _group("Продавец", labels or ("Частное лицо", "Магазин", "Компания"))


def _condition() -> dict[str, Any]:
    return _group("Состояние", ("Новое", "Б/у"))


def _goods() -> list[dict[str, Any]]:
    return [_seller(), _condition()]


def _section(
    slug: str,
    label: str,
    kinds: tuple[str, ...],
    filters: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "category_slug": slug,
        "label": label,
        "question": "Какой товар?",
        "roles": _opts(*kinds),
        "filters": filters if filters is not None else _goods(),
    }


SPORT_SECTIONS: dict[str, dict[str, Any]] = {
    "sport": _section(
        "sports-hobby-sportivnye-tovary",
        "Спортивные товары",
        (
            "Мячи",
            "Ракетки",
            "Клюшки",
            "Боксёрские перчатки",
            "Шлемы",
            "Коньки",
            "Лыжи",
            "Сноуборды",
            "Роликовые коньки",
            "Скейтборды",
            "Другие спортивные товары",
        ),
    ),
    "fitness": _section(
        "sports-hobby-fitnes-i-trenazhery",
        "Фитнес и тренажёры",
        (
            "Беговые дорожки",
            "Велотренажёры",
            "Эллиптические тренажёры",
            "Гантели",
            "Гири",
            "Штанги и блины",
            "Коврики для йоги",
            "Эспандеры",
            "Другие тренажёры",
        ),
    ),
    "nutrition": _section(
        "sports-hobby-sportivnoe-pitanie",
        "Спортивное питание",
        (
            "Протеин",
            "Гейнеры",
            "Креатин",
            "Аминокислоты",
            "Изотоники",
            "Спортивные батончики",
            "Другое спортивное питание",
        ),
        [_seller()],
    ),
    "camping": _section(
        "sports-hobby-turizm-i-kemping",
        "Туризм и кемпинг",
        (
            "Палатки",
            "Спальники",
            "Туристические коврики",
            "Туристические рюкзаки",
            "Туристические горелки",
            "Термосы",
            "Треккинговые палки",
            "Другие товары для кемпинга",
        ),
    ),
    "hunting": _section(
        "sports-hobby-ohota-i-rybalka",
        "Охота и рыбалка",
        (
            "Удочки",
            "Спиннинги",
            "Катушки",
            "Блёсны и приманки",
            "Садки и подсачеки",
            "Эхолоты",
            "Охотничьи ножи",
            "Манки",
            "Другие товары для рыбалки и охоты",
        ),
    ),
    "music": _section(
        "sports-hobby-muzykalnye-instrumenty",
        "Музыкальные инструменты",
        (
            "Гитары",
            "Скрипки",
            "Барабаны",
            "Пианино",
            "Синтезаторы",
            "Духовые инструменты",
            "Укулеле",
            "Другие музыкальные инструменты",
        ),
    ),
    "kyrgyz": _section(
        "sports-hobby-kyrgyzskie-muzyk-nye-inst-menty",
        "Кыргызские музык.ные инст.менты",
        (
            "Комуз",
            "Кыл кыяк",
            "Темир комуз",
            "Чоор",
            "Сыбызгы",
            "Добулбас",
            "Другие кыргызские инструменты",
        ),
        [_seller("Частное лицо", "Мастерская", "Магазин"), _condition()],
    ),
    "yurts": _section(
        "sports-hobby-yurty-i-natsionalnye-izdeliya",
        "Юрты и национальные изделия",
        (
            "Юрты",
            "Тундуки",
            "Ууки",
            "Канаты для юрты",
            "Боо",
            "Другие национальные изделия",
        ),
        [_seller("Частное лицо", "Мастерская", "Магазин"), _condition()],
    ),
    "felt": _section(
        "sports-hobby-shyrdaki-i-izdeliya-iz-voyloka",
        "Шырдаки и изделия из войлока",
        (
            "Шырдаки",
            "Ала кийиз",
            "Войлочные ковры",
            "Войлочные сумки",
            "Войлочные тапочки",
            "Другие изделия из войлока",
        ),
        [_seller("Частное лицо", "Мастерская", "Магазин"), _condition()],
    ),
    "horse": _section(
        "sports-hobby-konnyy-sport-i-verhovaya-ezda",
        "Конный спорт и верховая езда",
        (
            "Сёдла",
            "Уздечки",
            "Вальтрапы",
            "Стремена",
            "Хлысты",
            "Амуниция",
            "Другие товары для верховой езды",
        ),
    ),
    "collect": _section(
        "sports-hobby-kollektsionirovanie",
        "Коллекционирование",
        (
            "Монеты",
            "Банкноты",
            "Марки",
            "Значки",
            "Модели",
            "Другие предметы коллекционирования",
        ),
    ),
    "board": _section(
        "sports-hobby-nastolnye-igry",
        "Настольные игры",
        (
            "Тогуз коргоол",
            "Шахматы",
            "Шашки",
            "Нарды",
            "Карты",
            "Настольные стратегии",
            "Пазлы",
            "Другие настольные игры",
        ),
    ),
    "craft": _section(
        "sports-hobby-rukodelie-i-tvorchestvo",
        "Рукоделие и творчество",
        (
            "Спицы и крючки",
            "Наборы для вышивания",
            "Бисер",
            "Макраме",
            "Валяние",
            "Мыловарение",
            "Другие товары для рукоделия",
        ),
    ),
    "antique": _section(
        "sports-hobby-antikvariat-i-predmety-iskusstva",
        "Антиквариат и предметы искусства",
        (
            "Картины",
            "Скульптуры",
            "Иконы",
            "Старинная посуда",
            "Антикварные часы",
            "Другие предметы искусства",
        ),
    ),
    "other": _section(
        "sports-hobby-prochee-dlya-sporta-otdyha-i-hobbi",
        "Прочее для спорта, отдыха и хобби",
        (
            "Металлоискатели",
            "Бинокли",
            "Воздушные змеи",
            "Другие товары для хобби",
        ),
    ),
}


def build_sport_section_catalog(section_key: str) -> dict[str, Any] | None:
    return SPORT_SECTIONS.get(section_key)
