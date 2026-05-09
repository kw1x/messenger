"""Kafka topic catalogue.

Versioned via the topic name (``.v1`` suffix) so backwards-incompatible
schema changes ship as new topics rather than breaking existing consumers.
"""

from __future__ import annotations

from typing import Final

#: Carries every persisted chat message. Partition key = chat_id, which
#: guarantees per-chat ordering on the consumer side.
CHAT_MESSAGES_V1: Final[str] = "chat.messages.v1"

#: Delivery / read receipts produced by presence-gateway and consumed by
#: chat-core to keep ``Message.delivery_status`` up to date.
CHAT_RECEIPTS_V1: Final[str] = "chat.receipts.v1"

#: User presence transitions (online/offline). Partition key = user_id.
PRESENCE_EVENTS_V1: Final[str] = "presence.events.v1"

ALL_TOPICS: Final[tuple[str, ...]] = (
    CHAT_MESSAGES_V1,
    CHAT_RECEIPTS_V1,
    PRESENCE_EVENTS_V1,
)
