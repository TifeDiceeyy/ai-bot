from collections.abc import AsyncIterator
from typing import Any

import pytest
from aiogram.exceptions import TelegramConflictError

from studio_ai.telegram.dispatcher import ConflictAwareDispatcher


class SessionStub:
    timeout = 10


class ConflictBotStub:
    session = SessionStub()

    async def __call__(self, method: object, **kwargs: Any) -> list[object]:
        del method, kwargs
        raise TelegramConflictError(
            method="getUpdates",  # type: ignore[arg-type]
            message="Conflict",
        )


@pytest.mark.asyncio
async def test_polling_conflict_is_not_retried() -> None:
    updates: AsyncIterator[object] = ConflictAwareDispatcher._listen_updates(
        ConflictBotStub(),  # type: ignore[arg-type]
    )
    with pytest.raises(TelegramConflictError):
        await anext(updates)
