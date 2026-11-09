"""Electronics V2 Package A — taxonomy + Create SoT."""
from __future__ import annotations

from app.seeds.electronics_sections_catalog import ELECTRONICS_SECTIONS
from app.seeds.electronics_v2 import (
    ELECTRONICS_V2_CANONICAL_LEAVES,
    ELECTRONICS_V2_CANONICAL_SLUGS,
    ELECTRONICS_V2_RETIRED_SLUGS,
    ELECTRONICS_V2_SECTION_TO_SLUG,
    build_electronics_v2_core_fields,
    electronics_v2_kind_count,
)


def test_electronics_v2_canonical_count_and_order() -> None:
    assert len(ELECTRONICS_V2_CANONICAL_LEAVES) == 19
    assert len(ELECTRONICS_V2_CANONICAL_SLUGS) == 19
    assert ELECTRONICS_V2_CANONICAL_LEAVES[0][0] == "electronics-smartfony-i-telefony"
    assert ELECTRONICS_V2_CANONICAL_LEAVES[3][0] == "electronics-televizory-i-proektory"
    assert ELECTRONICS_V2_CANONICAL_LEAVES[4][0] == "electronics-bytovaya-tehnika"
    assert ELECTRONICS_V2_CANONICAL_LEAVES[-1][0] == (
        "electronics-prochaya-tehnika-i-elektronika"
    )


def test_electronics_v2_legacy_retired() -> None:
    assert ELECTRONICS_V2_RETIRED_SLUGS == {
        "electronics-phones",
        "electronics-computers",
        "electronics-appliances",
        "electronics-tv",
    }
    assert ELECTRONICS_V2_RETIRED_SLUGS.isdisjoint(ELECTRONICS_V2_CANONICAL_SLUGS)


def test_electronics_v2_kinds_97_unique() -> None:
    assert electronics_v2_kind_count() == 97
    assert len(ELECTRONICS_SECTIONS) == 19


def test_electronics_v2_catalog_identity_maps_canonical_slugs() -> None:
    assert set(ELECTRONICS_V2_SECTION_TO_SLUG.values()) == ELECTRONICS_V2_CANONICAL_SLUGS
    for key, cat in ELECTRONICS_SECTIONS.items():
        assert cat["category_slug"] == ELECTRONICS_V2_SECTION_TO_SLUG[key]
        assert cat["category_slug"] in ELECTRONICS_V2_CANONICAL_SLUGS


def test_electronics_v2_core_fields_shape() -> None:
    cores = build_electronics_v2_core_fields()
    assert set(cores) == ELECTRONICS_V2_CANONICAL_SLUGS
    phones = cores["electronics-smartfony-i-telefony"]
    keys = [row[0] for row in phones]
    assert keys[0] == "electronics_kind"
    assert "electronics_brand" in keys
    assert "electronics_model" in keys
    assert "storage" in keys
    assert "ram" in keys
    assert "storage_drive" not in keys
    assert "price" in keys
    assert "negotiable" in keys
    assert "contact_methods" in keys

    kind = next(r for r in phones if r[0] == "electronics_kind")
    assert kind[1] == "Вид товара"
    assert kind[3] is True

    computers = cores["electronics-noutbuki-i-kompyutery"]
    ckeys = [row[0] for row in computers]
    assert "screen_size" in ckeys
    assert "diagonal" not in ckeys
    assert "storage" in ckeys

    parts = cores["electronics-komplektuyuschie-dlya-kompyuterov"]
    pkeys = [row[0] for row in parts]
    assert "capacity_gb" in pkeys
    assert "volume" not in pkeys

    appliances = cores["electronics-bytovaya-tehnika"]
    akeys = [row[0] for row in appliances]
    assert "volume_l" in akeys
    assert "load_capacity" in akeys

    climate = cores["electronics-klimaticheskaya-tehnika"]
    ckeys = [row[0] for row in climate]
    assert "device_type" in ckeys
    assert "power_rating" not in ckeys  # bare digits deferred

    accessories = cores["electronics-zapchasti-i-aksessuary"]
    brand = next(r for r in accessories if r[0] == "electronics_brand")
    assert brand[5]["depends_on"]["field"] == "electronics_kind"


def test_electronics_v2_brand_model_dependency() -> None:
    cores = build_electronics_v2_core_fields()
    phones = cores["electronics-smartfony-i-telefony"]
    brand = next(r for r in phones if r[0] == "electronics_brand")
    model = next(r for r in phones if r[0] == "electronics_model")
    assert brand[5]["depends_on"]["field"] == "electronics_kind"
    assert model[5]["depends_on"]["field"] == "electronics_brand"
    apple_models = [
        o for o in model[5]["choices"] if o.get("parent") == "Apple"
    ]
    assert any(o["label"] == "iPhone 15" for o in apple_models)
    for o in apple_models:
        assert "Смартфоны" in (o.get("for_kinds") or [])


def test_electronics_v2_office_distinct() -> None:
    cores = build_electronics_v2_core_fields()
    print_kinds = [
        o["label"]
        for o in next(
            r
            for r in cores["electronics-orgtehnika"]
            if r[0] == "electronics_kind"
        )[5]["choices"]
    ]
    office_kinds = [
        o["label"]
        for o in next(
            r
            for r in cores["electronics-tehnika-dlya-ofisa"]
            if r[0] == "electronics_kind"
        )[5]["choices"]
    ]
    assert "Принтеры" in print_kinds
    assert "ИБП" in office_kinds
    assert set(print_kinds).isdisjoint(office_kinds)


def test_electronics_v2_storage_stable_values() -> None:
    cores = build_electronics_v2_core_fields()
    phones = cores["electronics-smartfony-i-telefony"]
    storage = next(r for r in phones if r[0] == "storage")
    values = {o["value"] for o in storage[5]["choices"]}
    labels = {o["label"] for o in storage[5]["choices"]}
    assert "128gb" in values
    assert "128 ГБ" in labels
