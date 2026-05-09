"""Domain-level constants and enums.

Kept apart from the ORM models so that pure-Python code (Pydantic schemas,
services, tests) can import them without dragging in SQLAlchemy.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final

NAMING_CONVENTION: Final[dict[str, str]] = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

USERNAME_MAX_LENGTH: Final = 64
PASSWORD_HASH_MAX_LENGTH: Final = 255
PASSWORD_MIN_LENGTH: Final = 8
PASSWORD_MAX_LENGTH: Final = 128

CHAT_TITLE_MAX_LENGTH: Final = 120

MESSAGE_BODY_MAX_LENGTH: Final = 4000

OUTBOX_TOPIC_MAX_LENGTH: Final = 128
OUTBOX_PARTITION_KEY_MAX_LENGTH: Final = 128
OUTBOX_LAST_ERROR_MAX_LENGTH: Final = 500

REFRESH_TOKEN_HASH_MAX_LENGTH: Final = 128


class ChatKind(StrEnum):
    DIRECT = "direct"
    GROUP = "group"


class DeliveryStatus(StrEnum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
