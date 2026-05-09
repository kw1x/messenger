from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

_engine: AsyncEngine = create_async_engine(
    settings.POSTGRES.dsn,
    echo=settings.ENVIRONMENT == "local",
    future=True,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=20,
    pool_recycle=3600,
    isolation_level="READ COMMITTED",
)

async_session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield a session bound to the request scope.

    The session does not auto-commit — service-layer code is responsible for
    transaction boundaries.
    """
    async with async_session_maker() as session:
        yield session


async def dispose_engine() -> None:
    await _engine.dispose()
