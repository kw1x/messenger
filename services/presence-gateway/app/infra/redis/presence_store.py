from __future__ import annotations

from uuid import UUID

import redis.asyncio as redis


class PresenceStore:
    """Redis-backed presence index.

    Each online user maps to a key with a short TTL; the WebSocket loop
    refreshes it on every heartbeat. If the heartbeat stops, the key expires
    naturally and the user shows up as offline without us having to do
    anything.
    """

    KEY_TEMPLATE = "presence:user:{user_id}"

    def __init__(self, client: redis.Redis, ttl_seconds: int) -> None:
        self._client = client
        self._ttl = ttl_seconds

    def _key(self, user_id: UUID) -> str:
        return self.KEY_TEMPLATE.format(user_id=user_id)

    async def mark_online(self, user_id: UUID) -> None:
        await self._client.set(self._key(user_id), "1", ex=self._ttl)

    async def heartbeat(self, user_id: UUID) -> None:
        await self._client.expire(self._key(user_id), self._ttl)

    async def mark_offline(self, user_id: UUID) -> None:
        await self._client.delete(self._key(user_id))

    async def is_online(self, user_id: UUID) -> bool:
        return bool(await self._client.exists(self._key(user_id)))
