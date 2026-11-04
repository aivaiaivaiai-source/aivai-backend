"""Visual evidence provider protocol — swap SigLIP / future models."""

from __future__ import annotations

from typing import Protocol

from app.visual_evidence.types import VisualEvidenceMediaInput, VisualEvidenceOutput


class VisualEvidenceProvider(Protocol):
    @property
    def model_version(self) -> str:
        ...

    @property
    def prompt_version(self) -> str:
        ...

    @property
    def prompt_hash(self) -> str:
        ...

    async def infer(
        self,
        *,
        listing_id: int,
        media_inputs: list[VisualEvidenceMediaInput],
        max_images: int,
        load_image_bytes: callable,
    ) -> VisualEvidenceOutput:
        ...
