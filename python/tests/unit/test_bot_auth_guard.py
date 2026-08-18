from pathlib import Path
from typing import Literal

from aiogram import Dispatcher
from aiogram.types import Update
from stub_session import stub_bot as _bot

from studio_ai.config import Settings
from studio_ai.core.types import EditInput, EditResult
from studio_ai.runtime import Runtime
from studio_ai.telegram.authorized_users import AuthorizedUserStore
from studio_ai.telegram.bot import create_router
from studio_ai.telegram.pending_store import InMemoryPendingStore, PendingEdit

ALLOWED = 42
OTHER = 999


class ExplodingEditor:
    id = "banana"
    license: Literal["commercial-ok"] = "commercial-ok"

    def is_available(self) -> bool:
        raise AssertionError("is_available() must not run for an unauthorized user")

    def cost_for_quality(self, quality: str) -> float | None:
        del quality
        return None

    async def edit(self, edit_input: EditInput) -> EditResult:
        del edit_input
        raise AssertionError("edit() must not run for an unauthorized user")


class ExplodingEngineer:
    id = "natural-passthrough"

    async def engineer(self, image: bytes, user_prompt: str) -> str:
        del image, user_prompt
        raise AssertionError("engineer() must not run for an unauthorized user")


def _runtime() -> Runtime:
    return Runtime(
        editors={"banana": ExplodingEditor()},  # type: ignore[dict-item]
        engineers={"natural-passthrough": ExplodingEngineer()},
    )


def _dispatcher(pending_store: InMemoryPendingStore, tmp_path: Path) -> Dispatcher:
    settings = Settings(ALLOWED_TELEGRAM_USER_ID=ALLOWED)
    user_store = AuthorizedUserStore(tmp_path / "authorized_users.json", ALLOWED)
    dispatcher = Dispatcher()
    dispatcher.include_router(
        create_router(_runtime(), pending_store, settings, user_store)
    )
    return dispatcher


def _from_user(user_id: int) -> dict[str, object]:
    return {"id": user_id, "is_bot": False, "first_name": "T"}


def _photo_update(update_id: int, user_id: int) -> Update:
    return Update.model_validate(
        {
            "update_id": update_id,
            "message": {
                "message_id": update_id,
                "date": 0,
                "chat": {"id": user_id, "type": "private"},
                "from": _from_user(user_id),
                "caption": "make it blue",
                "photo": [
                    {
                        "file_id": "file-1",
                        "file_unique_id": "u1",
                        "width": 10,
                        "height": 10,
                    }
                ],
            },
        }
    )


def _text_update(update_id: int, user_id: int, text: str) -> Update:
    return Update.model_validate(
        {
            "update_id": update_id,
            "message": {
                "message_id": update_id,
                "date": 0,
                "chat": {"id": user_id, "type": "private"},
                "from": _from_user(user_id),
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
                "from": _from_user(user_id),
                "chat_instance": "1",
                "data": data,
                "message": {
                    "message_id": 1,
                    "date": 0,
                    "chat": {"id": user_id, "type": "private"},
                    "text": "Pick a style:",
                },
            },
        }
    )


async def test_unauthorized_photo_never_reaches_pending_store(tmp_path: Path) -> None:
    pending_store = InMemoryPendingStore()
    dispatcher = _dispatcher(pending_store, tmp_path)
    bot = _bot()

    await dispatcher.feed_update(bot, _photo_update(1, OTHER))

    assert await pending_store.get(OTHER) is None


async def test_unauthorized_instruction_never_reaches_pending_store(
    tmp_path: Path,
) -> None:
    pending_store = InMemoryPendingStore()
    dispatcher = _dispatcher(pending_store, tmp_path)
    bot = _bot()

    await dispatcher.feed_update(bot, _text_update(1, OTHER, "make it blue"))

    assert await pending_store.get(OTHER) is None


async def test_unauthorized_editor_choice_never_calls_editor(tmp_path: Path) -> None:
    pending_store = InMemoryPendingStore()
    await pending_store.set(OTHER, PendingEdit("file-1", "make it blue"))
    dispatcher = _dispatcher(pending_store, tmp_path)
    bot = _bot()

    # If the guard didn't hold, choose_editor would read runtime.editors and
    # ExplodingEditor.is_available()/edit() would raise AssertionError.
    await dispatcher.feed_update(bot, _callback_update(1, OTHER, "editor:banana"))

    job = await pending_store.get(OTHER)
    assert job is not None
    assert job.editor_codename is None


async def test_unauthorized_quality_choice_never_downloads_or_calls_provider(
    tmp_path: Path,
) -> None:
    pending_store = InMemoryPendingStore()
    await pending_store.set(
        OTHER, PendingEdit("file-1", "make it blue", "banana")
    )
    dispatcher = _dispatcher(pending_store, tmp_path)
    bot = _bot()

    # If the guard didn't hold, this would reach _download_photo() (a real
    # network call) and then ExplodingEditor.edit()/ExplodingEngineer.engineer().
    await dispatcher.feed_update(bot, _callback_update(1, OTHER, "quality:natural"))

    # The pending job is only deleted once quality selection actually runs.
    assert await pending_store.get(OTHER) is not None


async def test_authorized_photo_reaches_pending_store(tmp_path: Path) -> None:
    pending_store = InMemoryPendingStore()
    dispatcher = _dispatcher(pending_store, tmp_path)
    bot = _bot()

    await dispatcher.feed_update(bot, _photo_update(1, ALLOWED))

    job = await pending_store.get(ALLOWED)
    assert job is not None
    assert job.file_id == "file-1"
    assert job.instruction == "make it blue"
