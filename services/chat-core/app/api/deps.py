"""FastAPI dependency wiring."""

from __future__ import annotations

from typing import Annotated

from aiokafka import AIOKafkaProducer
from fastapi import Cookie, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from hexachat_shared.auth.jwt import AccessTokenPayload, decode_access_token
from jwt.exceptions import PyJWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import CoreSettings, settings
from app.core.db import get_session
from app.infra.kafka.outbox_publisher import OutboxPublisher
from app.repositories.chat import ChatRepository
from app.repositories.message import MessageRepository
from app.repositories.outbox import OutboxRepository
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from app.services.chat import ChatService
from app.services.message import MessageService
from app.services.user import UserService


def get_settings_dep() -> CoreSettings:
    return settings


SettingsDep = Annotated[CoreSettings, Depends(get_settings_dep)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_PREFIX}{settings.V1_PREFIX}/auth/login",
    auto_error=False,
)


def _extract_token(
    header_token: Annotated[str | None, Depends(_oauth2)] = None,
    cookie_token: Annotated[str | None, Cookie(alias="access_token")] = None,
) -> str:
    token = header_token or cookie_token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


def get_current_token(
    token: Annotated[str, Depends(_extract_token)],
    settings: SettingsDep,
) -> AccessTokenPayload:
    try:
        return decode_access_token(token, settings=settings.JWT.to_shared())
    except PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc


CurrentToken = Annotated[AccessTokenPayload, Depends(get_current_token)]


def _user_repo(session: SessionDep) -> UserRepository:
    return UserRepository(session)


def _chat_repo(session: SessionDep) -> ChatRepository:
    return ChatRepository(session)


def _message_repo(session: SessionDep) -> MessageRepository:
    return MessageRepository(session)


def _outbox_repo(session: SessionDep) -> OutboxRepository:
    return OutboxRepository(session)


def _refresh_repo(session: SessionDep) -> RefreshTokenRepository:
    return RefreshTokenRepository(session)


def _user_service(user_repo: Annotated[UserRepository, Depends(_user_repo)]) -> UserService:
    return UserService(user_repo)


def _auth_service(
    session: SessionDep,
    user_repo: Annotated[UserRepository, Depends(_user_repo)],
    refresh_repo: Annotated[RefreshTokenRepository, Depends(_refresh_repo)],
    settings: SettingsDep,
) -> AuthService:
    return AuthService(session, user_repo, refresh_repo, settings)


def _chat_service(
    session: SessionDep,
    chat_repo: Annotated[ChatRepository, Depends(_chat_repo)],
) -> ChatService:
    return ChatService(session, chat_repo)


def _message_service(
    session: SessionDep,
    chat_service: Annotated[ChatService, Depends(_chat_service)],
    chat_repo: Annotated[ChatRepository, Depends(_chat_repo)],
    message_repo: Annotated[MessageRepository, Depends(_message_repo)],
    outbox_repo: Annotated[OutboxRepository, Depends(_outbox_repo)],
) -> MessageService:
    return MessageService(session, chat_service, chat_repo, message_repo, outbox_repo)


UserServiceDep = Annotated[UserService, Depends(_user_service)]
AuthServiceDep = Annotated[AuthService, Depends(_auth_service)]
ChatServiceDep = Annotated[ChatService, Depends(_chat_service)]
MessageServiceDep = Annotated[MessageService, Depends(_message_service)]


def get_kafka_producer(request: Request) -> AIOKafkaProducer:
    return request.app.state.kafka_producer  # type: ignore[no-any-return]


def get_outbox_publisher(request: Request) -> OutboxPublisher:
    return request.app.state.outbox_publisher  # type: ignore[no-any-return]


KafkaProducerDep = Annotated[AIOKafkaProducer, Depends(get_kafka_producer)]
OutboxPublisherDep = Annotated[OutboxPublisher, Depends(get_outbox_publisher)]
