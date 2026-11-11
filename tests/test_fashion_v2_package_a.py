"""Fashion V2 Package A — positive Size allowlist + independent expectations."""
from __future__ import annotations

from app.models.category_enums import CategoryFieldType
from app.seeds.fashion_sections_catalog import FASHION_SECTIONS
from app.seeds.fashion_v2 import (
    FASHION_V2_APPROVED_CONDITION_EXPECTATIONS,
    FASHION_V2_APPROVED_SIZE_EXPECTATIONS,
    FASHION_V2_CANONICAL_LEAVES,
    FASHION_V2_CANONICAL_SLUGS,
    FASHION_V2_CREATE_FORBIDDEN,
    FASHION_V2_LOCKED_NO_CONDITION_KINDS,
    FASHION_V2_LOCKED_NO_SIZE_KINDS,
    FASHION_V2_NO_CONDITION_KINDS,
    FASHION_V2_NO_SIZE_KINDS,
    FASHION_V2_RETIRED_SLUGS,
    FASHION_V2_SEARCH_ALLOWLIST,
    FASHION_V2_SEARCH_CONDITION_KIND_ALLOWLIST,
    FASHION_V2_SEARCH_EXCLUDE,
    FASHION_V2_SEARCH_SIZE_KIND_ALLOWLIST,
    FASHION_V2_SECTION_TO_SLUG,
    FASHION_V2_SIZE_KEYS,
    SEMANTIC_SIZE_CLOTHING_M,
    SEMANTIC_SIZE_CLOTHING_W,
    SEMANTIC_SIZE_SHOE_M,
    SEMANTIC_SIZE_SHOE_W,
    _M_SHOE,
    _M_SIZE,
    _W_SHOE,
    _W_SIZE,
    build_fashion_v2_core_fields,
    fashion_v2_assert_condition_contract,
    fashion_v2_assert_semantic_partition,
    fashion_v2_condition_visible_for_kind,
    fashion_v2_kind_count,
    fashion_v2_kind_matrix,
    fashion_v2_no_size_kinds,
    fashion_v2_semantic_kind_map,
    fashion_v2_shared_field_matrix,
    fashion_v2_size_kind_map,
    visible_specials_for_kind,
)

# Independent product expectations used by tests (must not be derived from
# production allowlist iteration alone — duplicate the approved contract).
_INDEPENDENT_SIZE_YES: dict[str, str] = {
    "Платья": SEMANTIC_SIZE_CLOTHING_W,
    "Юбки": SEMANTIC_SIZE_CLOTHING_W,
    "Блузки и рубашки": SEMANTIC_SIZE_CLOTHING_W,
    "Футболки и топы": SEMANTIC_SIZE_CLOTHING_W,
    "Женские джинсы": SEMANTIC_SIZE_CLOTHING_W,
    "Женские брюки": SEMANTIC_SIZE_CLOTHING_W,
    "Кофты и кардиганы": SEMANTIC_SIZE_CLOTHING_W,
    "Женская верхняя одежда": SEMANTIC_SIZE_CLOTHING_W,
    "Женские костюмы": SEMANTIC_SIZE_CLOTHING_W,
    "Другая женская одежда": SEMANTIC_SIZE_CLOTHING_W,
    "Рубашки": SEMANTIC_SIZE_CLOTHING_M,
    "Футболки и поло": SEMANTIC_SIZE_CLOTHING_M,
    "Мужские джинсы": SEMANTIC_SIZE_CLOTHING_M,
    "Мужские брюки": SEMANTIC_SIZE_CLOTHING_M,
    "Пиджаки и костюмы": SEMANTIC_SIZE_CLOTHING_M,
    "Мужская верхняя одежда": SEMANTIC_SIZE_CLOTHING_M,
    "Свитеры и толстовки": SEMANTIC_SIZE_CLOTHING_M,
    "Шорты": SEMANTIC_SIZE_CLOTHING_M,
    "Другая мужская одежда": SEMANTIC_SIZE_CLOTHING_M,
    "Туфли": SEMANTIC_SIZE_SHOE_W,
    "Босоножки": SEMANTIC_SIZE_SHOE_W,
    "Балетки": SEMANTIC_SIZE_SHOE_W,
    "Сапоги": SEMANTIC_SIZE_SHOE_W,
    "Женские ботинки": SEMANTIC_SIZE_SHOE_W,
    "Женские кроссовки": SEMANTIC_SIZE_SHOE_W,
    "Женские кеды": SEMANTIC_SIZE_SHOE_W,
    "Лоферы": SEMANTIC_SIZE_SHOE_W,
    "Женские тапочки": SEMANTIC_SIZE_SHOE_W,
    "Другая женская обувь": SEMANTIC_SIZE_SHOE_W,
    "Мужские туфли": SEMANTIC_SIZE_SHOE_M,
    "Мужские кроссовки": SEMANTIC_SIZE_SHOE_M,
    "Мужские ботинки": SEMANTIC_SIZE_SHOE_M,
    "Мужские кеды": SEMANTIC_SIZE_SHOE_M,
    "Сандалии": SEMANTIC_SIZE_SHOE_M,
    "Мужские тапочки": SEMANTIC_SIZE_SHOE_M,
    "Другая мужская обувь": SEMANTIC_SIZE_SHOE_M,
}

