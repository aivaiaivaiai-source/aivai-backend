"""Category Resolver orchestration — shadow mode, no auto-assign."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.category_resolver.catalog_snapshot import build_resolver_catalog_snapshot
from app.category_resolver.constants import RESOLVER_VERSION
from app.category_resolver.engine import CategoryResolverEngine
from app.core.config import Settings, get_settings
from app.core.exceptions import AppException, EntityNotFoundError, OwnershipError
from app.core.locale import DEFAULT_LOCALE
from app.media_classification.fingerprint import media_set_fingerprint
from app.models.category_resolver_enums import CategoryResolverStatus
from app.models.listing import Listing
from app.models.listing_user_intent_enums import ListingUserIntentStatus
from app.models.visual_evidence_enums import VisualEvidenceStatus
from app.repositories.category_alias_repository import CategoryAliasRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.category_resolver_repository import CategoryResolverRepository
from app.repositories.category_routing_rule_repository import CategoryRoutingRuleRepository
from app.repositories.category_moderation_rule_repository import CategoryModerationRuleRepository
from app.repositories.listing_repository import ListingRepository
from app.repositories.listing_user_intent_repository import ListingUserIntentRepository
from app.repositories.media_repository import MediaRepository
from app.repositories.visual_evidence_repository import VisualEvidenceRepository
from app.repositories.vehicle_repository import VehicleAliasRepository
from app.models.listing_category_resolver import (
    ListingCategoryResolverResult,
    build_resolver_idempotency_key,
)
from app.schemas.category_resolver import (
    CategoryResolverAlternative,
    CategoryResolverPathNode,
    CategoryResolverRead,
    CategoryResolverResolveResponse,
)
from app.services.category_draft_enrichment_service import CategoryDraftEnrichmentService
from app.services.category_routing_service import CategoryRoutingService
from app.services.category_snapshot import CategorySnapshotProvider
from app.user_intent.fingerprint import hybrid_resolver_input_fingerprint

logger = logging.getLogger(__name__)


class CategoryResolverService:
    """
    Hybrid resolver + optional draft enrichment (3C-4).

    When draft enrichment is enabled, may populate listing.category_id on drafts.
    AUTO_ASSIGN remains a separate, disabled finalization flag.
    """

    def __init__(
        self,
        session: AsyncSession,
        settings: Settings | None = None,
    ) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._listings = ListingRepository(session)
        self._intents = ListingUserIntentRepository(session)
        self._media = MediaRepository(session)
        self._visual = VisualEvidenceRepository(session)
        self._resolver_repo = CategoryResolverRepository(session)
        self._categories = CategoryRepository(session)

    @property
    def feature_enabled(self) -> bool:
        return bool(self._settings.CATEGORY_RESOLVER_ENABLED)

    @property
    def draft_enrichment_enabled(self) -> bool:
        return bool(
            self.feature_enabled
            and self._settings.CATEGORY_RESOLVER_DRAFT_ENRICHMENT_ENABLED
        )

    @property
    def auto_assign_enabled(self) -> bool:
        return bool(self._settings.CATEGORY_RESOLVER_AUTO_ASSIGN_ENABLED)

    @staticmethod
    def _ensure_owner(listing: Listing, actor_user_id: int) -> None:
        if listing.owner_id is None or listing.owner_id != actor_user_id:
            raise OwnershipError("You cannot access another user's listing.")

    async def get_result(
        self,
        listing_id: int,
        *,
        actor_user_id: int,
    ) -> CategoryResolverRead:
        listing = await self._listings.get_by_id(listing_id)
        if listing is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)
        self._ensure_owner(listing, actor_user_id)

        if not self.feature_enabled:
            return self._empty_read(listing_id, listing=listing)

        row = await self._resolver_repo.get_latest_for_listing(listing_id)
        if row is None:
            return self._empty_read(listing_id, listing=listing)
        return self._to_read(listing_id, row, listing=listing)

    async def enrich_draft_from_latest(
        self,
        listing_id: int,
        *,
        actor_user_id: int,
    ) -> CategoryResolverRead:
        """Idempotent: resolve if needed, then apply draft enrichment when allowed."""
        resolve_response = await self.resolve_for_listing(
            listing_id,
            actor_user_id=actor_user_id,
        )
        return resolve_response.result

    async def resolve_for_listing(
        self,
        listing_id: int,
        *,
        actor_user_id: int,
    ) -> CategoryResolverResolveResponse:
        if not self.feature_enabled:
            raise AppException("Category resolver is disabled.", status_code=404)
        if self.auto_assign_enabled:
            logger.warning(
                "category_resolver_auto_assign_enabled_but_shadow_only listing_id=%s",
                listing_id,
            )

        listing = await self._listings.get_by_id(listing_id)
        if listing is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)
        self._ensure_owner(listing, actor_user_id)

        intent_row = await self._intents.get_by_listing_id(listing_id)
        if intent_row is None or intent_row.intent_status != ListingUserIntentStatus.provided:
            raise AppException(
                "User intent must be provided before category resolution.",
                status_code=400,
            )
        raw_intent = (intent_row.raw_intent_text or "").strip()
        if not raw_intent:
            raise AppException("User intent text is empty.", status_code=400)

        media_fp = await self._current_media_fingerprint(listing_id)
        visual_row, visual_concepts = await self._load_visual_evidence(listing_id, media_fp)

        catalog = await self._build_catalog_snapshot()
        input_fp = hybrid_resolver_input_fingerprint(
            media_set_fingerprint=media_fp,
            intent_fingerprint=intent_row.intent_fingerprint,
            catalog_snapshot_hash=catalog.version_hash,
            resolver_version=RESOLVER_VERSION,
        )
        idempotency_key = build_resolver_idempotency_key(
            listing_id, input_fp, RESOLVER_VERSION
        )

        existing = await self._resolver_repo.get_by_idempotency_key(idempotency_key)
        if existing is not None:
            enrichment = await self._maybe_apply_draft_enrichment(
                listing=listing,
                row=existing,
                input_fp=input_fp,
                actor_user_id=actor_user_id,
            )
            await self._session.commit()
            refreshed = await self._listings.get_by_id(listing_id)
            return CategoryResolverResolveResponse(
                result=self._to_read(
                    listing_id,
                    existing,
                    listing=refreshed or listing,
                    enrichment=enrichment,
                ),
                created=False,
            )

        # Mark prior results stale when input revision changes.
        latest = await self._resolver_repo.get_latest_for_listing(listing_id)
        if latest is not None and latest.input_fingerprint != input_fp:
            if latest.status != CategoryResolverStatus.stale:
                latest.status = CategoryResolverStatus.stale

        engine = CategoryResolverEngine(self._routing_service())
        output = await engine.resolve(
            raw_intent_text=raw_intent,
            catalog=catalog,
            visual_concepts=visual_concepts,
        )

        now = datetime.now(UTC)
        row = ListingCategoryResolverResult(
            listing_id=listing_id,
            idempotency_key=idempotency_key,
            input_fingerprint=input_fp,
            catalog_snapshot_hash=catalog.version_hash,
            intent_fingerprint=intent_row.intent_fingerprint,
            intent_version=intent_row.intent_version,
            media_set_fingerprint=media_fp,
            visual_evidence_id=visual_row.id if visual_row else None,
            visual_model_version=visual_row.model_version if visual_row else None,
            visual_prompt_version=visual_row.prompt_version if visual_row else None,
            visual_calibration_version=visual_row.calibration_version if visual_row else None,
            resolver_version=RESOLVER_VERSION,
            status=output.status,
            suggested_category_id=output.suggested_category_id,
            suggested_slug=output.suggested_slug,
            confidence=output.confidence,
            needs_confirmation=output.needs_confirmation,
            candidate_path_json=output.candidate_path,
            alternatives_json=output.alternatives,
            evidence_summary_json=output.evidence_summary,
            intent_semantics_json=output.intent_semantics,
            completed_at=now,
        )
        await self._resolver_repo.create(row)

        enrichment = await self._maybe_apply_draft_enrichment(
            listing=listing,
            row=row,
            input_fp=input_fp,
            actor_user_id=actor_user_id,
        )

        logger.info(
            "category_resolver_shadow listing_id=%s status=%s suggested=%s fp=%s enriched=%s",
            listing_id,
            output.status.value,
            output.suggested_slug,
            input_fp[:8],
            enrichment.applied,
        )
        refreshed_listing = await self._listings.get_by_id(listing_id)
        await self._session.commit()
        return CategoryResolverResolveResponse(
            result=self._to_read(
                listing_id,
                row,
                listing=refreshed_listing or listing,
                enrichment=enrichment,
            ),
            created=True,
        )

    def _routing_service(self) -> CategoryRoutingService:
        locale = DEFAULT_LOCALE.value
        alias_repo = CategoryAliasRepository(self._session)
        routing_repo = CategoryRoutingRuleRepository(self._session)
        mod_repo = CategoryModerationRuleRepository(self._session)
        vehicle_repo = VehicleAliasRepository(self._session)
        provider = CategorySnapshotProvider(
            self._categories,
            alias_repo,
            routing_repo,
            mod_repo,
            vehicle_repo,
            locale=locale,
        )
        return CategoryRoutingService(provider)

    async def _build_catalog_snapshot(self):
        locale = DEFAULT_LOCALE.value
        return await build_resolver_catalog_snapshot(
            self._session,
            self._categories,
            CategoryAliasRepository(self._session),
            CategoryRoutingRuleRepository(self._session),
            CategoryModerationRuleRepository(self._session),
            VehicleAliasRepository(self._session),
            locale=locale,
        )

    async def _current_media_fingerprint(self, listing_id: int) -> str:
        rows = await self._media.list_by_listing(listing_id)
        ids = [
            m.id
            for m in sorted(rows, key=lambda r: (r.order, r.id))
            if not getattr(m, "is_placeholder", False) and m.original_storage_key
        ]
        return media_set_fingerprint(ids)

    async def _load_visual_evidence(
        self,
        listing_id: int,
        media_fp: str,
    ) -> tuple[object | None, tuple[str, ...]]:
        if not self._settings.MEDIA_VISUAL_EVIDENCE_ENABLED:
            return None, ()
        row = await self._visual.get_for_listing_fingerprint(listing_id, media_fp)
        if row is None:
            row = await self._visual.get_latest_for_listing(listing_id)
        if row is None or row.status not in (
            VisualEvidenceStatus.ready,
            VisualEvidenceStatus.no_match,
        ):
            return row, ()
        if row.status == VisualEvidenceStatus.no_match:
            return row, ()
        concepts = tuple(str(c) for c in (row.top_concepts_json or []) if c)
        return row, concepts

    async def _maybe_apply_draft_enrichment(
        self,
        *,
        listing: Listing,
        row: ListingCategoryResolverResult,
        input_fp: str,
        actor_user_id: int,
    ):
        from app.services.category_draft_enrichment_service import (
            CategoryDraftEnrichmentService,
            DraftEnrichmentResult,
        )

        if not self.draft_enrichment_enabled:
            return DraftEnrichmentResult(applied=False, reason="disabled")
        enricher = CategoryDraftEnrichmentService(self._session, self._settings)
        return await enricher.try_apply_from_resolver_result(
            listing,
            row,
            input_fingerprint=input_fp,
            actor_user_id=actor_user_id,
        )

    def _empty_read(
        self,
        listing_id: int,
        *,
        listing: Listing | None = None,
    ) -> CategoryResolverRead:
        selection_source = (
            getattr(listing, "category_selection_source", None) if listing else None
        )
        source = selection_source.value if selection_source else None
        return CategoryResolverRead(
            listing_id=listing_id,
            status=CategoryResolverStatus.no_match.value,
            feature_enabled=self.feature_enabled,
            auto_assign_enabled=self.auto_assign_enabled,
            draft_enrichment_enabled=self.draft_enrichment_enabled,
            category_selection_source=source,
            enrichment_category_id=listing.category_id if listing else None,
        )

    def _to_read(
        self,
        listing_id: int,
        row: ListingCategoryResolverResult,
        *,
        listing: Listing | None = None,
        enrichment=None,
    ) -> CategoryResolverRead:
        from app.category_resolver.draft_enrichment import enrichment_category_id

        path = [
            CategoryResolverPathNode(**node)
            for node in (row.candidate_path_json or [])
            if isinstance(node, dict)
        ]
        alts = [
            CategoryResolverAlternative(
                slug=str(a.get("slug", "")),
                score=float(a.get("score", 0)),
                reasons=list(a.get("reasons") or []),
            )
            for a in (row.alternatives_json or [])
            if isinstance(a, dict)
        ]
        applied = bool(enrichment and enrichment.applied)
        selection_source = (
            getattr(listing, "category_selection_source", None) if listing else None
        )
        source = selection_source.value if selection_source else None
        enrich_cat = listing.category_id if listing and applied else enrichment_category_id(row)
        if listing and selection_source and listing.category_id:
            enrich_cat = listing.category_id
        return CategoryResolverRead(
            listing_id=listing_id,
            status=row.status.value,
            suggested_category_id=row.suggested_category_id,
            suggested_slug=row.suggested_slug,
            confidence=row.confidence,
            needs_confirmation=bool(row.needs_confirmation),
            candidate_path=path,
            alternatives=alts,
            evidence_summary=dict(row.evidence_summary_json or {}),
            intent_semantics=dict(row.intent_semantics_json or {}),
            input_fingerprint=row.input_fingerprint,
            catalog_snapshot_hash=row.catalog_snapshot_hash,
            resolver_version=row.resolver_version,
            feature_enabled=self.feature_enabled,
            auto_assign_enabled=self.auto_assign_enabled,
            draft_enrichment_enabled=self.draft_enrichment_enabled,
            draft_enrichment_applied=applied,
            enrichment_category_id=enrich_cat,
            category_selection_source=source,
            updated_at=row.updated_at,
        )
