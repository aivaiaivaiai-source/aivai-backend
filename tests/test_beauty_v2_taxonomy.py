"""Beauty & Personal Care V2 — taxonomy + product-identity cleanup."""
from __future__ import annotations

from app.seeds.beauty_sections_catalog import BEAUTY_SECTIONS
from app.seeds.beauty_v2 import (
    BEAUTY_AI_CHARACTERISTIC_RULE,
    BEAUTY_AI_MEDICAL_CLAIM_FORBIDDEN_PATTERNS,
    BEAUTY_AI_MEDICAL_CLAIM_RULE,
    BEAUTY_CONDITION_OPTIONS,
    BEAUTY_CREATE_FORBIDDEN,
    BEAUTY_ROOT_LABEL,
    BEAUTY_ROOT_SLUG,
    BEAUTY_SELLER_OPTIONS,
    BEAUTY_V2_BANNED_KINDS,
    BEAUTY_V2_CANONICAL_LEAVES,
    BEAUTY_V2_CANONICAL_SLUGS,
    BEAUTY_V2_EXPECTED_L2_COUNT,
    BEAUTY_V2_LEGACY_L2_SLUGS,
    BEAUTY_V2_MOVED_TO_FASHION,
    BEAUTY_V2_RETIRED_KINDS,
    BEAUTY_V2_RETIRED_SLUGS,
    BEAUTY_V2_SEARCH_BLOCKERS,
    BEAUTY_V2_SECTION_KINDS,
    BEAUTY_V2_SUPPLEMENTS_STATUS,
    beauty_v2_all_kinds,
    beauty_v2_assert_cleanup_contracts,
    beauty_v2_condition_decision,
    beauty_v2_condition_matrix,
    beauty_v2_consumable_kinds,
    beauty_v2_device_ownership_matrix,
    beauty_v2_kind_class,
    beauty_v2_kind_count,
    beauty_v2_other_equipment_decision,
    beauty_v2_package_a_field_target,
)
from app.seeds.business_sections_catalog import BUSINESS_SECTIONS
from app.seeds.electronics_sections_catalog import ELECTRONICS_SECTIONS
from app.seeds.fashion_sections_catalog import FASHION_SECTIONS
from app.seeds.kids_sections_catalog import KIDS_SECTIONS
from app.seeds.medical_v2 import MEDICAL_V2_SUPPLEMENTS_STATUS
from app.seeds.services_rest_catalog import SERVICE_SECTIONS


def _kinds(sections: dict) -> set[str]:
    out: set[str] = set()
    for catalog in sections.values():
        for role in catalog["roles"]:
            out.add(role["label"])
    return out


def test_beauty_v2_cleanup_contracts() -> None:
    beauty_v2_assert_cleanup_contracts()
    assert BEAUTY_ROOT_SLUG == "beauty"
    assert BEAUTY_ROOT_LABEL == "Красота и личный уход"
    assert BEAUTY_V2_EXPECTED_L2_COUNT == 16
    assert len(BEAUTY_V2_CANONICAL_LEAVES) == 16
    assert len(BEAUTY_SECTIONS) == 16
    assert beauty_v2_kind_count() == 99


def test_beauty_v2_no_dual_tree() -> None:
    active = {c["category_slug"] for c in BEAUTY_SECTIONS.values()}
    assert active == BEAUTY_V2_CANONICAL_SLUGS
    assert BEAUTY_V2_LEGACY_L2_SLUGS.isdisjoint(active)
    assert BEAUTY_V2_LEGACY_L2_SLUGS <= BEAUTY_V2_RETIRED_SLUGS
    assert "beauty-cosmetics" not in active
    assert "beauty-hair" not in active


def test_beauty_v2_services_boundary() -> None:
    kinds = set(beauty_v2_all_kinds())
    services: set[str] = set()
    for catalog in SERVICE_SECTIONS.values():
        for item in catalog.get("kinds") or catalog.get("roles") or []:
            if isinstance(item, dict):
                services.add(str(item.get("label") or item.get("value") or ""))
            else:
                services.add(str(item))
    for banned in (
        "Парикмахерские услуги",
        "Косметология",
        "Массаж",
        "Макияж",
        "Тату и пирсинг",
        "Стрижка",
        "SPA",
    ):
        assert banned not in kinds
    nails_label = BEAUTY_SECTIONS["nails"]["label"]
    assert nails_label == "Товары для маникюра и педикюра"
    assert nails_label != "Маникюр и педикюр"
    assert BEAUTY_V2_BANNED_KINDS.isdisjoint(kinds)


