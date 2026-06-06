from __future__ import annotations

from app.repositories.category_alias_repository import CategoryAliasRepository
from app.repositories.category_moderation_rule_repository import CategoryModerationRuleRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.category_routing_rule_repository import CategoryRoutingRuleRepository
from app.repositories.vehicle_repository import VehicleAliasRepository
from app.schemas.category_intelligence import (
    CategoryDialogueRequest,
    CategoryDialogueResponse,
    CategoryIntelligenceRead,
    CategoryRoutingResult,
    VehicleResolveResult,
)
from app.services.category_dialogue_service import CategoryDialogueService
from app.services.category_moderation_service import CategoryModerationService
from app.services.category_routing_service import CategoryRoutingService
from app.services.category_snapshot import CategorySnapshotProvider
from app.services.vehicle_dictionary_service import VehicleDictionaryService


class CategoryIntelligenceService:
    """Facade for AI category routing, dialogue, vehicle dictionary, and moderation."""

    def __init__(
        self,
        category_repository: CategoryRepository,
        alias_repository: CategoryAliasRepository,
        routing_rule_repository: CategoryRoutingRuleRepository,
        moderation_rule_repository: CategoryModerationRuleRepository,
        vehicle_alias_repository: VehicleAliasRepository,
        *,
        locale: str | None = None,
    ) -> None:
        self._snapshot_provider = CategorySnapshotProvider(
            category_repository,
            alias_repository,
            routing_rule_repository,
            moderation_rule_repository,
            vehicle_alias_repository,
            locale=locale,
        )
        vehicle_dict = VehicleDictionaryService(self._snapshot_provider)
        self._routing = CategoryRoutingService(self._snapshot_provider)
        self._moderation = CategoryModerationService(self._snapshot_provider)
        self._dialogue = CategoryDialogueService(
            self._routing,
            self._moderation,
            category_repository,
        )
        self._categories = category_repository
        self._vehicles = vehicle_dict

    def invalidate_cache(self) -> None:
        """Call after admin/seed changes to refresh in-memory dictionaries."""
        self._snapshot_provider.invalidate()

    async def route_intent(self, text: str) -> CategoryRoutingResult:
        return await self._routing.route(text)

    async def dialogue(self, payload: CategoryDialogueRequest) -> CategoryDialogueResponse:
        return await self._dialogue.process(payload)

    async def resolve_vehicle(self, text: str) -> VehicleResolveResult:
        return await self._vehicles.resolve_from_text(text)

    async def get_category_intelligence(self, category_id: int) -> CategoryIntelligenceRead | None:
        row = await self._categories.get_with_intelligence(category_id)
        if row is None:
            return None
        return CategoryIntelligenceRead(
            id=row.id,
            name=row.name,
            slug=row.slug,
            parent_id=row.parent_id,
            entity_type=row.entity_type,
            description=row.description,
            requires_city=row.requires_city,
            ai_dialogue_hint=row.ai_dialogue_hint,
            core_fields=row.core_fields,
            optional_fields=row.optional_fields,
            filters=row.filters,
        )
