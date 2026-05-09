from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.const import ChatKind, DeliveryStatus


class _ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserResponse(_ORMModel):
    id: UUID
    username: str


class TokenPairResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChatResponse(_ORMModel):
    id: UUID
    kind: ChatKind
    title: str | None
    created_at: datetime


class MessageResponse(_ORMModel):
    id: UUID
    chat_id: UUID
    sender_id: UUID
    body: str
    delivery_status: DeliveryStatus
    created_at: datetime


class MessagePage(BaseModel):
    items: list[MessageResponse]
    next_cursor: str | None
