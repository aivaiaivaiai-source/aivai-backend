from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.listing import ListingRead


class ChatRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    listing_id: int
    buyer_id: int
    seller_id: int
    last_message_at: datetime | None
    unread_count: int = 0
    created_at: datetime
    updated_at: datetime
    listing: ListingRead
