# -*- coding: utf-8 -*-
"""Продажа «Медтовары».

Лекарственные препараты сюда не входят: таблетки, антибиотики, инсулин,
антисептики-лекарства и средства для похудения. Их продажа требует лицензии.
Клинические установки, стерилизаторы, кушетки и аппараты УЗИ остаются
в оборудовании для бизнеса. Солнцезащитные очки — в одежде.
Детские ходунки, подгузники и матрасы — в детском мире.
"""
from __future__ import annotations

from typing import Any


def _item(label: str) -> dict[str, Any]:
    return {"value": label, "label": label}


def _opts(*labels: str) -> list[dict[str, Any]]:
    return [_item(label) for label in labels]


def _group(label: str, options: tuple[str, ...]) -> dict[str, Any]:
    return {"label": label, "options": _opts(*options)}


def _seller() -> dict[str, Any]:
    return _group("Продавец", ("Аптека", "Частное лицо", "Магазин", "Компания"))


def _condition() -> dict[str, Any]:
    return _group("Состояние", ("Новое", "Б/у"))


def _section(slug: str, label: str, kinds: tuple[str, ...]) -> dict[str, Any]:
    return {
        "category_slug": slug,
        "label": label,
        "question": "Какой товар?",
        "roles": _opts(*kinds),
        "filters": [_seller(), _condition()],
    }


MED_SECTIONS: dict[str, dict[str, Any]] = {
    "ortho": _section(
        "medical-ortopedicheskie-tovary",
        "Ортопедические товары",
        (
            "Бандажи",
            "Корсеты",
            "Корректоры осанки",
            "Ортезы",
            "Вальгусные шины",
            "Ортопедические стельки",
            "Наколенники",
            "Ортопедические подушки",
            "Другие ортопедические товары",
        ),
    ),
    "rehab": _section(
        "medical-reabilitatsionnye-tovary",
        "Реабилитационные товары",
        (
            "Инвалидные коляски",
            "Медицинские ходунки",
            "Костыли",
            "Трости",
            "Роллаторы",
            "Другие реабилитационные товары",
        ),
    ),
    "care": _section(
        "medical-tovary-dlya-uhoda-za-bolnymi",
        "Товары для ухода за больными",
        (
            "Противопролежневые матрасы",
            "Подгузники для взрослых",
            "Впитывающие пелёнки",
            "Мочеприёмники",
            "Санитарные кресла",
            "Другие товары для ухода",
        ),
    ),
    "devices": _section(
        "medical-meditsinskie-pribory",
        "Медицинские приборы",
        (
            "Тонометры",
            "Градусники",
            "Пульсоксиметры",
            "Кварцевые лампы",
            "Бактерицидные рециркуляторы",
            "Алкотестеры",
            "Другие медицинские приборы",
        ),
    ),
    "consumables": _section(
        "medical-rashodnye-med-materialy",
        "Расходные мед материалы",
        (
            "Бинты и повязки",
            "Пластыри",
            "Шприцы",
            "Инфузионные системы",
            "Медицинские перчатки",
            "Другие расходные материалы",
        ),
    ),
    "ppe": _section(
        "medical-sredstva-individ-noy-zaschity",
        "Средства индивид.ной защиты",
        (
            "Медицинские маски",
            "Медицинские шапочки",
            "Бахилы",
            "Защитные экраны",
            "Другие средства защиты",
        ),
    ),
    "clothing": _section(
        "medical-meditsinskaya-odezhda",
        "Медицинская одежда",
        (
            "Медицинские халаты",
            "Медицинские костюмы",
            "Медицинские колпаки",
            "Медицинская обувь",
            "Другая медицинская одежда",
        ),
    ),
    "optics": _section(
        "medical-optika-i-tovary-dlya-zreniya",
        "Оптика и товары для зрения",
        (
            "Очки для зрения",
            "Оправы",
            "Контактные линзы",
            "Растворы для линз",
            "Футляры для очков",
            "Другие товары для зрения",
        ),
    ),
    "hearing": _section(
        "medical-tovary-dlya-sluha",
        "Товары для слуха",
        (
            "Слуховые аппараты",
            "Батарейки для слуховых аппаратов",
            "Другие товары для слуха",
        ),
    ),
    "diabetes": _section(
        "medical-tovary-dlya-diabetikov",
        "Товары для диабетиков",
        (
            "Глюкометры",
            "Тест-полоски",
            "Ланцеты",
            "Другие товары для диабетиков",
        ),
    ),
    "breathing": _section(
        "medical-ingalyatory-tovary-dlya-dyhaniya",
        "Ингаляторы/товары для дыхания",
        (
            "Небулайзеры",
            "Кислородные концентраторы",
            "Кислородные подушки",
            "Другие товары для дыхания",
        ),
    ),
    "massage": _section(
        "medical-massazh-i-reabilitatsiya",
        "Массаж и реабилитация",
        (
            "Массажёры",
            "Массажные кресла",
            "Массажные столы",
            "Турмалиновые коврики",
            "Другие товары для массажа",
        ),
    ),
    "furniture": _section(
        "medical-meditsinskaya-mebel",
        "Медицинская мебель",
        (
            "Медицинские кровати",
            "Каталки",
            "Процедурные столики",
            "Медицинские ширмы",
            "Медицинские шкафы",
            "Другая медицинская мебель",
        ),
    ),
    "firstaid": _section(
        "medical-aptechki-i-pervaya-pomosch",
        "Аптечки и первая помощь",
        (
            "Автомобильные аптечки",
            "Домашние аптечки",
            "Кровоостанавливающие жгуты",
            "Шины для иммобилизации",
            "Другие товары первой помощи",
        ),
    ),
    "supplements": _section(
        "medical-bady-i-tovary-dlya-zdorovya",
        "БАДы и товары для здоровья",
        (
            "Витаминные комплексы",
            "Омега-3",
            "Коллаген",
            "Минеральные комплексы",
            "Другие БАДы",
        ),
    ),
    "other": _section(
        "medical-prochie-medtovary",
        "Прочие медтовары",
        ("Грелки", "Пузыри для льда", "Другие медтовары"),
    ),
}


def build_med_section_catalog(section_key: str) -> dict[str, Any] | None:
    return MED_SECTIONS.get(section_key)
