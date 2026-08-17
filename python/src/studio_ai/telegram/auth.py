from aiogram.filters import Filter
from aiogram.types import CallbackQuery, Message

from studio_ai.config import Settings


class AuthorizedUserFilter(Filter):
    """Gate every message and callback to a single Telegram user id.

    Fails closed: if ALLOWED_TELEGRAM_USER_ID isn't configured, nothing
    matches.
    """

    def __init__(self, settings: Settings) -> None:
        self._allowed_user_id = settings.allowed_telegram_user_id

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        if self._allowed_user_id is None:
            return False
        user = event.from_user
        return user is not None and user.id == self._allowed_user_id
