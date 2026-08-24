from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.core.exceptions import AppException
from app.services.storage_service import StorageService
from app.storage.keys import (
    assert_safe_storage_key,
    listing_media_variant_key,
    listing_original_key,
)
from app.storage.local import LocalDiskStorage
from app.storage.memory import InMemoryObjectStorage
from app.storage.s3 import S3CompatibleStorage
from app.schemas.media import MediaRead


JPEG_MIN = b"\xff\xd8\xff" + b"\x00" * 16


def test_assert_safe_storage_key_rejects_traversal() -> None:
    with pytest.raises(AppException):
        assert_safe_storage_key("../etc/passwd")
    with pytest.raises(AppException):
        assert_safe_storage_key("/absolute/path")
    with pytest.raises(AppException):
        assert_safe_storage_key("media/../secret")
    with pytest.raises(AppException):
        assert_safe_storage_key("media\\..\\secret")


def test_listing_original_key_format() -> None:
    assert listing_original_key(12, 34, ".jpg") == "media/12/34/original.jpg"
    assert listing_media_variant_key(12, 34, "thumb", "png") == "media/12/34/thumb.png"


def test_local_disk_put_get_exists_delete(tmp_path: Path) -> None:
    store = LocalDiskStorage(tmp_path, public_base_url="/media/")
    key = "media/1/2/original.jpg"
    store.put(key, JPEG_MIN, content_type="image/jpeg")
    assert store.exists(key) is True
    assert store.get(key) == JPEG_MIN
    assert store.public_url(key) == "/media/media/1/2/original.jpg"
    store.delete(key)
    assert store.exists(key) is False
    store.delete(key)  # idempotent


def test_local_disk_rejects_path_escape(tmp_path: Path) -> None:
    store = LocalDiskStorage(tmp_path)
    with pytest.raises(AppException):
        store.put("../x.jpg", JPEG_MIN)


def test_put_retry_is_idempotent(tmp_path: Path) -> None:
    store = LocalDiskStorage(tmp_path)
    key = "media/1/2/original.jpg"
    store.put(key, JPEG_MIN)
    store.put(key, JPEG_MIN + b"\x01")
    assert store.get(key) == JPEG_MIN + b"\x01"


def test_storage_service_uses_backend_not_direct_write(tmp_path: Path) -> None:
    settings = SimpleNamespace(
        MEDIA_ROOT=str(tmp_path),
        MEDIA_URL="/media/",
        MEDIA_STORAGE_BACKEND="local",
    )
    backend = InMemoryObjectStorage()
    svc = StorageService(settings, backend=backend)  # type: ignore[arg-type]
    url = svc.put_bytes("media/9/9/original.jpg", JPEG_MIN, content_type="image/jpeg")
    assert url == "/media/media/9/9/original.jpg"
    assert backend.exists("media/9/9/original.jpg")
    assert not (tmp_path / "media" / "9" / "9" / "original.jpg").exists()


def test_storage_service_save_image_opaque_key(tmp_path: Path) -> None:
    settings = SimpleNamespace(MEDIA_ROOT=str(tmp_path), MEDIA_URL="/media/")
    backend = InMemoryObjectStorage()
    svc = StorageService(settings, backend=backend)  # type: ignore[arg-type]
    url = svc.save_image(JPEG_MIN, "image/jpeg")
    assert url.startswith("/media/uploads/")
    assert url.endswith(".jpg")


def test_media_read_hides_storage_key() -> None:
    assert "original_storage_key" not in MediaRead.model_fields
    assert "error_message" not in MediaRead.model_fields


def test_s3_adapter_with_mock_client() -> None:
    client = MagicMock()
    client.get_object.return_value = {"Body": MagicMock(read=MagicMock(return_value=JPEG_MIN))}
    store = S3CompatibleStorage(
        bucket="aivai-media",
        public_base_url="https://cdn.example.com/",
        client=client,
    )
    store.put("media/1/2/original.jpg", JPEG_MIN, content_type="image/jpeg")
    client.put_object.assert_called_once()
    kwargs = client.put_object.call_args.kwargs
    assert kwargs["Bucket"] == "aivai-media"
    assert kwargs["Key"] == "media/1/2/original.jpg"
    assert kwargs["Body"] == JPEG_MIN
    assert "ACL" not in kwargs  # private-by-default
    assert store.public_url("media/1/2/original.jpg") == (
        "https://cdn.example.com/media/1/2/original.jpg"
    )
    assert store.get("media/1/2/original.jpg") == JPEG_MIN
    store.delete("media/1/2/original.jpg")
    client.delete_object.assert_called_once()


def test_s3_exists_404() -> None:
    class _Err(Exception):
        response = {"Error": {"Code": "404"}, "ResponseMetadata": {"HTTPStatusCode": 404}}

    client = MagicMock()
    client.head_object.side_effect = _Err()
    store = S3CompatibleStorage(
        bucket="b",
        public_base_url="https://cdn.example.com/",
        client=client,
    )
    assert store.exists("media/1/2/original.jpg") is False
