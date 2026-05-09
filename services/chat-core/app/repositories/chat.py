from __future__ import annotations

from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Chat, ChatMember


class ChatRepoInterface(Protocol):
    async def add(self, chat: Chat, member_ids: list[UUID]) -> Chat: ...
    async def get(self, chat_id: UUID) -> Chat | None: ...
    async def list_for_user(self, user_id: UUID) -> list[Chat]: ...
    async def is_member(self, chat_id: UUID, user_id: UUID) -> bool: ...
    async def list_member_ids(self, chat_id: UUID) -> list[UUID]: ...
    async def add_member(self, chat_id: UUID, user_id: UUID) -> None: ...
    async def update_last_read(self, chat_id: UUID, user_id: UUID, message_id: UUID) -> None: ...


class ChatRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, chat: Chat, member_ids: list[UUID]) -> Chat:
        self.session.add(chat)
        await self.session.flush()
        self.session.add_all(ChatMember(chat_id=chat.id, user_id=uid) for uid in member_ids)
        await self.session.flush()
        await self.session.refresh(chat)
        return chat

    async def get(self, chat_id: UUID) -> Chat | None:
        return await self.session.get(Chat, chat_id)

    async def list_for_user(self, user_id: UUID) -> list[Chat]:
        stmt = (
            select(Chat)
            .join(ChatMember, ChatMember.chat_id == Chat.id)
            .where(ChatMember.user_id == user_id)
            .order_by(Chat.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def is_member(self, chat_id: UUID, user_id: UUID) -> bool:
        stmt = select(ChatMember.user_id).where(
            ChatMember.chat_id == chat_id,
            ChatMember.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def list_member_ids(self, chat_id: UUID) -> list[UUID]:
        stmt = select(ChatMember.user_id).where(ChatMember.chat_id == chat_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add_member(self, chat_id: UUID, user_id: UUID) -> None:
        self.session.add(ChatMember(chat_id=chat_id, user_id=user_id))
        await self.session.flush()

    async def update_last_read(self, chat_id: UUID, user_id: UUID, message_id: UUID) -> None:
        member = await self.session.get(ChatMember, {"chat_id": chat_id, "user_id": user_id})
        if member is not None:
            member.last_read_message_id = message_id
            await self.session.flush()
