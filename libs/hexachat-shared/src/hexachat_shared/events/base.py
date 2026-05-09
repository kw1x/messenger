from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


def _utcnow() -> datetime:
    return datetime.now(UTC)


class BaseEvent(BaseModel):
    """Base envelope for every Kafka event in HexaChat.

    Concrete events declare ``event_type`` as a ``Literal[...]`` so that
    discriminated unions on the consumer side stay exhaustive.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    #: Topic the event travels through. Subclasses override this and use it
    #: when calling :meth:`hexachat_shared.kafka.topics.partition_key_for`.
    topic: ClassVar[str]

    event_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime = Field(default_factory=_utcnow)
    schema_version: int = 1

    def to_bytes(self) -> bytes:
        """Serialise the event to UTF-8 JSON ready for Kafka."""
        return self.model_dump_json().encode("utf-8")
