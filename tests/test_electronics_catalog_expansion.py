"""Electronics V2 catalog expansion — market depth + scoping."""
from __future__ import annotations

from collections import Counter

from app.seeds.electronics_sections_catalog import ELECTRONICS_SECTIONS
from app.seeds.electronics_v2 import build_electronics_v2_core_fields


def _brand_opts(section: str):
    return next(
        g["options"]
        for g in ELECTRONICS_SECTIONS[section]["filters"]
        if g["label"] == "Марка"
    )


def _model_opts(section: str):
    return next(
        g["options"]
        for g in ELECTRONICS_SECTIONS[section]["filters"]
        if g["label"] == "Модель"
    )


def test_catalog_counts_expanded() -> None:
    brands = sum(
        len(g["options"])
        for s in ELECTRONICS_SECTIONS.values()
        for g in s["filters"]
        if g["label"] == "Марка"
    )
    models = sum(
        len(g["options"])
        for s in ELECTRONICS_SECTIONS.values()
        for g in s["filters"]
        if g["label"] == "Модель"
    )
    assert brands >= 160
    assert models >= 650


def test_no_duplicate_model_options_per_section() -> None:
    for key, sec in ELECTRONICS_SECTIONS.items():
        models = _model_opts(key) if any(g["label"] == "Модель" for g in sec["filters"]) else []
        c = Counter((o.get("parent"), o["label"]) for o in models)
        dups = [k for k, v in c.items() if v > 1]
        assert not dups, (key, dups)


def test_iphone_catalog_current_and_used() -> None:
    models = {
        o["label"]
        for o in _model_opts("phones")
        if o.get("parent") == "Apple"
    }
    for required in (
        "iPhone 17",
        "iPhone 17 Pro",
        "iPhone 17 Pro Max",
        "iPhone 17e",
        "iPhone Air",
        "iPhone 16",
        "iPhone 16 Plus",
        "iPhone 16 Pro",
        "iPhone 16 Pro Max",
        "iPhone 16e",
        "iPhone 15 Pro Max",
        "iPhone 14 Pro",
        "iPhone 13 mini",
        "iPhone 12",
        "iPhone 11",
        "iPhone XR",
        "iPhone SE (3rd generation)",
        "iPhone SE",
        "iPhone 8",
    ):
        assert required in models
    # no config-as-model
    assert not any("256GB" in m or "256 ГБ" in m for m in models)
    assert not any("Titanium" in m for m in models)


def test_samsung_phone_families() -> None:
    models = {
        o["label"]
        for o in _model_opts("phones")
        if o.get("parent") == "Samsung"
    }
    for required in (
        "Galaxy S25 Ultra",
        "Galaxy S24",
        "Galaxy S23",
        "Galaxy Z Fold6",
        "Galaxy Z Flip6",
        "Galaxy A55",
        "Galaxy A15",
        "Galaxy M35",
    ):
        assert required in models


def test_xiaomi_architecture_single_brand() -> None:
    brands = {o["label"] for o in _brand_opts("phones")}
    assert "Xiaomi" in brands
    assert "Redmi" not in brands
    assert "POCO" not in brands
    assert "Poco" not in brands
    models = {
        o["label"]
        for o in _model_opts("phones")
        if o.get("parent") == "Xiaomi"
    }
    assert "Redmi Note 14" in models
    assert "POCO X6" in models
    assert "Xiaomi 14" in models


def test_phone_model_scoping_not_on_tablet() -> None:
    phone_models = {o["label"] for o in _model_opts("phones") if o.get("parent") == "Apple"}
    tablet_models = {o["label"] for o in _model_opts("tablets") if o.get("parent") == "Apple"}
    assert "iPhone 17 Pro Max" in phone_models
    assert "iPhone 17 Pro Max" not in tablet_models
    assert any("iPad" in m for m in tablet_models)


def test_apple_models_not_under_samsung() -> None:
    samsung = [o for o in _model_opts("phones") if o.get("parent") == "Samsung"]
    assert not any("iPhone" in o["label"] for o in samsung)


def test_cores_reflect_expanded_catalog() -> None:
    cores = build_electronics_v2_core_fields()
    phones = cores["electronics-smartfony-i-telefony"]
    model = next(r for r in phones if r[0] == "electronics_model")
    apple = [o for o in model[5]["choices"] if o.get("parent") == "Apple"]
    labels = {o["label"] for o in apple}
    assert "iPhone 17 Pro Max" in labels
    assert "iPhone 16 Pro" in labels
    laptops = cores["electronics-noutbuki-i-kompyutery"]
    lm = next(r for r in laptops if r[0] == "electronics_model")
    apple_nb = {
        o["label"]
        for o in lm[5]["choices"]
        if o.get("parent") == "Apple" and "Ноутбуки" in (o.get("for_kinds") or [])
    }
    assert "MacBook Air 13-inch (M4)" in apple_nb
    assert "MacBook Pro 14-inch (M4)" in apple_nb


def test_appliances_representative() -> None:
    models = _model_opts("appliances")
    labels = {(o.get("parent"), o["label"]) for o in models}
    assert ("Samsung", "RB37") in labels or ("Samsung", "RB") in labels
    assert ("Xiaomi", "Robot Vacuum") in labels
    assert ("LG", "F2V5") in labels or ("LG", "F2") in labels


def test_games_have_no_title_catalog() -> None:
    """Игры: no brand→model game-title inventory."""
    consoles = ELECTRONICS_SECTIONS["consoles"]
    models = next(g["options"] for g in consoles["filters"] if g["label"] == "Модель")
    for o in models:
        kinds = o.get("for_kinds") or []
        assert "Игры" not in kinds


def test_seed_shape_idempotent_double_build() -> None:
    a = build_electronics_v2_core_fields()
    b = build_electronics_v2_core_fields()
    for slug in a:
        ma = next(r for r in a[slug] if r[0] == "electronics_model")
        mb = next(r for r in b[slug] if r[0] == "electronics_model")
        assert [o["label"] for o in ma[5]["choices"]] == [
            o["label"] for o in mb[5]["choices"]
        ]
