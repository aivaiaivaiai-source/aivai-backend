"""MediaCategoryClassifier protocol — swap models without changing API/Flutter."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.media_classification.types import (
    AllowedCategory,
    ClassificationMediaInput,
    ClassifierOutput,
)


@runtime_checkable
class MediaCategoryClassifier(Protocol):
    """
    classify(listing_context, media_inputs, allowed_categories) → ClassifierOutput

    Implementations MUST only reference category_ids from allowed_categories.
    Must not invent new slugs/categories.
    """

    @property
    def version(self) -> str:
        """Classifier model/version string used in idempotency keys."""

    async def classify(
        self,
        *,
        listing_id: int,
        media_inputs: list[ClassificationMediaInput],
        allowed_categories: list[AllowedCategory],
        max_images: int,
        high_confidence_threshold: float,
        medium_confidence_threshold: float,
    ) -> ClassifierOutput:
        ...
