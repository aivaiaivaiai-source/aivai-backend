"""Frozen category catalog snapshot loader."""

from __future__ import annotations

import json
from pathlib import Path

from benchmarks.media_classification.adapters.base import BenchCategory
from benchmarks.media_classification.runner.hashing import sha256_file, sha256_json


class CatalogSnapshot:
    def __init__(
        self,
        *,
        version: str,
        categories: list[BenchCategory],
        raw: dict,
        path: Path | None = None,
    ) -> None:
        self.version = version
        self.categories = categories
        self.raw = raw
        self.path = path
        self._by_slug = {c.slug: c for c in categories}
        self._by_id = {c.category_id: c for c in categories}

    @property
    def content_hash(self) -> str:
        if self.path is not None and self.path.is_file():
            return sha256_file(self.path)
        return sha256_json(self.raw)

    def get_by_slug(self, slug: str) -> BenchCategory | None:
        return self._by_slug.get(slug)

    def get_by_id(self, category_id: int) -> BenchCategory | None:
        return self._by_id.get(category_id)

    def active_categories(self) -> list[BenchCategory]:
        return [c for c in self.categories if c.is_active]

    def hierarchy_slugs(self, slug: str) -> tuple[str, ...]:
        cat = self._by_slug.get(slug)
        if cat is None:
            return ()
        chain: list[str] = []
        cur: BenchCategory | None = cat
        guard = 0
        while cur is not None and guard < 16:
            chain.append(cur.slug)
            if cur.parent_id is None:
                break
            cur = self._by_id.get(cur.parent_id)
            guard += 1
        chain.reverse()
        return tuple(chain)


def load_catalog(path: Path) -> CatalogSnapshot:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "categories" not in raw:
        raise ValueError(f"Invalid catalog snapshot: {path}")
    version = str(raw.get("catalog_version") or raw.get("version") or "unknown")
    rows = raw["categories"]
    if not isinstance(rows, list) or not rows:
        raise ValueError("catalog categories must be a non-empty list")

    by_id: dict[int, dict] = {}
    for row in rows:
        cid = int(row["id"])
        by_id[cid] = row

    def path_for(cid: int) -> tuple[str, ...]:
        names: list[str] = []
        cur = by_id.get(cid)
        guard = 0
        while cur is not None and guard < 16:
            names.append(str(cur["name"]))
            parent = cur.get("parent_id")
            if parent is None:
                break
            cur = by_id.get(int(parent))
            guard += 1
        names.reverse()
        return tuple(names)

    categories: list[BenchCategory] = []
    for row in rows:
        cid = int(row["id"])
        parent = row.get("parent_id")
        categories.append(
            BenchCategory(
                category_id=cid,
                slug=str(row["slug"]),
                name=str(row["name"]),
                parent_id=int(parent) if parent is not None else None,
                hierarchy_path=path_for(cid),
                is_active=bool(row.get("is_active", True)),
            )
        )
    return CatalogSnapshot(version=version, categories=categories, raw=raw, path=path)
