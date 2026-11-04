"""Deterministic stub when SigLIP unavailable — tests and safe fallback."""

from __future__ import annotations

from app.visual_evidence.types import (
    VisualEvidenceMediaInput,
    VisualEvidenceOutput,
)

STUB_MODEL_VERSION = "stub-visual-evidence-v0"
STUB_PROMPT_VERSION = "visual-evidence-prompts-v1"
STUB_PROMPT_HASH = "stub000000000000"
STUB_CALIBRATION_VERSION = "stub-calibration"


class StubVisualEvidenceProvider:
    @property
    def model_version(self) -> str:
        return STUB_MODEL_VERSION

    @property
    def prompt_version(self) -> str:
        return STUB_PROMPT_VERSION

    @property
    def prompt_hash(self) -> str:
        return STUB_PROMPT_HASH

    @property
    def calibration_version(self) -> str:
        return STUB_CALIBRATION_VERSION

    async def infer(
        self,
        *,
        listing_id: int,
        media_inputs: list[VisualEvidenceMediaInput],
        max_images: int,
        load_image_bytes: callable,
    ) -> VisualEvidenceOutput:
        del listing_id, load_image_bytes
        ordered = sorted(media_inputs, key=lambda m: m.order)[: max(1, max_images)]
        if not ordered:
            return VisualEvidenceOutput(no_match=True, images_inspected=0, notes="stub:empty")
        return VisualEvidenceOutput(
            no_match=True,
            images_inspected=len(ordered),
            notes="stub:no_inference",
        )
