"""Beauty Package A — AI medical claim + characteristic safety."""
from __future__ import annotations

from app.services.beauty_ai_medical_claim_guard import (
    assert_ordinary_words_not_banned,
    contains_unsupported_medical_claim,
    scrub_ai_invented_medical_claims,
)
from app.services.listing_content_generator import ListingContentGenerator
from app.seeds.beauty_v2 import BEAUTY_CREATE_FORBIDDEN


def test_ordinary_beauty_words_allowed() -> None:
    assert_ordinary_words_not_banned()
    assert not contains_unsupported_medical_claim("крем для кожи")
    assert not contains_unsupported_medical_claim("увлажнение и уход")
    assert not contains_unsupported_medical_claim("косметика для лица")


def test_therapeutic_claims_detected() -> None:
    for phrase in (
        "лечит акне",
        "лечебный крем",
        "лечебная маска",
        "излечивает",
        "устраняет заболевание",
        "гарантирует медицинский результат",
        "лечит дерматит",
        "лечит выпадение волос",
    ):
        assert contains_unsupported_medical_claim(phrase), phrase


def test_ai_invented_claim_scrubbed_when_user_neutral() -> None:
    scrubbed = scrub_ai_invented_medical_claims(
        user_seed="крем для кожи",
        generated="лечебный крем, лечит дерматит",
    )
    assert not contains_unsupported_medical_claim(scrubbed)
    assert "лечит" not in scrubbed.lower()
    assert "лечеб" not in scrubbed.lower()
    assert scrubbed in {"", "крем для кожи"} or "крем" in scrubbed.lower()


def test_user_stated_claim_not_silently_strengthened_beyond_seed() -> None:
    # Guard must not invent stronger claims than the user wrote.
    scrubbed = scrub_ai_invented_medical_claims(
        user_seed="крем для кожи",
        generated="крем для кожи. лечебный крем, лечит дерматит.",
    )
    assert "лечит дерматит" not in scrubbed.lower()
    assert "лечебный" not in scrubbed.lower()


def test_content_generator_beauty_neutral() -> None:
    title = ListingContentGenerator.generate_title(
        seed_text="крем для кожи",
        known_fields={"beauty_kind": "Кремы для лица"},
        category_slug="beauty-uhod-za-litsom",
    )
    assert "леч" not in title.lower()
    desc = ListingContentGenerator.generate_description(
        title=title,
        known_fields={"beauty_kind": "Кремы для лица", "city": "Бишкек"},
        category_slug="beauty-uhod-za-litsom",
        category_name="Уход за лицом",
        seed_text="крем для кожи",
    )
    assert not contains_unsupported_medical_claim(desc)
    assert "Продаётся" in desc


def test_forbidden_structured_keys_locked() -> None:
    for key in (
        "beauty_brand",
        "beauty_model",
        "volume",
        "shade",
        "spf",
        "package_state",
        "authenticity",
    ):
        assert key in BEAUTY_CREATE_FORBIDDEN
