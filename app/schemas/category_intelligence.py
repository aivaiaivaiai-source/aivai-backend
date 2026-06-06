from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.models.category_enums import (
    CategoryEntityType,
    CategoryFieldType,
    CategoryRuleType,
    ModerationAction,
)


class CategoryFieldRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    field_key: str
    label: str
    field_type: CategoryFieldType
    is_required: bool
    sort_order: int
    options: dict | None = None
    ai_hint: str | None = None


class CategoryFilterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    filter_key: str
    label: str
    filter_type: str
    sort_order: int
    config: dict | None = None


class CategoryRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rule_type: CategoryRuleType
    name: str
    pattern: str | None
    action: ModerationAction
    priority: int
    config: dict | None = None


class CategoryIntelligenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    parent_id: int | None
    entity_type: CategoryEntityType
    description: str | None = None
    requires_city: bool = True
    ai_dialogue_hint: str | None = None
    core_fields: list[CategoryFieldRead] = Field(default_factory=list)
    optional_fields: list[CategoryFieldRead] = Field(default_factory=list)
    filters: list[CategoryFilterRead] = Field(default_factory=list)


class CategoryRoutingResult(BaseModel):
    category_id: int | None = None
    category_slug: str | None = None
    category_name: str | None = None
    parent_slug: str | None = None
    confidence: float = 0.0
    mode: str = "unknown"
    reason: str | None = None
    extracted: dict[str, object] = Field(default_factory=dict)


class TextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


class CategoryDialogueRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    known_fields: dict[str, object] = Field(default_factory=dict)


class CategoryDialogueResponse(BaseModel):
    routing: CategoryRoutingResult
    missing_core_fields: list[CategoryFieldRead] = Field(default_factory=list)
    next_question: str | None = None
    moderation_action: ModerationAction = ModerationAction.allow
    moderation_reason: str | None = None
    in_marketplace_domain: bool = True
    message: str


class VehicleResolveResult(BaseModel):
    brand_id: int | None = None
    brand_name: str | None = None
    model_id: int | None = None
    model_name: str | None = None
    matched_alias: str | None = None
