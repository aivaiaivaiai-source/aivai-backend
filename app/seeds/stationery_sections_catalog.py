# -*- coding: utf-8 -*-
"""Продажа «Канцтовары и книги».

Вид — сама книга или сам товар. Детские книги остаются в детском мире.
Читалки и планшеты — в технике. Принтеры — в оргтехнике.
Пряжа, инструменты и антиквариат не из книг — в спорте и хобби.
"""
from __future__ import annotations

from typing import Any


def _item(label: str) -> dict[str, Any]:
    return {"value": label, "label": label}


def _opts(*labels: str) -> list[dict[str, Any]]:
    return [_item(label) for label in labels]


def _group(
    label: str,
    options: tuple[str, ...],
    applies_to: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    group: dict[str, Any] = {"label": label, "options": _opts(*options)}
    if applies_to:
        group["applies_to"] = list(applies_to)
    return group


def _seller() -> dict[str, Any]:
    return _group("Продавец", ("Частное лицо", "Магазин", "Компания"))


def _condition() -> dict[str, Any]:
    return _group("Состояние", ("Новое", "Б/у"))


_SCHOOL = (
    "Математика",
    "Алгебра",
    "Геометрия",
    "Кыргызский язык",
    "Русский язык",
    "Английский язык",
    "Литература",
    "История",
    "Биология",
    "Химия",
    "Физика",
    "География",
    "Информатика",
    "Прописи",
    "Школьные атласы",
)

_GRADES = tuple(f"{grade} класс" for grade in range(1, 12))


def _base_filters() -> list[dict[str, Any]]:
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
        "filters": filters if filters is not None else _base_filters(),
    }


STATIONERY_SECTIONS: dict[str, dict[str, Any]] = {
    "stationery": _section(
        "stationery-books-kantselyarskie-tovary",
        "Канцелярские товары",
        (
            "Ручки",
            "Карандаши",
            "Тетради",
            "Блокноты",
            "Ежедневники",
            "Пеналы",
            "Линейки",
            "Клей",
            "Корректоры",
            "Канцелярские ножницы",
            "Другие канцелярские товары",
        ),
    ),
    "textbooks": _section(
        "stationery-books-uchebniki-i-uchebnye-posobiya",
        "Учебники и учебные пособия",
        (
            *_SCHOOL,
            "Подготовка к ОРТ",
            "Вузские учебники",
            "Другие учебники",
        ),
        [
            *_base_filters(),
            _group("Класс", _GRADES, _SCHOOL),
            _group("Язык", ("Кыргызский", "Русский", "Английский")),
        ],
    ),
    "fiction": _section(
        "stationery-books-hudozhestvennaya-literatura",
        "Художественная литература",
        (
            "Романы",
            "Детективы",
            "Фантастика",
            "Фэнтези",
            "Поэзия",
            "Повести и рассказы",
            "Пьесы",
            "Другая художественная литература",
        ),
    ),
    "science": _section(
        "stationery-books-nauchnaya-literatura",
        "Научная литература",
        (
            "Научно-популярные",
            "Психология",
            "Саморазвитие",
            "Бизнес-книги",
            "Философия",
            "Право",
            "Другая научная литература",
        ),
    ),
    "religion": _section(
        "stationery-books-religioznaya-literatura",
        "Религиозная литература",
        (
            "Коран",
            "Библия",
            "Исламская литература",
            "Христианская литература",
            "Другая религиозная литература",
        ),
    ),
    "foreign": _section(
        "stationery-books-inostrannaya-literatura",
        "Иностранная литература",
        (
            "Книги на английском",
            "Книги на немецком",
            "Книги на турецком",
            "Книги на китайском",
            "Книги на корейском",
            "Другая иностранная литература",
        ),
    ),
    "ebooks": _section(
        "stationery-books-elektronnye-knigi",
        "Электронные книги",
        (
            "Аудиокниги",
            "Электронные учебные издания",
            "Электронная художественная литература",
            "Другие электронные издания",
        ),
    ),
    "art": _section(
        "stationery-books-tovary-dlya-tvorchestva-risovaniya",
        "Товары для творчества/рисования",
        (
            "Краски для рисования",
            "Кисти",
            "Цветные карандаши",
            "Фломастеры и маркеры",
            "Бумага для рисования",
            "Холсты",
            "Пластилин",
            "Мольберты",
            "Другие товары для рисования",
        ),
    ),
    "office": _section(
        "stationery-books-tovary-dlya-ofisa",
        "Товары для офиса",
        (
            "Бумага",
            "Папки и файлы",
            "Конверты",
            "Степлеры",
            "Дыроколы",
            "Штампы и печати",
            "Калькуляторы",
            "Бейджи",
            "Другие офисные товары",
        ),
    ),
    "globes": _section(
        "stationery-books-globusy-karty",
        "Глобусы, карты",
        (
            "Глобусы",
            "Настенные карты",
            "Дорожные карты",
            "Другие карты и глобусы",
        ),
    ),
    "music": _section(
        "stationery-books-muzykalnye-knigi-i-noty",
        "Музыкальные книги и ноты",
        (
            "Ноты",
            "Самоучители",
            "Песенники",
            "Другие ноты и музыкальные книги",
        ),
    ),
    "comics": _section(
        "stationery-books-komiksy-manga-grafich-e-romany",
        "Комиксы, манга/графич.е романы",
        (
            "Комиксы",
            "Манга",
            "Манхва",
            "Графические романы",
            "Другие комиксы",
        ),
    ),
    "magazines": _section(
        "stationery-books-zhurnaly-i-periodicheskie-izdaniya",
        "Журналы и периодические издания",
        (
            "Журналы",
            "Газеты",
            "Каталоги",
            "Другие периодические издания",
        ),
    ),
    "rare": _section(
        "stationery-books-kollektsionnye-i-redkie-izdaniya",
        "Коллекционные и редкие издания",
        (
            "Редкие книги",
            "Подарочные издания",
            "Книги с автографом",
            "Другие коллекционные издания",
        ),
    ),
    "other": _section(
        "stationery-books-prochie-knigi-i-kantstovary",
        "Прочие книги и канцтовары",
        (
            "Закладки",
            "Обложки для книг",
            "CD и DVD",
            "Другие книги и канцтовары",
        ),
    ),
}


def build_stationery_section_catalog(section_key: str) -> dict[str, Any] | None:
    return STATIONERY_SECTIONS.get(section_key)
