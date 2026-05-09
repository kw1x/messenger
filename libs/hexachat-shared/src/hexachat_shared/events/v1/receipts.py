from __future__ import annotations

from typing import ClassVar, Literal
from uuid import UUID

from hexachat_shared.events.base import BaseEvent
from hexachat_shared.kafka.topics import CHAT_RECEIPTS_V1


class MessageDelivered(BaseEvent):
    """Emitted by presence-gateway after at least one socket acknowledged."""

    topic: ClassVar[str] = CHAT_RECEIPTS_V1
    event_type: Literal["message_delivered"] = "message_delivered"

    message_id: UUID
    chat_id: UUID
    recipient_id: UUID


class MessageRead(BaseEvent):
    """Emitted when the user explicitly marks the conversation as read."""

    topic: ClassVar[str] = CHAT_RECEIPTS_V1
    event_type: Literal["message_read"] = "message_read"

    chat_id: UUID
    reader_id: UUID
    up_to_message_id: UUID
