"""Put/get variant blobs with versioned deterministic keys."""

from __future__ import annotations

from dataclasses import dataclass

from app.media_engine.variants import VariantOutput
from app.services.storage_service import StorageService
from app.storage.keys import listing_media_variant_key


@dataclass(frozen=True)
class StoredVariant:
    name: str
    key: str
    url: str
    width: int
    height: int


def variant_storage_key(
    listing_id: int,
    media_id: int,
    variant_name: str,
    *,
    pipeline_version: str,
    ext: str = ".jpg",
) -> str:
    return listing_media_variant_key(
        listing_id,
        media_id,
        variant_name,
        ext,
        pipeline_version=pipeline_version,
    )


def put_variants(
    storage: StorageService,
    *,
    listing_id: int,
    media_id: int,
    pipeline_version: str,
    variants: list[VariantOutput],
) -> list[StoredVariant]:
    stored: list[StoredVariant] = []
    for variant in variants:
        key = variant_storage_key(
            listing_id,
            media_id,
            variant.name,
            pipeline_version=pipeline_version,
        )
        url = storage.put_bytes(
            key,
            variant.content,
            content_type="image/jpeg",
        )
        stored.append(
            StoredVariant(
                name=variant.name,
                key=key,
                url=url,
                width=variant.width,
                height=variant.height,
            ),
        )
    return stored


def delete_pipeline_variants(
    storage: StorageService,
    *,
    listing_id: int,
    media_id: int,
    pipeline_version: str,
) -> None:
    for name in ("display", "feed", "thumb"):
        key = variant_storage_key(
            listing_id,
            media_id,
            name,
            pipeline_version=pipeline_version,
        )
        try:
            storage.delete_key(key)
        except Exception:
            pass