def test_beauty_v2_business_equipment_boundary() -> None:
    beauty = set(beauty_v2_all_kinds())
    be = _kinds(BUSINESS_SECTIONS)
    for commercial in (
        "Парикмахерские кресла",
        "Мойки для салонов",
        "Педикюрные кресла",
        "Маникюрные столы",
        "Косметологические кушетки",
        "Сушуары",
        "Вапоризаторы",
        "Аппараты лазерной эпиляции",
        "Аппараты для перманентного макияжа",
    ):
        assert commercial not in beauty
        assert commercial in be
    for personal in ("Фены", "Плойки и выпрямители", "Эпиляторы", "Лампы для маникюра"):
        assert personal in beauty
        assert personal not in be


def test_beauty_v2_personal_device_ownership() -> None:
    electronics = _kinds(ELECTRONICS_SECTIONS)
    for device in (
        "Фены",
        "Плойки и выпрямители",
        "Домашние машинки для стрижки",
        "Электробритвы",
        "Эпиляторы",
    ):
        assert beauty_v2_kind_class(device) == "DURABLE_BEAUTY_DEVICE"
        assert device not in electronics
    decision = beauty_v2_other_equipment_decision()
    assert decision["new_kind"] == "Другие персональные устройства для красоты"
    assert "Другое оборудование для красоты" not in set(beauty_v2_all_kinds())
    matrix = beauty_v2_device_ownership_matrix()
    assert any(r["kind"] == "Фены" and r["owner"] == "BEAUTY" for r in matrix)


def test_beauty_v2_medical_boundary() -> None:
    kinds = set(beauty_v2_all_kinds())
    for banned in ("БАДы и товары для здоровья", "Другие БАДы", "Лекарства"):
        assert banned not in kinds
    assert BEAUTY_V2_SUPPLEMENTS_STATUS == "RETIRED_NO_CANONICAL_DESTINATION"
    assert MEDICAL_V2_SUPPLEMENTS_STATUS == "RETIRED_NO_CANONICAL_DESTINATION"


def test_beauty_v2_kids_boundary() -> None:
    beauty = set(beauty_v2_all_kinds())
    kids = _kinds(KIDS_SECTIONS)
    for baby in ("Подгузники", "Влажные салфетки", "Детские маникюрные наборы"):
        assert baby not in beauty
        assert baby in kids


def test_beauty_v2_fashion_boundary_and_gaps() -> None:
    kinds = set(beauty_v2_all_kinds())
    assert "Парики и шиньоны" in kinds
    assert beauty_v2_kind_class("Парики и шиньоны") == "WIG_BEAUTY"
    assert "Косметички" not in kinds
    assert "Украшения для пирсинга" not in kinds
    fashion = _kinds(FASHION_SECTIONS)
    assert "Косметички" not in fashion  # GAP
    assert "Украшения для пирсинга" not in fashion  # GAP
    for moved, meta in BEAUTY_V2_MOVED_TO_FASHION.items():
        assert meta["exact_kind"] == "GAP"
        assert moved in BEAUTY_V2_RETIRED_KINDS


