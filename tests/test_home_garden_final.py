"""Home & Garden FINAL catalog structure tests."""
from __future__ import annotations

from collections import Counter

from app.seeds.home_garden_catalog_final import (
    FORBIDDEN_IN_HOME_GARDEN,
    HOME_GARDEN_L2_NAMES,
    HOME_GARDEN_L2_SLUGS,
    HOME_GARDEN_LEAF_SLUGS,
    HOME_GARDEN_NODES,
    L4_PARENT_SLUGS,
)
from app.seeds.home_garden_filters import fields_for_leaf
from app.seeds.home_garden_l3 import HOME_GARDEN_L3_SKELETON, _HOME_GARDEN_L3
from app.seeds.mobile_category_skeleton import MOBILE_CATEGORY_SKELETON


def test_exactly_28_l2_order() -> None:
    # Superseded by V2 (32 L2). Keep name for historical import stability.
    assert len(HOME_GARDEN_L2_SLUGS) == 32
    assert HOME_GARDEN_L2_NAMES[-1] == "Прочее для дома и сада"
    assert len(HOME_GARDEN_L2_NAMES) == 32


def test_l3_approved_furniture() -> None:
    furniture = _HOME_GARDEN_L3["home-garden-mebel-dlya-doma"]
    assert "Диваны" in furniture
    assert "Матрасы" in furniture
    assert "Мебельные гарнитуры" in furniture
    assert "Комплекты мебели" in furniture
    assert "Кухонная мебель" not in furniture
    assert "Мебель для прихожей" not in furniture


def test_l4_only_approved_parents() -> None:
    l4 = [(p, s, n) for p, s, n, so, d in HOME_GARDEN_NODES if d == 4]
    parents = {p for p, *_ in l4}
    assert parents == set(L4_PARENT_SLUGS)
    kitchen = [
        n
        for p, s, n in l4
        if p == "home-garden-mebel-dlya-doma-mebelnye-garnitury" and "Кухонн" in n
    ]
    assert kitchen == ["Кухонные гарнитуры"]


def test_prochee_has_no_children() -> None:
    kids = [s for p, s, *_ in HOME_GARDEN_NODES if p == "home-garden-prochee-dlya-doma-i-sada"]
    assert kids == []
    assert "home-garden-prochee-dlya-doma-i-sada" in HOME_GARDEN_LEAF_SLUGS


def test_no_mattress_in_sleep() -> None:
    sleep = _HOME_GARDEN_L3["home-garden-postelnoe-bele-i-pledy"]
    assert all("Матрас" not in n for n in sleep)


def test_no_mirror_in_decor() -> None:
    decor = _HOME_GARDEN_L3["home-garden-dekor-i-interer"]
    assert all("Зеркал" not in n for n in decor)


def test_no_motoblock_in_garden_tech() -> None:
    tech = _HOME_GARDEN_L3["home-garden-sadovaya-tehnika"]
    assert all("Мотоблок" not in n for n in tech)


def test_no_kids_swings() -> None:
    swings = _HOME_GARDEN_L3["home-garden-sadovye-kacheli-i-gamaki"]
    assert all("Детск" not in n for n in swings)
    names = {n for _p, _s, n, _so, _d in HOME_GARDEN_NODES}
    assert "Детские качели" not in names


def test_bath_stove_single_place() -> None:
    banya = _HOME_GARDEN_L3["home-garden-tovary-dlya-bani-i-sauny"]
    assert all("Печ" not in n for n in banya)
    stoves = [
        n
        for _p, _s, n, _so, _d in HOME_GARDEN_NODES
        if n == "Печи для бани и сауны"
    ]
    assert len(stoves) == 1


def test_swings_not_in_dacha() -> None:
    dacha = _HOME_GARDEN_L3["home-garden-besedki-navesy-i-tovary-dlya-dachi"]
    assert all("качел" not in n.lower() and "гамак" not in n.lower() for n in dacha)
    assert "Шезлонги" not in dacha
    assert "Скамейки для дачи" not in dacha


