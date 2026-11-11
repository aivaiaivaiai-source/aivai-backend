"""Fashion V2 Package B — Search SoT + semantic Size/Condition allowlists."""

from __future__ import annotations

from app.seeds.fashion_v2 import (
    FASHION_V2_APPROVED_CONDITION_EXPECTATIONS,
    FASHION_V2_APPROVED_SIZE_EXPECTATIONS,
    FASHION_V2_CANONICAL_SLUGS,
    FASHION_V2_LOCKED_NO_CONDITION_KINDS,
    FASHION_V2_LOCKED_NO_SIZE_KINDS,
    FASHION_V2_NO_CONDITION_KINDS,
    FASHION_V2_NO_SIZE_KINDS,
    FASHION_V2_SEARCH_ALLOWLIST,
    FASHION_V2_SEARCH_CONDITION_KIND_ALLOWLIST,
    FASHION_V2_SEARCH_EAV_KEYS,
    FASHION_V2_SEARCH_EXCLUDE,
    FASHION_V2_SEARCH_SIZE_KIND_ALLOWLIST,
    build_fashion_v2_core_fields,
    build_fashion_v2_search_filters,
    fashion_v2_all_kinds,
    fashion_v2_assert_condition_contract,
    fashion_v2_assert_semantic_partition,
    fashion_v2_condition_visible_for_kind,
)

# Independent expectations (must not only mirror production frozensets).
_INDEPENDENT_SIZE_YES = frozenset(
    {
        "Платья",
        "Юбки",
        "Рубашки",
        "Туфли",
        "Мужские кроссовки",
    }
)
_INDEPENDENT_SIZE_NO = frozenset(
    {
        "Трусы",
        "Носки",
        "Колготки",
        "Женские сумки",
        "Купальники",
        "Бельё для кормления",
    }
)
_INDEPENDENT_CONDITION_NO = frozenset(
    {
        "Бюстгальтеры",
        "Трусы",
        "Комплекты белья",
        "Носки",
        "Колготки",
        "Боди",
        "Другое бельё",
        "Бельё для кормления",
        "Купальники",
        "Плавки",
    }
)
_INDEPENDENT_CONDITION_YES = frozenset(
    {
        "Платья",
        "Рубашки",
        "Туфли",
        "Женские сумки",
        "Мужские наручные часы",
        "Спортивные костюмы",
    }
)
_FORBIDDEN_SEARCH = frozenset(
    {
        "season",
        "gender",
        "material",
        "brand",
        "color",
        "style",
        "watch_movement",
        "underwear_size",
        "price",
        "negotiable",
        "contact_methods",
    }
)


def test_fashion_v2_package_a_size_condition_contracts_still_hold() -> None:
    fashion_v2_assert_semantic_partition()
    fashion_v2_assert_condition_contract()
    assert len(FASHION_V2_APPROVED_SIZE_EXPECTATIONS) == 36
    assert len(FASHION_V2_NO_SIZE_KINDS) == 78
    assert len(FASHION_V2_APPROVED_CONDITION_EXPECTATIONS) == 104
    assert len(FASHION_V2_NO_CONDITION_KINDS) == 10


def test_fashion_v2_search_filters_cover_all_canonical_l2() -> None:
    filters = build_fashion_v2_search_filters()
    assert set(filters) == FASHION_V2_CANONICAL_SLUGS
    assert len(filters) == 17


def test_fashion_v2_search_eav_keys_are_short_allowlist() -> None:
    assert FASHION_V2_SEARCH_EAV_KEYS <= FASHION_V2_SEARCH_ALLOWLIST
    assert "price" not in FASHION_V2_SEARCH_EAV_KEYS
    assert "negotiable" not in FASHION_V2_SEARCH_EAV_KEYS
    assert "region" not in FASHION_V2_SEARCH_EAV_KEYS  # shared geo UX


def test_fashion_v2_search_filters_no_removed_or_create_only_fields() -> None:
    for slug, rows in build_fashion_v2_search_filters().items():
        keys = {r[0] for r in rows}
        assert keys <= FASHION_V2_SEARCH_EAV_KEYS, slug
        assert keys.isdisjoint(_FORBIDDEN_SEARCH), slug
        assert keys.isdisjoint(FASHION_V2_SEARCH_EXCLUDE), slug
        assert "fashion_kind" in keys, slug
        assert "seller_type" in keys, slug


def test_fashion_v2_underwear_section_search_no_size_no_condition() -> None:
    rows = build_fashion_v2_search_filters()["fashion-nizhnee-bele"]
    keys = {r[0] for r in rows}
    assert "size" not in keys
    assert "condition" not in keys
    assert keys == {"fashion_kind", "seller_type"}


