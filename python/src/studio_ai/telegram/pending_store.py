from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class PendingEdit:
    file_id: str
    instruction: str | None = None
    editor_codename: str | None = None


class PendingStore(Protocol):
    async def get(self, chat_id: int) -> PendingEdit | None: ...
    async def set(self, chat_id: int, edit: PendingEdit) -> None: ...
    async def delete(self, chat_id: int) -> None: ...


class InMemoryPendingStore:
    def __init__(self) -> None:
        self._data: dict[int, PendingEdit] = {}

    async def get(self, chat_id: int) -> PendingEdit | None:
        return self._data.get(chat_id)

    async def set(self, chat_id: int, edit: PendingEdit) -> None:
        self._data[chat_id] = edit

    async def delete(self, chat_id: int) -> None:
        self._data.pop(chat_id, None)
