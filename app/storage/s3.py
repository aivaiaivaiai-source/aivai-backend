"""S3-compatible object storage (AWS S3, Cloudflare R2, MinIO, …)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.exceptions import AppException
from app.storage.capabilities import ObjectHead, PresignedUpload
from app.storage.keys import assert_safe_storage_key

logger = logging.getLogger(__name__)


class S3CompatibleStorage:
    """
    Production adapter. Bucket is private-by-default (no public-read ACL).
    public_url() uses configured public base URL (CDN / custom domain / gateway).
    """

    def __init__(
        self,
        *,
        bucket: str,
        endpoint_url: str | None = None,
        region: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        public_base_url: str,
        addressing_style: str = "path",
        client: Any | None = None,
    ) -> None:
        if not bucket.strip():
            raise AppException("S3 bucket is not configured.", status_code=503)
        if not public_base_url.strip():
            raise AppException("S3 public base URL is not configured.", status_code=503)
        self._bucket = bucket.strip()
        base = public_base_url.strip()
        if not base.endswith("/"):
            base = f"{base}/"
        self._public_base = base
        if client is not None:
            self._client = client
        else:
            try:
                import boto3
                from botocore.config import Config as BotoConfig
            except ImportError as exc:
                raise AppException(
                    "boto3 is required for MEDIA_STORAGE_BACKEND=s3.",
                    status_code=503,
                ) from exc
            self._client = boto3.client(
                "s3",
                endpoint_url=endpoint_url or None,
                region_name=region or None,
                aws_access_key_id=access_key or None,
                aws_secret_access_key=secret_key or None,
                config=BotoConfig(
                    s3={"addressing_style": addressing_style},
                    signature_version="s3v4",
                ),
            )

    def put(self, key: str, data: bytes, *, content_type: str | None = None) -> None:
        safe = assert_safe_storage_key(key)
        extra: dict[str, str] = {}
        if content_type:
            extra["ContentType"] = content_type
        cache = self._cache_control_for_key(safe)
        if cache:
            extra["CacheControl"] = cache
        self._client.put_object(
            Bucket=self._bucket,
            Key=safe,
            Body=data,
            **extra,
        )

    @staticmethod
    def _cache_control_for_key(key: str) -> str | None:
        lower = key.lower()
        if "/original." in lower:
            return None
        if any(v in lower for v in ("/display.", "/feed.", "/thumb.")):
            return "public, max-age=31536000, immutable"
        return None

    def get(self, key: str) -> bytes:
        safe = assert_safe_storage_key(key)
        try:
            resp = self._client.get_object(Bucket=self._bucket, Key=safe)
        except Exception as exc:
            code = getattr(exc, "response", {}).get("Error", {}).get("Code", "")
            if code in {"404", "NoSuchKey", "NotFound"}:
                raise KeyError(key) from None
            logger.warning("s3_get_failed key=%s", safe)
            raise AppException("Failed to read media object.", status_code=503) from exc
        body = resp["Body"].read()
        return body if isinstance(body, (bytes, bytearray)) else bytes(body)

    def exists(self, key: str) -> bool:
        safe = assert_safe_storage_key(key)
        try:
            self._client.head_object(Bucket=self._bucket, Key=safe)
            return True
        except Exception as exc:
            code = getattr(exc, "response", {}).get("Error", {}).get("Code", "")
            if code in {"404", "NoSuchKey", "NotFound", "404 Not Found"}:
                return False
            status = getattr(exc, "response", {}).get("ResponseMetadata", {}).get(
                "HTTPStatusCode",
            )
            if status == 404:
                return False
            logger.warning("s3_head_failed key=%s", safe)
            raise AppException("Failed to check media object.", status_code=503) from exc

    def delete(self, key: str) -> None:
        safe = assert_safe_storage_key(key)
        try:
            self._client.delete_object(Bucket=self._bucket, Key=safe)
        except Exception:
            logger.warning("s3_delete_failed key=%s", safe)

    def public_url(self, key: str) -> str:
        safe = assert_safe_storage_key(key)
        return f"{self._public_base}{safe}"

    def head_object(self, key: str) -> ObjectHead | None:
        safe = assert_safe_storage_key(key)
        try:
            resp = self._client.head_object(Bucket=self._bucket, Key=safe)
        except Exception as exc:
            code = getattr(exc, "response", {}).get("Error", {}).get("Code", "")
            if code in {"404", "NoSuchKey", "NotFound", "404 Not Found"}:
                return None
            status = getattr(exc, "response", {}).get("ResponseMetadata", {}).get(
                "HTTPStatusCode",
            )
            if status == 404:
                return None
            logger.warning("s3_head_failed key=%s", safe)
            raise AppException("Failed to head media object.", status_code=503) from exc
        length = int(resp.get("ContentLength") or 0)
        return ObjectHead(
            key=safe,
            content_length=length,
            content_type=resp.get("ContentType"),
            etag=resp.get("ETag"),
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
        params = {
            "Bucket": self._bucket,
            "Key": safe,
            "ContentType": content_type,
        }
        url = self._client.generate_presigned_url(
            "put_object",
            Params=params,
            ExpiresIn=ttl,
            HttpMethod="PUT",
        )
        expires_at = datetime.now(UTC) + timedelta(seconds=ttl)
        return PresignedUpload(
            method="PUT",
            url=url,
            headers={"Content-Type": content_type},
            expires_at=expires_at,
        )
