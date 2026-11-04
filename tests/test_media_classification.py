"""Substage 2 — AI media classification foundation tests."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import Settings
from app.media_classification.dev_classifier import DevelopmentDeterministicClassifier
from app.media_classification.fingerprint import media_set_fingerprint
from app.media_classification.types import (
    AllowedCategory,
    CategoryCandidate,
    ClassificationMediaInput,
    ClassifierOutput,
)
from app.models.media_classification import build_classification_idempotency_key
from app.models.media_classification_enums import MediaClassificationStatus
from app.models.media_job import build_media_job_idempotency_key
from app.services.media_classification_service import (
    MediaClassificationService,
    confidence_band_for,
)


def test_feature_flag_default_false() -> None:
    assert Settings().MEDIA_AI_CLASSIFICATION_ENABLED is False


def test_fingerprint_changes_with_media_set() -> None:
    a = media_set_fingerprint([1, 2, 3])
    b = media_set_fingerprint([1, 3, 2])
    c = media_set_fingerprint([1, 2])
    assert a != b
    assert a != c
    assert media_set_fingerprint([1, 2, 3]) == a


def test_idempotency_key_stable() -> None:
    k = build_classification_idempotency_key(9, "abc", "dev-deterministic-v1")
    assert k == "listing:9:media_set:abc:clf:dev-deterministic-v1"


def test_media_job_key_includes_category_context() -> None:
    assert build_media_job_idempotency_key(1, "v2", category_id=7).endswith(":cat:7")


def test_confidence_bands() -> None:
    assert confidence_band_for(0.9, high=0.85, medium=0.55).value == "high"
    assert confidence_band_for(0.6, high=0.85, medium=0.55).value == "medium"
    assert confidence_band_for(0.2, high=0.85, medium=0.55).value == "low"


@pytest.mark.asyncio
async def test_dev_classifier_no_match_without_fixture() -> None:
    clf = DevelopmentDeterministicClassifier()
    allowed = [
        AllowedCategory(1, "transport-car-sale", "Продажа авто", 10, "Транспорт → Продажа авто"),
        AllowedCategory(2, "transport-auto-parts", "Автозапчасти", 10, "Транспорт → Автозапчасти"),
    ]
    out = await clf.classify(
        listing_id=1,
        media_inputs=[
            ClassificationMediaInput(1, 0, "listings/1/photo.jpg"),
            ClassificationMediaInput(2, 1, "listings/1/photo2.jpg"),
        ],
        allowed_categories=allowed,
        max_images=3,
        high_confidence_threshold=0.85,
        medium_confidence_threshold=0.55,
    )
    assert out.no_match is True
    assert out.candidates == []


@pytest.mark.asyncio
async def test_dev_classifier_catalog_bound_and_early_stop() -> None:
    clf = DevelopmentDeterministicClassifier()
    allowed = [
        AllowedCategory(1, "transport-car-sale", "Продажа авто", 10, "Транспорт → Продажа авто"),
        AllowedCategory(2, "transport-auto-parts", "Автозапчасти", 10, "Транспорт → Автозапчасти"),
    ]
    out = await clf.classify(
        listing_id=1,
        media_inputs=[
            ClassificationMediaInput(10, 0, "x/fixture-car-sale/a.jpg"),
            ClassificationMediaInput(11, 1, "x/fixture-car-sale/b.jpg"),
            ClassificationMediaInput(12, 2, "x/other.jpg"),
        ],
        allowed_categories=allowed,
        max_images=9,
        high_confidence_threshold=0.85,
        medium_confidence_threshold=0.55,
    )
    assert out.no_match is False
    assert len(out.candidates) == 1
    assert out.candidates[0].category_slug == "transport-car-sale"
    assert out.candidates[0].category_id == 1
    assert out.images_inspected == 1  # early stop on cover


@pytest.mark.asyncio
async def test_dev_classifier_rejects_unknown_slug_hint() -> None:
    """Hints for non-catalog slugs cannot invent categories."""
    clf = DevelopmentDeterministicClassifier()
    allowed = [
        AllowedCategory(2, "transport-auto-parts", "Автозапчасти", 10, "Транспорт → Автозапчасти"),
    ]
    out = await clf.classify(
        listing_id=1,
        media_inputs=[
            ClassificationMediaInput(1, 0, "x/fixture-car-sale/a.jpg"),
        ],
        allowed_categories=allowed,
        max_images=3,
        high_confidence_threshold=0.85,
        medium_confidence_threshold=0.55,
    )
    # car-sale not in allowed → vote ignored → no_match
    assert out.no_match is True


class _ScriptedClassifier:
    version = "scripted-v1"

    def __init__(self, output: ClassifierOutput) -> None:
        self._output = output

    async def classify(self, **kwargs) -> ClassifierOutput:
        del kwargs
        return self._output


@pytest.mark.asyncio
async def test_process_job_filters_non_catalog_candidates() -> None:
    settings = Settings(MEDIA_AI_CLASSIFICATION_ENABLED=True)
    session = AsyncMock()
    bogus = CategoryCandidate(999, "invented-luxury-cars", "Люкс", "Люкс", 0.99)
    valid = CategoryCandidate(5, "transport-car-sale", "Продажа авто", "Транспорт → Продажа авто", 0.9)
    clf = _ScriptedClassifier(
        ClassifierOutput(candidates=[bogus, valid], images_inspected=1, evidence_media_ids=[1])
    )
    svc = MediaClassificationService(session, settings, classifier=clf)

    row = SimpleNamespace(
        id=1,
        listing_id=3,
        status=MediaClassificationStatus.pending,
        attempt_count=0,
        created_at=datetime.now(UTC),
        media_set_fingerprint=media_set_fingerprint([1]),
        lease_owner=None,
        lease_until=None,
    )
    svc._repo.get_by_id = AsyncMock(return_value=row)
    svc._listings.get_by_id = AsyncMock(return_value=SimpleNamespace(id=3, category_id=None, owner_id=1))
    svc.current_media_fingerprint = AsyncMock(return_value=media_set_fingerprint([1]))
    svc._media.list_by_listing = AsyncMock(
        return_value=[SimpleNamespace(id=1, order=0, original_storage_key="k", is_placeholder=False)]
    )
    svc._load_allowed_categories = AsyncMock(
        return_value=[
            AllowedCategory(5, "transport-car-sale", "Продажа авто", 1, "Транспорт → Продажа авто"),
        ]
    )

    result = await svc.process_job(1)
    assert result.status == MediaClassificationStatus.succeeded
    assert len(result.candidates_json) == 1
    assert result.candidates_json[0]["category_id"] == 5
    assert result.predicted_category_id == 5


@pytest.mark.asyncio
async def test_stale_result_cannot_confirm() -> None:
    settings = Settings(MEDIA_AI_CLASSIFICATION_ENABLED=True)
    session = AsyncMock()
    svc = MediaClassificationService(session, settings)
    listing = SimpleNamespace(id=3, owner_id=1, category_id=None)
    svc._listings.get_by_id = AsyncMock(return_value=listing)
    svc._categories.get_by_id = AsyncMock(
        return_value=SimpleNamespace(id=5, is_active=True, slug="transport-car-sale")
    )
    svc.current_media_fingerprint = AsyncMock(return_value="fp-new")
    svc._repo.get_by_id = AsyncMock(
        return_value=SimpleNamespace(
            id=9,
            listing_id=3,
            media_set_fingerprint="fp-old",
            status=MediaClassificationStatus.succeeded,
            predicted_category_id=5,
        )
    )

    from app.core.exceptions import AppException

    with pytest.raises(AppException) as ei:
        await svc.confirm_category(
            3, actor_user_id=1, category_id=5, classification_id=9
        )
    assert ei.value.status_code == 409


@pytest.mark.asyncio
async def test_confirm_records_override_and_sets_category(monkeypatch) -> None:
    settings = Settings(
        MEDIA_AI_CLASSIFICATION_ENABLED=True,
        MEDIA_ASYNC_PIPELINE_ENABLED=True,
    )
    session = AsyncMock()
    session.commit = AsyncMock()
    svc = MediaClassificationService(session, settings)
    listing = SimpleNamespace(id=3, owner_id=1, category_id=None)
    svc._listings.get_by_id = AsyncMock(return_value=listing)
    svc._categories.get_by_id = AsyncMock(
        return_value=SimpleNamespace(id=8, is_active=True, slug="transport-auto-parts")
    )
    svc.current_media_fingerprint = AsyncMock(return_value="fp1")
    row = SimpleNamespace(
        id=9,
        listing_id=3,
        media_set_fingerprint="fp1",
        status=MediaClassificationStatus.succeeded,
        predicted_category_id=5,
        selected_category_id=None,
        user_overridden=False,
    )
    svc._repo.get_by_id = AsyncMock(return_value=row)

    async def _enqueue(*_a, **_k):
        return 2

    monkeypatch.setattr(
        "app.services.media_category_processing.enqueue_category_aware_media_for_listing",
        _enqueue,
    )
    monkeypatch.setattr(
        "app.core.redis.get_redis",
        lambda: None,
    )

    resp = await svc.confirm_category(
        3, actor_user_id=1, category_id=8, classification_id=9
    )
    assert resp.user_overridden is True
    assert resp.category_id == 8
    assert resp.media_jobs_enqueued == 2
    assert listing.category_id == 8
    assert row.status == MediaClassificationStatus.confirmed
    assert row.user_overridden is True


@pytest.mark.asyncio
async def test_ensure_job_noop_when_flag_off() -> None:
    settings = Settings(MEDIA_AI_CLASSIFICATION_ENABLED=False)
    session = AsyncMock()
    svc = MediaClassificationService(session, settings)
    assert await svc.ensure_job_for_listing(1, actor_user_id=1) is None


@pytest.mark.asyncio
async def test_ownership_on_get_status() -> None:
    settings = Settings(MEDIA_AI_CLASSIFICATION_ENABLED=True)
    session = AsyncMock()
    svc = MediaClassificationService(session, settings)
    svc._listings.get_by_id = AsyncMock(
        return_value=SimpleNamespace(id=1, owner_id=99, category_id=None)
    )
    from app.core.exceptions import AppException

    with pytest.raises(AppException) as ei:
        await svc.get_status(1, actor_user_id=1)
    assert ei.value.status_code == 403


@pytest.mark.asyncio
async def test_route_pipeline_still_blocks_null_auto() -> None:
    from app.media_engine.router import MediaPipelineKind, route_pipeline

    assert route_pipeline(None) == MediaPipelineKind.GENERAL
    assert route_pipeline("") == MediaPipelineKind.GENERAL
    assert route_pipeline("transport-car-sale") == MediaPipelineKind.AUTO
