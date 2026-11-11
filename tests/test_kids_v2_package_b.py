"""Kids V2 Package B — Search SoT + semantic Size/Age/Condition/Mounting."""

from __future__ import annotations

from app.seeds.kids_v2 import (
    KIDS_V2_APPROVED_AGE_EXPECTATIONS,
    KIDS_V2_APPROVED_SIZE_EXPECTATIONS,
    KIDS_V2_CANONICAL_GOODS_SLUGS,
    KIDS_V2_CREATE_FORBIDDEN,
    KIDS_V2_EXPECTED_KIND_COUNT,
    KIDS_V2_EXPECTED_L2_COUNT,
    KIDS_V2_LOCKED_NO_CONDITION_KINDS,
    KIDS_V2_MOUNTING_KINDS,
    KIDS_V2_SEARCH_ALLOWLIST,
    KIDS_V2_SEARCH_AGE_KIND_ALLOWLIST,
    KIDS_V2_SEARCH_EAV_KEYS,
    KIDS_V2_SEARCH_EXCLUDE,
    KIDS_V2_SEARCH_MOUNTING_KIND_ALLOWLIST,
    KIDS_V2_SEARCH_SIZE_KIND_ALLOWLIST,
    KIDS_V2_KIND_KEY,
    build_kids_v2_core_fields,
    build_kids_v2_search_filters,
    kids_v2_all_search_kind_audit,
    kids_v2_assert_contracts,
    kids_v2_approved_condition_kinds,
    kids_v2_search_condition_kind_allowlist,
)

# Independent Package A evidence — must not only mirror production frozensets.
_INDEPENDENT_SIZE_YES = frozenset(
    {
        "Боди и распашонки",
        "Ползунки",
        "Футболки и рубашки",
        "Платья и юбки",
        "Кофты и свитера",
        "Верхняя одежда",
        "Другая детская одежда",
        "Школьная форма",
    }
)
_INDEPENDENT_SIZE_NO = frozenset(
    {
        "Носки и колготки",
        "Нижнее бельё и пижамы",
        "Головные уборы",
        "Подгузники",
        "Туфли",
        "Молочные смеси",
    }
)
_INDEPENDENT_AGE_YES = frozenset(
    {
        "Погремушки и прорезыватели",
        "Мягкие игрушки",
        "Куклы",
        "Машинки",
        "Конструкторы",
        "Детские настольные игры",
        "Развивающие коврики",
        "Радиоуправляемые игрушки",
        "Другие игрушки",
    }
)
_INDEPENDENT_AGE_NO = frozenset(
    {
        "Молочные смеси",
        "Каши для прикорма",
        "Пюре для прикорма",
        "Книги для малышей",
        "Подгузники",
    }
)
_INDEPENDENT_CONDITION_NO = frozenset(
    {
        "Носки и колготки",
        "Нижнее бельё и пижамы",
        "Подгузники",
        "Молочные смеси",
        "Влажные салфетки",
    }
)
_INDEPENDENT_MOUNTING_YES = frozenset(
    {
        "Автолюльки",
        "Автокресла группы 1",
        "Автокресла группы 2-3",
        "Автокресла группы 1-2-3",
        "Бустеры",
    }
)
_FORBIDDEN_SEARCH = frozenset(
    {
        "season",
        "gender",
        "brand",
        "kids_brand",
        "material",
        "color",
        "diaper_size",
        "shoe_size",
        "school_grade",
        "bed_size",
        "wheel_diameter",
        "occasion",
        "packaging",
        "price",
        "negotiable",
        "contact_methods",
    }
)


def _options_for(filters: list, key: str) -> list[dict]:
    for row in filters:
        if row[0] != key:
            continue
        cfg = row[4] or {}
        return list(cfg.get("options") or cfg.get("choices") or [])
    return []


def _visible_option_labels(options: list[dict], kind: str) -> list[str]:
    out: list[str] = []
    for o in options:
        fk = o.get("for_kinds")
        if fk and kind not in fk:
            continue
        out.append(str(o.get("label") or o.get("value") or ""))
    return out