_INDEPENDENT_CATALOG: dict[str, tuple[str, ...]] = {
    SEMANTIC_SIZE_CLOTHING_W: _W_SIZE,
    SEMANTIC_SIZE_CLOTHING_M: _M_SIZE,
    SEMANTIC_SIZE_SHOE_W: _W_SHOE,
    SEMANTIC_SIZE_SHOE_M: _M_SHOE,
}

# Kinds previous audit treated as SIZE that stricter policy moves to NO_SIZE
# (excluding underwear — reported separately).
_PREVIOUSLY_SIZED_NOW_NO_SIZE_EXAMPLES = frozenset(
    {
        "Платья для беременных",
        "Пижамы",
        "Абайи",
        "Форма для общепита",
        "Элечек",
        "Свадебные платья",
        "Костюмы жениха",
        "Спортивные костюмы",
        "Купальники",
        "Плавки",
        "Бутсы",
        "Кроссовки для бега",
        "Дождевики",
        "Трусы",
        "Комплекты белья",
        "Боди",
        "Другое бельё",
    }
)


def test_fashion_v2_canonical_count_and_order() -> None:
    assert len(FASHION_V2_CANONICAL_LEAVES) == 17
    assert len(FASHION_V2_CANONICAL_SLUGS) == 17


def test_fashion_v2_legacy_and_tkani_retired() -> None:
    assert "fashion-clothing" in FASHION_V2_RETIRED_SLUGS
    assert "fashion-tkani-i-furnitura" in FASHION_V2_RETIRED_SLUGS
    assert FASHION_V2_RETIRED_SLUGS.isdisjoint(FASHION_V2_CANONICAL_SLUGS)


def test_fashion_v2_kinds_114() -> None:
    assert fashion_v2_kind_count() == 114
    assert len(fashion_v2_kind_matrix()) == 114


def test_fashion_v2_core_no_forbidden_fields() -> None:
    cores = build_fashion_v2_core_fields()
    assert set(cores) == FASHION_V2_CANONICAL_SLUGS
    for slug, fields in cores.items():
        keys = [r[0] for r in fields]
        for forbidden in FASHION_V2_CREATE_FORBIDDEN:
            assert forbidden not in keys, (slug, forbidden)
        assert keys[0] == "fashion_kind"
        assert "underwear_size" not in keys
        assert "suit_size" not in keys
        assert "clothing_size" not in keys
        assert "shoe_size" not in keys


def test_fashion_v2_season_gender_absent() -> None:
    cores = build_fashion_v2_core_fields()
    for slug, fields in cores.items():
        keys = {r[0] for r in fields}
        assert "season" not in keys
        assert "gender" not in keys


def test_fashion_v2_positive_allowlist_counts() -> None:
    fashion_v2_assert_semantic_partition()
    sized = fashion_v2_size_kind_map()
    no_size = fashion_v2_no_size_kinds()
    assert len(sized) == 36
    assert len(no_size) == 78
    assert len(sized) + len(no_size) == 114
    assert frozenset(no_size) == FASHION_V2_NO_SIZE_KINDS


def test_fashion_v2_independent_expectations_match_production() -> None:
    """Anti self-referential: production must match independent approved table."""
    assert _INDEPENDENT_SIZE_YES == FASHION_V2_APPROVED_SIZE_EXPECTATIONS
    sized = fashion_v2_semantic_kind_map()
    assert set(sized) == set(_INDEPENDENT_SIZE_YES)
    for kind, expected_group in _INDEPENDENT_SIZE_YES.items():
        key, group, options = sized[kind]
        assert key == "size"
        assert group == expected_group
        assert options == _INDEPENDENT_CATALOG[expected_group]


def test_fashion_v2_114_kind_special_invariant() -> None:
    empty_pickers = 0
    multi_special = 0
    with_size = 0
    without_size = 0
    for _section_key, cat in FASHION_SECTIONS.items():
        slug = str(cat["category_slug"])
        for role in cat["roles"]:
            kind = str(role["label"])
            specials = visible_specials_for_kind(slug, kind)
            if len(specials) > 1:
                multi_special += 1
            if not specials:
                without_size += 1
                assert kind not in _INDEPENDENT_SIZE_YES, kind
            else:
                with_size += 1
                assert kind in _INDEPENDENT_SIZE_YES, kind
                for key, n in specials:
                    assert key in FASHION_V2_SIZE_KEYS, (kind, key)
                    if n <= 0:
                        empty_pickers += 1
                    expected = _INDEPENDENT_CATALOG[_INDEPENDENT_SIZE_YES[kind]]
                    assert n == len(expected), (kind, n, len(expected))
    assert empty_pickers == 0
    assert multi_special == 0
    assert with_size == 36
    assert without_size == 78