def test_kitchen_set_one_place() -> None:
    hits = [
        (p, s, n)
        for p, s, n, so, d in HOME_GARDEN_NODES
        if "Кухонн" in n and "гарнитур" in n.lower()
    ]
    assert len(hits) == 1
    assert hits[0][1].endswith("kuhonnye-garnitury")


def test_unique_slugs() -> None:
    slugs = [s for _p, s, *_ in HOME_GARDEN_NODES]
    assert len(slugs) == len(set(slugs))


def test_skeleton_includes_final_l3_l4() -> None:
    sk_slugs = {row[1] for row in HOME_GARDEN_L3_SKELETON}
    target = {s for _p, s, _n, _so, d in HOME_GARDEN_NODES if d >= 3}
    assert sk_slugs == target
    mobile = {row[1] for row in MOBILE_CATEGORY_SKELETON}
    assert target.issubset(mobile)


_GOODS_BASE = {"seller_type", "price", "negotiable", "contact_methods"}


def test_dependent_filters_sofa_vs_mower_vs_seeds() -> None:
    sofa = {f[0] for f in fields_for_leaf("home-garden-mebel-dlya-doma-divany")}
    assert sofa == {"condition", "foldable"} | _GOODS_BASE
    assert "width_cm" not in sofa
    assert "material" not in sofa
    assert "power" not in sofa
    assert "city" not in sofa

    mower = {f[0] for f in fields_for_leaf("home-garden-sadovaya-tehnika-gazonokosilki")}
    assert mower == {
        "condition",
        "power_type",
        "self_propelled",
    } | _GOODS_BASE
    assert "brand" not in mower
    assert "power" not in mower
    assert "cutting_width" not in mower
    assert "foldable" not in mower

    trimmer = {
        f[0]
        for f in fields_for_leaf("home-garden-sadovaya-tehnika-trimmery-i-motokosy")
    }
    assert trimmer == {"condition", "power_type"} | _GOODS_BASE
    assert "brand" not in trimmer

    chainsaw = {
        f[0]
        for f in fields_for_leaf(
            "home-garden-sadovaya-tehnika-benzopily-i-elektropily"
        )
    }
    assert chainsaw == {"condition", "power_type"} | _GOODS_BASE
    assert "brand" not in chainsaw
    assert "bar_length" not in chainsaw

    seeds = {f[0] for f in fields_for_leaf("home-garden-semena-i-posadochnyy-material-semena-ovoschey")}
    assert seeds == _GOODS_BASE
    assert "plant_name" not in seeds
    assert "condition" not in seeds
    assert "power" not in seeds

    shovel = {f[0] for f in fields_for_leaf("home-garden-sadovyy-inventar-lopaty")}
    assert shovel == {"condition"} | _GOODS_BASE


def test_pool_vs_pump_filters() -> None:
    pool = {f[0] for f in fields_for_leaf("home-garden-basseyny-i-tovary-dlya-otdyha-karkasnye-basseyny")}
    pump = {
        f[0]
        for f in fields_for_leaf("home-garden-basseyny-i-tovary-dlya-otdyha-filtry-i-nasosy-dlya-basseynov")
    }
    assert pool == {"condition", "length_or_diameter"} | _GOODS_BASE
    assert "width_cm" not in pool
    assert "volume" not in pool
    assert pump == {"condition"} | _GOODS_BASE
    assert "throughput" not in pump
    assert "brand" not in pump


def test_forbidden_names_absent() -> None:
    names = {n for _p, _s, n, _so, _d in HOME_GARDEN_NODES}
    assert FORBIDDEN_IN_HOME_GARDEN.isdisjoint(names)


def test_no_duplicate_semantic_labels_under_same_parent() -> None:
    by_parent: dict[str, list[str]] = {}
    for p, _s, n, _so, _d in HOME_GARDEN_NODES:
        by_parent.setdefault(p, []).append(n)
    for p, names in by_parent.items():
        counts = Counter(names)
        dups = [n for n, c in counts.items() if c > 1]
        assert not dups, f"duplicate labels under {p}: {dups}"
