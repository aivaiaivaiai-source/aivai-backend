"""Resolver catalog snapshot — bounded immutable view over live PostgreSQL SoT."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.category_field import CategoryCoreField
from app.models.category_filter import CategoryFilter
from app.repositories.category_alias_repository import CategoryAliasRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.category_rule_repository import CategoryRuleRepository
from app.seeds.transport_canonical import RETIRED_TRANSPORT_SLUGS
from app.services.category_snapshot import (
    CategoryIntelligenceSnapshot,
    CategorySnapshotProvider,
    CategorySnapshotRow,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RoutabilityMetadata:
    routable: bool
    schema_ready: bool
    filter_ready: bool


@dataclass(frozen=True)
class ResolverCategoryNode:
    id: int
    slug: str
    name: str
    parent_id: int | None
    parent_slug: str | None
    depth: int
    path_slugs: tuple[str, ...]
    path_names: tuple[str, ...]
    entity_type: str | None
    is_active: bool
    routable: bool
    schema_ready: bool
    filter_ready: bool


@dataclass
class ResolverCatalogSnapshot:
    version_hash: str
    locale: str
    nodes_by_slug: dict[str, ResolverCategoryNode] = field(default_factory=dict)
    nodes_by_id: dict[int, ResolverCategoryNode] = field(default_factory=dict)
    children_by_parent_id: dict[int, list[int]] = field(default_factory=dict)
    intelligence: CategoryIntelligenceSnapshot | None = None

    def get(self, slug: str) -> ResolverCategoryNode | None:
        return self.nodes_by_slug.get(slug)

    def path_for(self, slug: str) -> list[ResolverCategoryNode]:
        node = self.get(slug)
        if node is None:
            return []
        return [self.nodes_by_slug[s] for s in node.path_slugs if s in self.nodes_by_slug]

    def descendants(self, slug: str) -> list[ResolverCategoryNode]:
        root = self.get(slug)
        if root is None:
            return []
        out: list[ResolverCategoryNode] = []
        stack = list(self.children_by_parent_id.get(root.id, []))
        while stack:
            cid = stack.pop()
            node = self.nodes_by_id.get(cid)
            if node is None:
                continue
            out.append(node)
            stack.extend(self.children_by_parent_id.get(cid, []))
        return out


class ResolverCatalogSnapshotBuilder:
    """Build resolver snapshot from CategorySnapshotProvider + readiness counts."""

    def __init__(
        self,
        session: AsyncSession,
        snapshot_provider: CategorySnapshotProvider,
        *,
        locale: str,
    ) -> None:
        self._session = session
        self._provider = snapshot_provider
        self._locale = locale

    async def build(self) -> ResolverCatalogSnapshot:
        intelligence = await self._provider.get()
        core_counts = await self._field_counts(CategoryCoreField)
        filter_counts = await self._field_counts(CategoryFilter)

        nodes_by_slug: dict[str, ResolverCategoryNode] = {}
        nodes_by_id: dict[int, ResolverCategoryNode] = {}
        children_by_parent_id: dict[int, list[int]] = {}

        for slug, row in intelligence.categories_by_slug.items():
            if slug in RETIRED_TRANSPORT_SLUGS:
                continue
            if not row.is_active:
                continue
            path_slugs, path_names, depth = self._build_path(row, intelligence)
            if not self._valid_parent_chain(path_slugs, intelligence):
                continue
            core_n = core_counts.get(row.id, 0)
            filter_n = filter_counts.get(row.id, 0)
            meta = RoutabilityMetadata(
                routable=True,
                schema_ready=core_n > 0,
                filter_ready=filter_n > 0,
            )
            node = ResolverCategoryNode(
                id=row.id,
                slug=row.slug,
                name=row.name,
                parent_id=row.parent_id,
                parent_slug=row.parent_slug,
                depth=depth,
                path_slugs=path_slugs,
                path_names=path_names,
                entity_type=self._entity_type(row, intelligence),
                is_active=True,
                routable=meta.routable,
                schema_ready=meta.schema_ready,
                filter_ready=meta.filter_ready,
            )
            nodes_by_slug[slug] = node
            nodes_by_id[row.id] = node
            if row.parent_id is not None:
                children_by_parent_id.setdefault(row.parent_id, []).append(row.id)

        version_hash = _compute_version_hash(nodes_by_id)
        return ResolverCatalogSnapshot(
            version_hash=version_hash,
            locale=self._locale,
            nodes_by_slug=nodes_by_slug,
            nodes_by_id=nodes_by_id,
            children_by_parent_id=children_by_parent_id,
            intelligence=intelligence,
        )

    async def _field_counts(self, model: type) -> dict[int, int]:
        stmt = select(model.category_id, func.count()).group_by(model.category_id)
        rows = (await self._session.execute(stmt)).all()
        return {int(cat_id): int(count) for cat_id, count in rows}

    @staticmethod
    def _entity_type(row: CategorySnapshotRow, snap: CategoryIntelligenceSnapshot) -> str | None:
        full = snap.categories_by_id.get(row.id)
        return None

    @staticmethod
    def _build_path(
        row: CategorySnapshotRow,
        snap: CategoryIntelligenceSnapshot,
    ) -> tuple[tuple[str, ...], tuple[str, ...], int]:
        slugs: list[str] = [row.slug]
        names: list[str] = [row.name]
        current = row
        depth = 0
        seen: set[int] = {row.id}
        while current.parent_id is not None:
            parent = snap.categories_by_id.get(current.parent_id)
            if parent is None or parent.id in seen:
                break
            slugs.insert(0, parent.slug)
            names.insert(0, parent.name)
            seen.add(parent.id)
            current = parent
            depth += 1
        return tuple(slugs), tuple(names), depth

    @staticmethod
    def _valid_parent_chain(path_slugs: tuple[str, ...], snap: CategoryIntelligenceSnapshot) -> bool:
        for slug in path_slugs:
            row = snap.categories_by_slug.get(slug)
            if row is None or not row.is_active or slug in RETIRED_TRANSPORT_SLUGS:
                return False
        return True


def _compute_version_hash(nodes_by_id: dict[int, ResolverCategoryNode]) -> str:
    parts = sorted(f"{n.id}:{n.slug}" for n in nodes_by_id.values())
    payload = "|".join(parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:32]


async def build_resolver_catalog_snapshot(
    session: AsyncSession,
    category_repository: CategoryRepository,
    alias_repository: CategoryAliasRepository,
    routing_rule_repository: CategoryRuleRepository,
    moderation_rule_repository: CategoryRuleRepository,
    vehicle_alias_repository,
    *,
    locale: str,
) -> ResolverCatalogSnapshot:
    provider = CategorySnapshotProvider(
        category_repository,
        alias_repository,
        routing_rule_repository,
        moderation_rule_repository,
        vehicle_alias_repository,
        locale=locale,
    )
    builder = ResolverCatalogSnapshotBuilder(session, provider, locale=locale)
    return await builder.build()
