from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.ai_global_rules import GLOBAL_AI_RULES
from app.schemas.category_intelligence import CategoryRoutingResult
from app.services.category_snapshot import (
    CategoryAliasSnapshot,
    CategoryIntelligenceSnapshot,
    CategorySnapshotProvider,
    apply_routing_confidence_policy,
)
from app.services.category_text import alias_lookup_variants, normalize_text


@dataclass(frozen=True)
class _StaticRoute:
    patterns: tuple[re.Pattern[str], ...]
    category_slug: str
    reason: str
    confidence: float = 0.85


class CategoryRoutingService:
    """
    Intent → category mapping without LLM.
    Uses in-memory snapshot (aliases, routing rules) — no per-token DB hits.
    """

    _OUT_OF_DOMAIN = re.compile(
        r"(философ|личн(?:ая|ой)\s+жизн|психолог|политик|религи|анекдот|погода\s+завтра)",
        re.IGNORECASE,
    )

    _STATIC_ROUTES: tuple[_StaticRoute, ...] = (
        _StaticRoute(
            (re.compile(r"привез|перевоз|достав|эвакуатор|грузоперевоз", re.I),),
            "services-transport",
            "service action (transport/delivery)",
            0.9,
        ),
        _StaticRoute(
            (
                re.compile(r"прода(?:ю|ть)|продам|sale\b", re.I),
                re.compile(r"коров|бык|телен|коз|овц|лошад|собак|кот|кошк|птиц", re.I),
            ),
            "animals-livestock",
            "live animal listing",
            0.88,
        ),
        _StaticRoute(
            (re.compile(r"молок|мясо|ферм|сельхоз|продукт", re.I),),
            "food-agri",
            "food / farm products",
            0.82,
        ),
        _StaticRoute(
            (re.compile(r"ремонт.*(?:айфон|iphone|телефон|ноутбук)", re.I),),
            "services-repair",
            "repair service for electronics",
            0.9,
        ),
        _StaticRoute(
            (
                re.compile(r"прода(?:ю|ть)|продам", re.I),
                re.compile(r"айфон|iphone|телефон|ноутбук|планшет|техник", re.I),
            ),
            "electronics-phones",
            "electronics object listing",
            0.88,
        ),
        _StaticRoute(
            (
                re.compile(r"прода(?:ю|ть)|продам", re.I),
                re.compile(r"камаз|газель|авто|машин|bmw|toyota|mercedes", re.I),
            ),
            "transport-cars",
            "vehicle object listing",
            0.86,
        ),
        _StaticRoute(
            (re.compile(r"квартир|дом|недвижим|участок|аренд.*кварт", re.I),),
            "real-estate-sale",
            "real estate",
            0.84,
        ),
        _StaticRoute(
            (re.compile(r"ваканс|работ|зарплат|ищу\s+работ", re.I),),
            "jobs-vacancies",
            "job listing",
            0.83,
        ),
    )

    def __init__(self, snapshot_provider: CategorySnapshotProvider) -> None:
        self._snapshots = snapshot_provider

    async def route(self, text: str) -> CategoryRoutingResult:
        raw = text.strip()
        if not raw:
            return CategoryRoutingResult(mode="empty", confidence=0.0, reason="empty text")

        if self._OUT_OF_DOMAIN.search(raw):
            return CategoryRoutingResult(
                mode="out_of_domain",
                confidence=0.95,
                reason="not marketplace domain",
            )

        snap = await self._snapshots.get()
        normalized = normalize_text(raw)
        extracted = self._extract_hints(raw, normalized, snap)

        candidates: list[tuple[float, str, str, CategorySnapshotRow | None]] = []

        for route in self._STATIC_ROUTES:
            if all(p.search(raw) for p in route.patterns):
                cat = snap.categories_by_slug.get(route.category_slug)
                if cat is not None:
                    candidates.append((route.confidence, "heuristic", route.reason, cat))

        for rule in snap.routing_rules:
            if rule.pattern.search(normalized):
                cat = snap.categories_by_slug.get(rule.target_category_slug)
                if cat is not None:
                    candidates.append((0.8, "rule", rule.name, cat))

        alias_hit = self._resolve_alias(snap, normalized, raw)
        if alias_hit is not None:
            conf = min(0.75, alias_hit.weight / 100.0)
            cat = snap.categories_by_id.get(alias_hit.category_id)
            if cat is not None:
                candidates.append((conf, "alias", f"alias:{alias_hit.alias}", cat))

        if not candidates:
            for root_slug in snap.root_category_slugs:
                cat = snap.categories_by_slug.get(root_slug)
                if cat is None:
                    continue
                if cat.slug.replace("-", " ") in normalized or normalize_text(cat.name) in normalized:
                    candidates.append(
                        (0.55, "suggestion", "root category name match — needs confirmation", cat)
                    )

        if not candidates:
            return CategoryRoutingResult(
                mode="suggestion",
                confidence=0.2,
                reason="category unknown — admin approval or clarification",
                extracted=extracted,
            )

        if len(candidates) >= 2:
            top_conf = max(c[0] for c in candidates)
            close = [c for c in candidates if abs(c[0] - top_conf) < 0.08]
            if len(close) >= 2:
                best = max(close, key=lambda c: c[0])
                cat = best[3]
                mode, cid, slug, name, parent, conf = apply_routing_confidence_policy(
                    confidence=best[0] * 0.9,
                    mode="clarification",
                    category_id=cat.id if cat else None,
                    category_slug=cat.slug if cat else None,
                    category_name=cat.name if cat else None,
                    parent_slug=cat.parent_slug if cat else None,
                    reason="ambiguous: multiple category signals",
                )
                return CategoryRoutingResult(
                    category_id=cid,
                    category_slug=slug,
                    category_name=name,
                    parent_slug=parent,
                    confidence=conf,
                    mode=mode,
                    reason="ambiguous: multiple category signals",
                    extracted=extracted,
                )

        best = max(candidates, key=lambda c: c[0])
        conf, mode, reason, cat = best[0], best[1], best[2], best[3]
        if cat is None:
            return CategoryRoutingResult(
                mode="suggestion",
                confidence=0.2,
                reason=reason,
                extracted=extracted,
            )

        mode, cid, slug, name, parent, conf = apply_routing_confidence_policy(
            confidence=conf,
            mode=mode,
            category_id=cat.id,
            category_slug=cat.slug,
            category_name=cat.name,
            parent_slug=cat.parent_slug,
            reason=reason,
        )

        return CategoryRoutingResult(
            category_id=cid,
            category_slug=slug,
            category_name=name,
            parent_slug=parent,
            confidence=conf,
            mode=mode,
            reason=reason,
            extracted=extracted,
        )

    def _resolve_alias(
        self,
        snap: CategoryIntelligenceSnapshot,
        normalized: str,
        raw: str,
    ) -> CategoryAliasSnapshot | None:
        for key in alias_lookup_variants(raw):
            hit = snap.aliases_by_compact.get(key) or snap.aliases_by_spaced.get(key)
            if hit is not None:
                return hit
        for token in normalized.split():
            if len(token) < 3:
                continue
            hit = snap.aliases_by_compact.get(token) or snap.aliases_by_spaced.get(token)
            if hit is not None:
                return hit
        return None

    def _extract_hints(
        self,
        raw: str,
        normalized: str,
        snap: CategoryIntelligenceSnapshot,
    ) -> dict[str, object]:
        extracted: dict[str, object] = {}

        for key in alias_lookup_variants(raw):
            veh = snap.vehicle_aliases_by_compact.get(key) or snap.vehicle_aliases_by_spaced.get(key)
            if veh is not None:
                if veh.brand_name:
                    extracted["vehicle_brand"] = veh.brand_name
                if veh.model_name:
                    extracted["vehicle_model"] = veh.model_name
                break

        if "vehicle_brand" not in extracted:
            for compact, veh in snap.vehicle_aliases_by_compact.items():
                if len(compact) >= 3 and compact in normalized.replace(" ", ""):
                    if veh.brand_name:
                        extracted["vehicle_brand"] = veh.brand_name
                    if veh.model_name:
                        extracted["vehicle_model"] = veh.model_name
                    break

        city_match = re.search(
            r"(?:в|город)\s+([a-zа-яё\-]{2,40})",
            normalized,
            re.IGNORECASE,
        )
        if city_match and GLOBAL_AI_RULES.city_required:
            extracted["city"] = city_match.group(1)

        return extracted
