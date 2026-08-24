"""Local disk object storage — DEV / local backend only."""

from __future__ import annotations

from pathlib import Path

from app.core.exceptions import AppException
from app.storage.capabilities import ObjectHead
from app.storage.keys import assert_safe_storage_key


class LocalDiskStorage:
    def __init__(self, root: str | Path, *, public_base_url: str = "/media/") -> None:
        self._root = Path(root).resolve()
        self._root.mkdir(parents=True, exist_ok=True)
        base = public_base_url.strip() or "/media/"
        if not base.endswith("/"):
            base = f"{base}/"
        self._public_base = base

    def _resolve(self, key: str) -> Path:
        safe = assert_safe_storage_key(key)
        path = (self._root / safe).resolve()
        try:
            path.relative_to(self._root)
        except ValueError as exc:
            raise AppException("Invalid storage key.", status_code=400) from exc
        return path

    def put(self, key: str, data: bytes, *, content_type: str | None = None) -> None:
        del content_type  # local disk does not persist content-type metadata
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def get(self, key: str) -> bytes:
        path = self._resolve(key)
        if not path.is_file():
            raise KeyError(key)
        return path.read_bytes()

    def exists(self, key: str) -> bool:
        return self._resolve(key).is_file()

    def delete(self, key: str) -> None:
        path = self._resolve(key)
        if path.is_file():
            path.unlink()

    def public_url(self, key: str) -> str:
        safe = assert_safe_storage_key(key)
        return f"{self._public_base}{safe}"

    def head_object(self, key: str) -> ObjectHead | None:
        path = self._resolve(key)
        if not path.is_file():
            return None
        return ObjectHead(
            key=assert_safe_storage_key(key),
            content_length=path.stat().st_size,
            content_type=None,
            etag=None,
        )
