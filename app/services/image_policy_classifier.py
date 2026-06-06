from __future__ import annotations

import re
from typing import Protocol, runtime_checkable

from app.models.image_moderation_enums import ImageModerationVerdict
from app.schemas.image_moderation import ImageClassificationInput, ImageClassificationResult

_REJECT_PATTERNS: tuple[tuple[re.Pattern[str], str, str], ...] = (
    (re.compile(r"(porn|nude|nsfw|sexual)", re.I), "PORNOGRAPHY", "explicit or sexual content"),
    (re.compile(r"(violence|gore|blood|corpse|brutal)", re.I), "VIOLENCE", "violence or gore"),
    (re.compile(r"(drug|narcotic|weed|cocaine|heroin)", re.I), "DRUGS", "prohibited substances"),
    (re.compile(r"(nazi|extremist|terror|isis|swastika)", re.I), "EXTREMISM", "extremist content"),
)

_QUEUE_PATTERNS: tuple[tuple[re.Pattern[str], str, str], ...] = (
    (re.compile(r"(passport|id[_-]?card|driver|license|document)", re.I), "SENSITIVE_DOCUMENT", "identity document"),
    (re.compile(r"(bank[_-]?card|credit[_-]?card|debit|iban)", re.I), "SENSITIVE_DOCUMENT", "payment card"),
)


@runtime_checkable
class ImagePolicyClassifier(Protocol):
    """Pluggable vision policy backend (OpenAI Vision, Rekognition, custom model, etc.)."""

    async def classify(self, payload: ImageClassificationInput) -> ImageClassificationResult: ...


class StubImagePolicyClassifier:
    """
    Deterministic stub for development and tests.

    Uses optional upload filename hints only — no pixel analysis, OCR, or external APIs.
    """

    provider = "stub"

    async def classify(self, payload: ImageClassificationInput) -> ImageClassificationResult:
        hint = (payload.source_name or "").lower()
        for pattern, code, detail in _REJECT_PATTERNS:
            if pattern.search(hint):
                return ImageClassificationResult(
                    verdict=ImageModerationVerdict.REJECT,
                    reason_code=code,
                    reason_detail=detail,
                    provider=self.provider,
                )
        for pattern, code, detail in _QUEUE_PATTERNS:
            if pattern.search(hint):
                return ImageClassificationResult(
                    verdict=ImageModerationVerdict.MODERATION_QUEUE,
                    reason_code=code,
                    reason_detail=detail,
                    provider=self.provider,
                )
        return ImageClassificationResult(
            verdict=ImageModerationVerdict.ALLOW,
            reason_code=None,
            reason_detail=None,
            provider=self.provider,
        )
