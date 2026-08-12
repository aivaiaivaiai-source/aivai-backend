from __future__ import annotations

import asyncio
import logging
import re
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from app.core.ai_global_rules import GLOBAL_AI_RULES
from app.core.config import get_settings
from app.core.locale import DEFAULT_LOCALE, normalize_locale
from app.models.category_enums import CategoryRuleType
from app.repositories.category_alias_repository import CategoryAliasRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.category_rule_repository import CategoryRuleRepository
from app.repositories.vehicle_repository import VehicleAliasRepository
from app.services.category_text import normalize_alias_compact, normalize_text

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CategorySnapshotRow:
    id: int
    slug: str
    name: str
    parent_id: int | None
    parent_slug: str | None
    is_active: bool
    requires_city: bool


@dataclass(frozen=True)
class CategoryAliasSnapshot:
    category_id: int
    category_slug: str
    category_name: str
    alias: str
    weight: int
    locale: str


@dataclass(frozen=True)
class CompiledRoutingRule:
    id: int
    name: str
    pattern: re.Pattern[str]
    target_category_slug: str
    priority: int


@dataclass(frozen=True)
class CompiledModerationRule:
    id: int
    name: str
    pattern: re.Pattern[str]
    action: str
    rule_type: str
    priority: int


@dataclass(frozen=True)
class VehicleAliasSnapshot:
    alias: str
    alias_compact: str
    brand_id: int | None
    brand_slug: str | None
    brand_name: str | None
    model_id: int | None
    model_name: str | None
    locale: str


@dataclass
class CategoryIntelligenceSnapshot:
    categories_by_slug: dict[str, CategorySnapshotRow] = field(default_factory=dict)
    categories_by_id: dict[int, CategorySnapshotRow] = field(default_factory=dict)
    aliases_by_spaced: dict[str, CategoryAliasSnapshot] = field(default_factory=dict)
    aliases_by_compact: dict[str, CategoryAliasSnapshot] = field(default_factory=dict)
    routing_rules: list[CompiledRoutingRule] = field(default_factory=list)
    moderation_rules: list[CompiledModerationRule] = field(default_factory=list)
    guardrail_rules: list[CompiledModerationRule] = field(default_factory=list)
    vehicle_aliases_by_compact: dict[str, VehicleAliasSnapshot] = field(default_factory=dict)
    vehicle_aliases_by_spaced: dict[str, VehicleAliasSnapshot] = field(default_factory=dict)
    root_category_slugs: list[str] = field(default_factory=list)
    locale: str = DEFAULT_LOCALE.value


@dataclass
class _ProcessCacheEntry:
    snapshot: CategoryIntelligenceSnapshot
    loaded_at: float


class _ProcessSnapshotCache:
    """Process-wide TTL cache shared across HTTP requests (no Redis)."""

    def __init__(self) -> None:
        self._entries: dict[str, _ProcessCacheEntry] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._meta_lock = asyncio.Lock()

    async def _lock_for(self, locale: str) -> asyncio.Lock:
        async with self._meta_lock:
            lock = self._locks.get(locale)
            if lock is None:
                lock = asyncio.Lock()
                self._locks[locale] = lock
            return lock

    def invalidate(self, locale: str | None = None) -> None:
        if locale is None:
            self._entries.clear()
            return
        self._entries.pop(locale, None)

    async def get(
        self,
        locale: str,
        ttl_seconds: float,
        loader: Callable[[], Awaitable[CategoryIntelligenceSnapshot]],
    ) -> CategoryIntelligenceSnapshot:
        now = time.monotonic()
        entry = self._entries.get(locale)
        if entry is not None and (now - entry.loaded_at) < ttl_seconds:
            return entry.snapshot

        lock = await self._lock_for(locale)
        async with lock:
            now = time.monotonic()
            entry = self._entries.get(locale)
            if entry is not None and (now - entry.loaded_at) < ttl_seconds:
                return entry.snapshot

            try:
                snapshot = await loader()
            except Exception:
                stale = self._entries.get(locale)
                if stale is not None:
                    logger.warning(
                        "Category snapshot reload failed; serving stale cache "
                        "for locale=%s",
                        locale,
                        exc_info=True,
                    )
                    return stale.snapshot
                raise

            self._entries[locale] = _ProcessCacheEntry(
                snapshot=snapshot,
                loaded_at=time.monotonic(),
            )
            return snapshot


_PROCESS_SNAPSHOT_CACHE = _ProcessSnapshotCache()


def reset_process_snapshot_cache() -> None:
    """Clear all process-level snapshot entries (tests / admin hooks)."""
    _PROCESS_SNAPSHOT_CACHE.invalidate()


