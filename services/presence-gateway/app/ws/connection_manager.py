from __future__ import annotations

import asyncio
from collections import defaultdict
from contextlib import suppress
from typing import Any
from uuid import UUID

from fastapi import WebSocket
from loguru import logger


class ConnectionManager:
    """In-memory registry of live WebSocket connections.

    Per-replica only — fan-out across replicas is the consumer group's job.
    The reference project's manager doubles as a Redis Pub/Sub bus; here we
    don't need that because each replica subscribes to Kafka independently.
    """

    def __init__(self) -> None:
        self._by_user: defaultdict[UUID, set[WebSocket]] = defaultdict(set)
        self._reverse: dict[WebSocket, UUID] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id: UUID, websocket: WebSocket) -> None:
        async with self._lock:
            self._by_user[user_id].add(websocket)
            self._reverse[websocket] = user_id
        logger.debug("user {} connected ({} sockets)", user_id, len(self._by_user[user_id]))

    async def disconnect(self, websocket: WebSocket) -> UUID | None:
        async with self._lock:
            user_id = self._reverse.pop(websocket, None)
            if user_id is not None:
                bucket = self._by_user.get(user_id)
                if bucket is not None:
                    bucket.discard(websocket)
                    if not bucket:
                        self._by_user.pop(user_id, None)
        return user_id

    def is_connected(self, user_id: UUID) -> bool:
        return user_id in self._by_user

    async def send_to_user(self, user_id: UUID, message: dict[str, Any]) -> int:
        """Push a JSON payload to every socket of a given user.

        Returns the number of sockets that accepted the payload — useful for
        deciding whether to emit a ``MessageDelivered`` receipt.
        """
        sockets = list(self._by_user.get(user_id, ()))
        if not sockets:
            return 0
        delivered = 0
        for ws in sockets:
            try:
                await ws.send_json(message)
                delivered += 1
            except Exception:
                with suppress(Exception):
                    await ws.close()
                await self.disconnect(ws)
        return delivered
