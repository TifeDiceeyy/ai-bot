from pathlib import Path
from typing import Any, Literal

from aiogram import Bot, Dispatcher
from aiogram.client.session.base import BaseSession
from aiogram.methods import TelegramMethod
from aiogram.types import Update

from studio_ai.config import Settings
from studio_ai.core.types import EditInput, EditResult
from studio_ai.runtime import Runtime
from studio_ai.telegram.bot import create_router
from studio_ai.telegram.egress_budget import FREE_TIER_EGRESS_BYTES, MonthlyEgressBudget
from studio_ai.telegram.pending_store import InMemoryPendingStore, PendingEdit

ALLOWED = 42


class StubSession(BaseSession):
    async def close(self) -> None:
        return None

    async def make_request(
        self, bot: Bot, method: TelegramMethod[Any], timeout: int | None = None
    ) -> Any:
        del bot, method, timeout
        return True

    async def stream_content(
        self,
        url: str,
        headers: dict[str, Any] | None = None,
        timeout: int = 30,
        chunk_size: int = 65536,
        raise_for_status: bool = True,
    ) -> Any:
        del url, headers, timeout, chunk_size, raise_for_status
        if False:  # pragma: no cover
            yield b""


def _bot() -> Bot:
    return Bot("123:test", session=StubSession())


class ExplodingEditor:
    id = "banana"
    license: Literal["commercial-ok"] = "commercial-ok"

    def is_available(self) -> bool:
        raise AssertionError("is_available() must not run once the budget is spent")

    def cost_for_quality(self, quality: str) -> float | None:
        del quality
        return None

    async def edit(self, edit_input: EditInput) -> EditResult:
        del edit_input
        raise AssertionError("edit() must not run once the budget is spent")


class ExplodingEngineer:
    id = "natural-passthrough"

    async def engineer(self, image: bytes, user_prompt: str) -> str:
        del image, user_prompt
        raise AssertionError("engineer() must not run once the budget is spent")


def _runtime() -> Runtime:
    return Runtime(
        editors={"banana": ExplodingEditor()},  # type: ignore[dict-item]
        engineers={"natural-passthrough": ExplodingEngineer()},
    )


def _dispatcher(
    pending_store: InMemoryPendingStore, budget: MonthlyEgressBudget
) -> Dispatcher:
    settings = Settings(ALLOWED_TELEGRAM_USER_ID=ALLOWED)
    dispatcher = Dispatcher()
    dispatcher.include_router(
        create_router(_runtime(), pending_store, settings, budget)
    )
    return dispatcher


def _callback_update(update_id: int, user_id: int, data: str) -> Update:
    return Update.model_validate(
        {
            "update_id": update_id,
            "callback_query": {
                "id": str(update_id),
                "from": {"id": user_id, "is_bot": False, "first_name": "T"},
                "chat_instance": "1",
                "data": data,
                "message": {
                    "message_id": 1,
                    "date": 0,
                    "chat": {"id": user_id, "type": "private"},
                    "text": "Pick a quality:",
                },
            },
        }
    )


async def test_quality_choice_is_blocked_once_the_monthly_budget_is_spent(
    tmp_path: Path,
) -> None:
    budget = MonthlyEgressBudget(tmp_path / "egress_budget.json")
    budget.record(FREE_TIER_EGRESS_BYTES)  # fully exhaust this month's budget

    pending_store = InMemoryPendingStore()
    await pending_store.set(ALLOWED, PendingEdit("file-1", "make it blue", "banana"))
    dispatcher = _dispatcher(pending_store, budget)

    # If the budget check didn't hold, this would reach _download_photo()
    # (a real network call) and then ExplodingEditor.edit().
    update = _callback_update(1, ALLOWED, "quality:natural")
    await dispatcher.feed_update(_bot(), update)

    # The pending job is only deleted once the edit actually runs.
    assert await pending_store.get(ALLOWED) is not None
