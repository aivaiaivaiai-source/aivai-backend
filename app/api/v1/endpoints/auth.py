from fastapi import APIRouter, Depends

from app.api.deps import get_auth_service
from app.core.rate_limit import enforce_auth_ip_rate_limit
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    _: None = Depends(enforce_auth_ip_rate_limit),
    auth: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return await auth.login_by_phone(body.phone, body.full_name)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    _: None = Depends(enforce_auth_ip_rate_limit),
    auth: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return await auth.refresh_tokens(body.refresh_token)
