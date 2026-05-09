from __future__ import annotations

import asyncio
import json
from contextlib import suppress
from typing import Any
from uuid import UUID

from aiokafka import AIOKafkaConsumer
from hexachat_shared.kafka.topics import CHAT_RECEIPTS_V1
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.const import DeliveryStatus
from app.core.config import CoreSettings
from app.repositories.chat import ChatRepository
from app.repositories.message import MessageRepository


class ReceiptsConsumer:
    """Consumes delivery / read receipts and updates message state.

    Manual commit only after a successful DB write — that gives us
    at-least-once processing semantics that pair correctly with the
    monotonic ``DeliveryStatus`` transitions in :class:`MessageRepository`.
    """

    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        settings: CoreSettings,
    ) -> None:
        self._session_factory = session_factory
        self._settings = settings
        self._consumer: AIOKafkaConsumer | None = None
        self._task: asyncio.Task[None] | None = None
        self._stop = asyncio.Event()

    async def start(self) -> None:
        self._consumer = AIOKafkaConsumer(
            CHAT_RECEIPTS_V1,
            bootstrap_servers=self._settings.KAFKA.BOOTSTRAP_SERVERS,
            client_id=f"{self._settings.KAFKA.CLIENT_ID}.receipts",
            group_id=self._settings.KAFKA.RECEIPTS_GROUP_ID,
            enable_auto_commit=False,
            auto_offset_reset="earliest",
        )
        await self._consumer.start()
        self._task = asyncio.create_task(self._run(), name="receipts-consumer")
        logger.info("Receipts consumer subscribed to {}", CHAT_RECEIPTS_V1)

    async def stop(self) -> None:
        self._stop.set()
        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        if self._consumer is not None:
            await self._consumer.stop()
            self._consumer = None
        logger.info("Receipts consumer stopped")

    async def _run(self) -> None:
        assert self._consumer is not None
        async for record in self._consumer:
            try:
                payload = json.loads(record.value)
                await self._handle(payload)
                await self._consumer.commit()
            except Exception:
                logger.exception("Failed to handle receipt {}", record.offset)
                await self._consumer.commit()

    async def _handle(self, payload: dict[str, Any]) -> None:
        event_type = payload.get("event_type")
        if event_type == "message_delivered":
            await self._mark_delivered(UUID(payload["message_id"]))
        elif event_type == "message_read":
            await self._mark_read(
                chat_id=UUID(payload["chat_id"]),
                reader_id=UUID(payload["reader_id"]),
                up_to_message_id=UUID(payload["up_to_message_id"]),
            )

    async def _mark_delivered(self, message_id: UUID) -> None:
        async with self._session_factory() as session, session.begin():
            await MessageRepository(session).bump_status([message_id], DeliveryStatus.DELIVERED)

    async def _mark_read(self, *, chat_id: UUID, reader_id: UUID, up_to_message_id: UUID) -> None:
        async with self._session_factory() as session, session.begin():
            await MessageRepository(session).bump_status([up_to_message_id], DeliveryStatus.READ)
            await ChatRepository(session).update_last_read(chat_id, reader_id, up_to_message_id)
