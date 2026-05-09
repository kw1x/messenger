from __future__ import annotations

from aiokafka import AIOKafkaProducer
from hexachat_shared.events.base import BaseEvent

from app.core.config import GatewaySettings


def build_producer(settings: GatewaySettings) -> AIOKafkaProducer:
    return AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA.BOOTSTRAP_SERVERS,
        client_id=settings.KAFKA.CLIENT_ID,
        acks="all",
        enable_idempotence=True,
        compression_type="zstd",
        linger_ms=5,
    )


async def publish(producer: AIOKafkaProducer, event: BaseEvent, *, key: str) -> None:
    await producer.send_and_wait(
        topic=event.topic,
        value=event.to_bytes(),
        key=key.encode("utf-8"),
    )
