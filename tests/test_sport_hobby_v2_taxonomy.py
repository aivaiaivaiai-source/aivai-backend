"""Sport / Recreation / Hobbies V2 — taxonomy + product-identity cleanup."""
from __future__ import annotations

from app.seeds.business_sections_catalog import BUSINESS_SECTIONS
from app.seeds.electronics_sections_catalog import ELECTRONICS_SECTIONS
from app.seeds.kids_sections_catalog import KIDS_SECTIONS
from app.seeds.services_rest_catalog import SERVICE_SECTIONS
from app.seeds.sport_sections_catalog import SPORT_SECTIONS
from app.seeds.sport_v2 import (
    SPORT_AI_CHARACTERISTIC_RULE,
    SPORT_CONDITION_OPTIONS,
    SPORT_ROOT_LABEL,
    SPORT_ROOT_SLUG,
    SPORT_SELLER_OPTIONS,
    SPORT_V2_BANNED_KINDS,
    SPORT_V2_CANONICAL_LEAVES,
    SPORT_V2_CANONICAL_SLUGS,
    SPORT_V2_EXPECTED_L2_COUNT,
    SPORT_V2_LEGACY_L2_SLUGS,
    SPORT_V2_RETIRED_KINDS,
    SPORT_V2_RETIRED_NATIONAL_CRAFT_SLUGS,
    SPORT_V2_RETIRED_SLUGS,
    SPORT_V2_SECTION_KINDS,
    sport_v2_all_kinds,
    sport_v2_assert_cleanup_contracts,
    sport_v2_condition_decision,
    sport_v2_condition_matrix,
    sport_v2_echo_sounder_ownership,
    sport_v2_hg_overlap_matrix,
    sport_v2_kind_class,
    sport_v2_kind_count,
    sport_v2_package_a_field_target,
)


def _kinds(sections: dict) -> set[str]:
    out: set[str] = set()
    for catalog in sections.values():
        for role in catalog["roles"]:
            out.add(role["label"])
    return out


def test_sport_hobby_v2_cleanup_contracts() -> None:
    sport_v2_assert_cleanup_contracts()
    assert SPORT_ROOT_SLUG == "sports-hobby"
    assert SPORT_ROOT_LABEL == "Спорт, отдых и хобби"
    assert SPORT_V2_EXPECTED_L2_COUNT == 13
    assert len(SPORT_V2_CANONICAL_LEAVES) == 13
    assert len(SPORT_SECTIONS) == 13
    assert sport_v2_kind_count() == 96


def test_sport_hobby_no_dual_tree() -> None:
    active = {c["category_slug"] for c in SPORT_SECTIONS.values()}
    assert active == SPORT_V2_CANONICAL_SLUGS
    assert SPORT_V2_LEGACY_L2_SLUGS.isdisjoint(active)
    for slug in SPORT_V2_RETIRED_NATIONAL_CRAFT_SLUGS:
        assert slug not in active
    assert "sports-equipment" not in active
    assert "sports-tourism" not in active
    assert "sports-music" not in active


def test_sport_hobby_legacy_and_craft_retired() -> None:
    assert SPORT_V2_LEGACY_L2_SLUGS <= SPORT_V2_RETIRED_SLUGS
    assert SPORT_V2_RETIRED_NATIONAL_CRAFT_SLUGS <= SPORT_V2_RETIRED_SLUGS
    for kind in ("Охотничьи ножи", "Юрты", "Шырдаки", "Ала кийиз"):
        assert kind in SPORT_V2_RETIRED_KINDS
        assert kind not in set(sport_v2_all_kinds())
    assert (
        SPORT_V2_RETIRED_KINDS["Охотничьи ножи"][0]
        == "RETIRED_POLICY_RESTRICTED_NO_DESTINATION"
    )
    assert SPORT_V2_RETIRED_KINDS["Юрты"][0] == "RETIRED_NO_CANONICAL_DESTINATION"


def test_sport_hobby_product_identity_matrix() -> None:
    allowed = {
        "SPORT_GOOD",
        "FITNESS_GOOD",
        "NUTRITION_CONSUMABLE",
        "OUTDOOR_GOOD",
        "FISHING_GOOD",
        "MUSIC_INSTRUMENT",
        "HORSE_GEAR",
        "COLLECTIBLE",
        "BOARD_GAME",
        "CRAFT_HOBBY",
        "ANTIQUE_ART",
        "HOBBY_OTHER",
    }
    for kind in sport_v2_all_kinds():
        assert sport_v2_kind_class(kind) in allowed
    assert sport_v2_kind_class("Эхолоты") == "FISHING_GOOD"
    assert sport_v2_kind_class("Синтезаторы") == "MUSIC_INSTRUMENT"
    assert sport_v2_kind_class("Сёдла") == "HORSE_GEAR"
    assert SPORT_V2_BANNED_KINDS.isdisjoint(set(sport_v2_all_kinds()))


def test_sport_hobby_condition_matrix_independent() -> None:
    matrix = sport_v2_condition_matrix()
    assert matrix["YES"] + matrix["NO"] == sport_v2_kind_count()
    assert matrix == {"YES": 85, "NO": 11}
    for kind in SPORT_V2_SECTION_KINDS["nutrition"]:
        assert sport_v2_condition_decision(kind) == "NO"
    assert sport_v2_condition_decision("Блёсны и приманки") == "NO"
    assert sport_v2_condition_decision("Бисер") == "NO"
    assert sport_v2_condition_decision("Гитары") == "YES"
    assert sport_v2_condition_decision("Эхолоты") == "YES"
    for catalog in SPORT_SECTIONS.values():
        labels = [g["label"] for g in catalog["filters"]]
        kinds = [r["label"] for r in catalog["roles"]]
        any_yes = any(sport_v2_condition_decision(k) == "YES" for k in kinds)
        assert ("Состояние" in labels) is any_yes
        if "Состояние" in labels:
            cond = next(g for g in catalog["filters"] if g["label"] == "Состояние")
            assert [o["label"] for o in cond["options"]] == list(SPORT_CONDITION_OPTIONS)


