from dataclasses import dataclass


@dataclass(slots=True)
class ContactInfo:
    chat_id: int
    label: str


class ContactInbox:
    """Open contact threads from unauthorized users, keyed by their chat id.

    In-memory only: lost on restart, same tradeoff as InMemoryPendingStore.
    """

    def __init__(self) -> None:
        self._threads: dict[int, ContactInfo] = {}

    def remember(self, chat_id: int, label: str) -> None:
        self._threads[chat_id] = ContactInfo(chat_id, label)

    def get(self, chat_id: int) -> ContactInfo | None:
        return self._threads.get(chat_id)

    def list_threads(self) -> list[ContactInfo]:
        return list(self._threads.values())


class AdminReplyState:
    """Which contact-thread chat id each admin is currently replying to."""

    def __init__(self) -> None:
        self._target_by_admin: dict[int, int] = {}

    def set(self, admin_chat_id: int, target_chat_id: int) -> None:
        self._target_by_admin[admin_chat_id] = target_chat_id

    def get(self, admin_chat_id: int) -> int | None:
        return self._target_by_admin.get(admin_chat_id)

    def clear(self, admin_chat_id: int) -> bool:
        return self._target_by_admin.pop(admin_chat_id, None) is not None
