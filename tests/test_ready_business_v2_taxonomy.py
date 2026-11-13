"""Ready Business V2 taxonomy + product identity (pre–Package A)."""
from __future__ import annotations

from app.seeds.business_sections_catalog import BUSINESS_SECTIONS
from app.seeds.ready_business_sections_catalog import READY_BUSINESS_SECTIONS
from app.seeds.ready_business_v2 import (
    READY_BUSINESS_AI_FINANCIAL_CLAIM_RULE,
    READY_BUSINESS_CONDITION_POLICY,
    READY_BUSINESS_CREATE_FORBIDDEN,
    READY_BUSINESS_FRANCHISE_SLUG,
    READY_BUSINESS_NEGOTIABLE_POLICY,
    READY_BUSINESS_POSTER_OPTIONS,
    READY_BUSINESS_PRICE_SEMANTICS,
    READY_BUSINESS_ROOT_LABEL,
    READY_BUSINESS_ROOT_SLUG,
    READY_BUSINESS_ROOT_UI_ALIAS,
    READY_BUSINESS_SEARCH_FORBIDDEN,
    READY_BUSINESS_V2_CANONICAL_LEAVES,
    READY_BUSINESS_V2_CANONICAL_SLUGS,
    READY_BUSINESS_V2_EXPECTED_L2_COUNT,
    READY_BUSINESS_V2_LEGACY_L2_SLUGS,
    READY_BUSINESS_V2_RETIRED_KINDS,
    READY_BUSINESS_V2_RETIRED_MODERN,
    READY_BUSINESS_V2_RETIRED_SLUGS,
    READY_BUSINESS_V2_SECTION_KINDS,
    ready_business_v2_all_kinds,
    ready_business_v2_assert_cleanup_contracts,
    ready_business_v2_condition_decision,
    ready_business_v2_kind_class,
    ready_business_v2_kind_count,
    ready_business_v2_package_a_field_target,
    ready_business_v2_premises_decision,
)
def _kinds(sections: dict) -> set[str]:
    out: set[str] = set()
    for catalog in sections.values():
        for role in catalog["roles"]:
            out.add(role["label"])
    return out


def test_ready_business_v2_cleanup_contracts() -> None:
    ready_business_v2_assert_cleanup_contracts()
    assert READY_BUSINESS_ROOT_SLUG == "ready-business"
    assert READY_BUSINESS_ROOT_LABEL == "Готовый бизнес и франшизы"
    assert READY_BUSINESS_ROOT_UI_ALIAS == "Готовый бизнес"
    assert READY_BUSINESS_V2_EXPECTED_L2_COUNT == 16
    assert len(READY_BUSINESS_V2_CANONICAL_LEAVES) == 16
    assert len(READY_BUSINESS_SECTIONS) == 16
    assert ready_business_v2_kind_count() == 70


def test_ready_business_no_dual_tree() -> None:
    active = {c["category_slug"] for c in READY_BUSINESS_SECTIONS.values()}
    assert active == READY_BUSINESS_V2_CANONICAL_SLUGS
    assert READY_BUSINESS_V2_LEGACY_L2_SLUGS.isdisjoint(active)
    for slug in READY_BUSINESS_V2_RETIRED_MODERN:
        assert slug not in active
    assert "ready-business-franchise" not in active
    assert READY_BUSINESS_FRANCHISE_SLUG in active


def test_ready_business_legacy_and_non_business_retired() -> None:
    assert READY_BUSINESS_V2_LEGACY_L2_SLUGS <= READY_BUSINESS_V2_RETIRED_SLUGS
    assert "ready-business-dolya-v-biznese-i-investitsii" in READY_BUSINESS_V2_RETIRED_SLUGS
    assert "ready-business-kriptobiznes-i-tsifrovye-aktivy" in READY_BUSINESS_V2_RETIRED_SLUGS
    assert "ready-business-biznes-pod-klyuch" in READY_BUSINESS_V2_RETIRED_SLUGS
    for kind in ("Линии", "Офисы", "Готовые ОсОО"):
        assert kind in READY_BUSINESS_V2_RETIRED_KINDS
        assert kind not in set(ready_business_v2_all_kinds())


def test_ready_business_product_identity_matrix() -> None:
    kinds = ready_business_v2_all_kinds()
    assert kinds
    for kind in kinds:
        klass = ready_business_v2_kind_class(kind)
        assert klass in ("READY_BUSINESS", "FRANCHISE")
    franchise = set(READY_BUSINESS_V2_SECTION_KINDS["franchise"])
    for kind in franchise:
        assert ready_business_v2_kind_class(kind) == "FRANCHISE"
    for kind in kinds:
        if kind not in franchise:
            assert ready_business_v2_kind_class(kind) == "READY_BUSINESS"


