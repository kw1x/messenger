from __future__ import annotations

from datetime import timedelta
from functools import lru_cache
from pathlib import Path
from typing import Literal

from hexachat_shared.auth.jwt import JWTSettings
from pydantic import BaseModel, Field, PostgresDsn, RedisDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT = Path(__file__).resolve().parents[3]


class PostgresSettings(BaseModel):
    HOST: str = "localhost"
    PORT: int = 5432
    USER: str = "hexachat"
    PASSWORD: str = "hexachat"
    DB: str = "hexachat"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def dsn(self) -> str:
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.USER,
                password=self.PASSWORD,
                host=self.HOST,
                port=self.PORT,
                path=self.DB,
            )
        )


class RedisSettings(BaseModel):
    HOST: str = "localhost"
    PORT: int = 6379
    DB: int = 0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def dsn(self) -> str:
        return str(RedisDsn.build(scheme="redis", host=self.HOST, port=self.PORT, path=str(self.DB)))


class KafkaSettings(BaseModel):
    BOOTSTRAP_SERVERS: str = "localhost:9092"
    CLIENT_ID: str = "chat-core"
    RECEIPTS_GROUP_ID: str = "chat-core.receipts"


class JwtConfig(BaseModel):
    SECRET_KEY: str = "please-change-me-to-32-bytes-of-randomness"
    ACCESS_TOKEN_EXPIRES_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRES_DAYS: int = 30

    def to_shared(self) -> JWTSettings:
        return JWTSettings(
            secret_key=self.SECRET_KEY,
            access_token_expires=timedelta(minutes=self.ACCESS_TOKEN_EXPIRES_MINUTES),
        )


class CoreSettings(BaseSettings):
    """Application settings.

    All env vars use ``SECTION_KEY`` form thanks to ``env_nested_delimiter``;
    e.g. ``POSTGRES_HOST``, ``KAFKA_BOOTSTRAP_SERVERS``, ``JWT_SECRET_KEY``.
    """

    model_config = SettingsConfigDict(
        env_file=_ROOT / ".env",
        env_nested_delimiter="_",
        env_nested_max_split=1,
        extra="ignore",
    )

    ENVIRONMENT: Literal["local", "staging", "production"] = Field(default="local", alias="CORE_ENVIRONMENT")
    LOG_LEVEL: str = Field(default="INFO", alias="CORE_LOG_LEVEL")
    PROJECT_NAME: str = "HexaChat — Core"
    API_PREFIX: str = "/api"
    V1_PREFIX: str = "/v1"
    CORS_ORIGINS: list[str] = ["*"]

    OUTBOX_BATCH_SIZE: int = Field(default=100, alias="CORE_OUTBOX_BATCH_SIZE")
    OUTBOX_POLL_INTERVAL_MS: int = Field(default=200, alias="CORE_OUTBOX_POLL_INTERVAL_MS")
    OUTBOX_MAX_ATTEMPTS: int = 10

    POSTGRES: PostgresSettings = PostgresSettings()
    REDIS: RedisSettings = RedisSettings()
    KAFKA: KafkaSettings = KafkaSettings()
    JWT: JwtConfig = JwtConfig()


@lru_cache(maxsize=1)
def get_settings() -> CoreSettings:
    return CoreSettings()


settings = get_settings()