def test_fashion_v2_entire_underwear_no_size() -> None:
    for kind in FASHION_V2_LOCKED_NO_SIZE_KINDS:
        if kind == "Бельё для кормления":
            slug = "fashion-odezhda-dlya-beremennyh-kormyaschih"
        else:
            slug = "fashion-nizhnee-bele"
        assert visible_specials_for_kind(slug, kind) == [], (slug, kind)
    cores = build_fashion_v2_core_fields()
    assert "underwear_size" not in {r[0] for r in cores["fashion-nizhnee-bele"]}
    for kind in (
        "Трусы",
        "Комплекты белья",
        "Боди",
        "Другое бельё",
        "Носки",
        "Колготки",
        "Бюстгальтеры",
    ):
        assert kind in FASHION_V2_LOCKED_NO_SIZE_KINDS
        assert kind not in fashion_v2_size_kind_map()


def test_fashion_v2_ordinary_clothing_and_shoes_catalogs() -> None:
    cores = build_fashion_v2_core_fields()
    women = next(r for r in cores["fashion-zhenskaya-odezhda"] if r[0] == "size")
    men = next(r for r in cores["fashion-muzhskaya-odezhda"] if r[0] == "size")
    w_shoe = next(r for r in cores["fashion-zhenskaya-obuv"] if r[0] == "size")
    m_shoe = next(r for r in cores["fashion-muzhskaya-obuv"] if r[0] == "size")
    assert [c["value"] for c in women[5]["choices"]] == list(_W_SIZE)
    assert [c["value"] for c in men[5]["choices"]] == list(_M_SIZE)
    assert [c["value"] for c in w_shoe[5]["choices"]] == list(_W_SHOE)
    assert [c["value"] for c in m_shoe[5]["choices"]] == list(_M_SHOE)
    assert women[2] == CategoryFieldType.multi_select
    assert women[5]["semantic_size_group"] == SEMANTIC_SIZE_CLOTHING_W


def test_fashion_v2_ambiguous_sections_have_no_size_field() -> None:
    cores = build_fashion_v2_core_fields()
    for slug in (
        "fashion-odezhda-dlya-beremennyh-kormyaschih",
        "fashion-nizhnee-bele",
        "fashion-domashnyaya-odezhda",
        "fashion-musulmanskaya-odezhda-aksessuary",
        "fashion-spetsodezhda-i-uniforma",
        "fashion-natsionalnaya-odezhda",
        "fashion-svadebnaya-i-vechernyaya-odezhda",
        "fashion-sportivnaya-odezhda-i-obuv",
        "fashion-prochee",
        "fashion-sumki-i-chemodany",
        "fashion-ukrasheniya-i-bizhuteriya",
        "fashion-chasy",
        "fashion-aksessuary",
    ):
        keys = {r[0] for r in cores[slug]}
        assert keys.isdisjoint(FASHION_V2_SIZE_KEYS), slug


def test_fashion_v2_proactive_demotions_documented() -> None:
    sized = set(fashion_v2_size_kind_map())
    for kind in _PREVIOUSLY_SIZED_NOW_NO_SIZE_EXAMPLES:
        assert kind not in sized, kind


def test_fashion_v2_search_policy_positive_allowlist() -> None:
    assert "fashion_kind" in FASHION_V2_SEARCH_ALLOWLIST
    assert "size" in FASHION_V2_SEARCH_ALLOWLIST
    assert "underwear_size" not in FASHION_V2_SEARCH_ALLOWLIST
    assert FASHION_V2_SEARCH_SIZE_KIND_ALLOWLIST == frozenset(
        FASHION_V2_APPROVED_SIZE_EXPECTATIONS
    )
    assert FASHION_V2_SEARCH_SIZE_KIND_ALLOWLIST.isdisjoint(
        FASHION_V2_LOCKED_NO_SIZE_KINDS
    )
    assert "Трусы" not in FASHION_V2_SEARCH_SIZE_KIND_ALLOWLIST
    assert "Платья" in FASHION_V2_SEARCH_SIZE_KIND_ALLOWLIST
    assert "underwear_size" in FASHION_V2_SEARCH_EXCLUDE


def test_fashion_v2_catalog_maps_canonical() -> None:
    assert set(FASHION_V2_SECTION_TO_SLUG.values()) == FASHION_V2_CANONICAL_SLUGS


