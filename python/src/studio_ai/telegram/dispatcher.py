import logging
from collections.abc import AsyncGenerator

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramConflictError
from aiogram.methods import GetUpdates
from aiogram.types import Update
from aiogram.utils.backoff import Backoff, BackoffConfig

LOGGER = logging.getLogger(__name__)
DEFAULT_BACKOFF = BackoffConfig(min_delay=1.0, max_delay=5.0, factor=1.3, jitter=0.1)


class ConflictAwareDispatcher(Dispatcher):
    """Preserve aiogram backoff, but never retry a duplicate poller conflict."""

    @classmethod
    async def _listen_updates(
        cls,
        bot: Bot,
        polling_timeout: int = 30,
        backoff_config: BackoffConfig = DEFAULT_BACKOFF,
        allowed_updates: list[str] | None = None,
    ) -> AsyncGenerator[Update]:
        del cls
        backoff = Backoff(config=backoff_config)
        get_updates = GetUpdates(
            timeout=polling_timeout,
            allowed_updates=allowed_updates,
        )
        request_timeout = (
            int(bot.session.timeout + polling_timeout)
            if bot.session.timeout
            else None
        )
        failed = False

        while True:
            try:
                updates = await bot(
                    get_updates,
                    request_timeout=request_timeout,
                )
            except TelegramConflictError:
                raise
            except Exception as error:
                failed = True
                LOGGER.error("Failed to fetch updates: %s", error)
                LOGGER.warning(
                    "Retrying Telegram after %.2f seconds (attempt %d)",
                    backoff.next_delay,
                    backoff.counter,
                )
                await backoff.asleep()
                continue

            if failed:
                LOGGER.info("Telegram connection restored")
                backoff.reset()
                failed = False

            for update in updates:
                yield update
                get_updates.offset = update.update_id + 1
