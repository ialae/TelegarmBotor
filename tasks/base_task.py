"""
BaseTask — the contract every task must implement.

Lifecycle
---------
1. TaskManager creates an instance: Task(chat_id, bot)
2. TaskManager calls: await task.run(user_input)
3. Inside run(), the task can:
   - call  await self.reply(text)   → send a message to the user
   - call  await self.ask(question) → send a question and PAUSE until
                                      the user answers (returns the answer)
4. When run() returns the task is considered finished.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from telegram import Bot

if TYPE_CHECKING:
    from .scheduler import Scheduler


class BaseTask(ABC):
    # One-line human-readable name shown in logs / help messages.
    name: str = "base"
    # Short description shown in /start
    description: str = "(no description)"
    # Example showing how to invoke this task
    usage: str = "(no usage example)"
    # Emoji icon for the /start menu
    icon: str = "🔧"
    # Prefix that triggers this task (used by auto-discovery).
    # Set to "" for the fallback task (ShellCommandTask).
    trigger: str = ""

    def __init__(
        self,
        chat_id: int,
        bot: Bot,
        scheduler: Scheduler | None = None,
    ) -> None:
        self.chat_id = chat_id
        self.bot = bot
        self.scheduler = scheduler
        self._input_queue: asyncio.Queue[str] = asyncio.Queue()
        self._waiting_for_input: bool = False

    # ------------------------------------------------------------------
    # Helpers available to subclasses
    # ------------------------------------------------------------------

    async def reply(self, text: str, parse_mode: str = "Markdown") -> None:
        """Send a plain message to the user."""
        # Telegram hard-caps messages at 4096 chars.
        if len(text) > 4096:
            text = text[:4090] + "\n..."
        await self.bot.send_message(
            chat_id=self.chat_id,
            text=text,
            parse_mode=parse_mode,
        )

    async def ask(self, question: str, parse_mode: str = "Markdown") -> str:
        """
        Send *question* to the user and suspend the task until they reply.

        Returns the user's answer as a plain string.
        """
        self._waiting_for_input = True
        await self.reply(question, parse_mode=parse_mode)
        answer = await self._input_queue.get()
        self._waiting_for_input = False
        return answer

    # ------------------------------------------------------------------
    # Called by TaskManager to feed a user reply back into the task
    # ------------------------------------------------------------------

    async def provide_input(self, text: str) -> None:
        """Push a user message into the task so ask() can return."""
        await self._input_queue.put(text)

    @property
    def is_waiting(self) -> bool:
        """True when the task is paused inside ask(), waiting for input."""
        return self._waiting_for_input

    # ------------------------------------------------------------------
    # Subclasses must implement this
    # ------------------------------------------------------------------

    @abstractmethod
    async def run(self, user_input: str) -> None:
        """
        Entry point for the task.

        Parameters
        ----------
        user_input:
            The raw text the user sent to trigger this task.
        """
        raise NotImplementedError
