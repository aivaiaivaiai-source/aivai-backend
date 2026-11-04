"""Deterministic Category Resolver engine — shadow/suggestion mode."""



from __future__ import annotations



import re

from dataclasses import dataclass, field



from app.category_resolver.action_compatibility import (

    action_compatibility_adjustment,

    is_generic_slug,

    specificity_bonus,

)

from app.category_resolver.catalog_snapshot import ResolverCatalogSnapshot, ResolverCategoryNode

from app.category_resolver.constants import (

    AMBIGUITY_MARGIN,

    INTENT_VISUAL_CONFLICT_PENALTY,

    RESOLVER_VERSION,

    SUGGEST_MIN_SCORE,

    VISUAL_SUPPORT_BONUS,

)

from app.category_resolver.intent_semantics import IntentAction, IntentSemantics, interpret_intent

from app.category_resolver.visual_signals import (

    detect_intent_visual_conflict,

    intent_slug_hints,

    is_job_action,

    is_rent_action,

    is_service_action,

    visual_slug_hints,

)

from app.models.category_resolver_enums import CategoryResolverStatus

from app.services.category_routing_service import CategoryRoutingService

from app.services.category_text import normalize_text



_L3_TEXT_KEYWORDS: tuple[tuple[re.Pattern[str], str], ...] = (

    (re.compile(r"двигател|мотор\b", re.I), "transport-auto-parts-dvigatel-i-navesnoe"),

    (re.compile(r"коробк|кпп", re.I), "transport-auto-parts-korobka-peredach-i-transmissiya"),

    (re.compile(r"шин[ыа]", re.I), "transport-tires-wheels-shiny"),

    (re.compile(r"\bдиск", re.I), "transport-tires-wheels-diski"),

    (re.compile(r"r17", re.I), "transport-tires-wheels-shiny"),

    (re.compile(r"r18", re.I), "transport-tires-wheels-diski"),

    (re.compile(r"экскаватор", re.I), "transport-special-equipment-ekskavatory"),

    (re.compile(r"фотограф", re.I), "services-foto-i-videosemka"),

)





@dataclass(frozen=True)

class ResolverCandidate:

    slug: str

    score: float

    reasons: tuple[str, ...]





@dataclass

class ResolverEngineOutput:

    status: CategoryResolverStatus

    suggested_slug: str | None = None

    suggested_category_id: int | None = None

    confidence: float = 0.0

    needs_confirmation: bool = True

    candidate_path: list[dict[str, object]] = field(default_factory=list)

    alternatives: list[dict[str, object]] = field(default_factory=list)

    evidence_summary: dict[str, object] = field(default_factory=dict)

    intent_semantics: dict[str, object] = field(default_factory=dict)

    resolver_version: str = RESOLVER_VERSION





