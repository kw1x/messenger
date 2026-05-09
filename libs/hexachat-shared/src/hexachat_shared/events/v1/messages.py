from __future__ import annotations

from typing import ClassVar, Literal
from uuid import UUID

from hexachat_shared.events.base import BaseEvent
from hexachat_shared.kafka.topics import CHAT_MESSAGES_V1


class MessageCreated(BaseEvent):
    """Emitted by chat-core whenever a new chat message is persisted.

    ``member_ids`` is denormalised on purpose so that presence-gateway never
    has to read from Postgres on the hot path.
    """

    topic: ClassVar[str] = CHAT_MESSAGES_V1
    event_type: Literal["message_created"] = "message_created"

    message_id: UUID
    chat_id: UUID
    sender_id: UUID
    body: str
    member_ids: list[UUID]
