"""Object storage abstraction (Stage 2) — no business logic."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ObjectStorage(Protocol):
    """Backend-agnostic blob store. Keys are logical; never filesystem paths."""

    def put(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str | None = None,
    ) -> None:
        """Idempotent upsert of bytes at key."""

    def get(self, key: str) -> bytes:
        """Return object bytes; raise KeyError if missing."""

    def exists(self, key: str) -> bool:
        """True if object exists at key."""

    def delete(self, key: str) -> None:
        """Idempotent delete — missing key is not an error."""

    def public_url(self, key: str) -> str:
        """Stable public or app-facing URL for this key (may be relative in local/dev)."""