def test_kids_package_a_contracts_still_locked() -> None:
    kids_v2_assert_contracts()
    assert len(KIDS_V2_CANONICAL_GOODS_SLUGS) == KIDS_V2_EXPECTED_L2_COUNT == 16
    assert KIDS_V2_EXPECTED_KIND_COUNT == 111


def test_kids_search_filters_cover_all_canonical_l2() -> None:
    filters = build_kids_v2_search_filters()
    assert set(filters) == KIDS_V2_CANONICAL_GOODS_SLUGS
    assert len(filters) == 16


def test_kids_search_eav_keys_are_short_allowlist() -> None:
    assert KIDS_V2_SEARCH_EAV_KEYS <= KIDS_V2_SEARCH_ALLOWLIST
    assert "price" not in KIDS_V2_SEARCH_EAV_KEYS
    assert "negotiable" not in KIDS_V2_SEARCH_EAV_KEYS
    assert "contact_methods" not in KIDS_V2_SEARCH_EAV_KEYS
    assert "region" not in KIDS_V2_SEARCH_EAV_KEYS


def test_kids_search_filters_no_removed_or_create_only_fields() -> None:
    for slug, rows in build_kids_v2_search_filters().items():
        keys = {r[0] for r in rows}
        assert keys <= KIDS_V2_SEARCH_EAV_KEYS, slug
        assert keys.isdisjoint(_FORBIDDEN_SEARCH), slug
        assert keys.isdisjoint(KIDS_V2_SEARCH_EXCLUDE), slug
        assert keys.isdisjoint(KIDS_V2_CREATE_FORBIDDEN), slug
        assert KIDS_V2_KIND_KEY in keys, slug
        assert "seller_type" in keys, slug


def test_kids_clothing_search_has_size_with_growth_catalog() -> None:
    rows = build_kids_v2_search_filters()["kids-detskaya-odezhda"]
    keys = {r[0] for r in rows}
    assert "size" in keys
    assert "condition" in keys
    opts = _options_for(rows, "size")
    visible = _visible_option_labels(opts, "Футболки и рубашки")
    assert len(visible) > 0
    assert "56" in visible and "158" in visible
    socks = _visible_option_labels(opts, "Носки и колготки")
    assert socks == []


def test_kids_hygiene_search_no_size_diapers_no_condition() -> None:
    rows = build_kids_v2_search_filters()["kids-podguzniki-i-gigiena"]
    keys = {r[0] for r in rows}
    assert "size" not in keys
    assert "diaper_size" not in keys
    # Condition only for durable «Детские горшки» (Package A allowlist).
    assert "condition" in keys
    cond_cfg = next(r[4] for r in rows if r[0] == "condition") or {}
    values = (cond_cfg.get("depends_on") or {}).get("values") or []
    assert "Подгузники" not in values
    assert "Влажные салфетки" not in values
    assert "Детские горшки" in values
    assert KIDS_V2_KIND_KEY in keys and "seller_type" in keys


def test_kids_food_search_no_age() -> None:
    rows = build_kids_v2_search_filters()["kids-detskoe-pitanie"]
    keys = {r[0] for r in rows}
    assert "age" not in keys
    assert keys == {KIDS_V2_KIND_KEY, "seller_type"}


def test_kids_toys_search_has_age() -> None:
    rows = build_kids_v2_search_filters()["kids-igrushki-igry-i-konstruktory"]
    keys = {r[0] for r in rows}
    assert "age" in keys
    opts = _options_for(rows, "age")
    visible = _visible_option_labels(opts, "Куклы")
    assert "До года" in visible
    formulaish = _visible_option_labels(opts, "Молочные смеси")
    assert formulaish == []


def test_kids_car_seat_search_has_mounting() -> None:
    rows = build_kids_v2_search_filters()["kids-avtokresla-i-perenoski"]
    keys = {r[0] for r in rows}
    assert "mounting" in keys
    opts = _options_for(rows, "mounting")
    labels = [str(o.get("label") or o.get("value")) for o in opts]
    assert "Isofix" in labels
    assert "Штатный ремень" in labels


