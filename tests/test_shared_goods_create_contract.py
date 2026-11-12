"""Independent shared Create contract parity (Backend SoT).

Does NOT derive expected values from the Kids builder under test.
Canonical expectations are fixed production AiVai goods standards +
shared_goods_create_contract module (cross-checked against closed domains).
"""
from __future__ import annotations

from app.models.category_enums import CategoryFieldType
from app.seeds.shared_goods_create_contract import (
    APPROVED_SHARED_FIELD_OVERRIDES,
    CANONICAL_GOODS_SHARED_FIELD_CONTRACT,
    CONTACT_METHOD_CHOICES,
    GOODS_NEGOTIABLE_CHOICES,
    GOODS_SELLER_CHOICES,
    assert_field_matches_canonical,
    extract_choice_values,
    field_row_by_key,
    options_from_field_row,
)

# Independent expected contract (closed-domain evidence — do not import kids_v2).
_INDEPENDENT_CONTACT = (
    "Только чат",
    "Только телефон",
    "Чат + телефон",
    "Чат + Wapp",
    "Телефон + Wapp",
    "Чат + Тел. + Wapp",
)
_INDEPENDENT_NEGOTIABLE = ("Есть торг", "Без торга")
_INDEPENDENT_SELLER = ("Частное лицо", "Магазин", "Другой")
_BANNED_KIDS_CONTACT = ("Звонок", "WhatsApp", "Telegram")
_BANNED_KIDS_NEGOTIABLE = ("Возможен", "Нет")


def _sample_fields(domain: str) -> list:
    if domain == "fashion":
        from app.seeds.fashion_v2 import build_fashion_v2_core_fields

        cores = build_fashion_v2_core_fields()
        return cores[next(iter(cores))]
    if domain == "electronics":
        from app.seeds.electronics_v2 import build_electronics_v2_core_fields

        cores = build_electronics_v2_core_fields()
        return cores[next(iter(cores))]
    if domain == "kids":
        from app.seeds.kids_v2 import build_kids_v2_core_fields

        return build_kids_v2_core_fields()["kids-detskaya-odezhda"]
    if domain == "food_agri":
        from app.seeds.food_agri_v2 import build_food_agri_v2_core_fields

        return build_food_agri_v2_core_fields()["food-agri-ovoschi-i-frukty"]
    if domain == "animals":
        from app.seeds.animals_v2 import build_animals_v2_core_fields

        return build_animals_v2_core_fields()["animals-sobaki"]
    if domain == "stationery":
        from app.seeds.stationery_v2 import build_stationery_v2_core_fields

        return build_stationery_v2_core_fields()[
            "stationery-books-kantselyarskie-tovary"
        ]
    if domain == "business_equipment":
        from app.seeds.business_equipment_v2 import (
            build_business_equipment_v2_core_fields,
        )

        return build_business_equipment_v2_core_fields()[
            "business-equipment-torgovoe-oborudovanie"
        ]
    if domain == "medical":
        from app.seeds.medical_v2 import build_medical_v2_core_fields

        return build_medical_v2_core_fields()["medical-meditsinskie-pribory"]
    if domain == "home_garden":
        from app.seeds.home_garden_filters import build_home_garden_core_fields

        cores = build_home_garden_core_fields()
        for fields in cores.values():
            if field_row_by_key(fields, "contact_methods") is not None:
                return fields
        raise AssertionError("HG leaf without contact_methods")
    if domain == "repair":
        from app.seeds.repair_v2 import build_repair_v2_core_fields

        cores = build_repair_v2_core_fields()
        return cores[next(iter(cores))]
    if domain == "services":
        from app.seeds.services_v2 import build_services_v2_core_fields

        cores = build_services_v2_core_fields()
        return cores[next(iter(cores))]
    if domain == "car_sale":
        from app.seeds.car_sale_v2 import CONTACT_METHOD_CHOICES as car_cm

        # car_sale exposes choices constant; synthesize comparable row shape.
        return [
            (
                "contact_methods",
                "Способы связи",
                CategoryFieldType.enum,
                True,
                0,
                {"choices": [{"value": c, "label": c} for c in car_cm]},
                None,
            )
        ]
    raise AssertionError(domain)


def test_shared_module_matches_independent_canonical() -> None:
    assert CONTACT_METHOD_CHOICES == _INDEPENDENT_CONTACT
    assert GOODS_NEGOTIABLE_CHOICES == _INDEPENDENT_NEGOTIABLE
    assert GOODS_SELLER_CHOICES == _INDEPENDENT_SELLER
    assert CANONICAL_GOODS_SHARED_FIELD_CONTRACT["contact_methods"]["choices"] == (
        _INDEPENDENT_CONTACT
    )


