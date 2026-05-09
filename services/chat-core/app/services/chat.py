from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.const import ChatKind
from app.core.exceptions import ChatNotFoundError, NotAChatMemberError
from app.models.chat import Chat
from app.repositories.chat import ChatRepoInterface


class ChatService:
    def __init__(self, session: AsyncSession, chat_repo: ChatRepoInterface) -> None:
        self.session = session
        self.chat_repo = chat_repo

    async def create_chat(self, *, kind: ChatKind, title: str | None, member_ids: list[UUID]) -> Chat:
        chat = Chat(kind=kind, title=title)
        chat = await self.chat_repo.add(chat, member_ids=member_ids)
        await self.session.commit()
        return chat

    async def list_my_chats(self, user_id: UUID) -> list[Chat]:
        return await self.chat_repo.list_for_user(user_id)

    async def add_member(self, *, chat_id: UUID, requester_id: UUID, new_member_id: UUID) -> None:
        if await self.chat_repo.get(chat_id) is None:
            raise ChatNotFoundError
        if not await self.chat_repo.is_member(chat_id, requester_id):
            raise NotAChatMemberError
        if not await self.chat_repo.is_member(chat_id, new_member_id):
            await self.chat_repo.add_member(chat_id, new_member_id)
        await self.session.commit()

    async def assert_member(self, *, chat_id: UUID, user_id: UUID) -> None:
        if not await self.chat_repo.is_member(chat_id, user_id):
            raise NotAChatMemberError