def test_fashion_v2_search_size_semantic_independent() -> None:
    assert _INDEPENDENT_SIZE_YES <= FASHION_V2_SEARCH_SIZE_KIND_ALLOWLIST
    assert _INDEPENDENT_SIZE_NO.isdisjoint(FASHION_V2_SEARCH_SIZE_KIND_ALLOWLIST)
    assert FASHION_V2_SEARCH_SIZE_KIND_ALLOWLIST == frozenset(
        FASHION_V2_APPROVED_SIZE_EXPECTATIONS
    )
    assert FASHION_V2_LOCKED_NO_SIZE_KINDS.isdisjoint(
        FASHION_V2_SEARCH_SIZE_KIND_ALLOWLIST
    )


def test_fashion_v2_search_condition_semantic_independent() -> None:
    assert _INDEPENDENT_CONDITION_NO == FASHION_V2_LOCKED_NO_CONDITION_KINDS
    assert _INDEPENDENT_CONDITION_NO == FASHION_V2_NO_CONDITION_KINDS
    assert _INDEPENDENT_CONDITION_YES <= FASHION_V2_SEARCH_CONDITION_KIND_ALLOWLIST
    for kind in _INDEPENDENT_CONDITION_NO:
        assert not fashion_v2_condition_visible_for_kind(kind)
    for kind in _INDEPENDENT_CONDITION_YES:
        assert fashion_v2_condition_visible_for_kind(kind)


def test_fashion_v2_search_size_options_match_approved_group() -> None:
    cores = build_fashion_v2_core_fields()
    filters = build_fashion_v2_search_filters()
    women_size = next(r for r in filters["fashion-zhenskaya-odezhda"] if r[0] == "size")
    cfg = women_size[4] or {}
    choices = cfg.get("choices") or cfg.get("options") or []
    dress_opts = [
        c["value"]
        for c in choices
        if "Платья" in (c.get("for_kinds") or [])
    ]
    assert dress_opts  # non-empty
    # Clothing RU sizes, not shoe sizes.
    assert "35" not in dress_opts
    assert "40" in dress_opts


def test_fashion_v2_114_kind_search_audit() -> None:
    """All 114 kinds: Search Size/Condition applicability matches Package A."""
    all_kinds = fashion_v2_all_kinds()
    assert len(all_kinds) == 114
    size_yes = set(FASHION_V2_SEARCH_SIZE_KIND_ALLOWLIST)
    cond_yes = set(FASHION_V2_SEARCH_CONDITION_KIND_ALLOWLIST)
    assert size_yes | set(FASHION_V2_NO_SIZE_KINDS) == all_kinds
    assert cond_yes | set(FASHION_V2_NO_CONDITION_KINDS) == all_kinds
    assert size_yes.isdisjoint(FASHION_V2_NO_SIZE_KINDS)
    assert cond_yes.isdisjoint(FASHION_V2_NO_CONDITION_KINDS)

    filters = build_fashion_v2_search_filters()
    for slug, rows in filters.items():
        by_key = {r[0]: r for r in rows}
        if "size" in by_key:
            cfg = by_key["size"][4] or {}
            dep = (cfg.get("depends_on") or {}).get("values") or []
            assert set(dep) <= size_yes
            assert set(dep).isdisjoint(FASHION_V2_NO_SIZE_KINDS)
        if "condition" in by_key:
            cfg = by_key["condition"][4] or {}
            dep = (cfg.get("depends_on") or {}).get("values") or []
            # Whole-section YES → no depends_on; mixed → explicit YES kinds.
            if dep:
                assert set(dep) <= cond_yes
                assert set(dep).isdisjoint(FASHION_V2_NO_CONDITION_KINDS)


def test_fashion_v2_sport_search_swimwear_no_condition() -> None:
    rows = build_fashion_v2_search_filters()["fashion-sportivnaya-odezhda-i-obuv"]
    cond = next(r for r in rows if r[0] == "condition")
    vals = ((cond[4] or {}).get("depends_on") or {}).get("values") or []
    assert "Купальники" not in vals
    assert "Плавки" not in vals
    assert "Спортивные костюмы" in vals
    assert "size" not in {r[0] for r in rows}


def test_fashion_v2_create_cores_unchanged_by_search_builder() -> None:
    """Package B must not alter Package A Create cores."""
    cores = build_fashion_v2_core_fields()
    underwear = {r[0] for r in cores["fashion-nizhnee-bele"]}
    assert "condition" not in underwear
    assert "size" not in underwear
    assert "season" not in underwear
    women = {r[0] for r in cores["fashion-zhenskaya-odezhda"]}
    assert "condition" in women
    assert "size" in women
