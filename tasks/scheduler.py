"""
Scheduler — persistent, reusable cron and one-shot job scheduling.

Any task can schedule recurring or one-time jobs via ``self.scheduler``.
Jobs survive bot restarts (persisted to a JSON file).

Cron expressions
----------------
Standard 5-field format::

    ┌─── minute (0-59)
    │ ┌─── hour (0-23)
    │ │ ┌─── day of month (1-31)
    │ │ │ ┌─── month (1-12)
    │ │ │ │ ┌─── day of week (0-7, 0 and 7 = Sunday)
    * * * * *

Supported syntax per field: ``*``, ``5``, ``1,3,5``, ``1-5``, ``*/15``,
``1-5/2``.  Shortcuts: ``@daily``, ``@hourly``, ``@weekly``, ``@monthly``,
``@yearly``.

Action types
------------
- ``notify``  — send a text message directly to the user.
- ``trigger`` — route a command through TaskManager to run a task.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Awaitable, Callable

from telegram import Bot

log = logging.getLogger(__name__)

# ── Constants ───────────────────────────────────────────────────────

TICK_INTERVAL_SECONDS = 30

ACTION_TYPE_NOTIFY = "notify"
ACTION_TYPE_TRIGGER = "trigger"
VALID_ACTION_TYPES = frozenset({ACTION_TYPE_NOTIFY, ACTION_TYPE_TRIGGER})

CRON_FIELD_COUNT = 5

CRON_SHORTCUTS: dict[str, str] = {
    "@yearly": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@hourly": "0 * * * *",
}

# Day-of-week bounds (cron convention: 0 and 7 both mean Sunday).
DOW_MIN = 0
DOW_MAX = 7


# ── Data models ─────────────────────────────────────────────────────


@dataclass
class CronSchedule:
    """Parsed representation of a 5-field cron expression."""

    minutes: set[int]
    hours: set[int]
    days_of_month: set[int]
    months: set[int]
    days_of_week: set[int]  # Python weekday: 0=Mon … 6=Sun


@dataclass
class ScheduledJob:
    """A single scheduled job (persisted to JSON)."""

    job_id: str
    chat_id: int
    label: str
    schedule: str  # cron expression or ISO datetime
    is_recurring: bool
    action_type: str  # "notify" or "trigger"
    action_payload: str
    created_at: str
    last_fired_at: str | None = None


# ── Cron parsing ────────────────────────────────────────────────────


def _cron_dow_to_python(cron_dow: int) -> int:
    """Convert cron day-of-week (0/7=Sun) to Python weekday (0=Mon … 6=Sun)."""
    return (cron_dow - 1) % 7


def _parse_cron_part(part: str, min_val: int, max_val: int) -> set[int]:
    """Parse one segment of a cron field (e.g. ``*/5``, ``1-5``, ``3``)."""
    step = 1
    if "/" in part:
        part, step_str = part.split("/", 1)
        step = int(step_str)

    if part == "*":
        return set(range(min_val, max_val + 1, step))

    if "-" in part:
        start_str, end_str = part.split("-", 1)
        return set(range(int(start_str), int(end_str) + 1, step))

    return {int(part)}


def _parse_cron_field(field_str: str, min_val: int, max_val: int) -> set[int]:
    """Parse one cron field (comma-separated parts) into a set of ints."""
    values: set[int] = set()
    for part in field_str.split(","):
        values |= _parse_cron_part(part.strip(), min_val, max_val)
    return values


def parse_cron(expression: str) -> CronSchedule:
    """Parse a 5-field cron expression (or shortcut) into a ``CronSchedule``.

    Raises:
        ValueError: If the expression is malformed.
    """
    resolved = CRON_SHORTCUTS.get(expression.strip().lower(), expression)
    fields = resolved.strip().split()
    if len(fields) != CRON_FIELD_COUNT:
        raise ValueError(
            f"Cron expression must have {CRON_FIELD_COUNT} fields, "
            f"got {len(fields)}: {expression!r}"
        )

    raw_dow = _parse_cron_field(fields[4], DOW_MIN, DOW_MAX)
    python_dow = {_cron_dow_to_python(d) for d in raw_dow}

    return CronSchedule(
        minutes=_parse_cron_field(fields[0], 0, 59),
        hours=_parse_cron_field(fields[1], 0, 23),
        days_of_month=_parse_cron_field(fields[2], 1, 31),
        months=_parse_cron_field(fields[3], 1, 12),
        days_of_week=python_dow,
    )


# ── Helpers ─────────────────────────────────────────────────────────


def _generate_job_id() -> str:
    """Return a short, unique job identifier."""
    return uuid.uuid4().hex[:8]


def _same_minute(dt_a: datetime, dt_b: datetime) -> bool:
    """Return True if both datetimes fall in the same calendar minute."""
    return dt_a.replace(second=0, microsecond=0) == dt_b.replace(
        second=0, microsecond=0
    )


# ── Type alias ──────────────────────────────────────────────────────

TriggerCallback = Callable[[int, str], Awaitable[None]]


# ── Scheduler ───────────────────────────────────────────────────────


class Scheduler:
    """Persistent job scheduler with cron and one-shot support.

    Parameters
    ----------
    bot:
        The Telegram Bot instance (used to send notification messages).
    data_file:
        Path to the JSON file where jobs are persisted.
    """

    def __init__(self, bot: Bot, data_file: Path) -> None:
        self._bot = bot
        self._data_file = data_file
        self._jobs: dict[str, ScheduledJob] = {}
        self._on_trigger: TriggerCallback | None = None
        self._tick_handle: asyncio.Task | None = None

    # ── Lifecycle ───────────────────────────────────────────────

    async def start(
        self,
        on_trigger: TriggerCallback | None = None,
    ) -> None:
        """Load persisted jobs and start the background tick loop.

        Args:
            on_trigger: Async callback invoked when a ``trigger`` job fires.
                Signature: ``async (chat_id: int, message: str) -> None``.
        """
        self._on_trigger = on_trigger
        self._load()
        self._tick_handle = asyncio.create_task(self._tick_loop())
        log.info("Scheduler started — %d job(s) loaded.", len(self._jobs))

    async def stop(self) -> None:
        """Cancel the tick loop and persist current state."""
        if self._tick_handle and not self._tick_handle.done():
            self._tick_handle.cancel()
            try:
                await self._tick_handle
            except asyncio.CancelledError:
                pass
        self._save()
        log.info("Scheduler stopped.")

    # ── Public API (used by tasks via self.scheduler) ───────────

    def add_job(
        self,
        *,
        chat_id: int,
        label: str,
        schedule: str,
        is_recurring: bool,
        action_type: str,
        action_payload: str,
    ) -> str:
        """Create a scheduled job and persist it. Returns the job ID.

        Args:
            chat_id: Telegram chat to target.
            label: Human-readable description.
            schedule: Cron expression (recurring) or ISO datetime (one-shot).
            is_recurring: True for cron, False for one-shot.
            action_type: ``"notify"`` or ``"trigger"``.
            action_payload: Message text (notify) or trigger command (trigger).

        Raises:
            ValueError: If the schedule or action_type is invalid.
        """
        _validate_job_params(schedule, is_recurring, action_type)

        job_id = _generate_job_id()
        job = ScheduledJob(
            job_id=job_id,
            chat_id=chat_id,
            label=label,
            schedule=schedule,
            is_recurring=is_recurring,
            action_type=action_type,
            action_payload=action_payload,
            created_at=datetime.now().isoformat(),
        )
        self._jobs[job_id] = job
        self._save()
        log.info("Job added: %s (%s)", job_id, label)
        return job_id

    def remove_job(self, job_id: str) -> bool:
        """Remove a job by ID. Returns True if found and removed."""
        if job_id not in self._jobs:
            return False
        del self._jobs[job_id]
        self._save()
        log.info("Job removed: %s", job_id)
        return True

    def list_jobs(self, chat_id: int | None = None) -> list[ScheduledJob]:
        """Return all jobs, optionally filtered by chat_id."""
        if chat_id is None:
            return list(self._jobs.values())
        return [j for j in self._jobs.values() if j.chat_id == chat_id]

    # ── Tick loop ───────────────────────────────────────────────

    async def _tick_loop(self) -> None:
        """Run forever, checking for due jobs every tick interval."""
        while True:
            await asyncio.sleep(TICK_INTERVAL_SECONDS)
            try:
                await self._process_due_jobs(datetime.now())
            except Exception:
                log.exception("Error in scheduler tick")

    async def _process_due_jobs(self, now: datetime) -> None:
        """Fire all due jobs and clean up expired one-shots."""
        expired_ids: list[str] = []
        for job in list(self._jobs.values()):
            if not self._is_due(job, now):
                continue
            await self._fire_job(job, now)
            if not job.is_recurring:
                expired_ids.append(job.job_id)

        for job_id in expired_ids:
            self._jobs.pop(job_id, None)
            log.info("One-shot job %s removed after firing.", job_id)
        if expired_ids:
            self._save()

    # ── Due-checking ────────────────────────────────────────────

    def _is_due(self, job: ScheduledJob, now: datetime) -> bool:
        """Check whether a job should fire right now."""
        if job.is_recurring:
            return self._is_due_cron(job, now)
        return self._is_due_oneshot(job, now)

    def _is_due_cron(self, job: ScheduledJob, now: datetime) -> bool:
        """Check if a recurring (cron) job matches the current minute."""
        if job.last_fired_at and _same_minute(
            datetime.fromisoformat(job.last_fired_at), now
        ):
            return False

        cron = parse_cron(job.schedule)
        return (
            now.minute in cron.minutes
            and now.hour in cron.hours
            and now.day in cron.days_of_month
            and now.month in cron.months
            and now.weekday() in cron.days_of_week
        )

    def _is_due_oneshot(self, job: ScheduledJob, now: datetime) -> bool:
        """Check if a one-shot job's target time has arrived."""
        if job.last_fired_at is not None:
            return False
        target = datetime.fromisoformat(job.schedule)
        return now >= target

    # ── Firing ──────────────────────────────────────────────────

    async def _fire_job(self, job: ScheduledJob, now: datetime) -> None:
        """Execute the action associated with a fired job."""
        job.last_fired_at = now.isoformat()
        self._save()
        log.info("Firing job %s (%s)", job.job_id, job.label)

        try:
            if job.action_type == ACTION_TYPE_NOTIFY:
                await self._send_notification(job)
            elif job.action_type == ACTION_TYPE_TRIGGER:
                await self._run_trigger(job)
        except Exception:
            log.exception("Failed to fire job %s (%s)", job.job_id, job.label)

    async def _send_notification(self, job: ScheduledJob) -> None:
        """Send a notification message to the user."""
        text = f"🔔 *{job.label}*\n\n{job.action_payload}"
        await self._bot.send_message(
            chat_id=job.chat_id,
            text=text,
            parse_mode="Markdown",
        )

    async def _run_trigger(self, job: ScheduledJob) -> None:
        """Route a trigger command through the registered callback."""
        if not self._on_trigger:
            log.warning(
                "Trigger job %s fired but no callback is registered.",
                job.job_id,
            )
            return
        await self._on_trigger(job.chat_id, job.action_payload)

    # ── Persistence ─────────────────────────────────────────────

    def _load(self) -> None:
        """Load jobs from the JSON data file."""
        if not self._data_file.exists():
            return
        try:
            raw = json.loads(self._data_file.read_text(encoding="utf-8"))
            for entry in raw:
                job = ScheduledJob(**entry)
                self._jobs[job.job_id] = job
        except (json.JSONDecodeError, TypeError, KeyError):
            log.exception(
                "Failed to load scheduled jobs from %s", self._data_file
            )

    def _save(self) -> None:
        """Persist all jobs to the JSON data file."""
        self._data_file.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(job) for job in self._jobs.values()]
        self._data_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


# ── Module-level validation ─────────────────────────────────────────


def _validate_job_params(
    schedule: str,
    is_recurring: bool,
    action_type: str,
) -> None:
    """Validate job parameters. Raises ValueError on bad input."""
    if action_type not in VALID_ACTION_TYPES:
        raise ValueError(
            f"action_type must be one of {VALID_ACTION_TYPES}, "
            f"got {action_type!r}"
        )
    if is_recurring:
        parse_cron(schedule)
    else:
        datetime.fromisoformat(schedule)