class CategorySnapshotProvider:
    """Loads routing/moderation dictionaries with a shared process-level TTL cache."""

    def __init__(
        self,
        category_repository: CategoryRepository,
        alias_repository: CategoryAliasRepository,
        routing_rule_repository: CategoryRuleRepository,
        moderation_rule_repository: CategoryRuleRepository,
        vehicle_alias_repository: VehicleAliasRepository,
        *,
        locale: str | None = None,
    ) -> None:
        self._categories = category_repository
        self._aliases = alias_repository
        self._routing_rules = routing_rule_repository
        self._moderation_rules = moderation_rule_repository
        self._vehicle_aliases = vehicle_alias_repository
        self._locale = normalize_locale(locale)

    def invalidate(self) -> None:
        _PROCESS_SNAPSHOT_CACHE.invalidate(self._locale)

    async def get(self) -> CategoryIntelligenceSnapshot:
        ttl = float(get_settings().CATEGORY_SNAPSHOT_TTL_SECONDS)
        return await _PROCESS_SNAPSHOT_CACHE.get(
            self._locale,
            ttl,
            self._load,
        )

    async def _load(self) -> CategoryIntelligenceSnapshot:
        snap = CategoryIntelligenceSnapshot(locale=self._locale)

        all_categories = await self._categories.get_all_active()
        slug_to_row: dict[str, CategorySnapshotRow] = {}
        for cat in all_categories:
            parent_slug = None
            if cat.parent_id is not None:
                parent = next((c for c in all_categories if c.id == cat.parent_id), None)
                parent_slug = parent.slug if parent else None
            row = CategorySnapshotRow(
                id=cat.id,
                slug=cat.slug,
                name=cat.name,
                parent_id=cat.parent_id,
                parent_slug=parent_slug,
                is_active=cat.is_active,
                requires_city=cat.requires_city,
            )
            slug_to_row[cat.slug] = row
            snap.categories_by_id[cat.id] = row
            if cat.parent_id is None:
                snap.root_category_slugs.append(cat.slug)

        snap.categories_by_slug = slug_to_row

        for alias_row in await self._aliases.list_enabled(self._locale):
            cat = snap.categories_by_id.get(alias_row.category_id)
            if cat is None or not cat.is_active:
                continue
            entry = CategoryAliasSnapshot(
                category_id=cat.id,
                category_slug=cat.slug,
                category_name=cat.name,
                alias=alias_row.alias,
                weight=alias_row.weight,
                locale=alias_row.locale,
            )
            spaced = alias_row.alias_normalized
            compact = alias_row.alias_compact
            self._register_alias(snap, spaced, compact, entry)

        for rule in await self._routing_rules.get_active_rules(rule_type=CategoryRuleType.routing):
            if not rule.pattern or not rule.config:
                continue
            target = rule.config.get("target_category_slug")
            if not target:
                continue
            try:
                compiled = re.compile(rule.pattern, re.IGNORECASE)
            except re.error:
                continue
            snap.routing_rules.append(
                CompiledRoutingRule(
                    id=rule.id,
                    name=rule.name,
                    pattern=compiled,
                    target_category_slug=str(target),
                    priority=rule.priority,
                )
            )
        snap.routing_rules.sort(key=lambda r: r.priority)

        for rule in await self._moderation_rules.get_active_rules(
            rule_type=CategoryRuleType.moderation
        ):
            if not rule.pattern:
                continue
            try:
                compiled = re.compile(rule.pattern, re.IGNORECASE)
            except re.error:
                continue
            snap.moderation_rules.append(
                CompiledModerationRule(
                    id=rule.id,
                    name=rule.name,
                    pattern=compiled,
                    action=rule.action.value,
                    rule_type=rule.rule_type.value,
                    priority=rule.priority,
                )
            )

        for rule in await self._moderation_rules.get_active_rules(
            rule_type=CategoryRuleType.guardrail
        ):
            if not rule.pattern:
                continue
            try:
                compiled = re.compile(rule.pattern, re.IGNORECASE)
            except re.error:
                continue
            snap.guardrail_rules.append(
                CompiledModerationRule(
                    id=rule.id,
                    name=rule.name,
                    pattern=compiled,
                    action=rule.action.value,
                    rule_type=rule.rule_type.value,
                    priority=rule.priority,
                )
            )

        for va in await self._vehicle_aliases.list_enabled(self._locale):
            if va.brand is not None and not va.brand.is_enabled:
                continue
            if va.model is not None and not va.model.is_enabled:
                continue
            brand = va.brand
            model = va.model
            entry = VehicleAliasSnapshot(
                alias=va.alias,
                alias_compact=va.alias_compact,
                brand_id=brand.id if brand else None,
                brand_slug=brand.slug if brand else None,
                brand_name=brand.name if brand else None,
                model_id=model.id if model else None,
                model_name=model.name if model else None,
                locale=va.locale,
            )
            snap.vehicle_aliases_by_compact[va.alias_compact] = entry
            snap.vehicle_aliases_by_spaced[va.alias_normalized] = entry

        return snap

    @staticmethod
    def _register_alias(
        snap: CategoryIntelligenceSnapshot,
        spaced: str,
        compact: str,
        entry: CategoryAliasSnapshot,
    ) -> None:
        existing = snap.aliases_by_compact.get(compact)
        if existing is None or entry.weight >= existing.weight:
            snap.aliases_by_compact[compact] = entry
            snap.aliases_by_spaced[spaced] = entry


def apply_routing_confidence_policy(
    *,
    confidence: float,
    mode: str,
    category_id: int | None,
    category_slug: str | None,
    category_name: str | None,
    parent_slug: str | None,
    reason: str | None,
) -> tuple[str, int | None, str | None, str | None, str | None, float]:
    """
    Downgrade aggressive auto-routing when confidence is low.
    Returns (mode, category_id, slug, name, parent_slug, adjusted_confidence).
    """
    rules = GLOBAL_AI_RULES
    if category_id is None:
        return mode, category_id, category_slug, category_name, parent_slug, confidence

    if confidence >= rules.auto_route_min_confidence:
        return mode, category_id, category_slug, category_name, parent_slug, confidence

    if confidence >= rules.clarification_below_confidence:
        return (
            "clarification",
            None,
            category_slug,
            category_name,
            parent_slug,
            confidence,
        )

    return (
        "suggestion",
        None,
        category_slug,
        category_name,
        parent_slug,
        confidence,
    )
