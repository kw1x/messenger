from __future__ import annotations

from datetime import datetime
from uuid import UUID

from hexachat_shared.events import MessageCreated
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.repositories.chat import ChatRepoInterface
from app.repositories.message import MessageRepoInterface
from app.repositories.outbox import OutboxRepoInterface
from app.services.chat import ChatService


class MessageService:
    def __init__(
        self,
        session: AsyncSession,
        chat_service: ChatService,
        chat_repo: ChatRepoInterface,
        message_repo: MessageRepoInterface,
        outbox_repo: OutboxRepoInterface,
    ) -> None:
        self.session = session
        self.chat_service = chat_service
        self.chat_repo = chat_repo
        self.message_repo = message_repo
        self.outbox_repo = outbox_repo

    async def post_message(self, *, chat_id: UUID, sender_id: UUID, body: str) -> Message:
        await self.chat_service.assert_member(chat_id=chat_id, user_id=sender_id)
        member_ids = await self.chat_repo.list_member_ids(chat_id)

        # ▼ The non-negotiable hot-path invariant: message + outbox event live
        # ▼ in the same transaction. Either both land in Postgres or neither
        # ▼ does. The publisher will then ship the event to Kafka.
        message = await self.message_repo.add(Message(chat_id=chat_id, sender_id=sender_id, body=body))
        event = MessageCreated(
            message_id=message.id,
            chat_id=chat_id,
            sender_id=sender_id,
            body=body,
            member_ids=member_ids,
        )
        await self.outbox_repo.enqueue(
            topic=event.topic,
            partition_key=str(chat_id),
            payload=event.model_dump(mode="json"),
        )
        await self.session.commit()
        return message

    async def list_history(
        self,
        *,
        chat_id: UUID,
        viewer_id: UUID,
        limit: int,
        cursor: tuple[datetime, UUID] | None,
    ) -> list[Message]:
        await self.chat_service.assert_member(chat_id=chat_id, user_id=viewer_id)
        return await self.message_repo.page(chat_id, limit, cursor)