def test_kids_shared_fields_match_canonical_not_local_catalog() -> None:
    fields = _sample_fields("kids")
    for key in ("seller_type", "price", "negotiable", "contact_methods"):
        assert_field_matches_canonical(
            domain="kids",
            field_key=key,
            row=field_row_by_key(fields, key),
        )
    contact = extract_choice_values(
        options_from_field_row(field_row_by_key(fields, "contact_methods"))
    )
    negotiable = extract_choice_values(
        options_from_field_row(field_row_by_key(fields, "negotiable"))
    )
    assert contact == _INDEPENDENT_CONTACT
    assert negotiable == _INDEPENDENT_NEGOTIABLE
    assert contact != _BANNED_KIDS_CONTACT
    assert negotiable != _BANNED_KIDS_NEGOTIABLE


def test_kids_all_leaves_share_same_contact_contract() -> None:
    from app.seeds.kids_v2 import build_kids_v2_core_fields

    for slug, fields in build_kids_v2_core_fields().items():
        row = field_row_by_key(fields, "contact_methods")
        assert_field_matches_canonical(
            domain="kids", field_key="contact_methods", row=row
        )
        neg = field_row_by_key(fields, "negotiable")
        assert_field_matches_canonical(
            domain="kids", field_key="negotiable", row=neg
        )
        assert slug.startswith("kids-")


def test_cross_domain_contact_methods_one_canonical_contract() -> None:
    for domain in (
        "fashion",
        "electronics",
        "home_garden",
        "repair",
        "services",
        "kids",
        "car_sale",
        "food_agri",
        "animals",
        "stationery",
        "business_equipment",
        "medical",
    ):
        fields = _sample_fields(domain)
        row = field_row_by_key(fields, "contact_methods")
        # contact_methods has no approved override among these domains
        assert (domain, "contact_methods") not in APPROVED_SHARED_FIELD_OVERRIDES
        assert_field_matches_canonical(
            domain=domain, field_key="contact_methods", row=row
        )


def test_goods_domains_seller_negotiable_price_parity() -> None:
    for domain in (
        "fashion",
        "electronics",
        "kids",
        "stationery",
        "business_equipment",
        "medical",
    ):
        fields = _sample_fields(domain)
        for key in ("seller_type", "price", "negotiable"):
            assert_field_matches_canonical(
                domain=domain,
                field_key=key,
                row=field_row_by_key(fields, key),
            )
    # Food/Agri: price+negotiable canonical; seller is approved override.
    food = _sample_fields("food_agri")
    for key in ("price", "negotiable"):
        assert_field_matches_canonical(
            domain="food_agri",
            field_key=key,
            row=field_row_by_key(food, key),
        )
    assert ("food_agri", "seller_type") in APPROVED_SHARED_FIELD_OVERRIDES
    seller = extract_choice_values(
        options_from_field_row(field_row_by_key(food, "seller_type"))
    )
    assert seller == ("Частное лицо", "Фермер", "Магазин", "Другой")

    animals = _sample_fields("animals")
    for key in ("price", "negotiable", "contact_methods"):
        assert_field_matches_canonical(
            domain="animals",
            field_key=key,
            row=field_row_by_key(animals, key),
        )
    assert ("animals", "seller_type") in APPROVED_SHARED_FIELD_OVERRIDES
    animals_seller = extract_choice_values(
        options_from_field_row(field_row_by_key(animals, "seller_type"))
    )
    assert animals_seller == (
        "Частное лицо",
        "Хозяйство",
        "Питомник",
        "Магазин",
        "Другой",
    )


def test_services_approved_override_not_forced_to_goods_negotiable() -> None:
    fields = _sample_fields("services")
    neg = field_row_by_key(fields, "negotiable")
    assert ("services", "negotiable") in APPROVED_SHARED_FIELD_OVERRIDES
    # Must not crash / force goods «Есть торг» onto Services.
    assert_field_matches_canonical(
        domain="services", field_key="negotiable", row=neg
    )
    got = extract_choice_values(options_from_field_row(neg))
    assert got != _INDEPENDENT_NEGOTIABLE
    assert got is not None and "По договорённости" in got


def test_global_invariant_shared_field_equals_shared_contract() -> None:
    """Reusable invariant: declared shared → structural equality unless override."""
    from app.seeds.kids_v2 import build_kids_v2_core_fields

    fields = build_kids_v2_core_fields()["kids-igrushki-igry-i-konstruktory"]
    for key in CANONICAL_GOODS_SHARED_FIELD_CONTRACT:
        assert_field_matches_canonical(
            domain="kids",
            field_key=key,
            row=field_row_by_key(fields, key),
        )
