"""Feed variant portrait aspect — matches AiVai feed card container."""

from __future__ import annotations

from io import BytesIO
from types import SimpleNamespace

from PIL import Image

from app.core.config import Settings
from app.media_engine.variants import (
    FEED_CONTAINER_ASPECT,
    FEED_ASPECT,
    HERO_ASPECT,
    THUMB_ASPECT,
    encode_all_variants,
    variant_specs,
)
from app.services.media_delivery_service import MediaDeliveryService
from app.storage.keys import listing_media_variant_key


def _boxfit_cover_crop_pct(iw: int, ih: int, cw: int, ch: int) -> tuple[float, float]:
    """Fraction of rendered image cropped on each axis (0..1)."""
    scale = max(cw / iw, ch / ih)
    rw, rh = iw * scale, ih * scale
    x_crop = max(0.0, (rw - cw) / rw) if rw > 0 else 0.0
    y_crop = max(0.0, (rh - ch) / rh) if rh > 0 else 0.0
    return x_crop, y_crop


def test_feed_aspect_matches_feed_container() -> None:
    assert FEED_ASPECT == HERO_ASPECT
    rel_diff = abs(FEED_ASPECT - FEED_CONTAINER_ASPECT) / FEED_CONTAINER_ASPECT
    assert rel_diff < 0.002, f"feed vs container aspect drift {rel_diff:.4%}"


def test_display_aspect_unchanged() -> None:
    specs = variant_specs(Settings())
    display = next(s for s in specs if s.name == "display")
    assert display.aspect == HERO_ASPECT


def test_thumb_remains_square() -> None:
    assert THUMB_ASPECT == 1.0
    specs = variant_specs(Settings())
    thumb = next(s for s in specs if s.name == "thumb")
    assert thumb.aspect == 1.0


def test_portrait_source_feed_is_portrait_not_landscape() -> None:
    """Listing 60 / photo 77 dimensions — tall phone photo."""
    img = Image.new("RGB", (2048, 3639), color=(100, 100, 100))
    outputs = encode_all_variants(img, focus=None, settings=Settings())
    feed = next(o for o in outputs if o.name == "feed")
    assert feed.width < feed.height, "feed must be portrait for tall sources"
    assert abs(feed.width / feed.height - FEED_ASPECT) < 0.001


def test_feed_dimensions_with_default_long_edge() -> None:
    settings = Settings()
    img = Image.new("RGB", (2048, 3639), color=(80, 80, 80))
    feed = next(o for o in encode_all_variants(img, focus=None, settings=settings) if o.name == "feed")
    # long_edge on height when aspect < 1
    assert feed.height == settings.MEDIA_ENGINE_FEED_LONG_EDGE
    assert feed.width == round(settings.MEDIA_ENGINE_FEED_LONG_EDGE * FEED_ASPECT)


def test_feed_cover_crop_near_zero_in_figma_container() -> None:
    settings = Settings()
    img = Image.new("RGB", (2048, 3639), color=(90, 90, 90))
    feed = next(o for o in encode_all_variants(img, focus=None, settings=settings) if o.name == "feed")
    x_crop, y_crop = _boxfit_cover_crop_pct(feed.width, feed.height, 209, 279)
    assert x_crop < 0.01, f"unexpected horizontal crop {x_crop:.2%}"
    assert y_crop < 0.01, f"unexpected vertical crop {y_crop:.2%}"


def test_v2_pipeline_variant_keys() -> None:
    key = listing_media_variant_key(60, 77, "feed", ".jpg", pipeline_version="v2")
    assert key == "media/60/77/v2/feed.jpg"


def test_legacy_v1_keys_still_resolve() -> None:
    """Immutable v1 blobs remain addressable; no reprocess required."""
    v1_key = listing_media_variant_key(60, 77, "feed", ".jpg", pipeline_version="v1")
    assert v1_key == "media/60/77/v1/feed.jpg"
    delivery = MediaDeliveryService(Settings(MEDIA_URL="/media/"))
    media = SimpleNamespace(
        url="/media/media/60/77/v1/display.jpg",
        original_storage_key="media/60/77/original.jpg",
        display_storage_key="media/60/77/v1/display.jpg",
        feed_storage_key="media/60/77/v1/feed.jpg",
        thumb_storage_key="media/60/77/v1/thumb.jpg",
        display_url=None,
        feed_url=None,
        thumb_url=None,
        lifecycle_status=SimpleNamespace(value="ready"),
    )
    # Patch lifecycle check — MediaLifecycleStatus enum in prod
    from app.models.media_enums import MediaLifecycleStatus

    media.lifecycle_status = MediaLifecycleStatus.ready
    variants = delivery.resolve_variants(media)
    assert variants.feed == "/media/media/60/77/v1/feed.jpg"
    assert variants.display == "/media/media/60/77/v1/display.jpg"


def test_new_media_uses_v2_default_pipeline_version() -> None:
    settings = Settings()
    assert settings.MEDIA_ASYNC_PIPELINE_VERSION == "v2"
    assert settings.MEDIA_PIPELINE_VERSION == "v2"


def test_feed_jpeg_decodes_to_expected_aspect() -> None:
    img = Image.new("RGB", (1200, 2000), color=(70, 70, 70))
    feed = next(o for o in encode_all_variants(img, focus=None, settings=Settings()) if o.name == "feed")
    decoded = Image.open(BytesIO(feed.content))
    assert decoded.width == feed.width
    assert decoded.height == feed.height
    assert abs(decoded.width / decoded.height - FEED_ASPECT) < 0.001
