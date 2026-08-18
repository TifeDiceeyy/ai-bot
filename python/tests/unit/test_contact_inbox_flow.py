from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from stub_session import StubSession

from studio_ai.config import Settings
from studio_ai.runtime import Runtime
from studio_ai.telegram.authorized_users import AuthorizedUserStore
from studio_ai.telegram.bot import INBOX_SELECT_PREFIX, create_router
from studio_ai.telegram.pending_store import InMemoryPendingStore

ADMIN = 42
STRANGER = 999


def _dispatcher(store: AuthorizedUserStore) -> tuple[Dispatcher, Bot, StubSession]:
    settings = Settings(ALLOWED_TELEGRAM_USER_ID=ADMIN)
    runtime = Runtime(editors={}, engineers={})
    dispatcher = Dispatcher()
    dispatcher.include_router(
        create_router(runtime, InMemoryPendingStore(), settings, store)
    )
    session = StubSession()
    bot = Bot("123:test", session=session)
    return dispatcher, bot, session


def _text_update(update_id: int, user_id: int, text: str) -> Update:
    return Update.model_validate(
        {
            "update_id": update_id,
            "message": {
                "message_id": update_id,
                "date": 0,
                "chat": {"id": user_id, "type": "private"},
                "from": {"id": user_id, "is_bot": False, "first_name": "T"},
                "text": text,
            },
        }
    )


def _callback_update(update_id: int, user_id: int, data: str) -> Update:
    return Update.model_validate(
        {
            "update_id": update_id,
            "callback_query": {
                "id": str(update_id),
                "from": {"id": user_id, "is_bot": False, "first_name": "A"},
                "chat_instance": "1",
                "data": data,
                "message": {
                    "message_id": 1,
                    "date": 0,
                    "chat": {"id": user_id, "type": "private"},
                    "text": "New message from T (id=999):",
                },
            },
        }
    )


async def test_select_then_reply_relays_message_to_the_right_stranger(
    tmp_path: Path,
) -> None:
    store = AuthorizedUserStore(tmp_path / "users.json", ADMIN)
    dispatcher, bot, session = _dispatcher(store)

    await dispatcher.feed_update(bot, _text_update(1, STRANGER, "need help please"))
    await dispatcher.feed_update(
        bot, _callback_update(2, ADMIN, f"{INBOX_SELECT_PREFIX}{STRANGER}")
    )
    await dispatcher.feed_update(bot, _text_update(3, ADMIN, "sure, what's up?"))

    assert len(session.copy_calls) == 1
    relayed = session.copy_calls[0]
    assert relayed.chat_id == STRANGER
    assert relayed.from_chat_id == ADMIN


async def test_plain_text_without_selecting_a_thread_is_not_relayed(
    tmp_path: Path,
) -> None:
    store = AuthorizedUserStore(tmp_path / "users.json", ADMIN)
    dispatcher, bot, session = _dispatcher(store)

    await dispatcher.feed_update(bot, _text_update(1, STRANGER, "need help please"))
    await dispatcher.feed_update(bot, _text_update(2, ADMIN, "just chatting"))

    assert session.copy_calls == []


async def test_done_stops_relaying_further_messages(tmp_path: Path) -> None:
    store = AuthorizedUserStore(tmp_path / "users.json", ADMIN)
    dispatcher, bot, session = _dispatcher(store)

    await dispatcher.feed_update(bot, _text_update(1, STRANGER, "need help please"))
    await dispatcher.feed_update(
        bot, _callback_update(2, ADMIN, f"{INBOX_SELECT_PREFIX}{STRANGER}")
    )
    await dispatcher.feed_update(bot, _text_update(3, ADMIN, "/done"))
    await dispatcher.feed_update(bot, _text_update(4, ADMIN, "no longer relayed"))

    assert session.copy_calls == []


async def test_multiple_strangers_do_not_cross_wire(tmp_path: Path) -> None:
    store = AuthorizedUserStore(tmp_path / "users.json", ADMIN)
    dispatcher, bot, session = _dispatcher(store)
    other_stranger = 555

    await dispatcher.feed_update(bot, _text_update(1, STRANGER, "hi from stranger 1"))
    await dispatcher.feed_update(
        bot, _text_update(2, other_stranger, "hi from stranger 2")
    )

    await dispatcher.feed_update(
        bot, _callback_update(3, ADMIN, f"{INBOX_SELECT_PREFIX}{other_stranger}")
    )
    await dispatcher.feed_update(bot, _text_update(4, ADMIN, "reply for #2"))

    assert len(session.copy_calls) == 1
    assert session.copy_calls[0].chat_id == other_stranger
