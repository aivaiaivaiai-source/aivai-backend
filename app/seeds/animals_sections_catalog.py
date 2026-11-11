# -*- coding: utf-8 -*-
"""Продажа «Животные».

Вид — само животное, корм или товар. Мёд, соты и зерно остаются в продуктах.
Читалки и седла сюда не входят. Лекарства для животных не продаём без лицензии:
в ветаптеке только уходовые товары. Ветеринарные услуги — в Services.
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


# Canonical Animals seller override (Package A) — one catalog for all L2.
_SELLER = ("Частное лицо", "Хозяйство", "Питомник", "Магазин", "Другой")
_SEX = _opts("Самец", "Самка")
_CONDITION = _opts("Новое", "Б/у")

# Live-animal kinds are product/animal types — not breed catalogs (V2).
_SHEEP = ("Овцы", "Бараны", "Ягнята")
_GOATS = ("Козы", "Козлы", "Козлята")
_DOGS = ("Собаки", "Щенки", "Другие собаки")
_CATS = ("Кошки", "Котята", "Другие кошки")
_RABBITS = ("Кролики", "Декоративные кролики", "Другие кролики")


def _seller() -> dict[str, Any]:
    return _group("Кто продаёт", _opts(*_SELLER))


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
        [_seller()],
    ),
    "cattle": _section(
        "animals-korovy-byki-i-telyata",
        "Коровы, быки и телята",
        "Какое животное?",
        ("Коровы", "Быки", "Тёлки", "Телята", "Другой крупный рогатый скот"),
        [_seller()],
    ),
    "horses": _section(
        "animals-loshadi",
        "Лошади",
        "Какое животное?",
        ("Кобылы", "Жеребцы", "Мерины", "Жеребята", "Другие лошади"),
        [_seller()],
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
        [_seller()],
    ),
    "dogs": _section(
        "animals-sobaki",
        "Собаки",
        "Какое животное?",
        (*_DOGS, "Вязка собак"),
        [
            _seller(),
            _group("Пол", _SEX, _DOGS),
        ],
    ),
    "cats": _section(
        "animals-koshki",
        "Кошки",
        "Какое животное?",
        (*_CATS, "Вязка кошек"),
        [
            _seller(),
            _group("Пол", _SEX, _CATS),
        ],
    ),
    "rabbits": _section(
        "animals-kroliki",
        "Кролики",
        "Какое животное?",
        _RABBITS,
        [_seller(), _group("Пол", _SEX)],
    ),
    "bees": _section(
        "animals-pchelovodstvo",
        "Пчеловодство",
        "Что ищете?",
        ("Пчелосемьи", "Пчёлы", "Ульи", "Рамки", "Другое для пчеловодства"),
        [
            _seller(),
            _group("Состояние", _CONDITION, ("Ульи", "Рамки")),
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
            _seller(),
            _group(
                "Состояние",
                _CONDITION,
                ("Аквариумы", "Оборудование для аквариума"),
            ),
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
        [_seller(), _group("Пол", _SEX)],
    ),
    "reptiles": _section(
        "animals-reptilii-ekzoticheskie-zhivotnye",
        "Рептилии/экзотические животные",
        "Какое животное?",
        ("Черепахи", "Змеи", "Ящерицы", "Пауки", "Другие экзотические животные"),
        [_seller(), _group("Пол", _SEX)],
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
        [_seller()],
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
        [_seller(), _group("Состояние", _CONDITION)],
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
        [_seller()],
    ),
    "other": _section(
        "animals-prochie-zhivotnye",
        "Прочие животные",
        "Какое животное?",
        ("Свиньи", "Ослы", "Верблюды", "Другие животные"),
        [_seller(), _group("Пол", _SEX)],
    ),
}


def build_animals_section_catalog(section_key: str) -> dict[str, Any] | None:
    return ANIMALS_SECTIONS.get(section_key)
