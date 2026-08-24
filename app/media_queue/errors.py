"""Media job processing errors."""

from __future__ import annotations


class MediaJobError(Exception):
    """Base media job error."""

    error_code: str = "MEDIA_JOB_ERROR"
    retryable: bool = False

    def __init__(self, message: str, *, error_code: str | None = None) -> None:
        super().__init__(message)
        if error_code:
            self.error_code = error_code


class RetryableMediaJobError(MediaJobError):
    retryable = True
    error_code = "MEDIA_JOB_RETRYABLE"


class PermanentMediaJobError(MediaJobError):
    retryable = False
    error_code = "MEDIA_JOB_PERMANENT"
