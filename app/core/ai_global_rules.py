from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AIGlobalRules:
    """Platform-wide AI assistant constraints (not category-specific seeds)."""

    city_required: bool = True
    minimal_friction: bool = True
    no_advanced_dialogue: bool = True
    no_unrelated_conversation: bool = True
    moderation_before_publish: bool = True

    # Routing safety
    auto_route_min_confidence: float = 0.72
    clarification_below_confidence: float = 0.55
    suggestion_below_confidence: float = 0.35

    # Admin / moderation future
    allow_admin_rule_override: bool = True
    allow_disable_aliases: bool = True
    allow_disable_categories: bool = True
    moderation_queue_enabled: bool = True


GLOBAL_AI_RULES = AIGlobalRules()
