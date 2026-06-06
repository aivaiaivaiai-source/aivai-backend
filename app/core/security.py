from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.core.config import Settings, get_settings


JWT_ISSUER = "aivai"
JWT_AUDIENCE = "aivai_users"

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    user_id: int,
    *,
    settings: Settings | None = None,
) -> str:
    s = settings or get_settings()
    exp = datetime.now(timezone.utc) + timedelta(minutes=s.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "exp": exp,
    }
    return jwt.encode(payload, s.JWT_SECRET_KEY, algorithm=s.ALGORITHM)


def create_refresh_token(
    user_id: int,
    *,
    settings: Settings | None = None,
) -> str:
    s = settings or get_settings()
    exp = datetime.now(timezone.utc) + timedelta(days=s.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "exp": exp,
    }
    return jwt.encode(payload, s.JWT_SECRET_KEY, algorithm=s.ALGORITHM)


def decode_token(raw_token: str, *, settings: Settings | None = None) -> dict:
    """Decode and validate JWT. Propagates ``jose.JWTError`` on invalid or expired tokens."""
    s = settings or get_settings()
    return jwt.decode(
        raw_token,
        s.JWT_SECRET_KEY,
        algorithms=[s.ALGORITHM],
        issuer=JWT_ISSUER,
        audience=JWT_AUDIENCE,
    )


def hash_password(plain_password: str) -> str:
    return _pwd_ctx.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_ctx.verify(plain_password, hashed_password)


__all__ = (
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "hash_password",
    "verify_password",
)
