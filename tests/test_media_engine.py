from __future__ import annotations

from io import BytesIO

import pytest
from PIL import Image

from app.core.config import Settings
from app.media_engine.decode import decode_image_safe
from app.media_engine.enhance import compute_enhance_params, enhance_image
from app.media_engine.framing import compute_crop_box
from app.media_engine.router import MediaPipelineKind, route_pipeline
from app.media_engine.variants import encode_all_variants, variant_specs
from app.media_queue.errors import PermanentMediaJobError
from app.storage.keys import listing_media_variant_key


def _jpeg_bytes(w: int = 200, h: int = 150) -> bytes:
    img = Image.new("RGB", (w, h), color=(120, 80, 60))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_route_auto_for_car_sale() -> None:
    assert route_pipeline("transport-car-sale") == MediaPipelineKind.AUTO
    assert route_pipeline("other") == MediaPipelineKind.GENERAL


def test_versioned_variant_key() -> None:
    key = listing_media_variant_key(1, 2, "display", ".jpg", pipeline_version="v1")
    assert key == "media/1/2/v1/display.jpg"


def test_decode_rejects_huge_dimensions() -> None:
    settings = Settings(MEDIA_MAX_DECODE_PIXELS=1000)
    with pytest.raises(PermanentMediaJobError, match="pixel"):
        decode_image_safe(_jpeg_bytes(2000, 2000), content_type="image/jpeg", settings=settings)


def test_decode_accepts_valid_jpeg() -> None:
    settings = Settings()
    decoded = decode_image_safe(_jpeg_bytes(), content_type="image/jpeg", settings=settings)
    assert decoded.width == 200
    assert decoded.height == 150


def test_enhance_is_conservative() -> None:
    img = Image.new("RGB", (100, 100), color=(128, 128, 128))
    params = compute_enhance_params(img, Settings())
    assert 0.93 <= params.brightness <= 1.14
    assert params.contrast <= 1.18
    assert params.saturation <= 1.19
    out = enhance_image(img, Settings())
    assert out.size == img.size


def test_framing_fallback_full_image() -> None:
    crop = compute_crop_box(800, 600, target_aspect=430 / 573, bbox=None)
    assert crop.width > 0
    assert crop.height > 0


def test_encode_all_variants_produces_three() -> None:
    img = Image.new("RGB", (1200, 900), color=(90, 90, 90))
    outputs = encode_all_variants(img, focus=None, settings=Settings())
    names = {o.name for o in outputs}
    assert names == {"display", "feed", "thumb"}
    for o in outputs:
        assert o.content[:2] == b"\xff\xd8"
        assert o.width > 0 and o.height > 0


def test_variant_specs_centralized() -> None:
    specs = variant_specs(Settings())
    assert len(specs) == 3
    assert specs[0].name == "display"


@pytest.mark.asyncio
async def test_engine_ready_with_inmemory_storage() -> None:
    from datetime import UTC, datetime
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.media_engine.engine import AiVaiMediaEngine
    from app.media_queue.processor import MediaProcessorOutcome
    from app.models.image_moderation_enums import ImageModerationVerdict, MediaModerationStatus
    from app.models.media_enums import MediaLifecycleStatus
    from app.storage.memory import InMemoryObjectStorage
    from app.services.storage_service import StorageService

    content = _jpeg_bytes(640, 480)
    backend = InMemoryObjectStorage()
    key = "media/1/10/original.jpg"
    backend.put(key, content, content_type="image/jpeg")
    storage = StorageService(Settings(), backend=backend)

    media = SimpleNamespace(
        id=10,
        listing_id=1,
        original_storage_key=key,
        original_url=None,
        display_url=None,
        feed_url=None,
        thumb_url=None,
        url="/pending",
        lifecycle_status=MediaLifecycleStatus.processing,
        pipeline_version=None,
        processed_at=None,
        moderation_status=None,
        moderation_reason=None,
        moderated_at=None,
        focus_bbox_left=None,
        focus_bbox_top=None,
        focus_bbox_width=None,
        focus_bbox_height=None,
        focus_confidence=None,
        error_code=None,
        error_message=None,
    )
    job = SimpleNamespace(id=1, media_id=10, pipeline_version="v1")
    listing = SimpleNamespace(category=SimpleNamespace(slug="other"))
    session = MagicMock()
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=listing)

    engine = AiVaiMediaEngine(Settings(), classifier=MagicMock(), detector=MagicMock())
    engine._moderation.run_classification = AsyncMock(
        return_value=SimpleNamespace(
            verdict=ImageModerationVerdict.ALLOW,
            moderation_status=MediaModerationStatus.approved,
            moderation_reason=None,
            moderated_at=datetime.now(UTC),
        ),
    )

    with patch("app.media_engine.engine.ListingRepository", return_value=repo), patch(
        "app.media_engine.engine.StorageService",
        return_value=storage,
    ):
        result = await engine.process(session, job=job, media=media)

    assert result.outcome == MediaProcessorOutcome.ready
    assert media.lifecycle_status == MediaLifecycleStatus.ready
    assert media.display_url and media.feed_url and media.thumb_url
    assert media.url == media.display_url
    assert media.pipeline_version == "v1"
