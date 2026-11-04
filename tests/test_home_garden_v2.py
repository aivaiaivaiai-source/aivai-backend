"""Home & Garden V2 structure and semantic invariant tests."""
from __future__ import annotations

from app.seeds.home_garden_catalog_final import (
    FORBIDDEN_IN_HOME_GARDEN,
    HOME_GARDEN_L2_NAMES,
    HOME_GARDEN_L2_SLUGS,
    HOME_GARDEN_LEAF_SLUGS,
    HOME_GARDEN_NODES,
    L4_PARENT_SLUGS,
)
from app.seeds.home_garden_filters import HOME_GARDEN_FINAL_ALIAS_REMAP, fields_for_leaf
from app.seeds.home_garden_l3 import _HOME_GARDEN_L3


EXPECTED_L2 = [
    "Мебель",
    "Ковры",
    "Товары для сна",
    "Шторы, жалюзи и карнизы",
    "Посуда и кухонные принадлежности",
    "Бытовая химия и хозяйственные товары",
    "Товары для ванной комнаты",
    "Хранение и организация",
    "Декор и интерьер",
    "Зеркала",
    "Комнатные растения и цветы",
    "Искусственные цветы и растения",
    "Саженцы и рассада",
    "Семена и посадочный материал",
    "Горшки, кашпо и грунты",
    "Удобрения для растений",
    "Средства защиты растений",
    "Теплицы и парники",
    "Полив и орошение",
    "Садовый инвентарь",
    "Садовая техника",
    "Беседки, навесы и товары для дачи",
    "Мангалы, барбекю, тандыры и грили",
    "Бассейны и аксессуары",
    "Садовые качели и гамаки",
    "Товары для бани и сауны",
    "Камины, печи и аксессуары",
    "Ёмкости и резервуары",
    "Дрова и уголь",
    "Газовые баллоны",
    "Товары для праздников",
    "Прочее для дома и сада",
]


def test_v2_exactly_32_l2_order() -> None:
    assert len(HOME_GARDEN_L2_SLUGS) == 32
    assert HOME_GARDEN_L2_NAMES == EXPECTED_L2
    assert HOME_GARDEN_L2_NAMES[-1] == "Прочее для дома и сада"
    assert HOME_GARDEN_L2_NAMES[-5:-1] == [
        "Ёмкости и резервуары",
        "Дрова и уголь",
        "Газовые баллоны",
        "Товары для праздников",
    ]


def test_v2_new_l2_exist() -> None:
    assert "home-garden-emkosti-i-rezervuary" in HOME_GARDEN_L2_SLUGS
    assert "home-garden-drova-i-ugol" in HOME_GARDEN_L2_SLUGS
    assert "home-garden-gazovye-ballony" in HOME_GARDEN_L2_SLUGS
    assert "home-garden-tovary-dlya-prazdnikov" in HOME_GARDEN_L2_SLUGS
    assert "home-garden-gazovye-ballony" in HOME_GARDEN_LEAF_SLUGS


def test_v2_required_new_leaves() -> None:
    names = {n for _p, _s, n, _so, _d in HOME_GARDEN_NODES}
    for n in (
        "Сейфы",
        "Туалетные столики",
        "Ширмы и перегородки",
        "Комплектующие для мебели",
        "Шырдаки",
        "Жайнамазы",
        "Тошоки",
        "Мантышницы",
        "Скороварки",
        "Турки и кофейники",
        "Миски и кухонные тазы",
        "Подносы",
        "Термокружки",
        "Одноразовая посуда",
        "Веники и совки",
        "Полотенца",
        "Мешки и сумки для хранения",
        "Шкатулки",
        "Копилки",
        "Садовые фонтаны",
        "Садовые фигуры",
        "Ореховые деревья",
        "Рулонный и готовый газон",
        "Защитные сетки",
        "Затеняющие сетки",
        "Опрыскиватели",
        "Мотопомпы",
        "Компостеры",
        "Скарификаторы и аэраторы",
        "Летние души",
        "Уличные туалеты",
        "Запарники",
        "Банные шапки и текстиль",
        "Бочки",
        "Еврокубы",
        "Дрова",
        "Древесный уголь",
        "Ёлки",
        "Воздушные шары",
    ):
        assert n in names, n


def test_v2_kids_furniture_not_selectable() -> None:
    names = {n for _p, _s, n, _so, _d in HOME_GARDEN_NODES}
    assert "Детская мебель" not in names
    assert "Детские ковры" not in names
    assert "Детские гарнитуры" not in names
    furniture = _HOME_GARDEN_L3["home-garden-mebel-dlya-doma"]
    assert "Детская мебель" not in furniture


def test_v2_dacha_no_bench_lounger_dupes() -> None:
    dacha = _HOME_GARDEN_L3["home-garden-besedki-navesy-i-tovary-dlya-dachi"]
    assert "Шезлонги" not in dacha
    assert "Скамейки для дачи" not in dacha
    furniture_garden = _HOME_GARDEN_L3.get("home-garden-mebel-dlya-doma", [])
    # L4 under sadovaya
    l4 = [n for p, _s, n, _so, d in HOME_GARDEN_NODES if d == 4 and "sadovaya-mebel" in p]
    assert "Садовые скамейки" in l4
    assert "Лежаки и шезлонги" in l4


