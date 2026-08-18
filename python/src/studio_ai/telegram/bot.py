import asyncio
import logging
import sys
from io import BytesIO
from typing import cast

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramConflictError
from aiogram.filters import CommandStart
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from studio_ai.config import Settings, get_settings
from studio_ai.core.types import EditInput, EditQuality, ImageEditor
from studio_ai.runtime import Runtime, create_runtime
from studio_ai.telegram.auth import AuthorizedUserFilter
from studio_ai.telegram.dispatcher import ConflictAwareDispatcher
from studio_ai.telegram.lock import DuplicateInstanceError, ProcessLock
from studio_ai.telegram.pending_store import (
    InMemoryPendingStore,
    PendingEdit,
    PendingStore,
)

CONFLICT_EXIT_CODE = 78
LOGGER = logging.getLogger(__name__)


def editor_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Studio 1", callback_data="editor:banana"),
                InlineKeyboardButton(text="Studio 2", callback_data="editor:dream"),
            ]
        ]
    )


def quality_keyboard(editor: ImageEditor) -> InlineKeyboardMarkup:
    def label(name: str, quality: EditQuality) -> str:
        cost = editor.cost_for_quality(quality)
        return name if cost is None else f"{name} — ${cost:.2f}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=label("Natural", "natural"),
                    callback_data="quality:natural",
                ),
                InlineKeyboardButton(
                    text=label("Upscale", "upscale"),
                    callback_data="quality:upscale",
                ),
            ]
        ]
    )


async def _download_photo(bot: Bot, file_id: str) -> bytes | None:
    telegram_file = await bot.get_file(file_id)
    if not telegram_file.file_path:
        return None
    destination = BytesIO()
    await bot.download_file(telegram_file.file_path, destination=destination)
    return destination.getvalue()


def create_router(
    runtime: Runtime,
    pending_store: PendingStore,
    settings: Settings | None = None,
) -> Router:
    settings = settings or get_settings()
    router = Router()
    guard = AuthorizedUserFilter(settings)
    router.message.filter(guard)
    router.callback_query.filter(guard)

    @router.message(CommandStart())
    async def start(message: Message) -> None:
        await message.answer(
            "Send me a photo with a caption describing the edit "
            '(e.g. "change my shirt to blue"), or send the photo first and '
            "I'll ask what edit you want."
        )

    @router.message(F.photo)
    async def receive_photo(message: Message) -> None:
        if not message.photo:
            return
        largest = message.photo[-1]
        caption = message.caption.strip() if message.caption else None
        await pending_store.set(message.chat.id, PendingEdit(largest.file_id, caption))
        if caption:
            await message.answer("Pick a style:", reply_markup=editor_keyboard())
        else:
            await message.answer("Got the photo — now tell me what edit you'd like.")

    @router.message(F.text)
    async def receive_instruction(message: Message) -> None:
        job = await pending_store.get(message.chat.id)
        if job is None:
            await message.answer("Send a photo first, then describe the edit.")
            return
        if job.instruction:
            return
        job.instruction = message.text.strip() if message.text else ""
        await pending_store.set(message.chat.id, job)
        await message.answer("Pick a style:", reply_markup=editor_keyboard())

    @router.callback_query(F.data.startswith("editor:"))
    async def choose_editor(callback: CallbackQuery) -> None:
        message = callback.message
        if not isinstance(message, Message):
            await callback.answer()
            return
        codename = (callback.data or "").removeprefix("editor:")
        editor = runtime.editors.get(codename)
        job = await pending_store.get(message.chat.id)
        if job is None or not job.instruction or editor is None:
            await callback.answer(text="Nothing pending — send a photo first.")
            return
        job.editor_codename = codename
        await pending_store.set(message.chat.id, job)
        await callback.answer()
        await message.edit_text(
            "Pick a quality:", reply_markup=quality_keyboard(editor)
        )

    @router.callback_query(F.data.startswith("quality:"))
    async def choose_quality(callback: CallbackQuery, bot: Bot) -> None:
        message = callback.message
        if not isinstance(message, Message):
            await callback.answer()
            return
        quality_value = (callback.data or "").removeprefix("quality:")
        if quality_value not in ("natural", "upscale"):
            await callback.answer(text="Unknown quality.")
            return
        quality = cast(EditQuality, quality_value)
        job = await pending_store.get(message.chat.id)
        editor = (
            runtime.editors.get(job.editor_codename)
            if job and job.editor_codename
            else None
        )
        if job is None or not job.instruction or editor is None:
            await callback.answer(
                text="Nothing pending — send a photo and pick a style first."
            )
            return

        await pending_store.delete(message.chat.id)
        await callback.answer()
        await message.edit_text(f"Editing ({quality})…")
        engineer = runtime.engineers["natural-passthrough"]
        if not editor.is_available():
            await message.answer("Image editor is not available (missing FAL_KEY?).")
            return
        try:
            image = await _download_photo(bot, job.file_id)
            if image is None:
                await message.answer("Could not download that photo. Please try again.")
                return
            instruction = await engineer.engineer(image, job.instruction)
            result = await editor.edit(EditInput(image, instruction, quality))
            await message.answer_document(
                BufferedInputFile(result.image, filename="edited.png"),
                caption=f"{result.width}x{result.height}",
            )
        except Exception as error:
            LOGGER.exception("Edit failed for chat %s", message.chat.id)
            await message.answer(f"Edit failed: {error}")

    return router


async def main() -> None:
    settings = get_settings()
    if not settings.bot_token:
        raise RuntimeError(
            "BOT_TOKEN is not set. Copy .env.example to .env and fill it in."
        )

    runtime = create_runtime()
    bot = Bot(settings.bot_token)
    dispatcher = ConflictAwareDispatcher()
    dispatcher.include_router(
        create_router(runtime, InMemoryPendingStore(), settings)
    )
    me = await bot.get_me()
    LOGGER.info("Telegram bot @%s starting with long polling", me.username)
    await dispatcher.start_polling(bot)


def run() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )
    settings = get_settings()
    lock = ProcessLock(settings.bot_lock_path)
    try:
        with lock:
            asyncio.run(main())
    except DuplicateInstanceError as error:
        LOGGER.critical(
            "Cannot start: another Telegram bot is already running on this host: %s. "
            "Use `pm2 restart ai-bot` instead of starting the bot manually.",
            error,
        )
        raise SystemExit(CONFLICT_EXIT_CODE) from error
    except TelegramConflictError as error:
        LOGGER.critical(
            "Telegram polling stopped: another instance is already polling with "
            "this BOT_TOKEN. Stop the duplicate instance, then run "
            "`pm2 restart ai-bot`."
        )
        raise SystemExit(CONFLICT_EXIT_CODE) from error


if __name__ == "__main__":
    run()
