from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import ChatServiceDep, CurrentToken
from app.api.v1.schemas import AddMemberRequest, ChatResponse, CreateChatRequest

router = APIRouter(prefix="/chats", tags=["chats"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a direct or group chat",
)
async def create_chat(
    payload: CreateChatRequest,
    service: ChatServiceDep,
    token: CurrentToken,
) -> ChatResponse:
    member_ids = list({*payload.member_ids, token.user_id})
    chat = await service.create_chat(kind=payload.kind, title=payload.title, member_ids=member_ids)
    return ChatResponse.model_validate(chat)


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="List chats the current user belongs to",
)
async def list_chats(service: ChatServiceDep, token: CurrentToken) -> list[ChatResponse]:
    chats = await service.list_my_chats(token.user_id)
    return [ChatResponse.model_validate(c) for c in chats]


@router.post(
    "/{chat_id}/members",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Add a member to an existing chat",
)
async def add_member(
    chat_id: UUID,
    payload: AddMemberRequest,
    service: ChatServiceDep,
    token: CurrentToken,
) -> None:
    await service.add_member(chat_id=chat_id, requester_id=token.user_id, new_member_id=payload.user_id)