class CategoryResolverEngine:

    """Local deterministic resolver — no external LLM."""



    def __init__(self, routing_service: CategoryRoutingService) -> None:

        self._routing = routing_service



    async def resolve(

        self,

        *,

        raw_intent_text: str,

        catalog: ResolverCatalogSnapshot,

        visual_concepts: tuple[str, ...] = (),

    ) -> ResolverEngineOutput:

        intent = interpret_intent(raw_intent_text)

        normalized = normalize_text(raw_intent_text)

        evidence: dict[str, object] = {

            "intent_action": intent.action.value,

            "intent_terms": list(intent.subject_terms),

            "intent_qualifiers": list(intent.qualifiers),

            "visual": list(visual_concepts),

            "matched_aliases": [],

            "routing_hits": [],

            "scores": [],

        }

        conflict = detect_intent_visual_conflict(intent, visual_concepts)

        if conflict:

            evidence["conflict"] = "intent_visual_mismatch"



        if not raw_intent_text.strip():

            return ResolverEngineOutput(

                status=CategoryResolverStatus.no_match,

                evidence_summary=evidence,

                intent_semantics=intent.to_json(),

                needs_confirmation=True,

            )



        candidates: dict[str, ResolverCandidate] = {}



        def add(slug: str, score: float, reason: str) -> None:

            if slug in catalog.nodes_by_slug:

                existing = candidates.get(slug)

                if existing is None or score > existing.score:

                    candidates[slug] = ResolverCandidate(

                        slug=slug,

                        score=score,

                        reasons=(reason,) if existing is None else existing.reasons + (reason,),

                    )

                elif existing is not None:

                    candidates[slug] = ResolverCandidate(

                        slug=slug,

                        score=existing.score,

                        reasons=existing.reasons + (reason,),

                    )



        # 1) Legacy routing service signal (aliases + DB rules).

        route = await self._routing.route(raw_intent_text)

        if route.category_slug and route.category_slug in catalog.nodes_by_slug:

            base = float(route.confidence or 0.5)

            add(route.category_slug, base, f"routing:{route.mode}")

            evidence["routing_hits"].append(

                {"slug": route.category_slug, "mode": route.mode, "confidence": route.confidence}

            )



        # 2) Intent-driven slug hints.

        for slug in intent_slug_hints(intent):

            score = 0.78 + intent.confidence * 0.08

            if is_service_action(intent.action) and slug.startswith("services-") and slug != "services-transport":

                score = max(score, 0.92)

            if is_job_action(intent.action):

                score = max(score, 0.9)

            if intent.action in (IntentAction.SELL, IntentAction.BUY) and slug.startswith(

                ("transport-special-equipment", "transport-auto-parts", "transport-tires-wheels")

            ):

                score = max(score, 0.91)

            add(slug, score, "intent_hint")



        # 3) L3 keyword hits from raw text.

        for pattern, l3_slug in _L3_TEXT_KEYWORDS:

            if pattern.search(raw_intent_text) or pattern.search(normalized):

                if l3_slug in catalog.nodes_by_slug:

                    add(l3_slug, 0.9, "l3_keyword")



        # 4) Visual concept hints (supporting).

        if visual_concepts and not conflict:

            for slug in visual_slug_hints(visual_concepts, intent):

                add(slug, 0.55 + VISUAL_SUPPORT_BONUS, f"visual:{visual_concepts[0]}")



        # 5) Alias scan from catalog intelligence snapshot.

        intel = catalog.intelligence

        if intel is not None:

            for key, alias in intel.aliases_by_compact.items():

                if len(key) >= 3 and key in normalized.replace(" ", ""):

                    if alias.category_slug in catalog.nodes_by_slug:

                        add(alias.category_slug, alias.weight / 100.0, f"alias:{alias.alias}")

                        evidence["matched_aliases"].append(alias.alias)



        # 6) Action-family L1 bias.

        for slug in self._family_slugs(intent, catalog):

            add(slug, 0.45, "family_bias")



        if conflict:

            for slug in list(candidates):

                cand = candidates[slug]

                candidates[slug] = ResolverCandidate(

                    slug=slug,

                    score=max(0.0, cand.score - INTENT_VISUAL_CONFLICT_PENALTY),

                    reasons=cand.reasons + ("conflict_penalty",),

                )

            if "запчаст" in intent.subject_terms or "двигатель" in intent.subject_terms:

                add("transport-auto-parts", 0.93, "intent_parts_priority")

            if is_service_action(intent.action):

                for slug in intent_slug_hints(intent):

                    add(slug, 0.9, "intent_service_priority")

            if is_job_action(intent.action):

                for slug in intent_slug_hints(intent):

                    add(slug, 0.92, "intent_job_priority")



        # 7) Action ↔ category compatibility adjustments.

        adjusted: dict[str, ResolverCandidate] = {}

        for slug, cand in candidates.items():

            new_score, compat_tag = action_compatibility_adjustment(

                slug, intent, base_score=cand.score

            )

            reasons = cand.reasons + ((compat_tag,) if compat_tag else ())

            adjusted[slug] = ResolverCandidate(slug=slug, score=new_score, reasons=reasons)

        candidates = adjusted



        if not candidates:

            return ResolverEngineOutput(

                status=CategoryResolverStatus.no_match,

                evidence_summary=evidence,

                intent_semantics=intent.to_json(),

            )



        ranked = sorted(candidates.values(), key=lambda c: c.score, reverse=True)

        evidence["scores"] = [{"slug": c.slug, "score": round(c.score, 4)} for c in ranked[:8]]



        top = ranked[0]

        deepest = self._deepest_node(

            top.slug, catalog, ranked, intent, raw_intent_text=raw_intent_text

        )

        top_slug = deepest.slug if deepest else top.slug

        top_score = top.score

        if deepest and deepest.slug != top.slug:

            top_score = min(0.98, top.score + 0.04)



        margin = ranked[0].score - ranked[1].score if len(ranked) >= 2 else 1.0

        if len(ranked) >= 2 and margin < AMBIGUITY_MARGIN:

            competitor = ranked[1].slug

            spec_bonus = specificity_bonus(top_slug, intent, competitor)

            has_strong_intent = any(r.startswith("intent_hint") or r.startswith("l3_keyword") for r in top.reasons)

            if spec_bonus > 0 or (has_strong_intent and margin >= 0.04):

                top_score = min(0.98, top_score + spec_bonus + (0.04 if has_strong_intent else 0.0))

            else:

                return self._build_output(

                    status=CategoryResolverStatus.ambiguous,

                    slug=top_slug,

                    score=top_score * 0.85,

                    catalog=catalog,

                    ranked=ranked,

                    evidence=evidence,

                    intent=intent,

                    needs_confirmation=True,

                )



        if top_score < SUGGEST_MIN_SCORE:

            return self._build_output(

                status=CategoryResolverStatus.no_match,

                slug=None,

                score=top_score,

                catalog=catalog,

                ranked=ranked,

                evidence=evidence,

                intent=intent,

            )



        return self._build_output(

            status=CategoryResolverStatus.suggested,

            slug=top_slug,

            score=top_score,

            catalog=catalog,

            ranked=ranked,

            evidence=evidence,

            intent=intent,

            needs_confirmation=True,

        )



    @staticmethod

    def _family_slugs(intent: IntentSemantics, catalog: ResolverCatalogSnapshot) -> tuple[str, ...]:

        roots: list[str] = []

        if is_service_action(intent.action):

            roots.append("services")

        elif is_job_action(intent.action):

            roots.append("jobs")

        elif intent.action in (

            IntentAction.SELL,

            IntentAction.BUY,

            IntentAction.RENT_OUT,

            IntentAction.RENT_WANTED,

        ):

            if any(t in intent.subject_terms for t in ("квартира",)):

                roots.append("real-estate")

            elif any(t in intent.subject_terms for t in ("телефон",)):

                roots.append("electronics")

            elif any(

                t in intent.subject_terms

                for t in ("авто", "камаз", "грузовик", "мото", "лодка", "запчаст", "экскаватор", "шины", "диски", "двигатель", "коробка")

            ):

                roots.append("transport")

        elif intent.action == IntentAction.EXCHANGE:

            roots.append("free-exchange-swap")

        elif intent.action == IntentAction.GIVE_AWAY:

            roots.append("free-give")

        return tuple(s for s in roots if s in catalog.nodes_by_slug)



    @staticmethod

    def _deepest_node(

        slug: str,

        catalog: ResolverCatalogSnapshot,

        ranked: list[ResolverCandidate],

        intent: IntentSemantics,

        *,

        raw_intent_text: str = "",

    ) -> ResolverCategoryNode | None:

        node = catalog.get(slug)

        if node is None:

            return None

        best = node

        hint_slugs = set(intent_slug_hints(intent))

        for alt in ranked[:5]:

            hint_slugs.add(alt.slug)

        normalized = normalize_text(raw_intent_text)

        for pattern, l3_slug in _L3_TEXT_KEYWORDS:

            if pattern.search(raw_intent_text) or pattern.search(normalized):

                hint_slugs.add(l3_slug)

        for child in catalog.descendants(slug):

            if child.slug in hint_slugs:

                if child.depth >= best.depth:

                    best = child

        return best



    @staticmethod

    def _build_output(

        *,

        status: CategoryResolverStatus,

        slug: str | None,

        score: float,

        catalog: ResolverCatalogSnapshot,

        ranked: list[ResolverCandidate],

        evidence: dict[str, object],

        intent: IntentSemantics,

        needs_confirmation: bool = True,

    ) -> ResolverEngineOutput:

        path: list[dict[str, object]] = []

        cat_id: int | None = None

        if slug:

            path_nodes = catalog.path_for(slug)

            path = [{"id": n.id, "slug": n.slug, "name": n.name} for n in path_nodes]

            leaf = catalog.get(slug)

            cat_id = leaf.id if leaf else None



        alternatives = [

            {"slug": c.slug, "score": round(c.score, 4), "reasons": list(c.reasons)}

            for c in ranked[:5]

        ]

        return ResolverEngineOutput(

            status=status,

            suggested_slug=slug,

            suggested_category_id=cat_id,

            confidence=round(score, 4),

            needs_confirmation=needs_confirmation,

            candidate_path=path,

            alternatives=alternatives,

            evidence_summary=evidence,

            intent_semantics=intent.to_json(),

        )

