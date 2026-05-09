from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from hexachat_shared.logging import configure_logging
from loguru import logger

from app.api.main import router
from app.core.config import settings
from app.core.db import async_session_maker, dispose_engine
from app.infra.kafka.outbox_publisher import OutboxPublisher
from app.infra.kafka.producer import build_producer
from app.infra.kafka.receipts_consumer import ReceiptsConsumer

configure_logging(
    service="chat-core",
    level=settings.LOG_LEVEL,
    json=settings.ENVIRONMENT != "local",
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    producer = build_producer(settings)
    await producer.start()
    publisher = OutboxPublisher(
        session_factory=async_session_maker,
        producer=producer,
        settings=settings,
    )
    receipts = ReceiptsConsumer(session_factory=async_session_maker, settings=settings)

    await publisher.start()
    await receipts.start()

    app.state.kafka_producer = producer
    app.state.outbox_publisher = publisher

    logger.info("chat-core ready ({})", settings.ENVIRONMENT)
    try:
        yield
    finally:
        await receipts.stop()
        await publisher.stop()
        await producer.stop()
        await dispose_engine()


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

app.include_router(router)


@app.get("/healthz", tags=["meta"], include_in_schema=False)
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
