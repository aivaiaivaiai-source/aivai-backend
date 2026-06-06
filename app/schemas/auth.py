from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    phone: str | None = Field(default=None, max_length=32)
    full_name: str = Field(default="User", max_length=255)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
