from __future__ import annotations

import asyncio
import json
from contextlib import suppress
from typing import Any
from uuid import UUID

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from hexachat_shared.events import MessageDelivered
from hexachat_shared.kafka.topics import CHAT_MESSAGES_V1
from loguru import logger

from app.core.config import GatewaySettings
from app.infra.kafka.producer import publish
from app.ws.connection_manager import ConnectionManager


class MessagesConsumer:
    """Subscribes to ``chat.messages.v1`` and fans messages out to local sockets.

    The ``group_id`` is unique per replica (`hostname-pid`) — every replica
    gets every event, but each only delivers to its own connected users.
    Recipients that are not connected here are ignored: the replica that
    actually holds their socket will deliver it.
    """

    def __init__(
        self,
        *,
        manager: ConnectionManager,
        settings: GatewaySettings,
        receipts_producer: AIOKafkaProducer,
    ) -> None:
        self._manager = manager
        self._settings = settings
        self._receipts = receipts_producer
        self._consumer: AIOKafkaConsumer | None = None
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        self._consumer = AIOKafkaConsumer(
            CHAT_MESSAGES_V1,
            bootstrap_servers=self._settings.KAFKA.BOOTSTRAP_SERVERS,
            client_id=self._settings.KAFKA.CLIENT_ID,
            group_id=f"presence-gateway.{self._settings.REPLICA_ID}",
            auto_offset_reset="latest",
            enable_auto_commit=True,
        )
        await self._consumer.start()
        self._task = asyncio.create_task(self._run(), name="messages-consumer")
        logger.info("Subscribed to {} as group {}", CHAT_MESSAGES_V1, self._settings.REPLICA_ID)

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        if self._consumer is not None:
            await self._consumer.stop()
            self._consumer = None

    async def _run(self) -> None:
        assert self._consumer is not None
        async for record in self._consumer:
            try:
                payload = json.loads(record.value)
                await self._dispatch(payload)
            except Exception:
                logger.exception("Failed to dispatch message {}", record.offset)

    async def _dispatch(self, payload: dict[str, Any]) -> None:
        message_id = UUID(payload["message_id"])
        chat_id = UUID(payload["chat_id"])
        sender_id = UUID(payload["sender_id"])
        member_ids = [UUID(m) for m in payload["member_ids"]]
        envelope = {"type": "message", "data": payload}

        for member_id in member_ids:
            if member_id == sender_id:
                continue
            delivered = await self._manager.send_to_user(member_id, envelope)
            if delivered:
                await publish(
                    self._receipts,
                    MessageDelivered(message_id=message_id, chat_id=chat_id, recipient_id=member_id),
                    key=str(message_id),
                )
