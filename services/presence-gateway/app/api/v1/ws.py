from __future__ import annotations

import asyncio
from contextlib import suppress
from uuid import UUID

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from hexachat_shared.events import MessageRead, PresenceChanged
from hexachat_shared.events.v1.presence import PresenceStatus
from loguru import logger
from pydantic import ValidationError

from app.core.config import settings
from app.infra.kafka.producer import publish
from app.infra.redis.presence_store import PresenceStore
from app.ws.auth import WebSocketAuthError, authenticate
from app.ws.protocol import AckMessage, PingMessage, ReadMessage, inbound_adapter

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = Query(default=None),
) -> None:
    """The single WebSocket endpoint exposed by the gateway.

    The JWT travels as a query parameter — browsers can't set custom headers
    on the WS handshake. Tokens are short-lived (15 min by default) which
    bounds the impact of leakage via server logs.
    """
    try:
        token_payload = authenticate(token, settings)
    except WebSocketAuthError as exc:
        logger.info("WS auth rejected: {}", exc)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = token_payload.user_id
    state = websocket.app.state

    await websocket.accept()
    await state.connection_manager.connect(user_id, websocket)
    await state.presence_store.mark_online(user_id)
    await publish(
        state.gateway_producer,
        PresenceChanged(user_id=user_id, status=PresenceStatus.ONLINE),
        key=str(user_id),
    )

    heartbeat = asyncio.create_task(_heartbeat_loop(state.presence_store, user_id))

    try:
        while True:
            raw = await websocket.receive_json()
            await _handle_inbound(websocket, raw, user_id=user_id)
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("WS loop crashed for user {}", user_id)
    finally:
        heartbeat.cancel()
        with suppress(asyncio.CancelledError):
            await heartbeat

        await state.connection_manager.disconnect(websocket)
        if not state.connection_manager.is_connected(user_id):
            await state.presence_store.mark_offline(user_id)
            await publish(
                state.gateway_producer,
                PresenceChanged(user_id=user_id, status=PresenceStatus.OFFLINE),
                key=str(user_id),
            )


async def _heartbeat_loop(presence_store: PresenceStore, user_id: UUID) -> None:
    interval = settings.HEARTBEAT_INTERVAL_SECONDS
    while True:
        await asyncio.sleep(interval)
        await presence_store.heartbeat(user_id)


async def _handle_inbound(websocket: WebSocket, raw: object, *, user_id: UUID) -> None:
    state = websocket.app.state
    try:
        message = inbound_adapter.validate_python(raw)
    except ValidationError as exc:
        logger.debug("Bad inbound payload from {}: {}", user_id, exc)
        return

    match message:
        case AckMessage():
            return
        case ReadMessage(chat_id=chat_id, up_to_message_id=up_to_message_id):
            await publish(
                state.gateway_producer,
                MessageRead(chat_id=chat_id, reader_id=user_id, up_to_message_id=up_to_message_id),
                key=str(up_to_message_id),
            )
        case PingMessage():
            await websocket.send_json({"type": "pong"})
