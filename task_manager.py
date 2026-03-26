"""
TaskManager — routes Telegram messages to the right task and manages
the active-task lifecycle per chat.

How it works
------------
1.  On startup, auto_discover_tasks() scans the bot's ``custom_tasks/``
    folder for ``*_task.py`` files, imports every BaseTask subclass it
    finds, and registers it using the class's ``trigger`` attribute.

2.  On first message from a chat (or after the previous task finishes),
    TaskManager calls _resolve() to pick a Task class, instantiates it,
    and starts task.run() as a background asyncio.Task.

3.  While a task is running:
    - If the task is paused inside ask(), the next user message is fed
      directly to task.provide_input() so ask() can return.
    - Otherwise the message is treated as a NEW task request (the running
      task is cancelled first).

4.  When task.run() finishes (or raises), the slot for that chat is freed.

Multi-bot architecture
----------------------
Each bot gets its own ``TaskManager`` instance with a dedicated
``custom_tasks_dir`` and ``data_dir``.  The ``bot.py`` runner handles
discovery and creates one ``TaskManager`` per bot directory found
under ``bots/``.

Extending
---------
Drop a new ``*_task.py`` file into ``bots/<bot_name>/custom_tasks/``.
Make sure the class sets a ``trigger`` attribute (e.g. ``trigger = "weather"``).
It will be picked up automatically on the next bot restart.
"""

from __future__ import annotations

import asyncio
import importlib.util
import inspect
import logging
import sys
from pathlib import Path
from typing import Callable, Type

from telegram import Bot

from tasks.base_task import BaseTask
from tasks.scheduler import Scheduler
from tasks.shell_task import ShellCommandTask

log = logging.getLogger(__name__)

MatcherFn = Callable[[str], bool]

SCHEDULED_JOBS_FILENAME = "scheduled_jobs.json"


class TaskManager:
    """Routes Telegram messages to the right task for a specific bot.

    Parameters
    ----------
    bot:
        The Telegram Bot instance.
    custom_tasks_dir:
        Path to the directory containing ``*_task.py`` files for this bot.
    data_dir:
        Path to the directory for persistent data (scheduler jobs, etc.).
    """

    def __init__(
        self,
        bot: Bot,
        custom_tasks_dir: Path,
        data_dir: Path,
    ) -> None:
        self.bot = bot
        self._custom_tasks_dir = custom_tasks_dir
        self._data_dir = data_dir
        self._running: dict[int, asyncio.Task] = {}
        self._tasks: dict[int, BaseTask] = {}
        self._registry: list[tuple[MatcherFn, Type[BaseTask]]] = []
        self.scheduler = Scheduler(
            bot=bot,
            data_file=data_dir / SCHEDULED_JOBS_FILENAME,
        )

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, matcher: MatcherFn, task_class: Type[BaseTask]) -> None:
        """Add a task class with an explicit matcher function."""
        self._registry.append((matcher, task_class))

    def registered_task_classes(self) -> list[Type[BaseTask]]:
        """Return all registered task classes plus the fallback, in order."""
        return [cls for _, cls in self._registry] + [ShellCommandTask]

    # ------------------------------------------------------------------
    # Scheduler lifecycle
    # ------------------------------------------------------------------

    async def start_scheduler(self) -> None:
        """Start the background scheduler, wiring trigger jobs to handle_message."""
        await self.scheduler.start(on_trigger=self.handle_message)

    async def stop_scheduler(self) -> None:
        """Stop the background scheduler and persist jobs."""
        await self.scheduler.stop()

    # ------------------------------------------------------------------
    # Auto-discovery
    # ------------------------------------------------------------------

    def auto_discover_tasks(self) -> None:
        """Scan the bot's custom_tasks/ directory for ``*_task.py`` files and register them."""
        if not self._custom_tasks_dir.is_dir():
            log.info("No custom_tasks/ directory at %s — skipping.", self._custom_tasks_dir)
            return

        for filepath in sorted(self._custom_tasks_dir.glob("*_task.py")):
            module_name = f"_bot_tasks.{self._custom_tasks_dir.parent.name}.{filepath.stem}"
            try:
                module = _import_module_from_path(module_name, filepath)
            except Exception:
                log.exception("Failed to import %s", filepath)
                continue

            for _name, obj in inspect.getmembers(module, inspect.isclass):
                if not _is_registrable_task(obj):
                    continue
                trigger = obj.trigger
                matcher = _build_matcher(trigger)
                self.register(matcher, obj)
                log.info("Auto-registered %s (trigger=%r)", obj.__name__, trigger)

    # ------------------------------------------------------------------
    # Main entry point — called by the Telegram message handler
    # ------------------------------------------------------------------

    async def handle_message(self, chat_id: int, text: str) -> None:
        """Route an incoming user message to the appropriate task."""
        existing_task = self._tasks.get(chat_id)

        # If a task is paused waiting for user input, feed it this reply.
        if existing_task and existing_task.is_waiting:
            await existing_task.provide_input(text)
            return

        # Otherwise start a fresh task (cancel any still-running one first).
        await self._cancel(chat_id)
        task_instance = self._resolve(chat_id, text)
        self._tasks[chat_id] = task_instance

        async def _run_and_cleanup() -> None:
            try:
                await task_instance.run(text)
            except asyncio.CancelledError:
                pass
            except Exception as exc:
                log.exception("Task %s raised an unhandled exception", task_instance.name)
                try:
                    await task_instance.reply(f"❌ Unexpected error: {exc}")
                except Exception:
                    pass
            finally:
                self._running.pop(chat_id, None)
                self._tasks.pop(chat_id, None)

        loop = asyncio.get_event_loop()
        self._running[chat_id] = loop.create_task(_run_and_cleanup())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve(self, chat_id: int, text: str) -> BaseTask:
        """Pick the right task class for this message."""
        for matcher, task_class in self._registry:
            if matcher(text):
                return task_class(chat_id, self.bot, self.scheduler)
        # Default fallback
        return ShellCommandTask(chat_id, self.bot, self.scheduler)

    async def _cancel(self, chat_id: int) -> None:
        """Cancel any currently running task for this chat."""
        running = self._running.pop(chat_id, None)
        if running and not running.done():
            running.cancel()
            try:
                await running
            except (asyncio.CancelledError, Exception):
                pass
        self._tasks.pop(chat_id, None)


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------

def _is_registrable_task(cls: type) -> bool:
    """Return True if cls is a concrete BaseTask subclass with a trigger."""
    return (
        inspect.isclass(cls)
        and issubclass(cls, BaseTask)
        and cls is not BaseTask
        and hasattr(cls, "trigger")
        and cls.trigger  # empty trigger = fallback, skip
    )


def _build_matcher(trigger: str) -> MatcherFn:
    """Create a matcher function from a trigger prefix string."""
    prefix = trigger.lower()
    return lambda text: text.lower().startswith(prefix)


def _import_module_from_path(name: str, path: Path):
    """Import a Python module from an arbitrary file path.

    This avoids requiring the file to be inside a proper Python package
    hierarchy, which is important for per-bot custom_tasks directories.
    """
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module