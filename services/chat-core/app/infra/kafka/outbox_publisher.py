from __future__ import annotations

import asyncio
import json
from contextlib import suppress

from aiokafka import AIOKafkaProducer
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import CoreSettings
from app.repositories.outbox import OutboxRepository


class OutboxPublisher:
    """Background task that drains ``outbox_events`` into Kafka.

    Runs forever in the lifespan of the FastAPI app. Multiple chat-core
    replicas can run their own publisher concurrently — ``FOR UPDATE SKIP
    LOCKED`` makes that safe.
    """

    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        producer: AIOKafkaProducer,
        settings: CoreSettings,
    ) -> None:
        self._session_factory = session_factory
        self._producer = producer
        self._settings = settings
        self._wakeup = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self._stop = asyncio.Event()

    def notify(self) -> None:
        """Cheap signal from the API layer: «there's something new to ship»."""
        self._wakeup.set()

    async def start(self) -> None:
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._run(), name="outbox-publisher")
        logger.info("Outbox publisher started")

    async def stop(self) -> None:
        if self._task is None:
            return
        self._stop.set()
        self._wakeup.set()
        with suppress(asyncio.CancelledError):
            await self._task
        self._task = None
        logger.info("Outbox publisher stopped")

    async def _run(self) -> None:
        poll_seconds = self._settings.OUTBOX_POLL_INTERVAL_MS / 1000
        while not self._stop.is_set():
            try:
                shipped = await self._publish_one_batch()
            except Exception:
                logger.exception("Outbox publisher batch failed")
                shipped = 0

            if shipped == 0:
                with suppress(TimeoutError):
                    await asyncio.wait_for(self._wakeup.wait(), timeout=poll_seconds)
                self._wakeup.clear()

    async def _publish_one_batch(self) -> int:
        async with self._session_factory() as session, session.begin():
            repo = OutboxRepository(session)
            batch = await repo.claim_batch(self._settings.OUTBOX_BATCH_SIZE)
            if not batch:
                return 0

            published_ids = []
            for event in batch:
                try:
                    await self._producer.send_and_wait(
                        topic=event.topic,
                        value=json.dumps(event.payload).encode("utf-8"),
                        key=event.partition_key.encode("utf-8"),
                    )
                except Exception as exc:
                    logger.warning("Failed to publish outbox event {}: {}", event.id, exc)
                    await repo.mark_failed(event.id, repr(exc))
                    continue
                published_ids.append(event.id)

            await repo.mark_published(published_ids)
            return len(published_ids)
