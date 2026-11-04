from __future__ import annotations

from app.schemas.category_intelligence import VehicleResolveResult
from app.services.category_snapshot import CategorySnapshotProvider
from app.services.category_text import alias_lookup_variants, normalize_alias_keys
from app.services.vehicle_execution import (
    APPROVED_MODEL_EXECUTIONS,
    EXECUTION_PLACEMENT_SLUG,
    detect_execution_from_text,
)


def _slugify_name(name: str | None) -> str:
    return (name or "").strip().lower().replace(" ", "-")


class VehicleDictionaryService:
    """Resolve colloquial vehicle names via in-memory snapshot (no per-query DB scan)."""

    def __init__(self, snapshot_provider: CategorySnapshotProvider) -> None:
        self._snapshots = snapshot_provider

    def _enrich(
        self,
        result: VehicleResolveResult,
        *,
        text: str,
        brand_name: str | None,
        model_name: str | None,
    ) -> VehicleResolveResult:
        brand_slug = _slugify_name(brand_name)
        model_slug = _slugify_name(model_name)
        allowed = APPROVED_MODEL_EXECUTIONS.get((brand_slug, model_slug))
        if not allowed:
            return result

        detected = detect_execution_from_text(text)
        requires_choice = len(allowed) > 1
        if detected is not None and detected in allowed:
            return result.model_copy(
                update={
                    "vehicle_execution": detected.value,
                    "execution_resolved": True,
                    "suggested_placement_slug": EXECUTION_PLACEMENT_SLUG[detected],
                    "requires_execution_choice": requires_choice,
                }
            )
        if len(allowed) == 1:
            only = allowed[0]
            return result.model_copy(
                update={
                    "vehicle_execution": only.value,
                    "execution_resolved": True,
                    "suggested_placement_slug": EXECUTION_PLACEMENT_SLUG[only],
                    "requires_execution_choice": False,
                }
            )
        # Dual model without explicit cargo/passenger signal — do not guess.
        return result.model_copy(
            update={
                "vehicle_execution": None,
                "execution_resolved": False,
                "suggested_placement_slug": None,
                "requires_execution_choice": True,
            }
        )

    async def resolve_from_text(self, text: str) -> VehicleResolveResult:
        snap = await self._snapshots.get()
        for key in alias_lookup_variants(text):
            hit = snap.vehicle_aliases_by_compact.get(key) or snap.vehicle_aliases_by_spaced.get(key)
            if hit is not None:
                base = VehicleResolveResult(
                    brand_id=hit.brand_id,
                    brand_name=hit.brand_name,
                    model_id=hit.model_id,
                    model_name=hit.model_name,
                    matched_alias=hit.alias,
                )
                return self._enrich(
                    base,
                    text=text,
                    brand_name=hit.brand_name,
                    model_name=hit.model_name,
                )

        spaced, compact = normalize_alias_keys(text)
        normalized_joined = compact
        best_len = 0
        best: VehicleResolveResult | None = None
        best_brand: str | None = None
        best_model: str | None = None
        for alias_compact, hit in snap.vehicle_aliases_by_compact.items():
            if len(alias_compact) >= 3 and alias_compact in normalized_joined:
                if len(alias_compact) > best_len:
                    best_len = len(alias_compact)
                    best_brand = hit.brand_name
                    best_model = hit.model_name
                    best = VehicleResolveResult(
                        brand_id=hit.brand_id,
                        brand_name=hit.brand_name,
                        model_id=hit.model_id,
                        model_name=hit.model_name,
                        matched_alias=hit.alias,
                    )
        if best is None:
            return VehicleResolveResult()
        return self._enrich(
            best,
            text=text,
            brand_name=best_brand,
            model_name=best_model,
        )
