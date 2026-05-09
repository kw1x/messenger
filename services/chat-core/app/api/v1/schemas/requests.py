from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from app.const import (
    CHAT_TITLE_MAX_LENGTH,
    MESSAGE_BODY_MAX_LENGTH,
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    USERNAME_MAX_LENGTH,
    ChatKind,
)


class UserRegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=USERNAME_MAX_LENGTH)
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)


class CreateChatRequest(BaseModel):
    kind: ChatKind
    title: str | None = Field(default=None, max_length=CHAT_TITLE_MAX_LENGTH)
    member_ids: list[UUID] = Field(min_length=1)


class AddMemberRequest(BaseModel):
    user_id: UUID


class PostMessageRequest(BaseModel):
    body: str = Field(min_length=1, max_length=MESSAGE_BODY_MAX_LENGTH)
