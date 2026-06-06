from __future__ import annotations

import re

from app.core.ai_global_rules import GLOBAL_AI_RULES
from app.models.category_enums import ModerationAction
from app.services.category_snapshot import CategorySnapshotProvider
from app.services.category_text import normalize_text


class CategoryModerationService:
    """
    Moderation layer — separated from routing.
    Uses compiled moderation/guardrail rules from snapshot (no routing rule mixing).
    """

    _MEDICAL_BLOCK = re.compile(
        r"(антибиотик|гормон|инъекц|рецепт|prescription|antibiotic|hormone|injection)",
        re.IGNORECASE,
    )
    _BUSINESS_SUSPICIOUS = re.compile(
        r"(mlm|пирамид|франшиз.*fake|сетевой\s+маркетинг|pyramid)",
        re.IGNORECASE,
    )
    _TRUST_SENSITIVE = re.compile(
        r"(паспорт|документ|найден|мошеннич|scam|passport|found\s+item)",
        re.IGNORECASE,
    )

    def __init__(self, snapshot_provider: CategorySnapshotProvider) -> None:
        self._snapshots = snapshot_provider

    async def evaluate(
        self,
        text: str,
        category_slug: str | None = None,
    ) -> tuple[ModerationAction, str | None]:
        if not GLOBAL_AI_RULES.moderation_before_publish:
            return ModerationAction.allow, None

        normalized = normalize_text(text)
        snap = await self._snapshots.get()

        action = self._evaluate_builtin(text, category_slug)
        if action is not None:
            return action

        action = self._evaluate_compiled(snap.moderation_rules, normalized)
        if action is not None:
            return action

        action = self._evaluate_compiled(snap.guardrail_rules, normalized)
        if action is not None:
            return action

        return ModerationAction.allow, None

    def _evaluate_builtin(
        self,
        text: str,
        category_slug: str | None,
    ) -> tuple[ModerationAction, str | None] | None:
        if self._MEDICAL_BLOCK.search(text) and (
            category_slug is None or category_slug.startswith("medical")
        ):
            return ModerationAction.block, "MEDICAL_GUARDRAILS: рецептурные/опасные медтовары"

        if self._BUSINESS_SUSPICIOUS.search(text):
            return ModerationAction.moderation_queue, "BUSINESS_MODERATION: подозрительное предложение"

        if self._TRUST_SENSITIVE.search(text):
            return ModerationAction.moderation_queue, "TRUST_AND_SAFETY: требуется проверка"

        return None

    @staticmethod
    def _evaluate_compiled(
        rules: list,
        normalized: str,
    ) -> tuple[ModerationAction, str | None] | None:
        for rule in sorted(rules, key=lambda r: r.priority):
            if rule.pattern.search(normalized):
                return ModerationAction(rule.action), rule.name
        return None
