"""AiVai Global Product Contract — Backend regression invariants.

See aivai_mobile/docs/AIVAI_GLOBAL_PRODUCT_CONTRACT.md
and aivai_mobile/docs/AIVAI_GLOBAL_INVARIANT_REGISTRY.md.

Foundation layer only: no Fashion Package A product imports.
Does not change product schemas. Pure policy / seed / helper checks.
"""

from __future__ import annotations

from app.models.category_enums import CategoryFieldType
from app.seeds.home_garden_filters import (
    HOME_GARDEN_CREATE_TEXT_ALLOWLIST,
    HOME_GARDEN_SEARCH_KEY_ALLOWLIST,
    HOME_GARDEN_SEARCH_KEY_EXCLUDE,
    FieldDef,
    create_field_component,
)

# Known demo/sample totals that must never be production Search defaults.
BANNED_FAKE_SEARCH_TOTALS = frozenset({55443, 1200})


def test_banned_fake_search_totals_are_documented() -> None:
    assert 55443 in BANNED_FAKE_SEARCH_TOTALS
    assert 1200 in BANNED_FAKE_SEARCH_TOTALS
    assert 0 not in BANNED_FAKE_SEARCH_TOTALS


def test_home_garden_search_keys_are_explicit_allowlist() -> None:
    assert "seller_type" in HOME_GARDEN_SEARCH_KEY_ALLOWLIST
    assert "condition" in HOME_GARDEN_SEARCH_KEY_ALLOWLIST
    # Create-only / detail fields must not silently become Search filters.
    assert "material" in HOME_GARDEN_SEARCH_KEY_EXCLUDE or (
        "material" not in HOME_GARDEN_SEARCH_KEY_ALLOWLIST
    )
    assert "plant_name" not in HOME_GARDEN_SEARCH_KEY_ALLOWLIST
    assert "width_cm" not in HOME_GARDEN_SEARCH_KEY_ALLOWLIST


def test_home_garden_default_text_allowlist_is_empty() -> None:
    assert HOME_GARDEN_CREATE_TEXT_ALLOWLIST == frozenset()


def test_structured_fields_do_not_map_to_inline_text() -> None:
    enum_field: FieldDef = (
        "condition",
        "Состояние",
        CategoryFieldType.enum,
        True,
        {"choices": [{"value": "new", "label": "Новое"}]},
        None,
    )
    number_field: FieldDef = (
        "width_cm",
        "Ширина",
        CategoryFieldType.number,
        False,
        None,
        None,
    )
    string_field: FieldDef = (
        "material",
        "Материал",
        CategoryFieldType.string,
        False,
        None,
        None,
    )
    assert create_field_component(enum_field) == "picker"
    assert create_field_component(number_field) == "numeric_dialog"
    assert create_field_component(string_field) == "forbidden_structured_inline_text"


def test_retired_home_garden_legacy_slugs_are_declared() -> None:
    from app.seeds.home_garden_canonical import RETIRED_HOME_GARDEN_LEGACY_SLUGS

    assert len(RETIRED_HOME_GARDEN_LEGACY_SLUGS) > 0
    for slug in RETIRED_HOME_GARDEN_LEGACY_SLUGS:
        assert isinstance(slug, str) and slug.startswith("home-")


def test_media_idempotency_helpers_remain_importable() -> None:
    from app.services.media_category_processing import (
        cleanup_duplicate_actionable_media_jobs,
    )

    assert callable(cleanup_duplicate_actionable_media_jobs)


def test_picker_parent_helper_exists_on_repository() -> None:
    from app.repositories.category_repository import CategoryRepository

    assert hasattr(CategoryRepository, "has_active_children")


def test_search_allowlist_cannot_equal_unscoped_create_dump() -> None:
    """Positive Search allowlist must be narrower than 'everything Create-like'."""
    # HG Search is an explicit allowlist, not an open dump of Create keys.
    assert len(HOME_GARDEN_SEARCH_KEY_ALLOWLIST) >= 1
    assert "plant_name" not in HOME_GARDEN_SEARCH_KEY_ALLOWLIST
    # Shared vocabulary on Create does not auto-imply every key is a Search filter.
    assert "width_cm" not in HOME_GARDEN_SEARCH_KEY_ALLOWLIST
