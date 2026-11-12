"""Kids V2 Package A — Create SoT + independent semantic expectations (post-Samsung)."""
from __future__ import annotations

from app.models.category_enums import CategoryFieldType
from app.seeds.kids_sections_catalog import KIDS_SECTIONS
from app.seeds.kids_v2 import (
    KIDS_V2_APPROVED_AGE_EXPECTATIONS,
    KIDS_V2_APPROVED_SIZE_EXPECTATIONS,
    KIDS_V2_CANONICAL_GOODS_SLUGS,
    KIDS_V2_CREATE_FORBIDDEN,
    KIDS_V2_EXPECTED_KIND_COUNT,
    KIDS_V2_EXPECTED_L2_COUNT,
    KIDS_V2_LOCKED_NO_CONDITION_KINDS,
    KIDS_V2_MOUNTING_KINDS,
    KIDS_V2_SCHOOL_KIND_OWNERSHIP,
    KIDS_V2_SCHOOL_SLUG,
    SEMANTIC_AGE_TOYS,
    SEMANTIC_CLOTHING_GROWTH,
    _AGE_TOYS,
    _CLOTHING_GROWTH,
    build_kids_v2_core_fields,
    kids_v2_all_kind_audit,
    kids_v2_approved_condition_kinds,
    kids_v2_assert_contracts,
    kids_v2_complexity_histogram,
    kids_v2_kind_count,
    kids_v2_search_policy_prep,
    kids_v2_size_semantic_map,
)

_INDEPENDENT_SIZE_YES: dict[str, str] = {
    "Боди и распашонки": SEMANTIC_CLOTHING_GROWTH,
    "Ползунки": SEMANTIC_CLOTHING_GROWTH,
    "Футболки и рубашки": SEMANTIC_CLOTHING_GROWTH,
    "Платья и юбки": SEMANTIC_CLOTHING_GROWTH,
    "Кофты и свитера": SEMANTIC_CLOTHING_GROWTH,
    "Верхняя одежда": SEMANTIC_CLOTHING_GROWTH,
    "Другая детская одежда": SEMANTIC_CLOTHING_GROWTH,
    "Школьная форма": SEMANTIC_CLOTHING_GROWTH,
}

_INDEPENDENT_AGE_YES: dict[str, str] = {
    "Погремушки и прорезыватели": SEMANTIC_AGE_TOYS,
    "Мягкие игрушки": SEMANTIC_AGE_TOYS,
    "Куклы": SEMANTIC_AGE_TOYS,
    "Машинки": SEMANTIC_AGE_TOYS,
    "Конструкторы": SEMANTIC_AGE_TOYS,
    "Детские настольные игры": SEMANTIC_AGE_TOYS,
    "Развивающие коврики": SEMANTIC_AGE_TOYS,
    "Радиоуправляемые игрушки": SEMANTIC_AGE_TOYS,
    "Другие игрушки": SEMANTIC_AGE_TOYS,
}

_INDEPENDENT_NO_CONDITION = frozenset(
    {
        "Нижнее бельё и пижамы",
        "Носки и колготки",
        "Пелёнки",
        "Товары для кормления",
        "Подгузники",
        "Подгузники-трусики",
        "Одноразовые пелёнки",
        "Влажные салфетки",
        "Крем и присыпка",
        "Другие товары гигиены",
        "Молочные смеси",
        "Каши для прикорма",
        "Пюре для прикорма",
        "Другое детское питание",
        "Аспираторы для малышей",
        "Детские маникюрные наборы",
        "Воздушные шары и декор",
    }
)

_NO_SIZE_PERSONAL_EXAMPLES = frozenset(
    {"Носки и колготки", "Головные уборы", "Нижнее бельё и пижамы", "Подгузники", "Туфли"}
)


def test_kids_v2_package_a_contracts() -> None:
    kids_v2_assert_contracts()
    assert kids_v2_kind_count() == KIDS_V2_EXPECTED_KIND_COUNT
    assert len(KIDS_SECTIONS) == KIDS_V2_EXPECTED_L2_COUNT
    assert len(KIDS_V2_CANONICAL_GOODS_SLUGS) == KIDS_V2_EXPECTED_L2_COUNT