def test_v2_no_irrigation_tanks_leaf() -> None:
    poliv = _HOME_GARDEN_L3["home-garden-poliv-i-oroshenie"]
    assert "Ёмкости для полива" not in poliv
    assert all("ёмкост" not in n.lower() and "емкост" not in n.lower() for n in poliv)


def test_v2_charcoal_only_under_fuel() -> None:
    charcoal = [
        (p, s, n)
        for p, s, n, _so, _d in HOME_GARDEN_NODES
        if n == "Древесный уголь"
    ]
    assert len(charcoal) == 1
    assert charcoal[0][0] == "home-garden-drova-i-ugol"
    bbq = _HOME_GARDEN_L3["home-garden-mangaly-barbekyu-tandyr-grili"]
    assert "Древесный уголь" not in bbq


def test_v2_mattress_only_furniture() -> None:
    mattress = [n for _p, _s, n, _so, _d in HOME_GARDEN_NODES if "Матрас" in n]
    assert mattress == ["Матрасы"]
    sleep = _HOME_GARDEN_L3["home-garden-postelnoe-bele-i-pledy"]
    assert all("Матрас" not in n for n in sleep)


def test_v2_holiday_l4_parents() -> None:
    assert "home-garden-tovary-dlya-prazdnikov-novogodnie-tovary" in L4_PARENT_SLUGS
    assert "home-garden-tovary-dlya-prazdnikov-vozdushnye-shary-i-aksessuary" in L4_PARENT_SLUGS
    assert "home-garden-mebel-dlya-doma-detskaya-mebel" not in L4_PARENT_SLUGS


def test_v2_filter_schemas_representative() -> None:
    safe = {f[0] for f in fields_for_leaf("home-garden-mebel-dlya-doma-seyfy")}
    assert safe == {"safe_purpose", "lock_type", "condition"}

    barrel = {f[0] for f in fields_for_leaf("home-garden-emkosti-i-rezervuary-bochki")}
    assert barrel == {"capacity", "material", "condition"}

    coal = {f[0] for f in fields_for_leaf("home-garden-drova-i-ugol-ugol")}
    assert "condition" not in coal

    gas = {f[0] for f in fields_for_leaf("home-garden-gazovye-ballony")}
    assert "gas_cylinder_purpose" in gas
    assert "capacity" in gas
    assert "condition" in gas

    seeds = {f[0] for f in fields_for_leaf("home-garden-semena-i-posadochnyy-material-semena-ovoschey")}
    assert "condition" not in seeds

    toshok = {f[0] for f in fields_for_leaf("home-garden-postelnoe-bele-i-pledy-toshoki")}
    mattress = {f[0] for f in fields_for_leaf("home-garden-mebel-dlya-doma-matrasy")}
    assert "sleeping_place_size" not in toshok
    assert "sleeping_place_size" in mattress

    balloons = {
        f[0]
        for f in fields_for_leaf(
            "home-garden-tovary-dlya-prazdnikov-vozdushnye-shary-i-aksessuary-vozdushnye-shary"
        )
    }
    assert "capacity" not in balloons
    assert "safe_purpose" not in balloons
    assert "power_type" not in balloons


def test_v2_aliases_point_to_active_leaves() -> None:
    leaf_or_l2 = set(HOME_GARDEN_LEAF_SLUGS) | set(HOME_GARDEN_L2_SLUGS)
    nodes = {s for _p, s, *_ in HOME_GARDEN_NODES}
    for alias, target in HOME_GARDEN_FINAL_ALIAS_REMAP.items():
        assert target in nodes, f"{alias} → {target}"
        assert target in leaf_or_l2 or any(
            s.startswith(target + "-") for s in HOME_GARDEN_LEAF_SLUGS
        ) or target in HOME_GARDEN_LEAF_SLUGS


def test_v2_alias_samples() -> None:
    assert HOME_GARDEN_FINAL_ALIAS_REMAP["сейф"].endswith("-seyfy")
    assert HOME_GARDEN_FINAL_ALIAS_REMAP["бинбэг"].endswith("-kresla")
    assert HOME_GARDEN_FINAL_ALIAS_REMAP["шырдак"].endswith("-shyrdaki")
    assert HOME_GARDEN_FINAL_ALIAS_REMAP["тошок"].endswith("-toshoki")
    assert HOME_GARDEN_FINAL_ALIAS_REMAP["манты казан"].endswith("-mantyshnitsy")
    assert HOME_GARDEN_FINAL_ALIAS_REMAP["еврокуб"].endswith("-evrokuby")
    assert HOME_GARDEN_FINAL_ALIAS_REMAP["кара-кече"].endswith("-ugol")
    assert HOME_GARDEN_FINAL_ALIAS_REMAP["навоз"].endswith("-organicheskie-udobreniya")
    assert "gazovye-ballony" in HOME_GARDEN_FINAL_ALIAS_REMAP["газовый баллон"]


def test_v2_forbidden_absent() -> None:
    names = {n for _p, _s, n, _so, _d in HOME_GARDEN_NODES}
    assert FORBIDDEN_IN_HOME_GARDEN.isdisjoint(names)
