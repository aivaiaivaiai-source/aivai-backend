"""Substage 3C-2 — local visual evidence foundation tests."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import Settings
from app.media_classification.fingerprint import media_set_fingerprint
from app.models.listing_visual_evidence import build_visual_evidence_idempotency_key
from app.models.visual_evidence_enums import VisualEvidenceStatus
from app.services.visual_evidence_service import VisualEvidenceService
from app.visual_evidence.stub_provider import StubVisualEvidenceProvider
from app.visual_evidence.types import (
    VisualConceptObservation,
    VisualEvidenceOutput,
)


def test_visual_evidence_flags_default_off() -> None:
    s = Settings()
    assert s.MEDIA_VISUAL_EVIDENCE_ENABLED is False
    assert s.MEDIA_DESCRIPTION_MODE_ENABLED is False


def test_idempotency_key_includes_model_and_prompt() -> None:
    key = build_visual_evidence_idempotency_key(
        5,
        "abc123",
        "local-visual-evidence-v0-siglip2-base",
        "visual-evidence-prompts-v1",
        "visual-evidence-calibration-v1",
    )
    assert "listing:5" in key
    assert "ve:" in key
    assert "visual-evidence-prompts-v1" in key
    assert "cal:visual-evidence-calibration-v1" in key


def test_fingerprint_order_sensitive() -> None:
    a = media_set_fingerprint([1, 2, 3])
    b = media_set_fingerprint([1, 3, 2])
    assert a != b


@pytest.mark.asyncio
async def test_ensure_idempotent_same_fingerprint() -> None:
    settings = Settings(MEDIA_VISUAL_EVIDENCE_ENABLED=True)
    provider = StubVisualEvidenceProvider()
    session = AsyncMock()
    svc = VisualEvidenceService(session, settings, provider=provider)

    listing = SimpleNamespace(id=1, owner_id=10, category_id=None)
    svc._listings.get_by_id = AsyncMock(return_value=listing)
    svc._media.list_by_listing = AsyncMock(
        return_value=[
            SimpleNamespace(id=100, order=0, is_placeholder=False, original_storage_key="k1"),
        ]
    )
    fp = media_set_fingerprint([100])
    existing = SimpleNamespace(
        id=7,
        status=VisualEvidenceStatus.pending,
        media_set_fingerprint=fp,
    )
    svc._repo = MagicMock()
    svc._repo.get_by_idempotency_key = AsyncMock(return_value=existing)
    svc._repo.get_latest_for_listing = AsyncMock(return_value=None)
    svc._repo.create = AsyncMock()

    row = await svc.ensure_job_for_listing(1, actor_user_id=10)
    assert row is existing
    svc._repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_process_marks_stale_when_fingerprint_changed() -> None:
    settings = Settings(MEDIA_VISUAL_EVIDENCE_ENABLED=True)
    provider = StubVisualEvidenceProvider()
    session = MagicMock()
    session.flush = AsyncMock()
    svc = VisualEvidenceService(session, settings, provider=provider)

    row = SimpleNamespace(
        id=1,
        listing_id=2,
        status=VisualEvidenceStatus.pending,
        media_set_fingerprint="old_fp",
        attempt_count=0,
        created_at=None,
    )
    svc._repo.get_by_id = AsyncMock(return_value=row)
    svc.current_media_fingerprint = AsyncMock(return_value="new_fp")

    result = await svc.process_job(1)
    assert result.status == VisualEvidenceStatus.stale


@pytest.mark.asyncio
async def test_stub_provider_no_match() -> None:
    provider = StubVisualEvidenceProvider()
    out = await provider.infer(
        listing_id=1,
        media_inputs=[],
        max_images=3,
        load_image_bytes=AsyncMock(),
    )
    assert out.no_match is True


def test_observation_json_roundtrip() -> None:
    obs = VisualConceptObservation(
        concept="TRUCK",
        score=0.82,
        evidence_media_ids=[1, 2],
    )
    restored = VisualConceptObservation.from_json(obs.to_json())
    assert restored.concept == "TRUCK"
    assert restored.score == 0.82
    assert restored.evidence_media_ids == [1, 2]


def test_visual_evidence_output_not_category() -> None:
    out = VisualEvidenceOutput(
        observations=[
            VisualConceptObservation("TRUCK", 0.9, [1]),
        ],
        top_concepts=["TRUCK"],
        images_inspected=1,
    )
    assert out.top_concepts == ["TRUCK"]
    assert out.no_match is False
