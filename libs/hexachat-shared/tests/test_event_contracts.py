from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from hexachat_shared.auth.jwt import (
    JWTSettings,
    decode_access_token,
    encode_access_token,
)
from hexachat_shared.events import (
    MessageCreated,
    MessageDelivered,
    MessageRead,
    PresenceChanged,
)
from hexachat_shared.events.v1.presence import PresenceStatus
from hexachat_shared.kafka.topics import (
    CHAT_MESSAGES_V1,
    CHAT_RECEIPTS_V1,
    PRESENCE_EVENTS_V1,
)
from jwt.exceptions import PyJWTError


def _roundtrip[T](event: T) -> T:
    klass = type(event)
    return klass.model_validate_json(event.to_bytes())  # type: ignore[attr-defined,no-any-return]


def test_message_created_roundtrip() -> None:
    event = MessageCreated(
        message_id=uuid4(),
        chat_id=uuid4(),
        sender_id=uuid4(),
        body="hello",
        member_ids=[uuid4(), uuid4()],
    )
    assert _roundtrip(event) == event
    assert event.topic == CHAT_MESSAGES_V1


def test_receipt_events_roundtrip() -> None:
    delivered = MessageDelivered(message_id=uuid4(), chat_id=uuid4(), recipient_id=uuid4())
    read = MessageRead(chat_id=uuid4(), reader_id=uuid4(), up_to_message_id=uuid4())
    assert _roundtrip(delivered) == delivered
    assert _roundtrip(read) == read
    assert delivered.topic == read.topic == CHAT_RECEIPTS_V1


def test_presence_event_roundtrip() -> None:
    event = PresenceChanged(user_id=uuid4(), status=PresenceStatus.ONLINE)
    assert _roundtrip(event) == event
    assert event.topic == PRESENCE_EVENTS_V1


def test_jwt_roundtrip() -> None:
    settings = JWTSettings(secret_key="x" * 32, access_token_expires=timedelta(minutes=5))
    user_id = uuid4()
    token = encode_access_token(user_id=user_id, username="alice", settings=settings)

    payload = decode_access_token(token, settings=settings)
    assert payload.user_id == user_id
    assert payload.username == "alice"
    assert payload.exp > datetime.now(UTC)


def test_jwt_invalid_secret_rejected() -> None:
    settings = JWTSettings(secret_key="x" * 32)
    other = JWTSettings(secret_key="y" * 32)
    token = encode_access_token(user_id=uuid4(), username="alice", settings=settings)

    with pytest.raises(PyJWTError):
        decode_access_token(token, settings=other)
