"""WebSocket wire protocol — the public contract between browser clients
and the gateway."""

from __future__ import annotations

from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, TypeAdapter


class AckMessage(BaseModel):
    type: Literal["ack"] = "ack"
    message_id: UUID


class ReadMessage(BaseModel):
    type: Literal["read"] = "read"
    chat_id: UUID
    up_to_message_id: UUID


class PingMessage(BaseModel):
    type: Literal["ping"] = "ping"


InboundMessage = Annotated[AckMessage | ReadMessage | PingMessage, Field(discriminator="type")]
inbound_adapter = TypeAdapter(InboundMessage)


class OutboundEnvelope(BaseModel):
    type: Literal["message", "presence", "pong"]
    data: dict[str, Any] | None = None
