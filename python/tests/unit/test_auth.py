from aiogram.types import CallbackQuery, Message

from studio_ai.config import Settings
from studio_ai.telegram.auth import AuthorizedUserFilter

ALLOWED = 42
OTHER = 999


def _message(user_id: int | None) -> Message:
    payload: dict[str, object] = {
        "message_id": 1,
        "date": 0,
        "chat": {"id": 1, "type": "private"},
        "text": "/start",
    }
    if user_id is not None:
        payload["from"] = {"id": user_id, "is_bot": False, "first_name": "T"}
    return Message.model_validate(payload)


def _callback(user_id: int) -> CallbackQuery:
    return CallbackQuery.model_validate(
        {
            "id": "1",
            "from": {"id": user_id, "is_bot": False, "first_name": "T"},
            "chat_instance": "1",
            "data": "editor:banana",
        }
    )


async def test_allows_the_configured_user() -> None:
    guard = AuthorizedUserFilter(Settings(ALLOWED_TELEGRAM_USER_ID=ALLOWED))

    assert await guard(_message(ALLOWED)) is True


async def test_rejects_every_other_user() -> None:
    guard = AuthorizedUserFilter(Settings(ALLOWED_TELEGRAM_USER_ID=ALLOWED))

    assert await guard(_message(OTHER)) is False


async def test_fails_closed_when_unset() -> None:
    guard = AuthorizedUserFilter(Settings(ALLOWED_TELEGRAM_USER_ID=None))

    assert await guard(_message(ALLOWED)) is False


async def test_rejects_events_with_no_user() -> None:
    guard = AuthorizedUserFilter(Settings(ALLOWED_TELEGRAM_USER_ID=ALLOWED))

    assert await guard(_message(None)) is False


async def test_callback_queries_are_gated_the_same_way() -> None:
    guard = AuthorizedUserFilter(Settings(ALLOWED_TELEGRAM_USER_ID=ALLOWED))

    assert await guard(_callback(ALLOWED)) is True
    assert await guard(_callback(OTHER)) is False
