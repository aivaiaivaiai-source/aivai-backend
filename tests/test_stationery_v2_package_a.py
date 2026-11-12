"""Stationery & Books V2 Package A — Create SoT + independent expectations."""
from __future__ import annotations

import json

from app.models.category_enums import CategoryFieldType
from app.seeds.shared_goods_create_contract import (
    CONTACT_METHOD_CHOICES,
    GOODS_NEGOTIABLE_CHOICES,
    GOODS_SELLER_CHOICES,
    assert_field_matches_canonical,
    extract_choice_values,
    field_row_by_key,
    options_from_field_row,
)
from app.seeds.stationery_sections_catalog import STATIONERY_SECTIONS
from app.seeds.stationery_v2 import (
    STATIONERY_CONDITION_CHOICES,
    STATIONERY_CONDITION_KEY,
    STATIONERY_CREATE_FORBIDDEN,
    STATIONERY_GRADE_KEY,
    STATIONERY_KIND_KEY,
    STATIONERY_SCHOOL_GRADE_KINDS,
    STATIONERY_SCHOOL_GRADE_OPTIONS,
    STATIONERY_SELLER_KEY,
    STATIONERY_SELLER_TARGET,
    STATIONERY_V2_EXPECTED_L2_COUNT,
    build_stationery_v2_core_fields,
    stationery_v2_all_kind_audit,
    stationery_v2_assert_package_a_contracts,
    stationery_v2_complexity_histogram,
    stationery_v2_condition_yes_kinds,
    stationery_v2_kind_count,
)

# Independent approved expectations (do not derive from builder alone).
_INDEPENDENT_SELLER = ("Частное лицо", "Магазин", "Другой")
_INDEPENDENT_CONDITION = ("Новое", "Б/у")
_INDEPENDENT_CONTACT = CONTACT_METHOD_CHOICES
_INDEPENDENT_NEGOTIABLE = GOODS_NEGOTIABLE_CHOICES
_INDEPENDENT_GRADE = tuple(f"{n} класс" for n in range(1, 12))

_INDEPENDENT_GRADE_YES = frozenset(
    {
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
    }
)
_INDEPENDENT_GRADE_NO = frozenset(
    {
        "Подготовка к ОРТ",
        "Вузские учебники",
        "Другие учебники",
        "Романы",
        "Ручки",
        "Школьные рюкзаки",
        "Калькуляторы",
    }
)

_INDEPENDENT_CONDITION_YES = frozenset(
    {
        "Пеналы",
        "Школьные рюкзаки",
        "Мешки для сменной обуви",
        "Канцелярские ножницы",
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
        "Подготовка к ОРТ",
        "Вузские учебники",
        "Другие учебники",
        "Романы",
        "Детективы",
        "Фантастика",
        "Фэнтези",
        "Поэзия",
        "Повести и рассказы",
        "Пьесы",
        "Другая художественная литература",
        "Научно-популярные",
        "Психология",
        "Саморазвитие",
        "Бизнес-книги",
        "Философия",
        "Право",
        "Другая научная литература",
        "Коран",
        "Библия",
        "Исламская литература",
        "Христианская литература",
        "Другая религиозная литература",
        "Книги на английском",
        "Книги на немецком",
        "Книги на турецком",
        "Книги на китайском",
        "Книги на корейском",
        "Другая иностранная литература",
        "Кисти",
        "Холсты",
        "Мольберты",
        "Степлеры",
        "Дыроколы",
        "Штампы и печати",
        "Калькуляторы",
        "Глобусы",
        "Настенные карты",
        "Ноты",
        "Самоучители",
        "Песенники",
        "Другие ноты и музыкальные книги",
        "Комиксы",
        "Манга",
        "Манхва",
        "Графические романы",
        "Другие комиксы",
        "Журналы",
        "Редкие книги",
        "Подарочные издания",
        "Книги с автографом",
        "Другие коллекционные издания",
        "CD и DVD",
    }
)
_INDEPENDENT_CONDITION_NO = frozenset(
    {
        "Ручки",
        "Карандаши",
        "Тетради",
        "Блокноты",
        "Ежедневники",
        "Школьные дневники",
        "Линейки",
        "Клей",
        "Корректоры",
        "Другие канцелярские товары",
        "Аудиокниги",
        "Электронные учебные издания",
        "Электронная художественная литература",
        "Другие электронные издания",
        "Краски для рисования",
        "Цветные карандаши",
        "Фломастеры и маркеры",
        "Бумага для рисования",
        "Пластилин",
        "Другие товары для рисования",
        "Бумага",
        "Папки и файлы",
        "Конверты",
        "Бейджи",
        "Другие офисные товары",
        "Дорожные карты",
        "Другие карты и глобусы",
        "Газеты",
        "Каталоги",
        "Другие периодические издания",
        "Закладки",
        "Обложки для книг",
        "Другие книги и канцтовары",
    }
)


