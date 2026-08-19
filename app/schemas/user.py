from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    phone: str = Field(..., max_length=32)
    full_name: str = Field(..., max_length=255)


class UserCreate(UserBase):
    pass


class UserByPhoneRequest(BaseModel):
    phone: str = Field(..., max_length=32)
    full_name: str = Field(default="User", max_length=255)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=128)


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    balance: Decimal
    city: str | None = None
    avatar_url: str | None = None
    rating: int = 0
    reviews_count: int = 0
    listings_created_count: int = 0
    last_login: datetime | None
    created_at: datetime
    updated_at: datetime
