from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outbox import OutboxEvent


class OutboxRepoInterface(Protocol):
    async def enqueue(self, *, topic: str, partition_key: str, payload: dict[str, Any]) -> OutboxEvent: ...
    async def claim_batch(self, batch_size: int) -> list[OutboxEvent]: ...
    async def mark_published(self, ids: list[UUID]) -> None: ...
    async def mark_failed(self, event_id: UUID, error: str) -> None: ...


class OutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def enqueue(self, *, topic: str, partition_key: str, payload: dict[str, Any]) -> OutboxEvent:
        event = OutboxEvent(topic=topic, partition_key=partition_key, payload=payload)
        self.session.add(event)
        await self.session.flush()
        return event

    async def claim_batch(self, batch_size: int) -> list[OutboxEvent]:
        """Claim a batch of unpublished events with ``FOR UPDATE SKIP LOCKED``.

        Multiple chat-core replicas can run the publisher in parallel without
        ever fighting over the same row.
        """
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.published_at.is_(None))
            .order_by(OutboxEvent.created_at.asc())
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_published(self, ids: list[UUID]) -> None:
        if not ids:
            return
        await self.session.execute(
            update(OutboxEvent).where(OutboxEvent.id.in_(ids)).values(published_at=datetime.now(UTC))
        )

    async def mark_failed(self, event_id: UUID, error: str) -> None:
        await self.session.execute(
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(attempts=OutboxEvent.attempts + 1, last_error=error[:500])
        )
