import asyncio
import logging
import sys
from io import BytesIO
from typing import cast

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError, TelegramConflictError
from aiogram.filters import Command, CommandObject, CommandStart, Filter
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
from studio_ai.telegram.auth import AuthorizedUserFilter, UnauthorizedUserFilter
from studio_ai.telegram.authorized_users import AuthorizedUserStore
from studio_ai.telegram.contact_inbox import AdminReplyState, ContactInbox
from studio_ai.telegram.dispatcher import ConflictAwareDispatcher
from studio_ai.telegram.lock import DuplicateInstanceError, ProcessLock
from studio_ai.telegram.pending_store import (
    InMemoryPendingStore,
    PendingEdit,
    PendingStore,
)

CONFLICT_EXIT_CODE = 78
LOGGER = logging.getLogger(__name__)

INBOX_OPEN_CALLBACK = "inbox:open"
INBOX_SELECT_PREFIX = "inbox:select:"


class ActiveReplyFilter(Filter):
    """Matches a plain-text message from an admin currently in reply mode.

    Commands (leading "/") are excluded so /done, /promote, etc. still work
    while replying. Returns the resolved target chat id as extra handler
    kwargs (aiogram's dict-return filter convention).
    """

    def __init__(self, state: AdminReplyState) -> None:
        self._state = state

    async def __call__(self, message: Message) -> bool | dict[str, object]:
        if message.text and message.text.startswith("/"):
            return False
        target_chat_id = self._state.get(message.chat.id)
        if target_chat_id is None:
            return False
        return {"target_chat_id": target_chat_id}


def inbox_keyboard(threads: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=label, callback_data=f"{INBOX_SELECT_PREFIX}{chat_id}"
                )
            ]
            for chat_id, label in threads
        ]
    )


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
    user_store: AuthorizedUserStore | None = None,
) -> Router:
    settings = settings or get_settings()
    user_store = user_store or AuthorizedUserStore(
        settings.authorized_users_path, settings.allowed_telegram_user_id
    )
    router = Router()
    guard = AuthorizedUserFilter(user_store)
    inbox = ContactInbox()
    reply_state = AdminReplyState()

    @router.message(CommandStart(), guard)
    async def start(message: Message) -> None:
        await message.answer(
            "Send me a photo with a caption describing the edit "
            '(e.g. "change my shirt to blue"), or send the photo first and '
            "I'll ask what edit you want."
        )

    @router.message(Command("promote"), guard)
    async def promote(message: Message, command: CommandObject) -> None:
        target = (command.args or "").strip()
        if not target.lstrip("-").isdigit():
            await message.answer("Usage: /promote <telegram_user_id>")
            return
        user_store.add(int(target))
        await message.answer(f"User {target} is now authorized.")

    @router.message(Command("revoke"), guard)
    async def revoke(message: Message, command: CommandObject) -> None:
        target = (command.args or "").strip()
        if not target.lstrip("-").isdigit():
            await message.answer("Usage: /revoke <telegram_user_id>")
            return
        if user_store.remove(int(target)):
            await message.answer(f"User {target} is no longer authorized.")
        else:
            await message.answer(f"User {target} wasn't authorized.")

    @router.message(Command("done"), guard)
    async def done(message: Message) -> None:
        if reply_state.clear(message.chat.id):
            await message.answer("Stopped replying.")
        else:
            await message.answer("You weren't replying to anyone.")

    def _inbox_reply() -> tuple[str, InlineKeyboardMarkup | None]:
        threads = [(t.chat_id, t.label) for t in inbox.list_threads()]
        if not threads:
            return "Inbox is empty.", None
        return "Open contact threads:", inbox_keyboard(threads)

    @router.message(Command("inbox"), guard)
    async def inbox_command(message: Message) -> None:
        text, markup = _inbox_reply()
        await message.answer(text, reply_markup=markup)

    @router.callback_query(guard, F.data == INBOX_OPEN_CALLBACK)
    async def open_inbox(callback: CallbackQuery) -> None:
        message = callback.message
        if not isinstance(message, Message):
            await callback.answer()
            return
        text, markup = _inbox_reply()
        await message.answer(text, reply_markup=markup)
        await callback.answer()

    @router.callback_query(guard, F.data.startswith(INBOX_SELECT_PREFIX))
    async def select_thread(callback: CallbackQuery) -> None:
        message = callback.message
        if not isinstance(message, Message):
            await callback.answer()
            return
        target_chat_id = int((callback.data or "").removeprefix(INBOX_SELECT_PREFIX))
        thread = inbox.get(target_chat_id)
        reply_state.set(message.chat.id, target_chat_id)
        label = thread.label if thread else str(target_chat_id)
        await callback.answer()
        await message.answer(
            f"Replying to {label}. Send your message, or /done to stop."
        )

    @router.message(guard, ActiveReplyFilter(reply_state))
    async def send_reply(message: Message, bot: Bot, target_chat_id: int) -> None:
        try:
            await bot.copy_message(
                chat_id=target_chat_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id,
            )
        except TelegramAPIError as error:
            LOGGER.warning(
                "Failed to relay admin reply to %s: %s", target_chat_id, error
            )
            await message.reply(f"Could not deliver: {error}")
            return
        await message.reply("Sent.")

    @router.message(UnauthorizedUserFilter(user_store))
    async def contact_admin(message: Message, bot: Bot) -> None:
        admin_ids = user_store.list_ids()
        user = message.from_user
        if user is None:
            return
        who = f"{user.full_name} (id={user.id})" + (
            f" @{user.username}" if user.username else ""
        )
        inbox.remember(message.chat.id, who)
        for admin_id in admin_ids:
            try:
                await bot.send_message(
                    admin_id,
                    f"New message from {who}:",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="View inbox",
                                    callback_data=INBOX_OPEN_CALLBACK,
                                )
                            ]
                        ]
                    ),
                )
                await bot.forward_message(
                    chat_id=admin_id,
                    from_chat_id=message.chat.id,
                    message_id=message.message_id,
                )
            except TelegramAPIError as error:
                LOGGER.warning(
                    "Failed to relay contact message to admin %s: %s",
                    admin_id,
                    error,
                )
        if admin_ids:
            await message.answer(
                "You're not authorized to use this bot. Your message has been "
                "forwarded to the admin."
            )
        else:
            await message.answer("You're not authorized to use this bot.")

    @router.message(guard, F.photo)
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

    @router.message(guard, F.text)
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

    @router.callback_query(guard, F.data.startswith("editor:"))
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

    @router.callback_query(guard, F.data.startswith("quality:"))
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
