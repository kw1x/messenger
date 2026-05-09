from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Query, status

from app.api.deps import CurrentToken, MessageServiceDep, OutboxPublisherDep
from app.api.v1.schemas import MessagePage, MessageResponse, PostMessageRequest
from app.core.exceptions import InvalidPaginationCursorError
from app.repositories.message import decode_cursor, encode_cursor

router = APIRouter(prefix="/chats/{chat_id}/messages", tags=["messages"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Post a new message into the chat",
)
async def post_message(
    chat_id: UUID,
    payload: PostMessageRequest,
    service: MessageServiceDep,
    token: CurrentToken,
    publisher: OutboxPublisherDep,
    background: BackgroundTasks,
) -> MessageResponse:
    message = await service.post_message(chat_id=chat_id, sender_id=token.user_id, body=payload.body)
    background.add_task(publisher.notify)
    return MessageResponse.model_validate(message)


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="Paginated chat history (keyset, newest first)",
)
async def list_messages(
    chat_id: UUID,
    service: MessageServiceDep,
    token: CurrentToken,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: Annotated[str | None, Query(description="Opaque cursor returned by the previous page")] = None,
) -> MessagePage:
    decoded = None
    if cursor is not None:
        try:
            decoded = decode_cursor(cursor)
        except (ValueError, TypeError) as exc:
            raise InvalidPaginationCursorError from exc

    items = await service.list_history(chat_id=chat_id, viewer_id=token.user_id, limit=limit, cursor=decoded)
    next_cursor = encode_cursor(items[-1]) if len(items) == limit else None
    return MessagePage(
        items=[MessageResponse.model_validate(m) for m in items],
        next_cursor=next_cursor,
    )
