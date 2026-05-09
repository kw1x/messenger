from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from pydantic import BaseModel, ConfigDict

ALGORITHM = "HS256"


@dataclass(frozen=True, slots=True)
class JWTSettings:
    """Minimal JWT configuration shared between chat-core and gateway."""

    secret_key: str
    access_token_expires: timedelta = timedelta(minutes=15)


class AccessTokenPayload(BaseModel):
    """The decoded body of a HexaChat access token."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    sub: UUID
    username: str
    exp: datetime

    @property
    def user_id(self) -> UUID:
        return self.sub


def encode_access_token(
    *,
    user_id: UUID,
    username: str,
    settings: JWTSettings,
    issued_at: datetime | None = None,
) -> str:
    issued_at = issued_at or datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "username": username,
        "iat": int(issued_at.timestamp()),
        "exp": int((issued_at + settings.access_token_expires).timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str, *, settings: JWTSettings) -> AccessTokenPayload:
    """Decode and validate an access token.

    Raises :class:`jwt.PyJWTError` (or subclass) on any failure — callers map
    those to the appropriate HTTP / WebSocket close codes.
    """
    raw = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    return AccessTokenPayload.model_validate(raw)
