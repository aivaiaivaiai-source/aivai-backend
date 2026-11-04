"""SigLIP2 local visual evidence provider (LOCAL VISUAL EVIDENCE V0)."""

from __future__ import annotations

import logging
import time

from app.visual_evidence.calibration.decision_policy import (
    aggregate_multi_image_scores,
    apply_decision_policy,
    load_calibration_config,
)
from app.visual_evidence.calibration.prompt_utils import compute_prompt_hash
from app.visual_evidence.siglip2_runtime import (
    DEFAULT_PROMPT_SET,
    PROMPT_VERSION,
    get_siglip2_runtime,
)
from app.visual_evidence.types import (
    VisualConceptObservation,
    VisualEvidenceMediaInput,
    VisualEvidenceOutput,
)

logger = logging.getLogger(__name__)


class SigLIP2VisualEvidenceProvider:
    """Object-centric zero-shot visual evidence — NOT category classifier."""

    def __init__(self) -> None:
        self._runtime = get_siglip2_runtime()
        self._calibration = load_calibration_config()

    @property
    def model_version(self) -> str:
        return self._runtime.model_version

    @property
    def prompt_version(self) -> str:
        return PROMPT_VERSION

    @property
    def prompt_hash(self) -> str:
        return compute_prompt_hash(DEFAULT_PROMPT_SET)

    @property
    def calibration_version(self) -> str:
        return self._calibration.calibration_version

    async def infer(
        self,
        *,
        listing_id: int,
        media_inputs: list[VisualEvidenceMediaInput],
        max_images: int,
        load_image_bytes: callable,
    ) -> VisualEvidenceOutput:
        del listing_id
        ordered = sorted(media_inputs, key=lambda m: m.order)
        limit = max(1, min(max_images, len(ordered) or 1))
        selected = ordered[:limit]

        per_image_scores: list[dict[str, float]] = []
        concept_media: dict[str, set[int]] = {}
        inspected = 0

        t0 = time.perf_counter()
        for media in selected:
            try:
                blob = await load_image_bytes(media.storage_key)
            except Exception as exc:
                logger.warning(
                    "visual_evidence_image_load_failed media_id=%s err=%s",
                    media.media_id,
                    type(exc).__name__,
                )
                continue
            try:
                per_image = self._runtime.score_image_bytes(blob)
            except Exception as exc:
                logger.warning(
                    "visual_evidence_infer_failed media_id=%s err=%s",
                    media.media_id,
                    type(exc).__name__,
                )
                continue
            inspected += 1
            per_image_scores.append(per_image)
            for concept, score in per_image.items():
                if score >= self._calibration.min_evidence_score:
                    concept_media.setdefault(concept, set()).add(media.media_id)

        processing_ms = int((time.perf_counter() - t0) * 1000)
        if inspected == 0:
            return VisualEvidenceOutput(
                no_match=True,
                images_inspected=0,
                notes="no_images_scored",
            )

        aggregated = aggregate_multi_image_scores(
            per_image_scores,
            config=self._calibration,
        )
        decision = apply_decision_policy(aggregated, config=self._calibration)

        if decision.no_match:
            return VisualEvidenceOutput(
                no_match=True,
                images_inspected=inspected,
                notes=(
                    f"processed_ms={processing_ms}; "
                    f"calibration={self._calibration.calibration_version}; "
                    f"{decision.notes}"
                ),
            )

        observations: list[VisualConceptObservation] = []
        for concept, score in zip(
            decision.accepted_concepts,
            decision.evidence_scores,
            strict=True,
        ):
            media_ids = sorted(concept_media.get(concept, set()))
            if not media_ids:
                continue
            observations.append(
                VisualConceptObservation(
                    concept=concept,
                    score=score,
                    evidence_media_ids=media_ids,
                )
            )

        if not observations:
            return VisualEvidenceOutput(
                no_match=True,
                images_inspected=inspected,
                notes=f"processed_ms={processing_ms}; no_media_backing",
            )

        observations.sort(key=lambda o: o.score, reverse=True)
        top_concepts = [o.concept for o in observations[:5]]
        return VisualEvidenceOutput(
            observations=observations,
            top_concepts=top_concepts,
            images_inspected=inspected,
            no_match=False,
            notes=(
                f"processed_ms={processing_ms}; "
                f"calibration={self._calibration.calibration_version}; "
                f"policy={self._calibration.policy_family}"
            ),
        )
