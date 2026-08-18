from pathlib import Path

from aiogram.types import CallbackQuery, Message

from studio_ai.telegram.auth import AuthorizedUserFilter, UnauthorizedUserFilter
from studio_ai.telegram.authorized_users import AuthorizedUserStore

ALLOWED = 42
OTHER = 999


def _store(tmp_path: Path, bootstrap: int | None) -> AuthorizedUserStore:
    return AuthorizedUserStore(tmp_path / "authorized_users.json", bootstrap)


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


async def test_allows_the_configured_user(tmp_path: Path) -> None:
    guard = AuthorizedUserFilter(_store(tmp_path, ALLOWED))

    assert await guard(_message(ALLOWED)) is True


async def test_rejects_every_other_user(tmp_path: Path) -> None:
    guard = AuthorizedUserFilter(_store(tmp_path, ALLOWED))

    assert await guard(_message(OTHER)) is False


async def test_fails_closed_when_unset(tmp_path: Path) -> None:
    guard = AuthorizedUserFilter(_store(tmp_path, None))

    assert await guard(_message(ALLOWED)) is False


async def test_rejects_events_with_no_user(tmp_path: Path) -> None:
    guard = AuthorizedUserFilter(_store(tmp_path, ALLOWED))

    assert await guard(_message(None)) is False


async def test_callback_queries_are_gated_the_same_way(tmp_path: Path) -> None:
    guard = AuthorizedUserFilter(_store(tmp_path, ALLOWED))

    assert await guard(_callback(ALLOWED)) is True
    assert await guard(_callback(OTHER)) is False


async def test_unauthorized_filter_is_the_inverse(tmp_path: Path) -> None:
    guard = UnauthorizedUserFilter(_store(tmp_path, ALLOWED))

    assert await guard(_message(ALLOWED)) is False
    assert await guard(_message(OTHER)) is True