def test_stationery_package_a_contracts() -> None:
    stationery_v2_assert_package_a_contracts()
    assert stationery_v2_kind_count() == 105
    assert len(STATIONERY_SECTIONS) == STATIONERY_V2_EXPECTED_L2_COUNT == 15


def test_stationery_independent_seller_contract() -> None:
    assert STATIONERY_SELLER_TARGET == _INDEPENDENT_SELLER == GOODS_SELLER_CHOICES
    cores = build_stationery_v2_core_fields()
    for slug, fields in cores.items():
        row = field_row_by_key(fields, STATIONERY_SELLER_KEY)
        assert row is not None, slug
        assert row[1] == "Продавец"
        assert extract_choice_values(options_from_field_row(row)) == _INDEPENDENT_SELLER
        values = extract_choice_values(options_from_field_row(row))
        assert "Компания" not in values
        assert "Школа" not in values
        assert "Книжный магазин" not in values
        assert "Издательство" not in values


def test_stationery_shared_price_negotiable_contacts() -> None:
    cores = build_stationery_v2_core_fields()
    for slug, fields in cores.items():
        for key in ("seller_type", "price", "negotiable", "contact_methods"):
            assert_field_matches_canonical(
                domain="stationery",
                field_key=key,
                row=field_row_by_key(fields, key),
            )
        price = field_row_by_key(fields, "price")
        assert price[2] == CategoryFieldType.price
        assert price[3] is True
        assert price[1] == "Цена"
        keys = {r[0] for r in fields}
        assert keys.isdisjoint(STATIONERY_CREATE_FORBIDDEN)
        assert "language" not in keys
        assert "item_type" not in keys
        assert "brand" not in keys
        assert "author" not in keys
        assert "isbn" not in keys


def test_stationery_condition_independent_allowlist() -> None:
    yes = stationery_v2_condition_yes_kinds()
    assert yes == _INDEPENDENT_CONDITION_YES
    assert len(yes) == 72
    assert STATIONERY_CONDITION_CHOICES == _INDEPENDENT_CONDITION
    audit = stationery_v2_all_kind_audit()
    assert len(audit) == 105
    for row in audit:
        expected = "YES" if row["kind"] in _INDEPENDENT_CONDITION_YES else "NO"
        assert row["condition"] == expected, row["kind"]
        assert row["condition_in_schema"] is True
        if row["kind"] in _INDEPENDENT_CONDITION_NO:
            assert row["condition"] == "NO"
    # School goods: matrix-driven, not assumed equal.
    by_kind = {r["kind"]: r for r in audit}
    assert by_kind["Школьные дневники"]["condition"] == "NO"
    assert by_kind["Школьные рюкзаки"]["condition"] == "YES"
    assert by_kind["Мешки для сменной обуви"]["condition"] == "YES"


def test_stationery_grade_independent_allowlist() -> None:
    assert STATIONERY_SCHOOL_GRADE_KINDS == _INDEPENDENT_GRADE_YES
    assert STATIONERY_SCHOOL_GRADE_OPTIONS == _INDEPENDENT_GRADE
    assert len(_INDEPENDENT_GRADE_YES) == 15
    audit = stationery_v2_all_kind_audit()
    for row in audit:
        expected = "YES" if row["kind"] in _INDEPENDENT_GRADE_YES else "NO"
        assert row["grade"] == expected, row["kind"]
        assert row["grade_in_schema"] is True
        if row["kind"] in _INDEPENDENT_GRADE_NO:
            assert row["grade"] == "NO"
    # Grade never required.
    cores = build_stationery_v2_core_fields()
    textbooks = cores["stationery-books-uchebniki-i-uchebnye-posobiya"]
    grade = field_row_by_key(textbooks, STATIONERY_GRADE_KEY)
    assert grade is not None
    assert grade[3] is False


