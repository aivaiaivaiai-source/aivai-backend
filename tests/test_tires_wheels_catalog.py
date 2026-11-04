"""Tires catalog: per-direction sizes and accessories, no brand/model."""
from app.seeds.tires_wheels_catalog import (
    TIRES_DIRECTIONS,
    build_tires_catalog,
    tires_directions,
)


def test_directions_skip_watercraft() -> None:
    values = [value for value, _label in TIRES_DIRECTIONS]
    assert "passenger_cars" in values
    assert "cargo" in values
    assert "watercraft" not in values
    assert tires_directions()[0]["label"] == "Легковые автомобили"


def test_each_direction_has_own_sizes_and_accessories() -> None:
    passenger = build_tires_catalog("passenger_cars")
    cargo = build_tires_catalog("cargo")
    farm = build_tires_catalog("farm_machinery")
    bike = build_tires_catalog("bicycles")
    assert passenger is not None and cargo is not None
    assert farm is not None and bike is not None
    assert build_tires_catalog("watercraft") is None

    def kind(cat: dict, value: str) -> dict:
        return next(item for item in cat["kinds"] if item["value"] == value)

    passenger_tires = kind(passenger, "tires")
    cargo_tires = kind(cargo, "tires")
    assert "205" in [s["label"] for s in passenger_tires["widths"]]
    assert "R16" in [s["label"] for s in passenger_tires["diameters"]]
    assert "Michelin" in [s["label"] for s in passenger_tires["brands"]]
    assert "315" in [s["label"] for s in cargo_tires["widths"]]
    assert "R22.5" in [s["label"] for s in cargo_tires["diameters"]]
    assert "Schwalbe" in [s["label"] for s in kind(bike, "tires")["brands"]]
    assert "Schwalbe" not in [s["label"] for s in passenger_tires["brands"]]
    assert [s["label"] for s in passenger_tires["brands"]] != [
        s["label"] for s in cargo_tires["brands"]
    ]

    passenger_acc = [s["label"] for s in kind(passenger, "accessories")["accessory_types"]]
    farm_acc = [s["label"] for s in kind(farm, "accessories")["accessory_types"]]
    bike_acc = [s["label"] for s in kind(bike, "accessories")["accessory_types"]]
    assert "Колпаки" in passenger_acc
    assert "Грузы колёс" in farm_acc
    assert "Бескамерный набор" in bike_acc
    assert passenger_acc != farm_acc

    labels = [item["label"] for item in passenger["kinds"]]
    assert labels == [
        "Шины",
        "Диски",
        "Колёса в сборе",
        "Аксессуары для шин и дисков",
    ]
