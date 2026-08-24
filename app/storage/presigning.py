"""Helpers for optional storage capabilities."""

from __future__ import annotations

from app.core.exceptions import AppException
from app.storage.base import ObjectStorage
from app.storage.capabilities import HeadableStorage, PresigningStorage


def as_presigning(backend: ObjectStorage) -> PresigningStorage:
    if not isinstance(backend, PresigningStorage):
        raise AppException(
            "Direct upload requires S3-compatible presigned PUT support.",
            status_code=503,
        )
    return backend


def as_headable(backend: ObjectStorage) -> HeadableStorage:
    if not isinstance(backend, HeadableStorage):
        raise AppException("Storage backend does not support HEAD metadata.", status_code=503)
    return backend
