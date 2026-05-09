from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import and_, or_, select, tuple_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.const import DeliveryStatus
from app.models.message import Message


class MessageRepoInterface(Protocol):
    async def add(self, message: Message) -> Message: ...
    async def page(
        self,
        chat_id: UUID,
        limit: int,
        cursor: tuple[datetime, UUID] | None,
    ) -> list[Message]: ...
    async def bump_status(
        self,
        message_ids: list[UUID],
        status: DeliveryStatus,
    ) -> None: ...


class MessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, message: Message) -> Message:
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def page(
        self,
        chat_id: UUID,
        limit: int,
        cursor: tuple[datetime, UUID] | None,
    ) -> list[Message]:
        """Keyset pagination by ``(created_at desc, id desc)``.

        ``cursor`` represents the last item from the previous page; the next
        page starts strictly after it (in descending order).
        """
        stmt = select(Message).where(Message.chat_id == chat_id)
        if cursor is not None:
            cursor_at, cursor_id = cursor
            stmt = stmt.where(
                or_(
                    Message.created_at < cursor_at,
                    and_(Message.created_at == cursor_at, Message.id < cursor_id),
                )
            )
        stmt = stmt.order_by(Message.created_at.desc(), Message.id.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def bump_status(
        self,
        message_ids: list[UUID],
        status: DeliveryStatus,
    ) -> None:
        if not message_ids:
            return
        rank = {DeliveryStatus.SENT: 0, DeliveryStatus.DELIVERED: 1, DeliveryStatus.READ: 2}
        keep_below = [s for s, r in rank.items() if r < rank[status]]
        if not keep_below:
            return
        stmt = (
            update(Message)
            .where(Message.id.in_(message_ids))
            .where(Message.delivery_status.in_(keep_below))
            .values(delivery_status=status)
        )
        await self.session.execute(stmt)


def encode_cursor(message: Message) -> str:
    import base64

    raw = f"{message.created_at.isoformat()}|{message.id}".encode()
    return base64.urlsafe_b64encode(raw).decode("ascii")


def decode_cursor(cursor: str) -> tuple[datetime, UUID]:
    import base64

    raw = base64.urlsafe_b64decode(cursor.encode("ascii")).decode("utf-8")
    iso, uid = raw.split("|", maxsplit=1)
    return datetime.fromisoformat(iso), UUID(uid)


# Convenience tuple type used by API layer to thread the cursor without
# leaking SQLAlchemy types.
__all__ = [
    "MessageRepoInterface",
    "MessageRepository",
    "decode_cursor",
    "encode_cursor",
    "tuple_",  # re-export for type hints in deps if needed
]
