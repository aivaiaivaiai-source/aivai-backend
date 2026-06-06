from __future__ import annotations

from app.schemas.category_intelligence import VehicleResolveResult
from app.services.category_snapshot import CategoryIntelligenceSnapshot, CategorySnapshotProvider
from app.services.category_text import alias_lookup_variants, normalize_alias_keys


class VehicleDictionaryService:
    """Resolve colloquial vehicle names via in-memory snapshot (no per-query DB scan)."""

    def __init__(self, snapshot_provider: CategorySnapshotProvider) -> None:
        self._snapshots = snapshot_provider

    async def resolve_from_text(self, text: str) -> VehicleResolveResult:
        snap = await self._snapshots.get()
        for key in alias_lookup_variants(text):
            hit = snap.vehicle_aliases_by_compact.get(key) or snap.vehicle_aliases_by_spaced.get(key)
            if hit is not None:
                return VehicleResolveResult(
                    brand_id=hit.brand_id,
                    brand_name=hit.brand_name,
                    model_id=hit.model_id,
                    model_name=hit.model_name,
                    matched_alias=hit.alias,
                )

        spaced, compact = normalize_alias_keys(text)
        normalized_joined = compact
        best_len = 0
        best: VehicleResolveResult | None = None
        for alias_compact, hit in snap.vehicle_aliases_by_compact.items():
            if len(alias_compact) >= 3 and alias_compact in normalized_joined:
                if len(alias_compact) > best_len:
                    best_len = len(alias_compact)
                    best = VehicleResolveResult(
                        brand_id=hit.brand_id,
                        brand_name=hit.brand_name,
                        model_id=hit.model_id,
                        model_name=hit.model_name,
                        matched_alias=hit.alias,
                    )
        return best or VehicleResolveResult()
