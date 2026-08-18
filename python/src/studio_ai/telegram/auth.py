from aiogram.filters import Filter
from aiogram.types import CallbackQuery, Message

from studio_ai.telegram.authorized_users import AuthorizedUserStore


def _is_authorized(
    event: Message | CallbackQuery, store: AuthorizedUserStore
) -> bool:
    user = event.from_user
    return user is not None and store.is_authorized(user.id)


class AuthorizedUserFilter(Filter):
    """Gate a handler to users in the AuthorizedUserStore.

    Fails closed: an empty store (e.g. ALLOWED_TELEGRAM_USER_ID never set)
    matches nothing.
    """

    def __init__(self, store: AuthorizedUserStore) -> None:
        self._store = store

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        return _is_authorized(event, self._store)


class UnauthorizedUserFilter(Filter):
    """The inverse of AuthorizedUserFilter, for the contact-admin fallback."""

    def __init__(self, store: AuthorizedUserStore) -> None:
        self._store = store

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        return not _is_authorized(event, self._store)