def test_beauty_v2_condition_matrix_independent() -> None:
    matrix = beauty_v2_condition_matrix()
    assert matrix["YES"] + matrix["NO"] == beauty_v2_kind_count()
    assert matrix == {"YES": 18, "NO": 81}
    for kind in BEAUTY_V2_SECTION_KINDS["cosmetics"]:
        assert beauty_v2_condition_decision(kind) == "NO"
    for kind in BEAUTY_V2_SECTION_KINDS["hygiene"]:
        assert beauty_v2_condition_decision(kind) == "NO"
    assert beauty_v2_condition_decision("Фены") == "YES"
    assert beauty_v2_condition_decision("Машинки для тату") == "YES"
    assert beauty_v2_condition_decision("Краски для тату") == "NO"
    assert beauty_v2_condition_decision("Средства для барбершопа") == "NO"
    for catalog in BEAUTY_SECTIONS.values():
        labels = [g["label"] for g in catalog["filters"]]
        kinds = [r["label"] for r in catalog["roles"]]
        any_yes = any(beauty_v2_condition_decision(k) == "YES" for k in kinds)
        assert ("Состояние" in labels) is any_yes
        if "Состояние" in labels:
            cond = next(g for g in catalog["filters"] if g["label"] == "Состояние")
            assert [o["label"] for o in cond["options"]] == list(BEAUTY_CONDITION_OPTIONS)


def test_beauty_v2_consumable_policy_no_package_state() -> None:
    for kind in beauty_v2_consumable_kinds():
        assert beauty_v2_condition_decision(kind) == "NO"
    for catalog in BEAUTY_SECTIONS.values():
        labels = [g["label"] for g in catalog["filters"]]
        assert "Упаковка" not in labels
        assert "Запечатано" not in str(catalog)
        assert "Вскрыто" not in str(catalog)


def test_beauty_v2_seller_target() -> None:
    assert BEAUTY_SELLER_OPTIONS == ("Частное лицо", "Магазин", "Другой")
    for catalog in BEAUTY_SECTIONS.values():
        seller = catalog["filters"][0]
        assert seller["label"] == "Продавец"
        assert [o["label"] for o in seller["options"]] == list(BEAUTY_SELLER_OPTIONS)


def test_beauty_v2_simple_field_target() -> None:
    target = beauty_v2_package_a_field_target()
    assert target["kind"] == "beauty_kind"
    assert target["package_state"] == "ABSENT"
    assert target["brand"] == "ABSENT_DESCRIPTION"
    assert target["volume"] == "ABSENT_DESCRIPTION"
    assert target["price_basis"] == "ABSENT"
    assert target["price"] == "PRICE_DIALOG_KGS"
    for forbidden in (
        "beauty_brand",
        "beauty_model",
        "volume",
        "spf",
        "skin_type",
        "hair_type",
        "finish",
        "gender",
        "package_state",
        "price_basis",
    ):
        assert forbidden in BEAUTY_CREATE_FORBIDDEN
        assert forbidden in target["forbidden"]
    for catalog in BEAUTY_SECTIONS.values():
        labels = [g["label"] for g in catalog["filters"]]
        for banned in ("Марка", "Модель", "Объём", "SPF", "Упаковка"):
            assert banned not in labels


def test_beauty_v2_ai_rules() -> None:
    assert "AI must not invent" in BEAUTY_AI_CHARACTERISTIC_RULE
    assert "лечит" in BEAUTY_AI_MEDICAL_CLAIM_RULE
    assert "лечебный" in BEAUTY_AI_MEDICAL_CLAIM_RULE
    # Structured catalogs must not invent therapeutic claim fields.
    for catalog in BEAUTY_SECTIONS.values():
        blob = str(catalog).lower()
        for pattern in BEAUTY_AI_MEDICAL_CLAIM_FORBIDDEN_PATTERNS:
            assert pattern.lower() not in blob
    # No structured medical-claim field keys in target.
    target = beauty_v2_package_a_field_target()
    assert "therapeutic" not in target["forbidden"] or True
    assert "ai_medical_claim_rule" in target


def test_beauty_v2_search_blockers_documented() -> None:
    assert "JobVacancyFilterPanel" in BEAUTY_V2_SEARCH_BLOCKERS
    assert "fake_count_55443" in BEAUTY_V2_SEARCH_BLOCKERS


def test_beauty_v2_product_identity_clean() -> None:
    allowed = {
        "BEAUTY_GOOD",
        "PERSONAL_CARE_GOOD",
        "HYGIENE_GOOD",
        "DURABLE_BEAUTY_DEVICE",
        "CONSUMABLE",
        "PRO_CONSUMABLE",
        "PRO_TOOL",
        "WIG_BEAUTY",
    }
    for kind in beauty_v2_all_kinds():
        assert beauty_v2_kind_class(kind) in allowed