def test_ready_business_condition_absent() -> None:
    assert READY_BUSINESS_CONDITION_POLICY == "ABSENT"
    for kind in ready_business_v2_all_kinds():
        assert ready_business_v2_condition_decision(kind) == "NO"
    for catalog in READY_BUSINESS_SECTIONS.values():
        assert "Состояние" not in [g["label"] for g in catalog["filters"]]


def test_ready_business_poster_contract() -> None:
    assert READY_BUSINESS_POSTER_OPTIONS == ("Владелец", "Представитель", "Другой")
    for catalog in READY_BUSINESS_SECTIONS.values():
        poster = catalog["filters"][0]
        assert poster["label"] == "Кто разместил"
        assert [o["label"] for o in poster["options"]] == list(
            READY_BUSINESS_POSTER_OPTIONS
        )
        assert "Франчайзер" not in [o["label"] for o in poster["options"]]
        assert "Частное лицо" not in [o["label"] for o in poster["options"]]


def test_ready_business_premises_matrix_independent() -> None:
    expected_no = {
        "Интернет-магазины",
        "Витрины",
        "Маркетплейсы",
        "Другие онлайн-магазины",
        "Франшиза точки",
        "Региональная франшиза",
        "Мастер-франшиза",
        "Другие франшизы",
    }
    for kind in ready_business_v2_all_kinds():
        decision = ready_business_v2_premises_decision(kind)
        if kind in expected_no:
            assert decision == "NO", kind
        else:
            assert decision == "YES", kind
    # Catalog filters must match matrix (not self-prove via copying only).
    for key, catalog in READY_BUSINESS_SECTIONS.items():
        labels = [g["label"] for g in catalog["filters"]]
        has_premises = "Помещение" in labels
        kinds = [r["label"] for r in catalog["roles"]]
        if key in ("online", "franchise"):
            assert has_premises is False
            assert all(ready_business_v2_premises_decision(k) == "NO" for k in kinds)
        else:
            assert has_premises is True
            assert all(ready_business_v2_premises_decision(k) == "YES" for k in kinds)


def test_ready_business_price_semantics_and_simple_target() -> None:
    assert READY_BUSINESS_PRICE_SEMANTICS["ready_business"] == "ASKING_SALE_PRICE"
    assert READY_BUSINESS_PRICE_SEMANTICS["franchise"] == "ENTRY_START_PRICE"
    assert READY_BUSINESS_NEGOTIABLE_POLICY == "CANONICAL_YES"
    target = ready_business_v2_package_a_field_target()
    assert target["condition"] == "ABSENT"
    assert target["poster"] == "poster_type"
    assert "revenue" in target["forbidden"]
    assert "profit" in READY_BUSINESS_CREATE_FORBIDDEN
    assert "royalty" in READY_BUSINESS_SEARCH_FORBIDDEN
    assert "AI must not invent" in READY_BUSINESS_AI_FINANCIAL_CLAIM_RULE


def test_ready_business_platform_coherence() -> None:
    rb = _kinds(READY_BUSINESS_SECTIONS)
    be = _kinds(BUSINESS_SECTIONS)
    # Equipment catalogs must not share ready-business going-concern kinds.
    assert "Линии" not in rb
    assert rb.isdisjoint(
        {"Холодильные витрины", "Промышленные прямострочки", "Генераторы"}
    )
    assert be.isdisjoint({"Кафе", "Рестораны", "Автомойки"})
    # Services / Jobs ownership sample — consulting/vacancy not RB kinds.
    assert "Бухгалтерские услуги" not in rb
    assert rb.isdisjoint({"Вакансия", "Резюме"})
    # Finance L2 label no longer says investment.
    finance = READY_BUSINESS_SECTIONS["finance"]
    assert finance["label"] == "Финансовый бизнес"
    assert "Офисы" not in [r["label"] for r in finance["roles"]]
    # Boxes kept under auto as operating auto-business identity.
    assert "Боксы" in READY_BUSINESS_V2_SECTION_KINDS["auto"]
    assert ready_business_v2_kind_class("Боксы") == "READY_BUSINESS"


def test_ready_business_sections_catalog_matches_v2() -> None:
    assert set(READY_BUSINESS_SECTIONS) == set(READY_BUSINESS_V2_SECTION_KINDS)
    for key, kinds in READY_BUSINESS_V2_SECTION_KINDS.items():
        roles = [r["label"] for r in READY_BUSINESS_SECTIONS[key]["roles"]]
        assert tuple(roles) == kinds
