# -*- coding: utf-8 -*-
"""Продажа «Животные».

Вид — само животное, корм или товар. Мёд, соты и зерно остаются в продуктах.
Читалки и седла сюда не входят. Лекарства для животных не продаём без лицензии:
в ветаптеке только уходовые товары. Осмотр и вакцинация — услуга, не препарат.
"""
from __future__ import annotations

from typing import Any


def _item(label: str, kinds: tuple[str, ...] | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"value": label, "label": label}
    if kinds:
        row["for_kinds"] = list(kinds)
    return row


def _opts(*labels: str) -> list[dict[str, Any]]:
    return [_item(label) for label in labels]


def _group(
    label: str,
    options: list[dict[str, Any]],
    applies_to: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    group: dict[str, Any] = {"label": label, "options": options}
    if applies_to:
        group["applies_to"] = list(applies_to)
    return group


def _seller(*labels: str) -> dict[str, Any]:
    return _group("Продавец", _opts(*labels))


def _condition(applies_to: tuple[str, ...] | None = None) -> dict[str, Any]:
    return _group("Состояние", _opts("Новое", "Б/у"), applies_to)


_FARM = ("Частное лицо", "Хозяйство", "Компания")
_PET = ("Частное лицо", "Питомник", "Магазин")
_SHOP = ("Частное лицо", "Магазин", "Компания")
_SEX = _opts("Самец", "Самка")

_SHEEP = ("Овцы", "Бараны", "Ягнята")
_GOATS = ("Козы", "Козлы", "Козлята")
_DOGS = (
    "Алабаи",
    "Немецкие овчарки",
    "Хаски",
    "Шпицы",
    "Йоркширские терьеры",
    "Той-терьеры",
    "Питбули",
    "Дворняги",
)
_CATS = (
    "Дворовые",
    "Британские",
    "Шотландские",
    "Сфинксы",
    "Мейн-куны",
    "Персидские",
    "Сиамские",
)


def _section(
    slug: str,
    label: str,
    question: str,
    kinds: tuple[str, ...],
    filters: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "category_slug": slug,
        "label": label,
        "question": question,
        "roles": _opts(*kinds),
        "filters": filters,
    }


ANIMALS_SECTIONS: dict[str, dict[str, Any]] = {
    "sheep": _section(
        "animals-ovtsy-barany-i-kozy",
        "Овцы, бараны и козы",
        "Какое животное?",
        (*_SHEEP, *_GOATS, "Другие овцы и козы"),
        [
            _seller(*_FARM),
            _group(
                "Назначение",
                [
                    _item("Для разведения"),
                    _item("На откорм"),
                    _item("На забой"),
                    _item("Для молока", ("Козы",)),
                ],
            ),
            _group(
                "Порода",
                [
                    _item("Гиссарские", _SHEEP),
                    _item("Эдильбаевские", _SHEEP),
                    _item("Арашан", _SHEEP),
                    _item("Романовские", _SHEEP),
                    _item("Зааненские", _GOATS),
                    _item("Местные"),
                ],
            ),
        ],
    ),
    "cattle": _section(
        "animals-korovy-byki-i-telyata",
        "Коровы, быки и телята",
        "Какое животное?",
        ("Коровы", "Быки", "Тёлки", "Телята", "Другой крупный рогатый скот"),
        [
            _seller(*_FARM),
            _group(
                "Назначение",
                [
                    _item("Для разведения"),
                    _item("На откорм"),
                    _item("На забой"),
                    _item("Для молока", ("Коровы", "Тёлки")),
                ],
            ),
            _group(
                "Порода",
                _opts("Голштин", "Швицкая", "Алатауская", "Симментальская", "Местные"),
            ),
        ],
    ),
    "horses": _section(
        "animals-loshadi",
        "Лошади",
        "Какое животное?",
        ("Кобылы", "Жеребцы", "Мерины", "Жеребята", "Другие лошади"),
        [
            _seller(*_FARM),
            _group(
                "Назначение",
                _opts("Для разведения", "Для работы", "Для верховой езды"),
            ),
        ],
    ),
    "poultry": _section(
        "animals-ptitsevodstvo",
        "Птицеводство",
        "Какое животное?",
        (
            "Куры",
            "Петухи",
            "Цыплята",
            "Инкубационные яйца",
            "Утки",
            "Гуси",
            "Индейки",
            "Перепела",
            "Другая птица",
        ),
        [
            _seller(*_FARM),
            _group(
                "Назначение",
                [
                    _item("Для разведения"),
                    _item("На забой"),
                    _item("Для яиц", ("Куры", "Утки", "Гуси", "Индейки", "Перепела")),
                ],
            ),
            _group(
                "Порода",
                [
                    _item("Домашние", ("Куры", "Петухи", "Цыплята")),
                    _item("Бройлеры", ("Куры", "Петухи", "Цыплята")),
                    _item("Несушки", ("Куры",)),
                    _item("Бойцовые", ("Куры", "Петухи")),
                ],
                ("Куры", "Петухи", "Цыплята"),
            ),
        ],
    ),
    "dogs": _section(
        "animals-sobaki",
        "Собаки",
        "Какое животное?",
        (*_DOGS, "Вязка собак", "Другие собаки"),
        [
            _seller(*_PET),
            _group("Пол", _SEX, (*_DOGS, "Другие собаки")),
        ],
    ),
    "cats": _section(
        "animals-koshki",
        "Кошки",
        "Какое животное?",
        (*_CATS, "Вязка кошек", "Другие кошки"),
        [
            _seller(*_PET),
            _group("Пол", _SEX, (*_CATS, "Другие кошки")),
        ],
    ),
    "rabbits": _section(
        "animals-kroliki",
        "Кролики",
        "Какое животное?",
        ("Калифорнийские", "Новозеландские", "Великаны", "Декоративные", "Другие кролики"),
        [_seller(*_PET), _group("Пол", _SEX)],
    ),
    "bees": _section(
        "animals-pchelovodstvo",
        "Пчеловодство",
        "Что ищете?",
        ("Пчелосемьи", "Пчёлы", "Ульи", "Рамки", "Другое для пчеловодства"),
        [
            _seller(*_FARM),
            _condition(("Ульи", "Рамки")),
        ],
    ),
    "fish": _section(
        "animals-ryby-i-akvariumistika",
        "Рыбы и аквариумистика",
        "Что ищете?",
        (
            "Аквариумные рыбы",
            "Прудовые рыбы",
            "Аквариумы",
            "Оборудование для аквариума",
            "Другие рыбы и аквариумы",
        ),
        [
            _seller(*_SHOP),
            _condition(("Аквариумы", "Оборудование для аквариума")),
        ],
    ),
    "rodents": _section(
        "animals-gryzuny",
        "Грызуны",
        "Какое животное?",
        (
            "Хомяки",
            "Морские свинки",
            "Крысы",
            "Мыши",
            "Шиншиллы",
            "Дегу",
            "Другие грызуны",
        ),
        [_seller(*_PET), _group("Пол", _SEX)],
    ),
    "reptiles": _section(
        "animals-reptilii-ekzoticheskie-zhivotnye",
        "Рептилии/экзотические животные",
        "Какое животное?",
        ("Черепахи", "Змеи", "Ящерицы", "Пауки", "Другие экзотические животные"),
        [_seller(*_PET), _group("Пол", _SEX)],
    ),
    "feed": _section(
        "animals-seno-korma-i-kormovye-dobavki",
        "Сено, Корма и кормовые добавки",
        "Какой товар?",
        (
            "Сено",
            "Солома",
            "Комбикорм",
            "Отруби",
            "Премиксы",
            "Соль-лизунец",
            "Другие корма",
        ),
        [_seller(*_SHOP)],
    ),
    "accessories": _section(
        "animals-tovary-aksessuary-dlya-zhivotnyh",
        "Товары/аксессуары для животных",
        "Какой товар?",
        (
            "Ошейники",
            "Поводки",
            "Переноски",
            "Клетки",
            "Миски",
            "Лежанки",
            "Игрушки для животных",
            "Другие аксессуары для животных",
        ),
        [_seller(*_SHOP), _condition()],
    ),
    "vetgoods": _section(
        "animals-vetapteka-i-veterinarnye-tovary",
        "Ветаптека и ветеринарные товары",
        "Какой товар?",
        (
            "Шампуни для животных",
            "Ошейники от блох",
            "Витамины для животных",
            "Ветеринарные бинты",
            "Термометры для животных",
            "Другие ветеринарные товары",
        ),
        [
            _seller("Ветаптека", "Частное лицо", "Магазин", "Компания"),
            _condition(),
        ],
    ),
    "vetservices": _section(
        "animals-veterinarnye-uslugi",
        "Ветеринарные услуги",
        "Какая услуга?",
        (
            "Осмотр",
            "Вакцинация",
            "Стерилизация и кастрация",
            "Хирургия",
            "Стационар",
            "Груминг",
            "Другие ветеринарные услуги",
        ),
        [
            _group(
                "Исполнитель",
                [
                    _item("Ветеринар"),
                    _item("Клиника"),
                    _item("Грумер", ("Груминг",)),
                    _item("Компания"),
                ],
            ),
        ],
    ),
    "other": _section(
        "animals-prochie-zhivotnye",
        "Прочие животные",
        "Какое животное?",
        ("Свиньи", "Ослы", "Верблюды", "Другие животные"),
        [_seller(*_FARM)],
    ),
}


def build_animals_section_catalog(section_key: str) -> dict[str, Any] | None:
    return ANIMALS_SECTIONS.get(section_key)
