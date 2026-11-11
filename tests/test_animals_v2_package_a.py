"""Animals V2 Package A — Create SoT + independent expectations."""
from __future__ import annotations

from app.models.category_enums import CategoryFieldType
from app.seeds.animals_sections_catalog import ANIMALS_SECTIONS
from app.seeds.animals_v2 import (
    ANIMALS_CONDITION_CHOICES,
    ANIMALS_CONDITION_KEY,
    ANIMALS_CREATE_FORBIDDEN,
    ANIMALS_GENDER_CHOICES,
    ANIMALS_GENDER_KEY,
    ANIMALS_KIND_KEY,
    ANIMALS_SELLER_CHOICES,
    ANIMALS_SELLER_KEY,
    ANIMALS_V2_CONDITION_APPROVED_KINDS,
    ANIMALS_V2_EXPECTED_L2_COUNT,
    ANIMALS_V2_SEX_APPROVED_KINDS,
    animals_v2_all_kind_audit,
    animals_v2_assert_package_a_contracts,
    animals_v2_complexity_histogram,
    animals_v2_kind_count,
    animals_v2_search_policy_prep,
    build_animals_v2_core_fields,
)
from app.seeds.shared_goods_create_contract import (
    APPROVED_SHARED_FIELD_OVERRIDES,
    CONTACT_METHOD_CHOICES,
    GOODS_NEGOTIABLE_CHOICES,
    assert_field_matches_canonical,
    extract_choice_values,
    field_row_by_key,
    options_from_field_row,
)

# Independent approved expectations (do not derive from builder alone).
_INDEPENDENT_SELLER = (
    "Частное лицо",
    "Хозяйство",
    "Питомник",
    "Магазин",
    "Другой",
)
_INDEPENDENT_SEX = ("Самец", "Самка")
_INDEPENDENT_CONDITION = ("Новое", "Б/у")
_INDEPENDENT_CONTACT = CONTACT_METHOD_CHOICES
_INDEPENDENT_NEGOTIABLE = GOODS_NEGOTIABLE_CHOICES

_INDEPENDENT_SEX_YES = frozenset(
    {
        "Собаки",
        "Щенки",
        "Другие собаки",
        "Кошки",
        "Котята",
        "Другие кошки",
        "Кролики",
        "Декоративные кролики",
        "Другие кролики",
        "Хомяки",
        "Морские свинки",
        "Крысы",
        "Мыши",
        "Шиншиллы",
        "Дегу",
        "Другие грызуны",
        "Черепахи",
        "Змеи",
        "Ящерицы",
        "Пауки",
        "Другие экзотические животные",
        "Свиньи",
        "Ослы",
        "Верблюды",
        "Другие животные",
    }
)
_INDEPENDENT_SEX_NO = frozenset(
    {
        "Овцы",
        "Бараны",
        "Ягнята",
        "Козы",
        "Козлы",
        "Козлята",
        "Другие овцы и козы",
        "Коровы",
        "Быки",
        "Тёлки",
        "Телята",
        "Другой крупный рогатый скот",
        "Кобылы",
        "Жеребцы",
        "Мерины",
        "Жеребята",
        "Другие лошади",
        "Куры",
        "Петухи",
        "Цыплята",
        "Инкубационные яйца",
        "Утки",
        "Гуси",
        "Индейки",
        "Перепела",
        "Другая птица",
        "Вязка собак",
        "Вязка кошек",
        "Пчелосемьи",
        "Пчёлы",
        "Ульи",
        "Рамки",
        "Другое для пчеловодства",
        "Аквариумные рыбы",
        "Прудовые рыбы",
        "Аквариумы",
        "Оборудование для аквариума",
        "Другие рыбы и аквариумы",
        "Сено",
        "Солома",
        "Комбикорм",
        "Отруби",
        "Премиксы",
        "Соль-лизунец",
        "Другие корма",
        "Ошейники",
        "Поводки",
        "Переноски",
        "Клетки",
        "Миски",
        "Лежанки",
        "Игрушки для животных",
        "Другие аксессуары для животных",
        "Шампуни для животных",
        "Ошейники от блох",
        "Витамины для животных",
        "Ветеринарные бинты",
        "Термометры для животных",
        "Другие ветеринарные товары",
    }
)
_INDEPENDENT_CONDITION_YES = frozenset(
    {
        "Ошейники",
        "Поводки",
        "Переноски",
        "Клетки",
        "Миски",
        "Лежанки",
        "Игрушки для животных",
        "Другие аксессуары для животных",
        "Ульи",
        "Рамки",
        "Аквариумы",
        "Оборудование для аквариума",
    }
)


def test_animals_package_a_contracts() -> None:
    animals_v2_assert_package_a_contracts()
    assert animals_v2_kind_count() == sum(
        len(c["roles"]) for c in ANIMALS_SECTIONS.values()
    )
    assert len(ANIMALS_SECTIONS) == ANIMALS_V2_EXPECTED_L2_COUNT == 15


