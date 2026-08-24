"""Optional object-storage capabilities (presigned upload, HEAD metadata)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class ObjectHead:
    key: str
    content_length: int
    content_type: str | None
    etag: str | None = None


@dataclass(frozen=True)
class PresignedUpload:
    method: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    expires_at: datetime | None = None


@runtime_checkable
class PresigningStorage(Protocol):
    def presign_put(
        self,
        key: str,
        *,
        content_type: str,
        content_length: int,
        expires_seconds: int,
    ) -> PresignedUpload: ...

    def head_object(self, key: str) -> ObjectHead | None: ...


@runtime_checkable
class HeadableStorage(Protocol):
    def head_object(self, key: str) -> ObjectHead | None: ...
