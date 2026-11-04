"""Deterministic development classifier — NOT production vision AI.

Capability (honest):
- Catalog-bound only (never invents categories).
- Multi-photo → one decision.
- Early-stop when scripted/high confidence.
- Optional weak storage-key fixtures for tests/dev wiring.
- Does NOT use RT-DETR as category authority.
- Does NOT call paid external APIs.

Replace via MediaCategoryClassifier when a real vision model is chosen.
"""

from __future__ import annotations

from app.media_classification.types import (
    AllowedCategory,
    CategoryCandidate,
    ClassificationMediaInput,
    ClassifierOutput,
)


class DevelopmentDeterministicClassifier:
    """Wiring + tests classifier. Not a marketplace vision model."""

    def __init__(self, *, version: str = "dev-deterministic-v1") -> None:
        self._version = version

    @property
    def version(self) -> str:
        return self._version

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
        del listing_id, medium_confidence_threshold
        by_slug = {c.slug: c for c in allowed_categories}
        ordered = sorted(media_inputs, key=lambda m: m.order)
        limit = max(1, min(max_images, len(ordered) or 1))
        inspected: list[ClassificationMediaInput] = []
        votes: dict[str, float] = {}

        for media in ordered[:limit]:
            inspected.append(media)
            slug = self._hint_slug(media)
            if slug and slug in by_slug:
                votes[slug] = votes.get(slug, 0.0) + 1.0
                # Early confidence: single clear cover signal is enough.
                if votes[slug] >= 1.0 and high_confidence_threshold <= 0.95:
                    break
            # Ambiguous path: continue to next photo when no signal.
            elif len(inspected) < min(3, limit):
                continue
            else:
                break

        if not votes:
            return ClassifierOutput(
                candidates=[],
                no_match=True,
                images_inspected=len(inspected),
                evidence_media_ids=[m.media_id for m in inspected],
                notes="dev_classifier:no_signal",
            )

        total = sum(votes.values())
        ranked = sorted(votes.items(), key=lambda kv: kv[1], reverse=True)
        candidates: list[CategoryCandidate] = []
        for slug, score in ranked[:3]:
            cat = by_slug[slug]
            candidates.append(
                CategoryCandidate(
                    category_id=cat.category_id,
                    category_slug=cat.slug,
                    category_name=cat.name,
                    hierarchy_path=cat.hierarchy_path,
                    confidence=score / total,
                )
            )

        return ClassifierOutput(
            candidates=candidates,
            no_match=False,
            images_inspected=len(inspected),
            evidence_media_ids=[m.media_id for m in inspected],
            notes="dev_classifier:fixture_or_hint",
        )

    def _hint_slug(self, media: ClassificationMediaInput) -> str | None:
        hint = (media.content_hint or "").strip().lower()
        key = (media.storage_key or "").strip().lower()
        blob = f"{hint} {key}"
        # Explicit test fixtures only — not general vision.
        if "fixture-car-sale" in blob or "aivai-class=transport-car-sale" in blob:
            return "transport-car-sale"
        if "fixture-auto-parts" in blob or "aivai-class=transport-auto-parts" in blob:
            return "transport-auto-parts"
        if "fixture-phones" in blob or "aivai-class=electronics-phones" in blob:
            return "electronics-phones"
        return None
