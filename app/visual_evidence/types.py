"""Visual evidence result types — object-centric, NOT category assignment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class VisualEvidenceMediaInput:
    media_id: int
    order: int
    storage_key: str


@dataclass(frozen=True)
class VisualConceptObservation:
    concept: str
    score: float
    evidence_media_ids: list[int]

    def to_json(self) -> dict[str, Any]:
        return {
            "concept": self.concept,
            "score": round(float(self.score), 6),
            "evidence_media_ids": list(self.evidence_media_ids),
        }

    @staticmethod
    def from_json(raw: dict[str, Any]) -> VisualConceptObservation:
        ids_raw = raw.get("evidence_media_ids") or []
        media_ids = [int(x) for x in ids_raw if x is not None]
        return VisualConceptObservation(
            concept=str(raw.get("concept") or ""),
            score=float(raw.get("score") or 0),
            evidence_media_ids=media_ids,
        )


@dataclass
class VisualEvidenceOutput:
    observations: list[VisualConceptObservation] = field(default_factory=list)
    top_concepts: list[str] = field(default_factory=list)
    images_inspected: int = 0
    no_match: bool = False
    notes: str | None = None
