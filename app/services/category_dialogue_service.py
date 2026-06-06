from __future__ import annotations

import re
from typing import Any

from app.core.ai_global_rules import GLOBAL_AI_RULES
from app.models.category_enums import CategoryFieldType, ModerationAction
from app.repositories.category_repository import CategoryRepository
from app.schemas.category_intelligence import (
    CategoryDialogueRequest,
    CategoryDialogueResponse,
    CategoryFieldRead,
)
from app.services.category_moderation_service import CategoryModerationService
from app.services.category_routing_service import CategoryRoutingService
from app.services.category_text import normalize_text


class CategoryDialogueService:
    """
    AI dialogue layer: route intent, ask only missing CORE fields, never optional/advanced.
    """

    _FIELD_EXTRACTORS: dict[str, re.Pattern[str]] = {
        "city": re.compile(r"(?:в|город)\s+([a-zа-яё\-]{2,40})", re.I),
        "price": re.compile(r"(?:цена|за)\s*(\d[\d\s]{2,12})", re.I),
        "year": re.compile(r"\b(19|20)\d{2}\b"),
        "rooms": re.compile(r"(\d+)\s*-?\s*комнат", re.I),
        "salary": re.compile(r"(?:зарплат|от)\s*(\d[\d\s]{2,12})", re.I),
        "size": re.compile(r"\b(?:размер|size)\s*[:=]?\s*([xsml\d]{1,6})\b", re.I),
        "memory": re.compile(r"\b(\d+)\s*(?:гб|gb)\b", re.I),
        "brand": re.compile(r"\b(iphone|айфон|samsung|xiaomi|toyota|bmw|mercedes|камаз)\b", re.I),
        "model": re.compile(r"\b(camry|камри|corolla|x5|model\s+y)\b", re.I),
    }

    def __init__(
        self,
        routing_service: CategoryRoutingService,
        moderation_service: CategoryModerationService,
        category_repository: CategoryRepository,
    ) -> None:
        self._routing = routing_service
        self._moderation = moderation_service
        self._categories = category_repository

    async def process(self, payload: CategoryDialogueRequest) -> CategoryDialogueResponse:
        text = payload.text.strip()
        routing = await self._routing.route(text)

        if routing.mode == "out_of_domain":
            return CategoryDialogueResponse(
                routing=routing,
                in_marketplace_domain=False,
                message="Я помогаю только с объявлениями на маркетплейсе AiVai. Опишите, что хотите продать, купить или найти.",
            )

        if routing.mode == "clarification":
            hint = routing.category_name or "категорию"
            return CategoryDialogueResponse(
                routing=routing,
                message=(
                    f"Похоже на «{hint}», но хочу уточнить. "
                    "Вы продаёте, покупаете или заказываете услугу?"
                ),
            )

        mod_action, mod_reason = await self._moderation.evaluate(
            text,
            category_slug=routing.category_slug,
        )
        if mod_action == ModerationAction.block:
            return CategoryDialogueResponse(
                routing=routing,
                moderation_action=mod_action,
                moderation_reason=mod_reason,
                message="Такое объявление нельзя опубликовать автоматически.",
            )

        known = dict(payload.known_fields)
        auto = self._extract_from_text(text)
        for key, val in auto.items():
            known.setdefault(key, val)
        if routing.extracted:
            for key, val in routing.extracted.items():
                if key == "city":
                    known.setdefault("city", val)
                elif key == "vehicle_brand":
                    known.setdefault("brand", val)
                elif key == "vehicle_model":
                    known.setdefault("model", val)

        if routing.category_id is None:
            msg = "Уточните, пожалуйста: что именно вы хотите — продать, купить или заказать услугу?"
            if routing.mode == "suggestion" and routing.category_name:
                msg = (
                    f"Возможно, это «{routing.category_name}». "
                    "Подтвердите или опишите точнее."
                )
            return CategoryDialogueResponse(
                routing=routing,
                moderation_action=mod_action,
                moderation_reason=mod_reason,
                message=msg,
            )

        category = await self._categories.get_with_intelligence(routing.category_id)
        if category is None:
            return CategoryDialogueResponse(
                routing=routing,
                message="Категория не найдена. Попробуйте описать иначе.",
            )

        core_reads = [
            CategoryFieldRead.model_validate(f)
            for f in sorted(category.core_fields, key=lambda x: x.sort_order)
        ]

        if GLOBAL_AI_RULES.city_required and category.requires_city and not self._has_value(known, "city"):
            city_field = next((f for f in core_reads if f.field_key == "city"), None)
            if city_field is None:
                city_field = CategoryFieldRead(
                    field_key="city",
                    label="Город",
                    field_type=CategoryFieldType.city,
                    is_required=True,
                    sort_order=0,
                    ai_hint="В каком городе?",
                )
                core_reads = [city_field] + [f for f in core_reads if f.field_key != "city"]

        missing = [f for f in core_reads if f.is_required and not self._field_satisfied(f, known)]

        if not missing:
            msg = f"Отлично, могу оформить объявление в категории «{category.name}»."
            if mod_action == ModerationAction.moderation_queue:
                msg = "Объявление отправлено на проверку модератору перед публикацией."
            return CategoryDialogueResponse(
                routing=routing,
                missing_core_fields=[],
                moderation_action=mod_action,
                moderation_reason=mod_reason,
                message=msg,
            )

        first = missing[0]
        question = first.ai_hint or f"Подскажите: {first.label.lower()}?"
        return CategoryDialogueResponse(
            routing=routing,
            missing_core_fields=missing,
            next_question=question,
            moderation_action=mod_action,
            moderation_reason=mod_reason,
            message=question,
        )

    def _extract_from_text(self, text: str) -> dict[str, Any]:
        if GLOBAL_AI_RULES.no_advanced_dialogue:
            allowed = set(self._FIELD_EXTRACTORS.keys())
        else:
            allowed = set(self._FIELD_EXTRACTORS.keys())

        out: dict[str, Any] = {}
        norm = normalize_text(text)
        for key, pattern in self._FIELD_EXTRACTORS.items():
            if key not in allowed:
                continue
            m = pattern.search(text) or pattern.search(norm)
            if m:
                out[key] = m.group(1).strip() if m.lastindex else m.group(0).strip()
        return out

    @staticmethod
    def _has_value(known: dict[str, Any], key: str) -> bool:
        val = known.get(key)
        if val is None:
            return False
        if isinstance(val, str):
            return bool(val.strip())
        return True

    def _field_satisfied(self, field: CategoryFieldRead, known: dict[str, Any]) -> bool:
        if self._has_value(known, field.field_key):
            return True
        aliases = {
            "brand": ("vehicle_brand", "марка"),
            "model": ("vehicle_model", "модель"),
        }
        for alt in aliases.get(field.field_key, ()):
            if self._has_value(known, alt):
                return True
        return False
