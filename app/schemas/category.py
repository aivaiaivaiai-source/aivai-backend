from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    parent_id: int | None
    entity_type: str | None = None


class CategoryTreeNode(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    parent_id: int | None = None
    entity_type: str | None = None
    children: list["CategoryTreeNode"] = Field(default_factory=list)
