from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(..., min_length=1, max_length=2000)


class ReviewReplyUpdate(BaseModel):
    owner_reply: str | None = Field(default=None, max_length=2000)


class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    author_id: int
    subject_id: int
    author_name: str
    rating: int
    comment: str
    owner_reply: str | None
    created_at: datetime