def test_animals_independent_seller_contract() -> None:
    assert ANIMALS_SELLER_CHOICES == _INDEPENDENT_SELLER
    assert ("animals", "seller_type") in APPROVED_SHARED_FIELD_OVERRIDES
    cores = build_animals_v2_core_fields()
    for slug, fields in cores.items():
        row = field_row_by_key(fields, ANIMALS_SELLER_KEY)
        assert row is not None
        assert row[1] == "Кто продаёт"
        assert extract_choice_values(options_from_field_row(row)) == _INDEPENDENT_SELLER
        assert "Ветаптека" not in extract_choice_values(options_from_field_row(row))
        assert "Компания" not in extract_choice_values(options_from_field_row(row))


def test_animals_shared_price_negotiable_contacts() -> None:
    cores = build_animals_v2_core_fields()
    for slug, fields in cores.items():
        for key in ("price", "negotiable", "contact_methods"):
            assert_field_matches_canonical(
                domain="animals",
                field_key=key,
                row=field_row_by_key(fields, key),
            )
        price = field_row_by_key(fields, "price")
        assert price[2] == CategoryFieldType.price
        assert price[3] is True
        assert price[1] == "Цена"
        contact = extract_choice_values(
            options_from_field_row(field_row_by_key(fields, "contact_methods"))
        )
        negotiable = extract_choice_values(
            options_from_field_row(field_row_by_key(fields, "negotiable"))
        )
        assert contact == _INDEPENDENT_CONTACT
        assert negotiable == _INDEPENDENT_NEGOTIABLE
        keys = {r[0] for r in fields}
        assert "price_basis" not in keys
        assert keys.isdisjoint(ANIMALS_CREATE_FORBIDDEN)
        assert "age" not in keys and "breed" not in keys


def test_animals_sex_independent_allowlist() -> None:
    assert ANIMALS_V2_SEX_APPROVED_KINDS == _INDEPENDENT_SEX_YES
    assert ANIMALS_GENDER_CHOICES == _INDEPENDENT_SEX
    audit = animals_v2_all_kind_audit()
    for row in audit:
        expected = "YES" if row["kind"] in _INDEPENDENT_SEX_YES else "NO"
        assert row["sex"] == expected, row["kind"]
        assert row["sex_in_schema"] is True
        if row["kind"] in _INDEPENDENT_SEX_NO:
            assert row["sex"] == "NO"
    # Kind already encodes sex → no redundant gender.
    for encoded in ("Бараны", "Быки", "Кобылы", "Петухи", "Козлы", "Жеребцы", "Мерины"):
        assert encoded in _INDEPENDENT_SEX_NO


def test_animals_condition_independent_allowlist() -> None:
    assert ANIMALS_V2_CONDITION_APPROVED_KINDS == _INDEPENDENT_CONDITION_YES
    assert ANIMALS_CONDITION_CHOICES == _INDEPENDENT_CONDITION
    audit = animals_v2_all_kind_audit()
    for row in audit:
        expected = "YES" if row["kind"] in _INDEPENDENT_CONDITION_YES else "NO"
        assert row["condition"] == expected, row["kind"]
        assert row["condition_in_schema"] is True
        if row["class"] in {"live_animal", "feed", "vet_consumable"}:
            assert row["condition"] == "NO"


def test_animals_all_kind_audit_components() -> None:
    audit = animals_v2_all_kind_audit()
    assert len(audit) == animals_v2_kind_count()
    for row in audit:
        assert row["animals_kind_valid"] is True
        assert row["seller"] == list(_INDEPENDENT_SELLER)
        assert row["price"] is True
        assert row["price_basis"] is True  # True means absent-from-schema check passed
        assert row["forbidden"] == []
        assert row["components"][ANIMALS_KIND_KEY] == "enum"
        assert row["components"]["price"] == "price"
        assert row["ownership"] == "animals"


def test_animals_create_complexity_simple() -> None:
    hist = animals_v2_complexity_histogram()
    assert hist["5+"] == 0
    assert hist["3"] == 0  # kind + at most one of sex/condition
    assert hist["1"] + hist["2"] == animals_v2_kind_count()


def test_animals_search_policy_prep() -> None:
    policy = animals_v2_search_policy_prep()
    allow = set(policy["allow"])
    assert ANIMALS_KIND_KEY in allow
    assert ANIMALS_SELLER_KEY in allow
    assert ANIMALS_GENDER_KEY in allow
    assert ANIMALS_CONDITION_KEY in allow
    assert "geo" in allow
    assert "breed" not in allow
    assert "age" not in allow
    assert "price_basis" not in allow


def test_animals_cores_cover_all_active_l2() -> None:
    cores = build_animals_v2_core_fields()
    assert len(cores) == ANIMALS_V2_EXPECTED_L2_COUNT
    for slug, fields in cores.items():
        assert field_row_by_key(fields, ANIMALS_KIND_KEY) is not None
        kind_row = field_row_by_key(fields, ANIMALS_KIND_KEY)
        assert kind_row[1] == "Товар"
        opts = extract_choice_values(options_from_field_row(kind_row))
        assert opts and len(opts) > 0
