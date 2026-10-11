from typing import Any

import pytest
from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import SetMyCommands, TelegramMethod

from studio_ai.editors.fal_editor import FalEditor, QualityTier
from studio_ai.telegram.bot import (
    CONFLICT_EXIT_CODE,
    bot_commands,
    quality_keyboard,
    register_commands,
)

TEST_TOKEN = "42:TEST"


class RecordingSession(BaseSession):
    """Records Telegram calls instead of sending them; optionally fails them."""

    def __init__(self, fail: bool = False) -> None:
        super().__init__()
        self.fail = fail
        self.calls: list[TelegramMethod[Any]] = []

    async def close(self) -> None:
        return None

    async def make_request(
        self, bot: Bot, method: TelegramMethod[Any], timeout: int | None = None
    ) -> Any:
        del bot, timeout
        self.calls.append(method)
        if self.fail:
            raise TelegramBadRequest(method=method, message="Bad Request: test")
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
        if False:  # pragma: no cover - makes this an async generator
            yield b""


def test_conflict_exit_code_is_dedicated() -> None:
    assert CONFLICT_EXIT_CODE == 78


def test_quality_keyboard_uses_editor_costs() -> None:
    editor = FalEditor(
        id="test",
        endpoint="test/endpoint",
        quality={
            "natural": QualityTier({}, 0.15),
            "upscale": QualityTier({}, 0.30),
        },
    )
    keyboard = quality_keyboard(editor)
    buttons = keyboard.inline_keyboard[0]
    assert [button.text for button in buttons] == [
        "Natural — $0.15",
        "Upscale — $0.30",
    ]


def test_bot_commands_lists_start_for_the_menu_button() -> None:
    assert [(c.command, c.description) for c in bot_commands()] == [
        ("start", "Start a new edit"),
    ]


async def test_register_commands_sends_set_my_commands() -> None:
    session = RecordingSession()
    await register_commands(Bot(TEST_TOKEN, session=session))
    assert len(session.calls) == 1
    call = session.calls[0]
    assert isinstance(call, SetMyCommands)
    assert call.commands == bot_commands()


async def test_register_commands_failure_does_not_stop_the_bot(
    caplog: pytest.LogCaptureFixture,
) -> None:
    session = RecordingSession(fail=True)
    await register_commands(Bot(TEST_TOKEN, session=session))
    assert "Could not register bot commands" in caplog.text
