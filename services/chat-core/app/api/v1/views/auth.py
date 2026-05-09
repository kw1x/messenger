from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import AuthServiceDep, SettingsDep
from app.api.v1.schemas import TokenPairResponse
from app.core.exceptions import InvalidRefreshTokenError

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"


def _set_refresh_cookie(response: Response, *, token: str, expires_in_days: int, secure: bool) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        max_age=expires_in_days * 24 * 60 * 60,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/api/v1/auth",
    )


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    summary="Exchange username + password for an access token",
)
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: AuthServiceDep,
    settings: SettingsDep,
    response: Response,
) -> TokenPairResponse:
    pair = await service.login(username=form.username, password=form.password)
    _set_refresh_cookie(
        response,
        token=pair.refresh_token,
        expires_in_days=settings.JWT.REFRESH_TOKEN_EXPIRES_DAYS,
        secure=settings.ENVIRONMENT != "local",
    )
    return TokenPairResponse(access_token=pair.access_token)


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    summary="Rotate the refresh cookie and mint a new access token",
)
async def refresh(
    service: AuthServiceDep,
    settings: SettingsDep,
    response: Response,
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE_NAME)] = None,
) -> TokenPairResponse:
    if not refresh_token:
        raise InvalidRefreshTokenError
    pair = await service.refresh(refresh_token=refresh_token)
    _set_refresh_cookie(
        response,
        token=pair.refresh_token,
        expires_in_days=settings.JWT.REFRESH_TOKEN_EXPIRES_DAYS,
        secure=settings.ENVIRONMENT != "local",
    )
    return TokenPairResponse(access_token=pair.access_token)
