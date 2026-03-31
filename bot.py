"""
Multi-bot runner — discovers all bots under ``bots/`` and runs them
concurrently in a single process.

Each bot directory must contain a ``custom_tasks/`` subfolder.
Tokens are read from environment variables following the convention
``TELEGRAM_BOT_TOKEN_<BOT_NAME>`` (uppercase).
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from shared.store import SharedStore
from task_manager import TaskManager

load_dotenv()
logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger(__name__)

BOTS_DIR = Path(__file__).parent / "bots"
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID"))
TOKEN_ENV_PREFIX = "TELEGRAM_BOT_TOKEN_"


# ------------------------------------------------------------------
# Bot discovery
# ------------------------------------------------------------------


def _discover_bots() -> list[dict]:
    """Scan ``bots/`` for bot directories and map each to its token."""
    bots: list[dict] = []
    if not BOTS_DIR.is_dir():
        return bots

    for bot_dir in sorted(BOTS_DIR.iterdir()):
        if not bot_dir.is_dir() or bot_dir.name.startswith("_"):
            continue
        token_env_var = f"{TOKEN_ENV_PREFIX}{bot_dir.name.upper()}"
        token = os.getenv(token_env_var)
        if not token:
            log.warning(
                "Skipping bot '%s' — env var %s not set.",
                bot_dir.name,
                token_env_var,
            )
            continue
        bots.append({
            "name": bot_dir.name,
            "token": token,
            "custom_tasks_dir": bot_dir / "custom_tasks",
            "data_dir": bot_dir / "data",
        })
    return bots


# ------------------------------------------------------------------
# Per-bot application builder
# ------------------------------------------------------------------


def _is_authorized(update: Update) -> bool:
    """Check if the sender is the allowed user."""
    return update.effective_user.id == ALLOWED_USER_ID


_BOT_NAME_KEY = "bot_name"
_TASK_MANAGER_KEY = "task_manager"


def _build_bot_app(bot_config: dict):
    """Build an ``Application`` with message handlers for a single bot.

    The ``TaskManager`` is NOT created here — it is created and stored in
    ``app.bot_data`` by ``_run_all_bots`` after ``app.initialize()`` is
    called (the Bot instance is only ready after initialization).
    """
    bot_name: str = bot_config["name"]

    def _build_help_text(tm: TaskManager, name: str) -> str:
        header = f"📖  *{name.capitalize()} Bot — Help*"
        separator = "━━━━━━━━━━━━━━━━━━━━━"

        sections: list[str] = []
        for task_class in tm.registered_task_classes():
            usage_lines = task_class.usage.strip().splitlines()
            formatted_usage = "\n".join(
                f"    {line.strip()}" for line in usage_lines
            )
            sections.append(
                f"{task_class.icon}  *{task_class.name.capitalize()}*\n"
                f"_{task_class.description}_\n\n"
                f"{formatted_usage}"
            )

        body = f"\n\n{separator}\n\n".join(sections)
        footer = "🔹  /help — Show this overview"
        return f"{header}\n{separator}\n\n{body}\n\n{separator}\n{footer}"

    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not _is_authorized(update):
            return
        tm: TaskManager = context.application.bot_data[_TASK_MANAGER_KEY]
        name: str = context.application.bot_data[_BOT_NAME_KEY]
        await update.message.reply_text(
            _build_help_text(tm, name), parse_mode="Markdown"
        )

    async def handle_message(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        if not _is_authorized(update):
            await update.message.reply_text("Unauthorized.")
            return
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, action="typing"
        )
        tm: TaskManager = context.application.bot_data[_TASK_MANAGER_KEY]
        await tm.handle_message(
            chat_id=update.effective_chat.id,
            text=update.message.text,
        )

    app = ApplicationBuilder().token(bot_config["token"]).build()
    app.bot_data[_BOT_NAME_KEY] = bot_name
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    return app


# ------------------------------------------------------------------
# Concurrent runner
# ------------------------------------------------------------------


async def _run_all_bots() -> None:
    """Discover all bots and run them concurrently until interrupted."""
    shared = SharedStore()
    bot_configs = _discover_bots()
    if not bot_configs:
        log.error(
            "No bots found under %s. "
            "Create a bot directory first (use the bot creator agent).",
            BOTS_DIR,
        )
        return

    apps: list[tuple[str, object]] = [
        (config["name"], _build_bot_app(config)) for config in bot_configs
    ]

    # Initialize all apps (connects the Bot, does NOT call post_init in PTB 22).
    # Then create & store each TaskManager now that app.bot is ready.
    for (name, app), config in zip(apps, bot_configs):
        await app.initialize()
        tm = TaskManager(
            bot=app.bot,
            custom_tasks_dir=config["custom_tasks_dir"],
            data_dir=config["data_dir"],
            shared=shared,
        )
        tm.auto_discover_tasks()
        await tm.start_scheduler()
        app.bot_data[_TASK_MANAGER_KEY] = tm
        log.info("Bot '%s' initialized.", name)

    try:
        for name, app in apps:
            await app.start()
            await app.updater.start_polling()
            log.info("Bot '%s' is polling.", name)

        log.info("All %d bot(s) running. Press Ctrl+C to stop.", len(apps))
        await asyncio.Event().wait()

    except asyncio.CancelledError:
        pass
    finally:
        for name, app in reversed(apps):
            log.info("Stopping bot '%s'...", name)
            tm: TaskManager | None = app.bot_data.get(_TASK_MANAGER_KEY)
            if tm:
                await tm.stop_scheduler()
            await app.updater.stop()
            await app.stop()
            await app.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(_run_all_bots())
    except KeyboardInterrupt:
        log.info("Shutdown complete.")