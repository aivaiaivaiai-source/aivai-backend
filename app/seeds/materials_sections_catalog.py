# -*- coding: utf-8 -*-
"""Продажа «Сырьё для производства».

Вид — само сырьё для цеха, не готовый товар. Доска, брус, фанера, цемент,
арматура и готовые краски остаются в ремонте. Мука, сахар и зерно — в продуктах.
Бумага для офиса — в канцтоварах. Кольца и серьги — в одежде. Шампуни и мыло —
в красоте. Пряжа и нитки живут здесь, не в рукоделии.
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
    names = labels or ("Оптовик", "Компания", "Частное лицо")
    return _group("Продавец", names)


def _condition() -> dict[str, Any]:
    return _group("Состояние", ("Новое", "Б/у"))


def _stock() -> list[dict[str, Any]]:
    return [_seller(), _condition()]


def _section(
    slug: str,
    label: str,
    kinds: tuple[str, ...],
    filters: list[dict[str, Any]] | None = None,
    question: str = "Какое сырьё?",
) -> dict[str, Any]:
    return {
        "category_slug": slug,
        "label": label,
        "question": question,
        "roles": _opts(*kinds),
        "filters": filters if filters is not None else _stock(),
    }


MATERIALS_SECTIONS: dict[str, dict[str, Any]] = {
    "fabric": _section(
        "materials-tkani-i-tekstilnoe-syre",
        "Ткани и текстильное сырьё",
        (
            "Хлопковые ткани",
            "Шёлк",
            "Льняные ткани",
            "Шерстяные ткани",
            "Синтетические ткани",
            "Трикотажное полотно",
            "Подкладочные ткани",
            "Другие ткани",
        ),
    ),
    "notions": _section(
        "materials-shveynaya-furnitura",
        "Швейная фурнитура",
        (
            "Молнии",
            "Пуговицы",
            "Кнопки",
            "Крючки и петли",
            "Тесьма",
            "Резинка",
            "Люверсы",
            "Другая швейная фурнитура",
        ),
    ),
    "leather": _section(
        "materials-kozha-i-kozhzameniteli",
        "Кожа и кожзаменители",
        (
            "Натуральная кожа",
            "Кожзаменитель",
            "Замша",
            "Мех",
            "Спилок",
            "Другая кожа и кожзам",
        ),
    ),
    "yarn": _section(
        "materials-nitki-pryazha-i-volokno",
        "Нитки, пряжа и волокно",
        (
            "Пряжа",
            "Нитки",
            "Шерсть",
            "Хлопковое волокно",
            "Шёлковое волокно",
            "Синтетическое волокно",
            "Другие нитки и волокно",
        ),
    ),
    "metal": _section(
        "materials-metally-metallicheskoe-syre",
        "Металлы/металлическое сырьё",
        (
            "Листовой прокат",
            "Сортовой прокат",
            "Катанка",
            "Цветные металлы",
            "Нержавеющая сталь",
            "Чугун",
            "Другое металлическое сырьё",
        ),
    ),
    "wood": _section(
        "materials-drevesina-i-drevesnoe-syre",
        "Древесина и древесное сырьё",
        (
            "Брёвна",
            "Пиловочник",
            "Шпон",
            "Щепа",
            "Опилки",
            "Горбыль",
            "Другое древесное сырьё",
        ),
    ),
    "plastic": _section(
        "materials-plastik-i-polimernoe-syre",
        "Пластик и полимерное сырьё",
        (
            "Гранулы полиэтилена",
            "Гранулы полипропилена",
            "Гранулы ПВХ",
            "ПЭТ",
            "АБС-пластик",
            "Другое полимерное сырьё",
        ),
    ),
    "rubber": _section(
        "materials-rezina-i-kauchuk",
        "Резина и каучук",
        (
            "Натуральный каучук",
            "Синтетический каучук",
            "Резиновая крошка",
            "Резиновые смеси",
            "Силикон",
            "Другая резина и каучук",
        ),
    ),
    "paper": _section(
        "materials-bumaga-i-karton",
        "Бумага и картон",
        (
            "Бумага в рулонах",
            "Картон",
            "Целлюлоза",
            "Макулатура",
            "Крафт",
            "Другая бумага и картон",
        ),
    ),
    "glass": _section(
        "materials-steklo-i-stekolnoe-syre",
        "Стекло и стекольное сырьё",
        (
            "Листовое стекло",
            "Стеклобой",
            "Стеклотара",
            "Зеркальное полотно",
            "Другое стекольное сырьё",
        ),
    ),
    "chemical": _section(
        "materials-himicheskoe-syre",
        "Химическое сырьё",
        (
            "Смолы",
            "Растворители",
            "Технические спирты",
            "Пластификаторы",
            "Катализаторы",
            "Другое химическое сырьё",
        ),
        [_seller()],
    ),
    "paint": _section(
        "materials-lakokrasochnoe-syre",
        "Лакокрасочное сырьё",
        (
            "Пигменты",
            "Связующие",
            "Олифа",
            "Растворители для красок",
            "Колеры оптом",
            "Другое лакокрасочное сырьё",
        ),
        [_seller()],
    ),
    "pack": _section(
        "materials-upakovochnye-materialy",
        "Упаковочные материалы",
        (
            "Стретч-плёнка",
            "Плёнка упаковочная",
            "Гофрокартон",
            "Пакеты",
            "Скотч",
            "Этикетки",
            "Другие упаковочные материалы",
        ),
    ),
    "food": _section(
        "materials-pischevoe-syre-i-ingredienty",
        "Пищевое сырьё и ингредиенты",
        (
            "Сухое молоко",
            "Сыворотка",
            "Патока",
            "Солод",
            "Желатин",
            "Ароматизаторы",
            "Пищевые добавки",
            "Какао-бобы",
            "Другое пищевое сырьё",
        ),
        [_seller()],
    ),
    "cosmetic": _section(
        "materials-syre-dlya-kosmetiki-parfyumerii",
        "Сырьё для косметики/парфюмерии",
        (
            "Базовые масла",
            "Эфирные масла",
            "ПАВ для косметики",
            "Отдушки для косметики",
            "Воски",
            "Пигменты для косметики",
            "Другое косметическое сырьё",
        ),
        [_seller()],
    ),
    "household": _section(
        "materials-syre-dlya-bytovoy-himii",
        "Сырьё для бытовой химии",
        (
            "Кальцинированная сода",
            "ПАВ для бытовой химии",
            "Отдушки для химии",
            "Загустители",
            "Наполнители",
            "Другое сырьё для бытовой химии",
        ),
        [_seller()],
    ),
    "jewelry": _section(
        "materials-dlya-yuvelirnogo-proizvodstva",
        "Для ювелирного производства",
        (
            "Золото",
            "Серебро",
            "Драгоценные камни",
            "Ювелирная фурнитура",
            "Ювелирная проволока",
            "Другое ювелирное сырьё",
        ),
    ),
    "import": _section(
        "materials-import-i-optovye-postavki-syrya",
        "Импорт и оптовые поставки сырья",
        (
            "Партия под заказ",
            "Контейнерная поставка",
            "Регулярные поставки",
            "Другие оптовые поставки",
        ),
        [_seller("Импортёр", "Оптовик", "Компания")],
        "Какая поставка?",
    ),
    "other": _section(
        "materials-prochee-syre-dlya-proizvodstva",
        "Прочее сырьё для производства",
        (
            "Вторсырьё",
            "Отходы производства",
            "Образцы",
            "Другое сырьё",
        ),
    ),
}


def build_materials_section_catalog(section_key: str) -> dict[str, Any] | None:
    return MATERIALS_SECTIONS.get(section_key)
