"""In-memory object storage for unit tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.storage.capabilities import ObjectHead, PresignedUpload
from app.storage.keys import assert_safe_storage_key


class InMemoryObjectStorage:
    def __init__(self, *, public_base_url: str = "/media/") -> None:
        self._objects: dict[str, bytes] = {}
        self._content_types: dict[str, str | None] = {}
        base = public_base_url.strip() or "/media/"
        if not base.endswith("/"):
            base = f"{base}/"
        self._public_base = base

    def put(self, key: str, data: bytes, *, content_type: str | None = None) -> None:
        safe = assert_safe_storage_key(key)
        self._objects[safe] = data
        self._content_types[safe] = content_type

    def get(self, key: str) -> bytes:
        safe = assert_safe_storage_key(key)
        if safe not in self._objects:
            raise KeyError(key)
        return self._objects[safe]

    def exists(self, key: str) -> bool:
        return assert_safe_storage_key(key) in self._objects

    def delete(self, key: str) -> None:
        safe = assert_safe_storage_key(key)
        self._objects.pop(safe, None)
        self._content_types.pop(safe, None)

    def public_url(self, key: str) -> str:
        safe = assert_safe_storage_key(key)
        return f"{self._public_base}{safe}"

    def head_object(self, key: str) -> ObjectHead | None:
        safe = assert_safe_storage_key(key)
        if safe not in self._objects:
            return None
        return ObjectHead(
            key=safe,
            content_length=len(self._objects[safe]),
            content_type=self._content_types.get(safe),
            etag=None,
        )

    def presign_put(
        self,
        key: str,
        *,
        content_type: str,
        content_length: int,
        expires_seconds: int,
    ) -> PresignedUpload:
        safe = assert_safe_storage_key(key)
        ttl = max(60, min(expires_seconds, 3600))
        token = f"mem-{safe}-{ttl}"
        return PresignedUpload(
            method="PUT",
            url=f"/test-presign/{token}",
            headers={"Content-Type": content_type, "X-Test-Key": safe},
            expires_at=datetime.now(UTC) + timedelta(seconds=ttl),
        )