# Independent Condition expectations (must not only mirror production frozenset).
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

_INDEPENDENT_CONDITION_YES_SAMPLES = frozenset(
    {
        "Платья",
        "Рубашки",
        "Туфли",
        "Мужские туфли",
        "Женские сумки",
        "Кольца",
        "Мужские наручные часы",
        "Ремни",
        "Пижамы",
        "Свадебные платья",
        "Спортивные костюмы",
        "Форма охраны",
        "Абайи",
        "Элечек",
    }
)


def test_fashion_v2_condition_contract_partition() -> None:
    fashion_v2_assert_condition_contract()
    assert len(FASHION_V2_APPROVED_CONDITION_EXPECTATIONS) == 104
    assert len(FASHION_V2_NO_CONDITION_KINDS) == 10
    assert FASHION_V2_LOCKED_NO_CONDITION_KINDS == _INDEPENDENT_CONDITION_NO
    assert FASHION_V2_NO_CONDITION_KINDS == _INDEPENDENT_CONDITION_NO


def test_fashion_v2_underwear_and_intimate_no_condition() -> None:
    cores = build_fashion_v2_core_fields()
    assert "condition" not in {r[0] for r in cores["fashion-nizhnee-bele"]}
    for kind in (
        "Бюстгальтеры",
        "Трусы",
        "Комплекты белья",
        "Носки",
        "Колготки",
        "Боди",
        "Другое бельё",
    ):
        assert not fashion_v2_condition_visible_for_kind(kind)
    assert not fashion_v2_condition_visible_for_kind("Бельё для кормления")
    assert not fashion_v2_condition_visible_for_kind("Купальники")
    assert not fashion_v2_condition_visible_for_kind("Плавки")
    # Maternity / sport still have condition field, scoped away from NO kinds.
    mat = next(
        r
        for r in cores["fashion-odezhda-dlya-beremennyh-kormyaschih"]
        if r[0] == "condition"
    )
    assert "Бельё для кормления" not in mat[5]["depends_on"]["values"]
    sport = next(
        r for r in cores["fashion-sportivnaya-odezhda-i-obuv"] if r[0] == "condition"
    )
    assert "Купальники" not in sport[5]["depends_on"]["values"]
    assert "Плавки" not in sport[5]["depends_on"]["values"]


def test_fashion_v2_condition_yes_samples_independent() -> None:
    for kind in _INDEPENDENT_CONDITION_YES_SAMPLES:
        assert fashion_v2_condition_visible_for_kind(kind), kind
        assert kind in FASHION_V2_APPROVED_CONDITION_EXPECTATIONS
    cores = build_fashion_v2_core_fields()
    women = next(r for r in cores["fashion-zhenskaya-odezhda"] if r[0] == "condition")
    assert [c["value"] for c in women[5]["choices"]] == ["Новое", "Б/у"]
    assert women[3] is True
    bags = next(r for r in cores["fashion-sumki-i-chemodany"] if r[0] == "condition")
    assert bags[5].get("depends_on") in (None, {})


def test_fashion_v2_size_and_condition_combination() -> None:
    assert fashion_v2_condition_visible_for_kind("Платья")
    assert "Платья" in fashion_v2_size_kind_map()
    assert not fashion_v2_condition_visible_for_kind("Трусы")
    assert "Трусы" not in fashion_v2_size_kind_map()
    assert fashion_v2_condition_visible_for_kind("Спортивные костюмы")
    assert "Спортивные костюмы" not in fashion_v2_size_kind_map()
    assert not fashion_v2_condition_visible_for_kind("Купальники")


def test_fashion_v2_seller_price_negotiable_contacts_universal() -> None:
    cores = build_fashion_v2_core_fields()
    for slug, fields in cores.items():
        keys = {r[0] for r in fields}
        assert "seller_type" in keys, slug
        assert "price" in keys, slug
        assert "negotiable" in keys, slug
        assert "contact_methods" in keys, slug
        assert "fashion_kind" in keys, slug


def test_fashion_v2_search_condition_allowlist() -> None:
    assert FASHION_V2_SEARCH_CONDITION_KIND_ALLOWLIST == frozenset(
        FASHION_V2_APPROVED_CONDITION_EXPECTATIONS
    )
    assert "Трусы" not in FASHION_V2_SEARCH_CONDITION_KIND_ALLOWLIST
    assert "Платья" in FASHION_V2_SEARCH_CONDITION_KIND_ALLOWLIST
    assert "condition" in FASHION_V2_SEARCH_ALLOWLIST


def test_fashion_v2_shared_field_matrix_114() -> None:
    rows = fashion_v2_shared_field_matrix()
    assert len(rows) == 114
    underwear = [r for r in rows if r[1] == "Трусы"][0]
    assert underwear[2] == "NO"  # size
    assert underwear[3] == "NO"  # condition
