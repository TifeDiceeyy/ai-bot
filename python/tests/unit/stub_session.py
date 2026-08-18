from typing import Any

from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.methods import CopyMessage, TelegramMethod
from aiogram.types import Message, MessageId

TYPED_MESSAGE_RETURNS = {"SendMessage", "ForwardMessage"}


class StubSession(BaseSession):
    """Never touches the network; returns typed responses for methods whose
    return value handler code actually reads (message_id, chat id).
    """

    def __init__(self) -> None:
        super().__init__()
        self._next_message_id = 1000
        self.copy_calls: list[CopyMessage] = []

    async def close(self) -> None:
        return None

    async def make_request(
        self, bot: Bot, method: TelegramMethod[Any], timeout: int | None = None
    ) -> Any:
        del bot, timeout
        self._next_message_id += 1
        name = type(method).__name__
        if name == "CopyMessage":
            assert isinstance(method, CopyMessage)
            self.copy_calls.append(method)
            return MessageId(message_id=self._next_message_id)
        if name in TYPED_MESSAGE_RETURNS:
            chat_id = method.chat_id  # type: ignore[attr-defined]
            return Message.model_validate(
                {
                    "message_id": self._next_message_id,
                    "date": 0,
                    "chat": {"id": chat_id, "type": "private"},
                }
            )
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


def stub_bot(token: str = "123:test") -> Bot:
    return Bot(token, session=StubSession())
