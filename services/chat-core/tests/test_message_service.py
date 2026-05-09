"""Verify the transactional-outbox invariant: a successful ``post_message``
writes the row AND enqueues a Kafka event in the same DB transaction."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from app.models.message import Message
from app.services.message import MessageService
from hexachat_shared.kafka.topics import CHAT_MESSAGES_V1


@pytest.mark.asyncio
async def test_post_message_writes_row_and_outbox_in_one_commit() -> None:
    chat_id, sender_id, member_id = uuid4(), uuid4(), uuid4()
    saved_message = Message(chat_id=chat_id, sender_id=sender_id, body="hello")
    saved_message.id = uuid4()

    session = AsyncMock()
    chat_service = AsyncMock()
    chat_service.assert_member = AsyncMock(return_value=None)

    chat_repo = AsyncMock()
    chat_repo.list_member_ids = AsyncMock(return_value=[sender_id, member_id])

    message_repo = AsyncMock()
    message_repo.add = AsyncMock(return_value=saved_message)

    enqueued: dict[str, Any] = {}

    async def _enqueue(*, topic: str, partition_key: str, payload: dict[str, Any]) -> None:
        enqueued.update(topic=topic, partition_key=partition_key, payload=payload)

    outbox_repo = AsyncMock()
    outbox_repo.enqueue = AsyncMock(side_effect=_enqueue)

    service = MessageService(
        session=session,
        chat_service=chat_service,
        chat_repo=chat_repo,
        message_repo=message_repo,
        outbox_repo=outbox_repo,
    )

    result = await service.post_message(chat_id=chat_id, sender_id=sender_id, body="hello")

    assert result is saved_message
    assert enqueued["topic"] == CHAT_MESSAGES_V1
    assert enqueued["partition_key"] == str(chat_id)
    assert enqueued["payload"]["message_id"] == str(saved_message.id)
    assert set(enqueued["payload"]["member_ids"]) == {str(sender_id), str(member_id)}

    session.commit.assert_awaited_once()
    message_repo.add.assert_awaited_once()
    outbox_repo.enqueue.assert_awaited_once()
