"""Worker readiness — pipeline models before job claims; SigLIP off critical path."""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.workers import media_worker


@pytest.mark.asyncio
async def test_preload_sets_models_ready(monkeypatch) -> None:
    media_worker._WORKER_MODELS_READY = False
    settings = Settings(
        FOCUS_BBOX_ENABLED=False,
        MEDIA_VISUAL_EVIDENCE_ENABLED=False,
    )
    await media_worker.preload_media_worker_models(settings)
    assert media_worker.media_worker_models_ready() is True


@pytest.mark.asyncio
async def test_media_ready_does_not_wait_for_siglip(monkeypatch) -> None:
    media_worker._WORKER_MODELS_READY = False
    prepared = {"n": 0}

    class _Runtime:
        def prepare(self) -> None:
            prepared["n"] += 1

    monkeypatch.setattr(
        "app.visual_evidence.siglip2_runtime.get_siglip2_runtime",
        lambda: _Runtime(),
    )
    settings = Settings(
        FOCUS_BBOX_ENABLED=False,
        MEDIA_VISUAL_EVIDENCE_ENABLED=True,
        MEDIA_VISUAL_EVIDENCE_USE_STUB=False,
    )
    # Critical-path preload must mark ready without touching SigLIP.
    await media_worker.preload_media_worker_models(settings)
    assert prepared["n"] == 0
    assert media_worker.media_worker_models_ready() is True

    await media_worker.preload_visual_evidence_models(settings)
    assert prepared["n"] == 1
