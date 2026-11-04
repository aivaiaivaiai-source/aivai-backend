"""Accessories catalog: each direction has its own types and brands."""
from app.seeds.accessories_tuning_catalog import (
    ACCESSORIES_DIRECTIONS,
    build_accessories_catalog,
)


def _labels(catalog: dict, key: str) -> list[str]:
    return [item["label"] for item in catalog[key]]


def test_directions_include_watercraft() -> None:
    values = [value for value, _label in ACCESSORIES_DIRECTIONS]
    assert values[0] == "passenger_cars"
    assert "watercraft" in values
    assert "bicycles" in values
    assert len(values) == 10


def test_each_direction_has_own_accessories() -> None:
    passenger = build_accessories_catalog("passenger_cars")
    moto = build_accessories_catalog("moto")
    bike = build_accessories_catalog("bicycles")
    water = build_accessories_catalog("watercraft")
    assert passenger is not None and moto is not None
    assert bike is not None and water is not None
    assert build_accessories_catalog("unknown") is None

    passenger_types = _labels(passenger, "types")
    assert "Автозвук и мультимедиа" in passenger_types
    assert "Шлемы" not in passenger_types
    assert "Спасательные жилеты" not in passenger_types
    assert "Шлемы" in _labels(moto, "types")
    assert "Велозамки" in _labels(bike, "types")
    assert "Спасательные жилеты" in _labels(water, "types")
    assert _labels(passenger, "types") != _labels(moto, "types")
    assert "Shoei" in _labels(moto, "brands")
    assert "Shoei" not in _labels(passenger, "brands")
    assert "Giro" in _labels(bike, "brands")
    assert "Giro" not in _labels(passenger, "brands")
