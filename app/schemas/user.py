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


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    balance: Decimal
    last_login: datetime | None
    created_at: datetime
    updated_at: datetime
