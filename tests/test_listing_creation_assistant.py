from __future__ import annotations

from decimal import Decimal

import pytest

from app.schemas.listing_assistant import PromotionOffer
from app.schemas.user import UserRead
from app.schemas.voice import VoiceIntent
from app.services.listing_content_generator import ListingContentGenerator
from app.services.promotion_flow import PromotionFlow
from app.services.voice_response_builder import VoiceResponseBuilder


def test_title_generation_iphone() -> None:
    known = {"city": "Бишкек"}
    title = ListingContentGenerator.generate_title(
        seed_text="продаю айфон 13 128 гб",
        known_fields=known,
        category_slug="electronics-phones",
    )
    assert "iPhone" in title or "13" in title
    assert "128" in title or "128GB" in title.upper()


def test_description_electronics_no_fake_specs() -> None:
    known = {"city": "Бишкек"}
    title = "iPhone 13 128GB"
    desc = ListingContentGenerator.generate_description(
        title=title,
        known_fields=known,
        category_slug="electronics-phones",
        category_name="Телефоны",
        seed_text="продаю айфон 13 128 гб в хорошем состоянии",
    )
    assert "iPhone" in desc
    assert len(desc) <= 600
    assert "256" not in desc
    assert "Pro Max" not in desc


def test_description_short_when_minimal_fields() -> None:
    known = {"city": "Ош", "price": "1000"}
    desc = ListingContentGenerator.generate_description(
        title="Товар",
        known_fields=known,
        category_slug="home-decor",
        category_name="Декор",
    )
    assert len(desc) < 400
    assert "Ош" in desc


def test_category_transport_description() -> None:
    known = {
        "brand": "Toyota",
        "model": "Camry",
        "year": "2018",
        "city": "Бишкек",
    }
    title = ListingContentGenerator.generate_title(
        seed_text="продаю камри",
        known_fields=known,
        category_slug="transport-cars",
    )
    desc = ListingContentGenerator.generate_description(
        title=title,
        known_fields=known,
        category_slug="transport-cars",
        category_name="Легковые",
    )
    assert "Toyota" in desc or "Camry" in desc
    assert "Продаётся" in desc


def test_category_animals_description() -> None:
    known = {"animal_type": "корова", "purpose": "дойная", "city": "село"}
    title = ListingContentGenerator.generate_title(
        seed_text="продаю корову",
        known_fields=known,
        category_slug="animals-livestock",
    )
    desc = ListingContentGenerator.generate_description(
        title=title,
        known_fields=known,
        category_slug="animals-livestock",
        category_name="Сельхоз",
    )
    assert "коров" in desc.lower() or "Коров" in desc


def test_category_services_description() -> None:
    known = {"service_type": "барбер", "city": "Бишкек"}
    desc = ListingContentGenerator.generate_description(
        title="Барбер",
        known_fields=known,
        category_slug="services-beauty",
        category_name="Красота",
    )
    assert "Оказываю" in desc or "услуг" in desc.lower()


def test_draft_preview_response_schema() -> None:
    from app.schemas.listing_assistant import DraftPreview
    from app.schemas.voice import VoiceCommandResponse

    preview = DraftPreview(
        title="iPhone 13",
        description="Продаётся iPhone 13.",
        category_id=1,
        category_slug="electronics-phones",
        known_fields={"city": "Бишкек"},
        price="50000",
        city="Бишкек",
    )
    intent = VoiceIntent(intent="create_listing", confidence=0.9, extracted={})
    resp = VoiceResponseBuilder.draft_preview(intent, preview=preview, message="Проверьте черновик.")
    VoiceCommandResponse.model_validate(resp.model_dump())
    assert resp.publish_confirmation_required is True
    assert resp.needs_photos is True
    assert resp.draft_preview is not None


def test_promotion_offer_shape() -> None:
    offer = PromotionFlow.build_offer(42)
    assert offer.enabled is True
    assert offer.price_kgs == Decimal("50")
    assert offer.listing_id == 42


def test_promotion_balance_sufficient() -> None:
    from datetime import UTC, datetime

    user = UserRead(
        id=1,
        phone="+70000000000",
        full_name="T",
        is_active=True,
        balance=Decimal("100"),
        last_login=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    intent = VoiceIntent(intent="create_listing", confidence=0.9, extracted={})
    resp = PromotionFlow.handle_response(
        intent,
        user=user,
        listing_id=10,
        text="да продвинуть",
    )
    assert "подключено" in resp.message.lower() or "Продвижение" in resp.message


def test_promotion_topup_when_low_balance() -> None:
    from datetime import UTC, datetime

    user = UserRead(
        id=1,
        phone="+70000000000",
        full_name="T",
        is_active=True,
        balance=Decimal("10"),
        last_login=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    intent = VoiceIntent(intent="create_listing", confidence=0.9, extracted={})
    resp = PromotionFlow.handle_response(
        intent,
        user=user,
        listing_id=10,
        text="хочу продвинуть",
    )
    assert resp.data is not None
    assert resp.data.get("topup_required") is True


def test_no_auto_publish_in_draft_preview() -> None:
    from app.schemas.listing_assistant import DraftPreview

    intent = VoiceIntent(intent="create_listing", confidence=0.9, extracted={})
    preview = DraftPreview(
        title="Test",
        description="Short.",
        category_id=1,
    )
    resp = VoiceResponseBuilder.draft_preview(intent, preview=preview, message="ok")
    assert "listing" not in (resp.data or {}) or "listing" not in str(resp.data.get("listing", ""))
    assert resp.publish_confirmation_required is True