def test_stationery_all_kind_audit_components() -> None:
    audit = stationery_v2_all_kind_audit()
    assert len(audit) == stationery_v2_kind_count() == 105
    for row in audit:
        assert row["stationery_kind_valid"] is True
        assert row["seller"] == list(_INDEPENDENT_SELLER)
        assert row["price"] is True
        assert row["forbidden"] == []
        assert row["language_absent"] is True
        assert row["item_type_absent"] is True
        assert row["components"][STATIONERY_KIND_KEY] == "enum"
        assert row["components"]["price"] == "price"
        assert row["ownership"] == "stationery"
        assert row["special_count"] <= 2


def test_stationery_create_complexity_simple() -> None:
    hist = stationery_v2_complexity_histogram()
    assert hist["3+"] == 0
    assert hist["0"] + hist["1"] + hist["2"] == 105
    assert hist["0"] == 33  # Condition NO kinds with no grade
    assert hist["2"] == 15  # school subjects: condition + grade


def test_stationery_cores_cover_all_active_l2() -> None:
    cores = build_stationery_v2_core_fields()
    assert len(cores) == STATIONERY_V2_EXPECTED_L2_COUNT
    for slug, fields in cores.items():
        kind_row = field_row_by_key(fields, STATIONERY_KIND_KEY)
        assert kind_row is not None
        assert kind_row[1] == "Товар"
        assert kind_row[3] is True
        opts = extract_choice_values(options_from_field_row(kind_row))
        assert opts and len(opts) > 0
        contact = extract_choice_values(
            options_from_field_row(field_row_by_key(fields, "contact_methods"))
        )
        assert contact == _INDEPENDENT_CONTACT
        negotiable = extract_choice_values(
            options_from_field_row(field_row_by_key(fields, "negotiable"))
        )
        assert negotiable == _INDEPENDENT_NEGOTIABLE


def test_stationery_seed_builder_idempotent() -> None:
    a = build_stationery_v2_core_fields()
    b = build_stationery_v2_core_fields()
    assert set(a) == set(b)
    for slug in a:
        assert json.dumps(a[slug], default=str, ensure_ascii=False) == json.dumps(
            b[slug], default=str, ensure_ascii=False
        )


def test_stationery_fresh_vs_builder_shape_stable() -> None:
    """Fresh seed and migrated DB both call the same builder — fingerprint stable."""
    cores = build_stationery_v2_core_fields()
    fingerprint = {
        slug: [
            (
                r[0],
                r[1],
                str(r[2]),
                bool(r[3]),
                int(r[4]),
                extract_choice_values(options_from_field_row(r)),
            )
            for r in fields
        ]
        for slug, fields in sorted(cores.items())
    }
    again = build_stationery_v2_core_fields()
    fingerprint2 = {
        slug: [
            (
                r[0],
                r[1],
                str(r[2]),
                bool(r[3]),
                int(r[4]),
                extract_choice_values(options_from_field_row(r)),
            )
            for r in fields
        ]
        for slug, fields in sorted(again.items())
    }
    assert fingerprint == fingerprint2
    assert STATIONERY_CONDITION_KEY in {
        r[0] for r in cores["stationery-books-hudozhestvennaya-literatura"]
    }
    assert STATIONERY_GRADE_KEY in {
        r[0] for r in cores["stationery-books-uchebniki-i-uchebnye-posobiya"]
    }
    # E-publications content kinds are all Condition NO → no condition core.
    ebooks = cores["stationery-books-elektronnye-knigi"]
    assert field_row_by_key(ebooks, STATIONERY_CONDITION_KEY) is None
    assert field_row_by_key(ebooks, STATIONERY_GRADE_KEY) is None
