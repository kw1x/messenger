from __future__ import annotations

from aiokafka import AIOKafkaProducer

from app.core.config import CoreSettings


def build_producer(settings: CoreSettings) -> AIOKafkaProducer:
    """Build the singleton producer used by both API and outbox publisher.

    ``acks=all`` + ``enable_idempotence`` give us exactly-once-per-partition
    delivery semantics, which combines nicely with the at-least-once outbox to
    yield effectively-once end-to-end behaviour.
    """
    return AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA.BOOTSTRAP_SERVERS,
        client_id=settings.KAFKA.CLIENT_ID,
        acks="all",
        enable_idempotence=True,
        compression_type="zstd",
        linger_ms=5,
    )