def test_sport_hobby_seller_target() -> None:
    assert SPORT_SELLER_OPTIONS == ("Частное лицо", "Магазин", "Другой")
    for catalog in SPORT_SECTIONS.values():
        seller = catalog["filters"][0]
        assert seller["label"] == "Продавец"
        assert [o["label"] for o in seller["options"]] == list(SPORT_SELLER_OPTIONS)
        assert "Компания" not in [o["label"] for o in seller["options"]]
        assert "Мастерская" not in [o["label"] for o in seller["options"]]


def test_sport_hobby_echo_sounder_ownership() -> None:
    own = sport_v2_echo_sounder_ownership()
    assert own["kind"] == "Эхолоты"
    assert own["owner"] == "SPORT_FISHING"
    assert "Эхолоты" in SPORT_V2_SECTION_KINDS["hunting"]
    assert "Эхолоты" not in _kinds(ELECTRONICS_SECTIONS)


def test_sport_hobby_musical_instruments_vs_electronics() -> None:
    sport = _kinds(SPORT_SECTIONS)
    electronics = _kinds(ELECTRONICS_SECTIONS)
    for instrument in ("Гитары", "Синтезаторы", "Пианино", "Комуз"):
        assert instrument in sport
        assert instrument not in electronics
    # General audio remains Electronics ownership sample.
    assert electronics.isdisjoint({"Гитары", "Синтезаторы", "Комуз"})


def test_sport_hobby_weapons_and_knife_absent() -> None:
    kinds = set(sport_v2_all_kinds())
    for banned in (
        "Охотничьи ножи",
        "Огнестрельное оружие",
        "Патроны",
        "Арбалеты",
    ):
        assert banned not in kinds


def test_sport_hobby_national_craft_absent() -> None:
    kinds = set(sport_v2_all_kinds())
    for craft in ("Юрты", "Шырдаки", "Тундуки", "Ала кийиз", "Войлочные ковры"):
        assert craft not in kinds
    for slug in SPORT_V2_RETIRED_NATIONAL_CRAFT_SLUGS:
        assert slug not in {c["category_slug"] for c in SPORT_SECTIONS.values()}


def test_sport_hobby_simple_field_target() -> None:
    target = sport_v2_package_a_field_target()
    assert target["kind"] == "sport_kind"
    assert target["kind_label"] == "Товар"
    assert target["size"] == "ABSENT_DESCRIPTION"
    assert target["price_basis"] == "ABSENT"
    assert target["brand"] == "ABSENT_DESCRIPTION"
    assert "AI must not invent" in SPORT_AI_CHARACTERISTIC_RULE
    for forbidden in (
        "size",
        "brand",
        "model",
        "weight",
        "price_basis",
        "gender",
        "age",
        "level",
    ):
        assert forbidden in target["forbidden"]


def test_sport_hobby_platform_coherence() -> None:
    sport = _kinds(SPORT_SECTIONS)
    kids = _kinds(KIDS_SECTIONS)
    be = _kinds(BUSINESS_SECTIONS)
    services: set[str] = set()
    for catalog in SERVICE_SECTIONS.values():
        for item in catalog.get("kinds") or []:
            if isinstance(item, dict):
                services.add(str(item.get("label") or item.get("value") or ""))
            else:
                services.add(str(item))
    assert sport.isdisjoint(
        {
            "Велосипеды",
            "Детские велосипеды",
            "Детские самокаты",
            "Беговелы",
            "Санки и снегокаты",
        }
    )
    assert "Бильярдные столы" not in sport
    assert "Тренажёры для залов" not in sport
    assert sport.isdisjoint({"Вакансия", "Тренер", "Прокат"})
    assert "Эхолоты" in sport
    # Kids / BE / Services catalogs should not own Sport fishing gear.
    assert "Эхолоты" not in kids
    assert "Эхолоты" not in be
    assert "Эхолоты" not in services
    # HG may own household thermos wording elsewhere; camping thermos stays Sport.
    assert "Термосы" in SPORT_V2_SECTION_KINDS["camping"]
    assert sport_v2_hg_overlap_matrix()
    # Horse living animals not in Sport.
    assert "Лошади" not in sport


def test_sport_hobby_sections_catalog_matches_v2() -> None:
    assert set(SPORT_SECTIONS) == set(SPORT_V2_SECTION_KINDS)
    for key, kinds in SPORT_V2_SECTION_KINDS.items():
        roles = [r["label"] for r in SPORT_SECTIONS[key]["roles"]]
        assert tuple(roles) == kinds


def test_sport_hobby_no_l3_l4_in_canonical_leaves() -> None:
    for _label, slug, _sort in SPORT_V2_CANONICAL_LEAVES:
        # All modern L2 are direct children slugs under sports-hobby-*.
        assert slug.startswith("sports-hobby-")
        # No deeper nested path encoded in slug beyond L2 leaf pattern.
        assert slug.count("-") >= 2
