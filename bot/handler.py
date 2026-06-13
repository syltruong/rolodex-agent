import logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.error import NetworkError, TimedOut
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from agent import ConversationManager
from bot.formatting import md_to_html

logger = logging.getLogger("rolodex.bot")


def setup_handlers(app: Application, conversations: ConversationManager) -> None:
    app.add_handler(CommandHandler("start", _start))
    app.add_handler(CommandHandler("clear", _make_clear(conversations)))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _make_chat(conversations)))
    app.add_error_handler(_error_handler)


async def _error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    if isinstance(context.error, (NetworkError, TimedOut)):
        logger.warning("Network error (transient): %s", context.error)
    else:
        logger.exception("Unhandled error", exc_info=context.error)


async def _start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hello! I'm Rolodex, your personal CRM assistant.\n"
        "Send me a brief about a conversation you just had, or ask me about a person.\n\n"
        "/clear — reset conversation history",
        parse_mode=ParseMode.HTML,
    )


def _make_clear(conversations: ConversationManager):
    async def _clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        conversations.clear(update.effective_chat.id)
        await update.message.reply_text("Conversation history cleared.")
    return _clear


def _make_chat(conversations: ConversationManager):
    async def _chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        try:
            await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        except (NetworkError, TimedOut):
            pass  # cosmetic — don't abort the real work
        response = await conversations.respond(chat_id, update.message.text)
        await update.message.reply_text(md_to_html(response), parse_mode=ParseMode.HTML)
    return _chat
