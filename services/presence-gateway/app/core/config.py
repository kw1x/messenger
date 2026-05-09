from __future__ import annotations

import os
import socket
from datetime import timedelta
from functools import lru_cache
from pathlib import Path
from typing import Literal

from hexachat_shared.auth.jwt import JWTSettings
from pydantic import BaseModel, Field, RedisDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT = Path(__file__).resolve().parents[3]


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
    CLIENT_ID: str = "presence-gateway"


class JwtConfig(BaseModel):
    SECRET_KEY: str = "please-change-me-to-32-bytes-of-randomness"
    ACCESS_TOKEN_EXPIRES_MINUTES: int = 15

    def to_shared(self) -> JWTSettings:
        return JWTSettings(
            secret_key=self.SECRET_KEY,
            access_token_expires=timedelta(minutes=self.ACCESS_TOKEN_EXPIRES_MINUTES),
        )


def _replica_id() -> str:
    """Stable per-process identifier used as a Kafka group_id suffix.

    Each gateway replica gets its own consumer group so that every replica
    receives every event — that's the basis of the fan-out story (ADR-0003).
    """
    return f"{socket.gethostname()}-{os.getpid()}"


class GatewaySettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ROOT / ".env",
        env_nested_delimiter="_",
        env_nested_max_split=1,
        extra="ignore",
    )

    ENVIRONMENT: Literal["local", "staging", "production"] = Field(default="local", alias="GATEWAY_ENVIRONMENT")
    LOG_LEVEL: str = Field(default="INFO", alias="GATEWAY_LOG_LEVEL")
    PROJECT_NAME: str = "HexaChat — Presence Gateway"
    API_PREFIX: str = "/api"
    V1_PREFIX: str = "/v1"
    CORS_ORIGINS: list[str] = ["*"]

    HEARTBEAT_INTERVAL_SECONDS: int = Field(default=20, alias="GATEWAY_HEARTBEAT_INTERVAL_SECONDS")
    PRESENCE_TTL_SECONDS: int = Field(default=60, alias="GATEWAY_PRESENCE_TTL_SECONDS")

    REDIS: RedisSettings = RedisSettings()
    KAFKA: KafkaSettings = KafkaSettings()
    JWT: JwtConfig = JwtConfig()

    REPLICA_ID: str = Field(default_factory=_replica_id)


@lru_cache(maxsize=1)
def get_settings() -> GatewaySettings:
    return GatewaySettings()


settings = get_settings()
