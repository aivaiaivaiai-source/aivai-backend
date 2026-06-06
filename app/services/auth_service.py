from __future__ import annotations

from jose import JWTError

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.schemas.auth import TokenResponse
from app.services.user_service import UserService


class AuthService:
    """Application auth use cases (login, refresh); delegates identity to ``UserService``."""

    def __init__(self, user_service: UserService) -> None:
        self._users = user_service

    async def login_by_phone(self, phone: str | None, full_name: str) -> TokenResponse:
        """Mock OTP: resolve or create user by phone and return a new token pair."""
        if phone is None or not phone.strip():
            raise UnauthorizedError("Phone is required.")

        settings = get_settings()
        user = await self._users.get_or_create_user_by_phone(phone, full_name)
        if not user.is_active:
            raise UnauthorizedError("User is inactive.")

        access = create_access_token(user.id, settings=settings)
        refresh = create_refresh_token(user.id, settings=settings)
        return TokenResponse(access_token=access, refresh_token=refresh)

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """Validate refresh JWT and mint a new access + refresh pair."""
        settings = get_settings()
        try:
            payload = decode_token(refresh_token, settings=settings)
        except JWTError as exc:
            raise UnauthorizedError("Invalid or expired refresh token.") from exc

        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type.")

        raw_sub = payload.get("sub")
        if raw_sub is None:
            raise UnauthorizedError("Invalid token payload.")

        try:
            user_id = int(raw_sub)
        except (TypeError, ValueError) as exc:
            raise UnauthorizedError("Invalid subject in token.") from exc

        user = await self._users.get_user_by_id(user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("User not found or inactive.")

        access = create_access_token(user.id, settings=settings)
        refresh = create_refresh_token(user.id, settings=settings)
        return TokenResponse(access_token=access, refresh_token=refresh)
