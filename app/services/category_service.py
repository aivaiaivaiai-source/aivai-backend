from __future__ import annotations

from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryTreeNode


class CategoryService:
    def __init__(self, category_repository: CategoryRepository) -> None:
        self._categories = category_repository

    async def _node_from_category(self, row: Category) -> CategoryTreeNode:
        children_rows = await self._categories.get_children_by_parent_id(row.id)
        children = [await self._node_from_category(c) for c in children_rows]
        return CategoryTreeNode(
            id=row.id,
            name=row.name,
            slug=row.slug,
            parent_id=row.parent_id,
            entity_type=row.entity_type.value if row.entity_type else None,
            children=children,
        )

    async def get_category_tree(self) -> list[CategoryTreeNode]:
        # TODO(v2): Recursive loading per node is fine for v1-scale trees; when the
        # category hierarchy grows, replace with a single-query strategy (PostgreSQL
        # recursive CTE) or a denormalized materialized path / nested-set model to
        # avoid N round-trips per depth level.
        roots = await self._categories.get_root_categories()
        return [await self._node_from_category(r) for r in roots]
