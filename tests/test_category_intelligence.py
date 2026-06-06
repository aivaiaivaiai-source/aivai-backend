from __future__ import annotations

import pytest

from app.core.ai_global_rules import GLOBAL_AI_RULES
from app.services.category_snapshot import apply_routing_confidence_policy
from app.services.category_text import (
    alias_lookup_variants,
    normalize_alias_compact,
    normalize_alias_keys,
    normalize_text,
)


@pytest.mark.parametrize(
    "raw,expected_compact",
    [
        ("LX 570", "lx570"),
        ("лх570", "lx570"),
        ("лексус 570", "lexus570"),
        ("lx570", "lx570"),
        ("  Камри  ", "camry"),
        ("МЕРС", "mercedes"),
        ("Li Auto", "liauto"),
        ("бид хан", "bydhan"),
    ],
)
def test_normalize_alias_compact(raw: str, expected_compact: str) -> None:
    assert normalize_alias_compact(raw) == expected_compact


def test_alias_lookup_variants_includes_compact_and_tokens() -> None:
    variants = alias_lookup_variants("продаю камри 70 в бишкеке")
    assert "camry" in variants or "camry70" in variants
    assert len(variants) >= 2


def test_normalize_alias_keys_pair() -> None:
    spaced, compact = normalize_alias_keys("LX-570")
    assert " " in spaced or spaced == "lx 570"
    assert compact == "lx570"


def test_apply_routing_confidence_policy_auto_route() -> None:
    mode, cid, *_ = apply_routing_confidence_policy(
        confidence=0.9,
        mode="heuristic",
        category_id=1,
        category_slug="transport-cars",
        category_name="Cars",
        parent_slug="transport",
        reason="test",
    )
    assert mode == "heuristic"
    assert cid == 1


def test_apply_routing_confidence_policy_clarification() -> None:
    mode, cid, slug, *_ = apply_routing_confidence_policy(
        confidence=0.6,
        mode="alias",
        category_id=5,
        category_slug="electronics-phones",
        category_name="Phones",
        parent_slug="electronics",
        reason="low",
    )
    assert mode == "clarification"
    assert cid is None
    assert slug == "electronics-phones"


def test_apply_routing_confidence_policy_suggestion() -> None:
    mode, cid, *_ = apply_routing_confidence_policy(
        confidence=0.3,
        mode="suggestion",
        category_id=2,
        category_slug="food-agri",
        category_name="Food",
        parent_slug=None,
        reason="low",
    )
    assert mode == "suggestion"
    assert cid is None


def test_global_ai_rules_defaults() -> None:
    assert GLOBAL_AI_RULES.city_required is True
    assert GLOBAL_AI_RULES.auto_route_min_confidence == 0.72
    assert GLOBAL_AI_RULES.no_unrelated_conversation is True


def test_seed_loader_upsert_logic_import() -> None:
    from app.seeds.loader import CategorySeedLoader

    assert CategorySeedLoader.__doc__


@pytest.mark.parametrize(
    "text,expected_substr",
    [
        ("  Камри  ", "camry"),
        ("МЕРС", "mercedes"),
    ],
)
def test_normalize_text_colloquial(text: str, expected_substr: str) -> None:
    assert expected_substr in normalize_text(text)


def test_routing_service_static_routes_exist() -> None:
    from app.services.category_routing_service import CategoryRoutingService

    assert len(CategoryRoutingService._STATIC_ROUTES) >= 5


def test_moderation_separate_from_routing_repos() -> None:
    from app.repositories.category_moderation_rule_repository import (
        CategoryModerationRuleRepository,
    )
    from app.repositories.category_routing_rule_repository import CategoryRoutingRuleRepository

    assert CategoryRoutingRuleRepository is not CategoryModerationRuleRepository


def test_city_required_threshold() -> None:
    assert GLOBAL_AI_RULES.clarification_below_confidence < GLOBAL_AI_RULES.auto_route_min_confidence
