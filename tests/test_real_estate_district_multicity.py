"""Recovered multi-city DISTRICT_BY_CITY coverage + seed idempotency."""
from __future__ import annotations

from app.seeds.real_estate_v2 import DISTRICT_BY_CITY, RE_CORE_FIELDS_BY_SLUG

EXPECTED = {
    "Бишкек": 223,
    "Ош": 10,
    "Манас": 8,
    "Каракол": 5,
    "Нарын": 5,
    "Талас": 4,
    "Баткен": 4,
    "Токмок": 7,
    "Кант": 5,
    "Кара-Балта": 6,
    "Кемин": 4,
    "Орловка": 4,
    "Кайынды": 4,
    "Сокулук": 3,
    "Шопоков": 1,
    "Беловодское": 4,
    "Айдаркен": 13,
}


def test_district_by_city_recovered_counts():
    assert set(DISTRICT_BY_CITY) == set(EXPECTED)
    for city, n in EXPECTED.items():
        assert len(DISTRICT_BY_CITY[city]) == n, city
    assert "Каинды" not in DISTRICT_BY_CITY


def test_bishkek_osh_stables_preserved():
    assert DISTRICT_BY_CITY["Бишкек"][0] == {"value": "mkr_3", "label": "3 мкр."}
    osh_center = next(i for i in DISTRICT_BY_CITY["Ош"] if i["label"] == "Центр")
    assert osh_center["value"] == "d001_30619"


def test_shared_label_centres_do_not_collide():
    values = {
        city: next(i["value"] for i in items if i["label"] == "Центр")
        for city, items in DISTRICT_BY_CITY.items()
        if any(i["label"] == "Центр" for i in items)
    }
    assert len(values) == len(set(values.values()))
    assert values["Ош"] != values["Манас"]


def test_all_stables_globally_unique():
    seen: set[str] = set()
    for city, items in DISTRICT_BY_CITY.items():
        for it in items:
            assert it["value"] not in seen, (city, it)
            seen.add(it["value"])


def test_leaf_schemas_embed_full_by_city():
    for slug, fields in RE_CORE_FIELDS_BY_SLUG.items():
        district = next(f for f in fields if f[0] == "district")
        opts = district[5]
        assert opts["scoped_by"] == "city"
        assert set(opts["by_city"]) == set(EXPECTED)
