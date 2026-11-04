"""Classification result types — catalog-bound only."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AllowedCategory:
    category_id: int
    slug: str
    name: str
    parent_id: int | None
    hierarchy_path: str  # e.g. "Транспорт → Продажа авто"


@dataclass(frozen=True)
class ClassificationMediaInput:
    media_id: int
    order: int
    storage_key: str
    """Bounded inference bytes may be loaded by orchestrator; classifier sees optional hint."""
    content_hint: str | None = None


@dataclass(frozen=True)
class CategoryCandidate:
    category_id: int
    category_slug: str
    category_name: str
    hierarchy_path: str
    confidence: float

    def to_json(self) -> dict[str, Any]:
        return {
            "category_id": self.category_id,
            "category_slug": self.category_slug,
            "category_name": self.category_name,
            "hierarchy_path": self.hierarchy_path,
            "confidence": round(float(self.confidence), 6),
        }

    @staticmethod
    def from_json(raw: dict[str, Any]) -> CategoryCandidate:
        return CategoryCandidate(
            category_id=int(raw["category_id"]),
            category_slug=str(raw["category_slug"]),
            category_name=str(raw["category_name"]),
            hierarchy_path=str(raw.get("hierarchy_path") or ""),
            confidence=float(raw.get("confidence") or 0),
        )


@dataclass
class ClassifierOutput:
    """Raw classifier decision before persistence."""

    candidates: list[CategoryCandidate] = field(default_factory=list)
    no_match: bool = False
    images_inspected: int = 0
    evidence_media_ids: list[int] = field(default_factory=list)
    notes: str | None = None
    # Reserved for future attribute extraction foundation.
    suggested_attributes: dict[str, Any] | None = None
