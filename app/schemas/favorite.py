from pydantic import BaseModel, Field


class FavoriteToggleRead(BaseModel):
    listing_id: int = Field(ge=1)
    favorited: bool
