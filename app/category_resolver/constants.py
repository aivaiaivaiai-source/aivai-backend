"""Category Resolver version and scoring thresholds."""

from __future__ import annotations

RESOLVER_VERSION = "category-resolver-v1"

# Minimum score to emit suggested (still shadow — no auto-assign).
SUGGEST_MIN_SCORE = 0.62
# Gap between top-1 and top-2 below which status becomes ambiguous.
AMBIGUITY_MARGIN = 0.08
# Visual concept support bonus cap.
VISUAL_SUPPORT_BONUS = 0.12
# Intent-visual conflict penalty.
INTENT_VISUAL_CONFLICT_PENALTY = 0.18
