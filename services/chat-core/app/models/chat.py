from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.const import CHAT_TITLE_MAX_LENGTH, ChatKind
from app.models.base import Base, TimestampMixin


class Chat(Base, TimestampMixin):
    __tablename__ = "chats"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    kind: Mapped[ChatKind] = mapped_column(
        Enum(ChatKind, name="chat_kind"),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(String(CHAT_TITLE_MAX_LENGTH), nullable=True)


class ChatMember(Base):
    __tablename__ = "chat_members"

    chat_id: Mapped[UUID] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    joined_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    last_read_message_id: Mapped[UUID | None] = mapped_column(nullable=True)
