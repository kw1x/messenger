from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.const import PASSWORD_HASH_MAX_LENGTH, USERNAME_MAX_LENGTH


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(USERNAME_MAX_LENGTH), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(PASSWORD_HASH_MAX_LENGTH), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