def test_kids_shoes_search_no_shoe_size() -> None:
    rows = build_kids_v2_search_filters()["kids-detskaya-obuv"]
    keys = {r[0] for r in rows}
    assert "shoe_size" not in keys
    assert "size" not in keys


def test_kids_search_size_semantic_independent() -> None:
    assert _INDEPENDENT_SIZE_YES <= KIDS_V2_SEARCH_SIZE_KIND_ALLOWLIST
    assert _INDEPENDENT_SIZE_NO.isdisjoint(KIDS_V2_SEARCH_SIZE_KIND_ALLOWLIST)
    assert KIDS_V2_SEARCH_SIZE_KIND_ALLOWLIST == frozenset(
        KIDS_V2_APPROVED_SIZE_EXPECTATIONS
    )


def test_kids_search_age_semantic_independent() -> None:
    assert _INDEPENDENT_AGE_YES <= KIDS_V2_SEARCH_AGE_KIND_ALLOWLIST
    assert _INDEPENDENT_AGE_NO.isdisjoint(KIDS_V2_SEARCH_AGE_KIND_ALLOWLIST)
    assert "Молочные смеси" not in KIDS_V2_SEARCH_AGE_KIND_ALLOWLIST
    assert KIDS_V2_SEARCH_AGE_KIND_ALLOWLIST == frozenset(
        KIDS_V2_APPROVED_AGE_EXPECTATIONS
    )


def test_kids_search_condition_semantic_independent() -> None:
    allow = kids_v2_search_condition_kind_allowlist()
    assert _INDEPENDENT_CONDITION_NO <= KIDS_V2_LOCKED_NO_CONDITION_KINDS
    assert _INDEPENDENT_CONDITION_NO.isdisjoint(allow)
    assert allow == kids_v2_approved_condition_kinds()


def test_kids_search_mounting_allowlist() -> None:
    assert _INDEPENDENT_MOUNTING_YES == KIDS_V2_SEARCH_MOUNTING_KIND_ALLOWLIST
    assert KIDS_V2_SEARCH_MOUNTING_KIND_ALLOWLIST == KIDS_V2_MOUNTING_KINDS


def test_kids_search_inherits_create_semantic_options() -> None:
    cores = build_kids_v2_core_fields()
    filters = build_kids_v2_search_filters()
    for slug in ("kids-detskaya-odezhda", "kids-igrushki-igry-i-konstruktory"):
        core_by_key = {r[0]: r for r in cores[slug]}
        for row in filters[slug]:
            key = row[0]
            if key not in {"size", "age", "condition", "mounting"}:
                continue
            core = core_by_key[key]
            core_opts = core[5] or {}
            filt_cfg = row[4] or {}
            assert core_opts.get("depends_on") == filt_cfg.get("depends_on")


def test_kids_all_kind_search_audit_complete() -> None:
    rows = kids_v2_all_search_kind_audit()
    assert len(rows) == KIDS_V2_EXPECTED_KIND_COUNT
    by_kind = {r["kind"]: r for r in rows}
    assert by_kind["Футболки и рубашки"]["search_size"] == "YES"
    assert by_kind["Носки и колготки"]["search_size"] == "NO"
    assert by_kind["Носки и колготки"]["search_condition"] == "NO"
    assert by_kind["Подгузники"]["search_size"] == "NO"
    assert by_kind["Молочные смеси"]["search_age"] == "NO"
    assert by_kind["Куклы"]["search_age"] == "YES"
    assert by_kind["Автолюльки"]["search_mounting"] == "YES"
    for r in rows:
        assert r["search_seller"] == "YES"
        assert "kids_kind" in r["visible_search_keys"]


def test_kids_platform_coherence_retired_not_in_search_map() -> None:
    filters = build_kids_v2_search_filters()
    for slug in (
        "kids-tovary-dlya-shkoly",
        "kids-detskie-sady-i-obrazovanie",
        "kids-toys",
        "kids-clothes",
        "kids-strollers",
    ):
        assert slug not in filters
