from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class RefreshTokenRepoInterface(Protocol):
    async def create(self, *, user_id: UUID, token: str, expires_at: datetime) -> RefreshToken: ...
    async def find_active(self, token: str) -> RefreshToken | None: ...
    async def revoke(self, token_id: UUID) -> None: ...


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, user_id: UUID, token: str, expires_at: datetime) -> RefreshToken:
        rt = RefreshToken(user_id=user_id, token_hash=hash_refresh_token(token), expires_at=expires_at)
        self.session.add(rt)
        await self.session.flush()
        await self.session.refresh(rt)
        return rt

    async def find_active(self, token: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(
            RefreshToken.token_hash == hash_refresh_token(token),
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > datetime.now(UTC),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke(self, token_id: UUID) -> None:
        await self.session.execute(
            update(RefreshToken).where(RefreshToken.id == token_id).values(revoked_at=datetime.now(UTC))
        )
