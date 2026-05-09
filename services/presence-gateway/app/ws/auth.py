from __future__ import annotations

from hexachat_shared.auth.jwt import AccessTokenPayload, decode_access_token
from jwt.exceptions import PyJWTError

from app.core.config import GatewaySettings


class WebSocketAuthError(Exception):
    """Raised when WS handshake credentials are missing or invalid."""


def authenticate(token: str | None, settings: GatewaySettings) -> AccessTokenPayload:
    if not token:
        raise WebSocketAuthError("missing token")
    try:
        return decode_access_token(token, settings=settings.JWT.to_shared())
    except PyJWTError as exc:
        raise WebSocketAuthError(str(exc)) from exc
