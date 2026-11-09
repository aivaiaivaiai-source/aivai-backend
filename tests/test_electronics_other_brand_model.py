"""Electronics open-catalog Brand/Model Other fallbacks."""
from __future__ import annotations

from collections import Counter

from app.seeds.electronics_sections_catalog import (
    ELECTRONICS_SECTIONS,
    OTHER_BRAND_LABEL,
    OTHER_BRAND_VALUE,
    OTHER_MODEL_LABEL,
    OTHER_MODEL_VALUE,
)
from app.seeds.electronics_v2 import build_electronics_v2_core_fields
from app.services.listing_field_value_service import ListingFieldValueService


def _choices(row) -> list[dict]:
    return list((row[5] or {}).get("choices") or [])


def test_other_brand_trailing_every_section_with_brands() -> None:
    cores = build_electronics_v2_core_fields()
    for slug, rows in cores.items():
        brand = next((r for r in rows if r[0] == "electronics_brand"), None)
        if brand is None:
            continue
        choices = _choices(brand)
        assert choices, slug
        assert choices[-1]["value"] == OTHER_BRAND_VALUE, slug
        assert choices[-1]["label"] == OTHER_BRAND_LABEL, slug
        assert sum(1 for c in choices if c["value"] == OTHER_BRAND_VALUE) == 1


def test_other_model_trailing_per_brand() -> None:
    cores = build_electronics_v2_core_fields()
    for slug, rows in cores.items():
        model = next((r for r in rows if r[0] == "electronics_model"), None)
        brand = next((r for r in rows if r[0] == "electronics_brand"), None)
        if model is None or brand is None:
            continue
        choices = _choices(model)
        parents = sorted(
            {
                str(c["parent"])
                for c in choices
                if c.get("parent") and c["parent"] != OTHER_BRAND_VALUE
            }
        )
        for parent in parents:
            sub = [c for c in choices if c.get("parent") == parent]
            assert sub[-1]["value"] == OTHER_MODEL_VALUE, (slug, parent)
            assert sub[-1]["label"] == OTHER_MODEL_LABEL, (slug, parent)
            assert (
                sum(1 for c in sub if c["value"] == OTHER_MODEL_VALUE) == 1
            ), (slug, parent)
        # other_brand must not unlock Model picker
        dep_values = set((model[5] or {}).get("depends_on", {}).get("values") or [])
        assert OTHER_BRAND_VALUE not in dep_values, slug


def test_no_duplicate_scope_parent_value() -> None:
    for key, sec in ELECTRONICS_SECTIONS.items():
        for group in sec["filters"]:
            if group["label"] not in {"Марка", "Модель"}:
                continue
            c = Counter(
                (o.get("parent"), o.get("value") or o["label"])
                for o in group["options"]
            )
            dups = [k for k, v in c.items() if v > 1]
            assert not dups, (key, group["label"], dups)


def test_closed_enums_unchanged() -> None:
    cores = build_electronics_v2_core_fields()
    phones = cores["electronics-smartfony-i-telefony"]
    seller = next(r for r in phones if r[0] == "seller_type")
    condition = next(r for r in phones if r[0] == "condition")
    seller_vals = {c["value"] for c in _choices(seller)}
    cond_vals = {c["value"] for c in _choices(condition)}
    assert seller_vals == {"Частное лицо", "Магазин", "Другой"}
    assert cond_vals == {"Новое", "Б/у"}
    assert OTHER_BRAND_VALUE not in seller_vals
    assert "other" not in cond_vals


def test_validate_electronics_seller_rejects_auto_sale_vocab() -> None:
    cores = build_electronics_v2_core_fields()
    foto = cores["electronics-foto-i-videotehnika"]
    seller = next(r for r in foto if r[0] == "seller_type")

    class D:
        field_key = "seller_type"
        options = seller[5]

    ListingFieldValueService._validate_enum_option(D, "Частное лицо")
    ListingFieldValueService._validate_enum_option(D, "Магазин")
    for bad in ("Собственник", "Автосалон", "Дилер"):
        try:
            ListingFieldValueService._validate_enum_option(D, bad)
            raise AssertionError(f"expected reject {bad}")
        except Exception as exc:
            assert getattr(exc, "code", None) == "INVALID_LISTING_FIELD"


def test_other_brand_model_values_accepted_by_validator() -> None:
    cores = build_electronics_v2_core_fields()
    photo = cores["electronics-foto-i-videotehnika"]
    brand = next(r for r in photo if r[0] == "electronics_brand")
    model = next(r for r in photo if r[0] == "electronics_model")

    class BrandDef:
        field_key = "electronics_brand"
        options = brand[5]

    class ModelDef:
        field_key = "electronics_model"
        options = model[5]

    ListingFieldValueService._validate_enum_option(BrandDef, OTHER_BRAND_VALUE)
    ListingFieldValueService._validate_enum_option(ModelDef, OTHER_MODEL_VALUE)


def test_catalog_counts_split_real_vs_other() -> None:
    brands = 0
    models = 0
    other_brands = 0
    other_models = 0
    for sec in ELECTRONICS_SECTIONS.values():
        for g in sec["filters"]:
            if g["label"] == "Марка":
                brands += len(g["options"])
                other_brands += sum(
                    1 for o in g["options"] if o.get("value") == OTHER_BRAND_VALUE
                )
            if g["label"] == "Модель":
                models += len(g["options"])
                other_models += sum(
                    1 for o in g["options"] if o.get("value") == OTHER_MODEL_VALUE
                )
    real_brands = brands - other_brands
    real_models = models - other_models
    assert other_brands == 19
    assert other_models >= 100
    assert real_brands >= 160
    assert real_models >= 650
