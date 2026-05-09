from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from hexachat_shared.auth.jwt import encode_access_token
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import CoreSettings
from app.core.exceptions import InvalidCredentialsError, InvalidRefreshTokenError
from app.core.security import verify_password
from app.repositories.refresh_token import RefreshTokenRepoInterface
from app.repositories.user import UserRepoInterface


class TokenPair:
    __slots__ = ("access_token", "refresh_token", "refresh_expires_at")

    def __init__(self, access_token: str, refresh_token: str, refresh_expires_at: datetime) -> None:
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.refresh_expires_at = refresh_expires_at


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        user_repo: UserRepoInterface,
        refresh_repo: RefreshTokenRepoInterface,
        settings: CoreSettings,
    ) -> None:
        self.session = session
        self.user_repo = user_repo
        self.refresh_repo = refresh_repo
        self.settings = settings

    async def login(self, *, username: str, password: str) -> TokenPair:
        user = await self.user_repo.get_by_username(username)
        if user is None or not user.is_active or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError
        return await self._issue_pair(user_id=user.id, username=user.username)

    async def refresh(self, *, refresh_token: str) -> TokenPair:
        active = await self.refresh_repo.find_active(refresh_token)
        if active is None:
            raise InvalidRefreshTokenError
        user = await self.user_repo.get_by_id(active.user_id)
        if user is None or not user.is_active:
            raise InvalidRefreshTokenError
        await self.refresh_repo.revoke(active.id)
        return await self._issue_pair(user_id=user.id, username=user.username)

    async def _issue_pair(self, *, user_id: UUID, username: str) -> TokenPair:
        access = encode_access_token(
            user_id=user_id,
            username=username,
            settings=self.settings.JWT.to_shared(),
        )
        refresh = secrets.token_urlsafe(48)
        expires_at = datetime.now(UTC) + timedelta(days=self.settings.JWT.REFRESH_TOKEN_EXPIRES_DAYS)
        await self.refresh_repo.create(user_id=user_id, token=refresh, expires_at=expires_at)
        await self.session.commit()
        return TokenPair(access, refresh, expires_at)