def test_kids_v2_school_retired_and_ownership_mapped() -> None:
    assert KIDS_V2_SCHOOL_SLUG not in KIDS_V2_CANONICAL_GOODS_SLUGS
    assert "school" not in KIDS_SECTIONS
    assert set(KIDS_V2_SCHOOL_KIND_OWNERSHIP) == {
        "Школьная форма",
        "Школьные дневники",
        "Школьные рюкзаки",
        "Мешки для сменной обуви",
        "Другие товары для школы",
    }
    assert KIDS_V2_SCHOOL_KIND_OWNERSHIP["Школьная форма"][0] == "MOVED"
    assert KIDS_V2_SCHOOL_KIND_OWNERSHIP["Школьные дневники"][0] == "EXACT_DESTINATION"
    assert KIDS_V2_SCHOOL_KIND_OWNERSHIP["Школьные рюкзаки"][0] == "EXACT_DESTINATION"
    assert (
        KIDS_V2_SCHOOL_KIND_OWNERSHIP["Мешки для сменной обуви"][0]
        == "EXACT_DESTINATION"
    )
    assert (
        KIDS_V2_SCHOOL_KIND_OWNERSHIP["Другие товары для школы"][0]
        == "NEAREST_DESTINATION"
    )
    clothes = {r["label"] for r in KIDS_SECTIONS["clothes"]["roles"]}
    assert "Школьная форма" in clothes


def test_kids_v2_independent_size_expectations() -> None:
    assert _INDEPENDENT_SIZE_YES == KIDS_V2_APPROVED_SIZE_EXPECTATIONS
    sized = kids_v2_size_semantic_map()
    assert set(sized) == set(_INDEPENDENT_SIZE_YES)
    for kind, group in _INDEPENDENT_SIZE_YES.items():
        key, got_group, options = sized[kind]
        assert key == "size"
        assert got_group == group
        assert options == _CLOTHING_GROWTH


def test_kids_v2_independent_age_expectations() -> None:
    assert _INDEPENDENT_AGE_YES == KIDS_V2_APPROVED_AGE_EXPECTATIONS
    assert "Молочные смеси" not in KIDS_V2_APPROVED_AGE_EXPECTATIONS


def test_kids_v2_independent_condition_expectations() -> None:
    approved = kids_v2_approved_condition_kinds()
    assert _INDEPENDENT_NO_CONDITION == KIDS_V2_LOCKED_NO_CONDITION_KINDS
    assert "Носки и колготки" in KIDS_V2_LOCKED_NO_CONDITION_KINDS
    assert approved.isdisjoint(KIDS_V2_LOCKED_NO_CONDITION_KINDS)
    all_kinds = {
        str(role["label"])
        for cat in KIDS_SECTIONS.values()
        for role in cat["roles"]
    }
    assert (approved | KIDS_V2_LOCKED_NO_CONDITION_KINDS) == all_kinds


def test_kids_v2_no_size_personal_and_dropped_groups() -> None:
    sized = kids_v2_size_semantic_map()
    for kind in _NO_SIZE_PERSONAL_EXAMPLES:
        assert kind not in sized
    cores = build_kids_v2_core_fields()
    for slug, fields in cores.items():
        keys = {r[0] for r in fields}
        assert "shoe_size" not in keys
        assert "diaper_size" not in keys


def test_kids_v2_formula_no_age_diapers_no_size() -> None:
    cores = build_kids_v2_core_fields()
    food = {r[0] for r in cores["kids-detskoe-pitanie"]}
    hygiene = {r[0] for r in cores["kids-podguzniki-i-gigiena"]}
    assert "age" not in food
    assert "diaper_size" not in hygiene
    assert "size" not in hygiene


