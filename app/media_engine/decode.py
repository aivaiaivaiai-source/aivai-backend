"""Safe single-pass image decode for Media Engine."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import Settings
from app.media_queue.errors import PermanentMediaJobError
from app.services.storage_service import _ALLOWED_CONTENT_TYPES, _magic_matches_head

_EXT_TO_CONTENT_TYPE = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


@dataclass(frozen=True)
class DecodedImage:
    image: Image.Image
    width: int
    height: int
    content_type: str
    ext: str


def content_type_from_key(key: str) -> str:
    lower = key.lower()
    for ext, ctype in _EXT_TO_CONTENT_TYPE.items():
        if lower.endswith(ext):
            return ctype
    raise PermanentMediaJobError(
        "Unsupported original extension.",
        error_code="UNSUPPORTED_FORMAT",
    )


def decode_image_safe(
    content: bytes,
    *,
    content_type: str,
    settings: Settings,
) -> DecodedImage:
    if len(content) > settings.MEDIA_MAX_IMAGE_BYTES:
        raise PermanentMediaJobError(
            "Image exceeds maximum allowed size.",
            error_code="IMAGE_TOO_LARGE",
        )
    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise PermanentMediaJobError(
            "Unsupported image content type.",
            error_code="UNSUPPORTED_FORMAT",
        )
    if not _magic_matches_head(content, content_type):
        raise PermanentMediaJobError(
            "File content does not match declared image type.",
            error_code="INVALID_MAGIC",
        )

    try:
        with Image.open(BytesIO(content)) as opened:
            opened.load()
            pixel_count = opened.width * opened.height
            if pixel_count <= 0:
                raise PermanentMediaJobError(
                    "Invalid image dimensions.",
                    error_code="INVALID_DIMENSIONS",
                )
            if pixel_count > settings.MEDIA_MAX_DECODE_PIXELS:
                raise PermanentMediaJobError(
                    "Image exceeds maximum pixel count.",
                    error_code="DECOMPRESSION_BOMB",
                )
            rgb = ImageOps.exif_transpose(opened).convert("RGB")
    except PermanentMediaJobError:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise PermanentMediaJobError(
            "Corrupt or unsupported image.",
            error_code="DECODE_FAILED",
        ) from exc

    ext = _CONTENT_TYPE_TO_EXT.get(content_type, ".jpg")
    return DecodedImage(
        image=rgb,
        width=rgb.width,
        height=rgb.height,
        content_type=content_type,
        ext=ext,
    )


_CONTENT_TYPE_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
