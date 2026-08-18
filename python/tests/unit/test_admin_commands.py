from pathlib import Path

from aiogram import Dispatcher
from aiogram.types import Update
from stub_session import stub_bot as _bot

from studio_ai.config import Settings
from studio_ai.runtime import Runtime
from studio_ai.telegram.authorized_users import AuthorizedUserStore
from studio_ai.telegram.bot import create_router
from studio_ai.telegram.pending_store import InMemoryPendingStore

ADMIN = 42
STRANGER = 999


def _dispatcher(store: AuthorizedUserStore) -> Dispatcher:
    settings = Settings(ALLOWED_TELEGRAM_USER_ID=ADMIN)
    runtime = Runtime(editors={}, engineers={})
    dispatcher = Dispatcher()
    dispatcher.include_router(
        create_router(runtime, InMemoryPendingStore(), settings, store)
    )
    return dispatcher


def _command_update(update_id: int, user_id: int, text: str) -> Update:
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


async def test_admin_can_promote_a_new_user(tmp_path: Path) -> None:
    store = AuthorizedUserStore(tmp_path / "users.json", ADMIN)
    dispatcher = _dispatcher(store)

    await dispatcher.feed_update(
        _bot(), _command_update(1, ADMIN, "/promote 555")
    )

    assert store.is_authorized(555)


async def test_non_admin_cannot_promote(tmp_path: Path) -> None:
    store = AuthorizedUserStore(tmp_path / "users.json", ADMIN)
    dispatcher = _dispatcher(store)

    await dispatcher.feed_update(
        _bot(), _command_update(1, STRANGER, "/promote 555")
    )

    assert not store.is_authorized(555)


async def test_admin_can_revoke_access(tmp_path: Path) -> None:
    store = AuthorizedUserStore(tmp_path / "users.json", ADMIN)
    store.add(555)
    dispatcher = _dispatcher(store)

    await dispatcher.feed_update(_bot(), _command_update(1, ADMIN, "/revoke 555"))

    assert not store.is_authorized(555)


async def test_promote_rejects_a_non_numeric_argument(tmp_path: Path) -> None:
    store = AuthorizedUserStore(tmp_path / "users.json", ADMIN)
    dispatcher = _dispatcher(store)

    await dispatcher.feed_update(
        _bot(), _command_update(1, ADMIN, "/promote not-a-number")
    )

    assert store.list_ids() == [ADMIN]
