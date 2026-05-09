from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from hexachat_shared.logging import configure_logging
from loguru import logger

from app.api.v1.main import router as v1_router
from app.core.config import settings
from app.infra.kafka.messages_consumer import MessagesConsumer
from app.infra.kafka.producer import build_producer
from app.infra.redis.presence_store import PresenceStore
from app.ws.connection_manager import ConnectionManager

configure_logging(
    service="presence-gateway",
    level=settings.LOG_LEVEL,
    json=settings.ENVIRONMENT != "local",
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    redis_client = redis.from_url(settings.REDIS.dsn, decode_responses=True)
    presence_store = PresenceStore(redis_client, ttl_seconds=settings.PRESENCE_TTL_SECONDS)
    manager = ConnectionManager()

    producer = build_producer(settings)
    await producer.start()

    consumer = MessagesConsumer(manager=manager, settings=settings, receipts_producer=producer)
    await consumer.start()

    app.state.redis = redis_client
    app.state.presence_store = presence_store
    app.state.connection_manager = manager
    app.state.gateway_producer = producer

    logger.info("presence-gateway ready (replica={})", settings.REPLICA_ID)
    try:
        yield
    finally:
        await consumer.stop()
        await producer.stop()
        await redis_client.aclose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix=settings.API_PREFIX)
