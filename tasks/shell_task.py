"""
ShellCommandTask — runs an arbitrary shell command requested by the user.

Demonstrates
------------
- Using self.reply() for output
- Using self.ask() to pause mid-execution and request confirmation
"""

from __future__ import annotations

import subprocess

from .base_task import BaseTask

# Commands that require an explicit "yes" before running.
DANGEROUS_KEYWORDS = {
    # Destructive file operations (cross-platform)
    "rm ", "rm -", "del ", "rmdir", "rd ", "shred",
    # System control
    "shutdown", "reboot", "poweroff", "halt", "init 0", "init 6",
    # Process killing
    "taskkill", "kill ", "killall", "pkill",
    # Disk / filesystem
    "format", "mkfs", "dd ", "fdisk", "parted",
    # Permissions / ownership
    "chmod 777", "chown",
    # Privilege escalation
    "sudo ",
    # Windows registry
    "reg delete", "reg add",
    # Dangerous redirects
    "> /dev/", "| rm",
    # Package removal
    "apt remove", "apt purge", "yum remove", "dnf remove",
    # Service control
    "systemctl stop", "systemctl disable",
}


def _is_dangerous(cmd: str) -> bool:
    lowered = cmd.lower()
    return any(kw in lowered for kw in DANGEROUS_KEYWORDS)


class ShellCommandTask(BaseTask):
    name = "shell"
    description = "Run any shell command on the host machine"
    usage = "dir, ping google.com, tasklist"
    icon = "💻"
    trigger = ""  # Fallback — matches everything not claimed by another task

    async def run(self, user_input: str) -> None:
        cmd = user_input.strip()

        # Ask for confirmation when the command looks risky.
        if _is_dangerous(cmd):
            answer = await self.ask(
                f"⚠️ *Potentially dangerous command detected:*\n"
                f"```\n{cmd}\n```\n"
                f"Type `yes` to confirm, anything else to cancel."
            )
            if answer.strip().lower() != "yes":
                await self.reply("❌ Command cancelled.")
                return

        await self.reply(f"▶️ Running: `{cmd}`")

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                stdin=subprocess.DEVNULL,
            )
            output = result.stdout or result.stderr or "(no output)"
        except subprocess.TimeoutExpired:
            output = "❌ Command timed out after 30 seconds."
        except Exception as exc:
            output = f"❌ Error: {exc}"

        await self.reply(f"```\n{output}\n```")
