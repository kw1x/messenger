from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Index, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.const import (
    OUTBOX_LAST_ERROR_MAX_LENGTH,
    OUTBOX_PARTITION_KEY_MAX_LENGTH,
    OUTBOX_TOPIC_MAX_LENGTH,
)
from app.models.base import Base


class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    __table_args__ = (
        Index(
            "ix_outbox_events_unpublished",
            "created_at",
            postgresql_where=text("published_at IS NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    topic: Mapped[str] = mapped_column(String(OUTBOX_TOPIC_MAX_LENGTH), nullable=False)
    partition_key: Mapped[str] = mapped_column(String(OUTBOX_PARTITION_KEY_MAX_LENGTH), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)
    attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(String(OUTBOX_LAST_ERROR_MAX_LENGTH), nullable=True)