def test_kids_v2_cores_nonempty_no_forbidden() -> None:
    cores = build_kids_v2_core_fields()
    assert set(cores) == KIDS_V2_CANONICAL_GOODS_SLUGS
    assert len(cores) == KIDS_V2_EXPECTED_L2_COUNT
    for slug, fields in cores.items():
        assert fields
        keys = [r[0] for r in fields]
        assert keys[0] == "kids_kind"
        for forbidden in KIDS_V2_CREATE_FORBIDDEN:
            assert forbidden not in keys, (slug, forbidden)
        assert "gender" not in keys
        assert "season" not in keys
        assert "kids_brand" not in keys
        price = next(r for r in fields if r[0] == "price")
        assert price[2] == CategoryFieldType.price


def test_kids_v2_clothing_size_for_kinds_and_options() -> None:
    cores = build_kids_v2_core_fields()
    size = next(r for r in cores["kids-detskaya-odezhda"] if r[0] == "size")
    assert size[2] == CategoryFieldType.multi_select
    opts = size[5] or {}
    choices = opts["choices"]
    assert len(choices) == len(_CLOTHING_GROWTH)
    for c in choices:
        assert "Футболки и рубашки" in c["for_kinds"]
        assert "Носки и колготки" not in c["for_kinds"]
        assert "Школьная форма" in c["for_kinds"]
    depends = opts["depends_on"]["values"]
    assert "Носки и колготки" not in depends
    assert "Футболки и рубашки" in depends


def test_kids_v2_socks_no_condition_field_visibility() -> None:
    cores = build_kids_v2_core_fields()
    cond = next(r for r in cores["kids-detskaya-odezhda"] if r[0] == "condition")
    values = (cond[5] or {}).get("depends_on", {}).get("values") or []
    assert "Носки и колготки" not in values
    assert "Нижнее бельё и пижамы" not in values
    assert "Футболки и рубашки" in values


def test_kids_v2_mounting_only_car_seats() -> None:
    cores = build_kids_v2_core_fields()
    for slug, fields in cores.items():
        keys = {r[0] for r in fields}
        if slug == "kids-avtokresla-i-perenoski":
            assert "mounting" in keys
            mount = next(r for r in fields if r[0] == "mounting")
            values = ((mount[5] or {}).get("depends_on") or {}).get("values") or []
            assert set(values) == set(KIDS_V2_MOUNTING_KINDS)
        else:
            assert "mounting" not in keys


def test_kids_v2_no_empty_pickers_no_inline_text() -> None:
    cores = build_kids_v2_core_fields()
    for slug, fields in cores.items():
        for row in fields:
            assert row[2] != CategoryFieldType.string, (slug, row[0])
            opts = row[5] or {}
            choices = opts.get("choices")
            if choices is not None:
                assert len(choices) > 0, (slug, row[0])


def test_kids_v2_all_kind_audit_and_complexity() -> None:
    rows = kids_v2_all_kind_audit()
    assert len(rows) == KIDS_V2_EXPECTED_KIND_COUNT
    hist = kids_v2_complexity_histogram()
    assert hist["0"] + hist["1"] + hist["2"] + hist["3+"] == KIDS_V2_EXPECTED_KIND_COUNT
    assert hist["3+"] == 0
    for row in rows:
        assert row["special_count"] <= 2
        if row["kind"] in _INDEPENDENT_SIZE_YES:
            assert row["size"] == "YES"
        else:
            assert row["size"] == "NO"
        if row["kind"] in _INDEPENDENT_AGE_YES:
            assert row["age"] == "YES"
            assert row["age_group"] == SEMANTIC_AGE_TOYS
            assert _AGE_TOYS  # scale present
        else:
            assert row["age"] == "NO"
        if row["kind"] in _INDEPENDENT_NO_CONDITION:
            assert row["condition"] == "NO"
        else:
            assert row["condition"] == "YES"


def test_kids_v2_search_policy_prep() -> None:
    policy = kids_v2_search_policy_prep()
    assert "kids_kind" in policy["allow"]
    assert "size" in policy["allow"]
    assert "diaper_size" in policy["exclude"]
    assert "shoe_size" in policy["exclude"]
    assert "gender" in policy["exclude"]
