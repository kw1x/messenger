from __future__ import annotations

from app.core.exceptions import UsernameAlreadyTakenError
from app.core.security import hash_password
from app.models.user import User
from app.repositories.user import UserRepoInterface


class UserService:
    def __init__(self, user_repo: UserRepoInterface) -> None:
        self.user_repo = user_repo

    async def register(self, *, username: str, password: str) -> User:
        if await self.user_repo.get_by_username(username) is not None:
            raise UsernameAlreadyTakenError(username)
        user = User(username=username, hashed_password=hash_password(password))
        return await self.user_repo.add(user)
