from __future__ import annotations

from fastapi import HTTPException

from app.models.job_create_intent import VALID_JOB_CREATE_INTENTS
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
from app.seeds.jobs_create_fields import is_jobs_create_intent_required
from app.services.category_dialogue_service import CategoryDialogueService
from app.services.category_moderation_service import CategoryModerationService
from app.services.category_routing_service import CategoryRoutingService
from app.services.category_snapshot import CategorySnapshotProvider
from app.services.currency_policy import default_currency_for
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

    async def get_category_intelligence(
        self,
        category_id: int,
        *,
        create_intent: str | None = None,
        deal_type: str | None = None,
    ) -> CategoryIntelligenceRead | None:
        row = await self._categories.get_with_intelligence(category_id)
        if row is None:
            return None

        intent = (create_intent or "").strip() or None
        if intent is not None and intent not in VALID_JOB_CREATE_INTENTS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid create intent '{intent}'. Expected hiring|job_seeking.",
            )

        jobs_requires_intent = is_jobs_create_intent_required(row.slug)
        if jobs_requires_intent and intent is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "create intent is required for Jobs V2 categories "
                    "(pass ?intent=hiring|job_seeking)."
                ),
            )
        if intent is not None and not jobs_requires_intent:
            # Other L1s ignore intent; do not fail.
            intent = None

        if intent is None:
            core = [
                f
                for f in row.core_fields
                if getattr(f, "create_intent", None) is None
            ]
        else:
            core = [
                f
                for f in row.core_fields
                if getattr(f, "create_intent", None) == intent
            ]

        core = sorted(core, key=lambda f: (f.sort_order, f.id))
        optional = sorted(row.optional_fields, key=lambda f: (f.sort_order, f.id))
        # Jobs Search V2: intent-scoped filters; other L1s keep search_intent=''.
        if intent is not None:
            filters = [
                f
                for f in row.filters
                if getattr(f, "search_intent", "") in (intent, "")
            ]
        else:
            filters = [
                f
                for f in row.filters
                if getattr(f, "search_intent", "") == ""
            ]
        filters = sorted(filters, key=lambda f: (f.sort_order, f.id))
        entity = getattr(row.entity_type, "value", None) or str(row.entity_type)
        default_cur = default_currency_for(
            row.slug,
            deal_type=deal_type,
            entity_type=entity,
        )
        return CategoryIntelligenceRead(
            id=row.id,
            name=row.name,
            slug=row.slug,
            parent_id=row.parent_id,
            entity_type=row.entity_type,
            description=row.description,
            requires_city=row.requires_city,
            ai_dialogue_hint=row.ai_dialogue_hint,
            create_intent=intent,
            default_currency=default_cur.value,
            core_fields=core,
            optional_fields=optional,
            filters=filters,
        )
