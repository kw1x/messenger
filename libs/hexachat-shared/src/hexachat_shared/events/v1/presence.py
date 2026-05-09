from __future__ import annotations

from enum import StrEnum
from typing import ClassVar, Literal
from uuid import UUID

from hexachat_shared.events.base import BaseEvent
from hexachat_shared.kafka.topics import PRESENCE_EVENTS_V1


class PresenceStatus(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"


class PresenceChanged(BaseEvent):
    topic: ClassVar[str] = PRESENCE_EVENTS_V1
    event_type: Literal["presence_changed"] = "presence_changed"

    user_id: UUID
    status: PresenceStatus
