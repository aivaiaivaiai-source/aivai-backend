"""Commercial optional direction-dependent fields. No capacity_count."""
from app.seeds.real_estate_v2 import (
    COMMERCIAL_DIRECTION_ITEMS,
    COMMERCIAL_SLUG,
    RE_CORE_FIELDS_BY_SLUG,
    RE_SEARCH_FILTERS_BY_SLUG,
)

DEPENDENT = {
    "floor_position",
    "entrance_type",
    "property_condition",
    "ceiling_height",
    "truck_access",
}


def _fields():
    return {row[0]: row for row in RE_CORE_FIELDS_BY_SLUG[COMMERCIAL_SLUG]}


def _directions(key: str) -> list[str]:
    options = _fields()[key][5]
    return list(options["depends_on"]["values"])


def test_five_optional_dependent_fields():
    fields = _fields()
    assert "capacity_count" not in fields
    for key in DEPENDENT:
        row = fields[key]
        assert row[3] is False
        assert row[5]["depends_on"]["field"] == "commercial_direction"


def test_direction_sets_and_max_three():
    floor = set(_directions("floor_position"))
    entrance = set(_directions("entrance_type"))
    condition = set(_directions("property_condition"))
    ceiling = set(_directions("ceiling_height"))
    truck = set(_directions("truck_access"))
    assert "base_territory" not in floor
    assert "base_territory" not in entrance
    assert "base_territory" not in condition
    assert "base_territory" not in ceiling
    assert ceiling == {
        "warehouse_logistics",
        "production_facility",
        "auto_business_space",
        "sports_leisure",
    }
    assert truck == {
        "warehouse_logistics",
        "production_facility",
        "auto_business_space",
        "base_territory",
    }
    all_dirs = {item["value"] for item in COMMERCIAL_DIRECTION_ITEMS}
    assert len(all_dirs) == 19
    for direction in all_dirs:
        visible = sum(
            direction in group
            for group in (floor, entrance, condition, ceiling, truck)
        )
        assert visible <= 3
    assert {"floor_position", "entrance_type", "property_condition"} == {
        key
        for key, group in (
            ("floor_position", floor),
            ("entrance_type", entrance),
            ("property_condition", condition),
            ("ceiling_height", ceiling),
            ("truck_access", truck),
        )
        if "mall_boutique" in group
    }
    assert {
        key
        for key, group in (
            ("floor_position", floor),
            ("entrance_type", entrance),
            ("property_condition", condition),
            ("ceiling_height", ceiling),
            ("truck_access", truck),
        )
        if "warehouse_logistics" in group
    } == {"property_condition", "ceiling_height", "truck_access"}
    assert [key for key, group in (
        ("floor_position", floor),
        ("entrance_type", entrance),
        ("property_condition", condition),
        ("ceiling_height", ceiling),
        ("truck_access", truck),
    ) if "base_territory" in group] == ["truck_access"]


def test_labels_and_stables():
    fields = _fields()
    assert fields["floor_position"][1] == "Расположение"
    assert fields["entrance_type"][1] == "Вход"
    assert fields["property_condition"][1] == "Состояние помещения"
    assert fields["ceiling_height"][1] == "Высота потолков"
    assert fields["ceiling_height"][2].value == "decimal"
    assert fields["ceiling_height"][5]["unit"] == "m"
    assert fields["truck_access"][1] == "Подъезд транспорта"
    condition = {item["value"]: item["label"] for item in fields["property_condition"][5]["choices"]}
    assert condition["ready"] == "Готово к использованию"
    assert "area" in fields
    assert fields["area"][2].value == "decimal"


def test_search_filters_skip_ceiling():
    keys = [row[0] for row in RE_SEARCH_FILTERS_BY_SLUG[COMMERCIAL_SLUG]]
    assert "ceiling_height" not in keys
    for key in ("floor_position", "entrance_type", "property_condition", "truck_access"):
        assert key in keys
    area = next(row for row in RE_SEARCH_FILTERS_BY_SLUG[COMMERCIAL_SLUG] if row[0] == "area")
    assert area[2].value == "range"
