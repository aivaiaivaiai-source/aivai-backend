# -*- coding: utf-8 -*-
"""Продажа товаров «Ремонт и строительство».

Это не услуга монтажа. Вид — товар, не работа и не сезон.
Не забирать: камины и печи, беседки, садовый инвентарь и технику,
ковры, шторы, зеркала, полив для сада, сырьё (металл чушкой,
древесина кругляком, лакокрасочное сырьё), спецтехнику с оператором.
"""
from __future__ import annotations

from typing import Any


def _opts(*labels: str) -> list[dict[str, str]]:
    return [{"value": label, "label": label} for label in labels]


def _group(
    label: str,
    options: tuple[str, ...],
    kinds: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    group: dict[str, Any] = {"label": label, "options": _opts(*options)}
    if kinds:
        group["applies_to"] = list(kinds)
    return group


def _seller(base: bool = False) -> dict[str, Any]:
    options = ("Частное лицо", "Магазин", "База", "Другой") if base else (
        "Частное лицо",
        "Магазин",
        "Другой",
    )
    return _group("Продавец", options)


def _condition() -> dict[str, Any]:
    return _group("Состояние", ("Новое", "Б/у"))


def _section(
    slug: str,
    label: str,
    kinds: tuple[str, ...],
    filters: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "category_slug": slug,
        "label": label,
        "question": "Какой товар?",
        "roles": _opts(*kinds),
        "filters": filters,
    }


REPAIR_SECTIONS: dict[str, dict[str, Any]] = {
    "materials": _section(
        "repair-construction-stroitelnye-materialy",
        "ЖБИ, сетки и плёнки",
        (
            "Железобетонные изделия",
            "Сетки строительные",
            "Плёнки и мембраны",
            "Геотекстиль",
            "Другие строительные материалы",
        ),
        [_seller(base=True), _condition()],
    ),
    "bricks": _section(
        "repair-construction-kirpichi-i-stroitelnye-bloki",
        "Кирпичи и строительные блоки",
        (
            "Кирпич",
            "Газоблок",
            "Пеноблок",
            "Шлакоблок",
            "Керамзитоблок",
            "Другие блоки",
        ),
        [_seller(base=True), _condition()],
    ),
    "mixes": _section(
        "repair-construction-tsement-smesi-sypuchie-materialy",
        "Цемент/смеси/сыпучие материалы",
        (
            "Цемент",
            "Песок и щебень",
            "Штукатурные смеси",
            "Шпаклёвки",
            "Наливные полы",
            "Кладочные смеси",
            "Другие сыпучие материалы",
        ),
        [
            _seller(base=True),
            _group("Фасовка", ("Мешок", "Биг-бэг", "Навал")),
        ],
    ),
    "lumber": _section(
        "repair-construction-pilomaterialy",
        "Пиломатериалы",
        (
            "Доска",
            "Брус",
            "Фанера",
            "OSB и ДСП",
            "Вагонка",
            "Другие пиломатериалы",
        ),
        [
            _seller(base=True),
            _condition(),
            _group("Влажность", ("Сухая", "Естественная влажность"), ("Доска", "Брус", "Вагонка")),
        ],
    ),
    "metal": _section(
        "repair-construction-metalloprokat",
        "Металлопрокат",
        (
            "Арматура",
            "Трубы стальные",
            "Уголок и швеллер",
            "Листовой металл",
            "Другой металлопрокат",
        ),
        [_seller(base=True), _condition()],
    ),
    "roof": _section(
        "repair-construction-krovlya-i-vodostoki",
        "Кровля и водостоки",
        (
            "Металлочерепица",
            "Профнастил",
            "Мягкая кровля",
            "Шифер",
            "Водостоки",
            "Другие кровельные материалы",
        ),
        [_seller(), _condition()],
    ),
    "facade": _section(
        "repair-construction-fasady-i-uteplenie",
        "Фасады и утепление",
        (
            "Сайдинг",
            "Фасадные панели",
            "Минеральная вата",
            "Пенопласт и пеноплекс",
            "Другие фасадные материалы",
        ),
        [
            _seller(),
            _condition(),
            _group("Толщина", ("50 мм", "100 мм"), ("Минеральная вата", "Пенопласт и пеноплекс")),
        ],
    ),
    "windows": _section(
        "repair-construction-okna-i-dveri",
        "Окна и двери",
        (
            "Окна ПВХ",
            "Деревянные окна",
            "Входные двери",
            "Межкомнатные двери",
            "Балконные блоки",
            "Подоконники",
            "Другие окна и двери",
        ),
        [
            _seller(),
            _condition(),
            _group(
                "Стеклопакет",
                ("Однокамерный", "Двухкамерный"),
                ("Окна ПВХ", "Деревянные окна", "Балконные блоки"),
            ),
        ],
    ),
    "floors": _section(
        "repair-construction-napolnye-pokrytiya",
        "Напольные покрытия",
        (
            "Ламинат",
            "Кварцвинил",
            "Линолеум",
            "Паркет",
            "Ковролин",
            "Другие напольные покрытия",
        ),
        [
            _seller(),
            _condition(),
            _group("Класс", ("31", "32", "33", "34"), ("Ламинат", "Кварцвинил")),
        ],
    ),
    "walls": _section(
        "repair-construction-stenovye-materialy-pokrytiya",
        "Стеновые материалы",
        (
            "Гипсокартон",
            "Обои",
            "Стеновые панели",
            "Декоративный камень",
            "Другие стеновые материалы",
        ),
        [_seller(), _condition()],
    ),
    "ceilings": _section(
        "repair-construction-potolki-i-potolochnye-sistemy",
        "Потолки и потолочные системы",
        (
            # Display clarifies goods (materials/systems), not installation service.
            "Материалы для натяжных потолков",
            "Подвесные потолки",
            "Потолочная плитка",
            "Галтели",
            "Другие потолочные материалы",
        ),
        [_seller(), _condition()],
    ),
    "tile": _section(
        "repair-construction-plitka-i-keramogranit",
        "Плитка и керамогранит",
        (
            "Настенная плитка",
            "Напольная плитка",
            "Керамогранит",
            "Мозаика",
            "Клинкер",
            "Другая плитка",
        ),
        [_seller(), _condition()],
    ),
    "paint": _section(
        "repair-construction-lakokrasochnye-materialy",
        "Краски и лаки",
        (
            "Интерьерные краски",
            "Фасадные краски",
            "Эмали",
            "Лаки",
            "Грунтовки",
            "Другие лакокрасочные материалы",
        ),
        [
            _seller(),
            _group("Упаковка", ("Запечатано", "Вскрыто")),
            _group("Объём", ("1 л", "3 л", "5 л", "10 л", "20 л")),
        ],
    ),
    "chemistry": _section(
        "repair-construction-klei-i-stroitelnaya-himiya",
        "Клеи и строительная химия",
        (
            "Плиточный клей",
            "Затирка",
            "Герметики",
            "Монтажная пена",
            "Гидроизоляция",
            "Растворители",
            "Другая строительная химия",
        ),
        [_seller(), _group("Упаковка", ("Запечатано", "Вскрыто"))],
    ),
    "finishing": _section(
        "repair-construction-otdelochnye-materialy",
        "Плинтусы и декор",
        (
            "Плинтусы",
            "Молдинги и уголки",
            "Лепнина",
            "Декоративные рейки",
            "Другие отделочные материалы",
        ),
        [_seller(), _condition()],
    ),
    "plumbing": _section(
        "repair-construction-santehnika-i-vodosnabzhenie",
        "Сантехника и водоснабжение",
        (
            "Трубы и фитинги",
            "Смесители",
            "Унитазы и инсталляции",
            "Раковины",
            "Ванны и душевые кабины",
            "Водонагреватели",
            "Насосы для воды",
            "Другая сантехника",
        ),
        [_seller(), _condition()],
    ),
    "electrical": _section(
        "repair-construction-elektrika-i-osveschenie",
        "Электрика и освещение",
        (
            "Кабель и провод",
            "Автоматы и щиты",
            "Розетки и выключатели",
            "Светильники",
            "Лампочки",
            "Другая электрика",
        ),
        [
            _seller(),
            _condition(),
            _group("Цоколь", ("E27", "E14", "GU10"), ("Лампочки",)),
        ],
    ),
    "climate": _section(
        "repair-construction-otoplenie-ventilyatsiya-i-klimat",
        "Отопление, вентиляция и климат",
        (
            "Котлы отопления",
            "Радиаторы",
            "Тёплый пол",
            "Вентиляция",
            "Другое климатическое оборудование",
        ),
        [_seller(), _condition()],
    ),
    "hand-tools": _section(
        "repair-construction-instrumenty",
        "Инструменты",
        (
            "Молотки и кувалды",
            "Отвёртки и ключи",
            "Измерительный инструмент",
            "Шпатели и кельмы",
            "Столярный инструмент",
            "Другой ручной инструмент",
        ),
        [_seller(), _condition()],
    ),
    "power-tools": _section(
        "repair-construction-elektroinstrumenty",
        "Электроинструменты",
        (
            "Дрели и шуруповёрты",
            "Перфораторы",
            "Болгарки",
            "Пилы и лобзики",
            "Шлифмашины",
            "Другие электроинструменты",
        ),
        [
            _seller(),
            _condition(),
            _group("Питание", ("Сеть", "Аккумулятор")),
        ],
    ),
    "ppe": _section(
        "repair-construction-spetsodezhda-i-sredstva-zaschity",
        "Спецодежда и средства защиты",
        (
            "Рабочие костюмы",
            "Каски",
            "Рабочие перчатки",
            "Строительная спецобувь",
            "Страховочные системы",
            "Респираторы и очки",
            "Другие средства защиты",
        ),
        [
            _seller(),
            _condition(),
            _group("Размер одежды", ("S", "M", "L", "XL", "XXL"), ("Рабочие костюмы", "Рабочие перчатки")),
            _group("Размер обуви", ("39-41", "42-44", "45-47"), ("Строительная спецобувь",)),
        ],
    ),
    "equipment": _section(
        "repair-construction-stroitelnoe-oborudovanie",
        "Строительное оборудование",
        (
            "Бетономешалки",
            "Виброплиты",
            "Компрессоры",
            "Генераторы",
            "Сварочные аппараты",
            "Другое строительное оборудование",
        ),
        [
            _seller(),
            _condition(),
            _group("Топливо", ("Бензин", "Дизель"), ("Генераторы",)),
        ],
    ),
    "scaffolding": _section(
        "repair-construction-lestnitsy-i-stroitelnye-lesa",
        "Лестницы и строительные леса",
        (
            "Строительные леса",
            "Вышки-туры",
            "Стремянки",
            "Готовые лестницы",
            "Другие лестницы и леса",
        ),
        [_seller(), _condition()],
    ),
    "fences": _section(
        "repair-construction-zabory-vorota-i-ograzhdeniya",
        "Заборы, ворота и ограждения",
        (
            "Сетка-рабица",
            "Штакетник",
            "Ворота и калитки",
            "Столбы для забора",
            "Другие ограждения",
        ),
        [_seller(), _condition()],
    ),
    "structures": _section(
        "repair-construction-navesy-i-metallokonstruktsii",
        "Навесы и металлоконструкции",
        (
            "Металлические каркасы",
            "Фермы",
            "Козырьки",
            "Ангары",
            "Другие металлоконструкции",
        ),
        [_seller(), _condition()],
    ),
    "forged": _section(
        "repair-construction-kovanye-izdeliya",
        "Кованые изделия",
        (
            "Кованые решётки",
            "Кованые перила",
            "Кованые элементы",
            "Другие кованые изделия",
        ),
        [_seller(), _condition()],
    ),
    "fasteners": _section(
        "repair-construction-krepezh-i-rashodnye-materialy",
        "Крепёж и расходные материалы",
        (
            "Саморезы и шурупы",
            "Гвозди и дюбели",
            "Анкеры и болты",
            "Крепёжные уголки",
            "Диски и свёрла",
            "Другие расходные материалы",
        ),
        [_seller(), _group("Фасовка", ("Штучно", "Упаковка"))],
    ),
    "other": _section(
        "repair-construction-prochee-dlya-remonta-stroitelstva",
        "Прочее для ремонта/строительства",
        (
            "Бытовки",
            "Строительные тачки",
            "Другое для ремонта и строительства",
        ),
        [_seller(), _condition()],
    ),
}


def build_repair_section_catalog(section_key: str) -> dict[str, Any] | None:
    return REPAIR_SECTIONS.get(section_key)
