import logging
from telegram.ext import Application
import config
from agent import build_agent, ConversationManager
from bot.handler import setup_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
# Silence noisy third-party loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)


def main() -> None:
    agent = build_agent()
    conversations = ConversationManager(agent)

    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    setup_handlers(app, conversations)

    logging.getLogger("rolodex").info("Starting rolodex-agent [backend: %s]", config.LLM_BACKEND)
    app.run_polling()


if __name__ == "__main__":
    main()
