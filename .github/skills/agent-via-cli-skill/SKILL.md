```skill
---
name: agent-via-cli-skill
description: Practical reference for launching and automating GitHub Copilot custom agents from the command line. Covers installation, authentication, agent file conventions, launch modes (non-interactive, interactive, delegate), permission bypass flags, and full autopilot command construction. Use this skill whenever writing scripts, CI pipelines, or instructions that invoke a GitHub Copilot agent via the CLI.
---

# GitHub Copilot CLI — Custom Agents Guide

This skill defines how to correctly invoke GitHub Copilot custom agents from the command line, both interactively and fully automated. Apply every rule here whenever constructing a CLI command that targets a `.agent.md` agent.

---

## 1. Platform Compatibility

| Platform | Support | Notes |
|---|---|---|
| Linux | Full | Native, first-class support |
| macOS | Full | Native, first-class support |
| Windows (WSL) | Recommended | Full Linux environment — most reliable on Windows |
| Windows (PowerShell) | Experimental | Requires PowerShell 6+, not pre-installed on Windows 11 (ships with 5.1) |

**Rule:** For cross-platform scripts or CI pipelines that target Windows, always instruct users to run inside **WSL**, not native PowerShell, to guarantee consistent behavior.

---

## 2. Installation

Choose the method that matches the target environment. Never mix methods on the same machine.

```bash
# Cross-platform — recommended default
npm install -g @github/copilot

# macOS / Linux only
brew install copilot-cli

# Windows only (native, not WSL)
winget install GitHub.Copilot
```

---

## 3. Authentication

Authentication is done once per machine inside an interactive session:

```bash
copilot
/login
```

Do not embed credentials in scripts. Authentication state is persisted by the CLI after the first `/login`.

---

## 4. Agent File Conventions

Custom agents are `.agent.md` files. Two scopes are supported:

| Scope | Path |
|---|---|
| Repository-level | `.github/agents/<agent-name>.agent.md` |
| User-level (global) | `~/.copilot/agents/<agent-name>.agent.md` |

**Naming rule:** The `--agent` flag value is the filename **without** the `.agent.md` extension.

```
.github/agents/refactor-agent.agent.md  →  --agent refactor-agent
.github/agents/telegramtaskor.agent.md  →  --agent telegramtaskor
```

Always prefer the repository-level scope for project-specific agents so the definition travels with the codebase.

---

## 5. Launch Modes

### Option 1 — Non-interactive (scripting / CI)

The preferred mode for automation. Runs the agent, executes the prompt, and exits.

```bash
copilot --agent <agent-name> --prompt "Your task description here"
```

### Option 2 — Interactive session

For exploratory use. Start a session and select the agent via slash command.

```bash
copilot
# Inside the session:
/agent
# → select your agent from the list
```

### Option 3 — Background async delegation

Commits unstaged changes to a new branch, opens a draft PR, and lets Copilot work asynchronously.

```bash
copilot
# Inside the session:
/delegate "Your task description"
```

Use `/delegate` only when the task is safe to run asynchronously without supervision.

---

## 6. Permission Bypass Flags

By default, Copilot prompts for confirmation before executing commands or editing files. In automation contexts, use these flags to suppress prompts.

| Flag | Scope of bypass |
|---|---|
| `--yolo` / `--allow-all` | Everything — tools, paths, and URLs |
| `--allow-all-tools` | All tool execution prompts only |
| `--allow-all-paths` | All file system path access prompts only |
| `--allow-tool shell(git:*)` | A specific tool or command only |

**Rule:** `--yolo` is an alias for `--allow-all`. They are equivalent. Use `--yolo` for brevity in scripts.

**Rule:** Prefer granular flags (`--allow-all-tools`, `--allow-all-paths`) when the task scope is known. Reserve `--yolo` for fully trusted, isolated environments only.

---

## 7. Full Autopilot Command

The canonical command for CI pipelines and unattended automation:

```bash
copilot --agent <agent-name> \
        --prompt "Your task here" \
        --autopilot \
        --yolo \
        --max-autopilot-continues 20
```

| Flag | Purpose |
|---|---|
| `--autopilot` | Run without requiring any user input |
| `--yolo` | Skip all permission prompts |
| `--max-autopilot-continues N` | Cap the agentic loop at N iterations to prevent runaway execution |

**Rule:** Always set `--max-autopilot-continues` when using `--autopilot`. Never run an uncapped autopilot loop in CI or any shared environment.

---

## 8. Quick Reference

| Goal | Command |
|---|---|
| Run agent non-interactively | `copilot --agent my-agent --prompt "..."` |
| Pick agent in interactive mode | `copilot` → `/agent` |
| Delegate to background async agent | `copilot` → `/delegate "..."` |
| Skip all permission prompts | Add `--yolo` |
| Full autopilot with safety cap | `--autopilot --yolo --max-autopilot-continues 20` |

---

## 9. Security Rules

`--yolo` / `--allow-all` grants Copilot permission to execute commands and edit files **without any review**. This carries real risk of unintended actions, data loss, or corruption.

**Non-negotiable rules when using `--yolo`:**

1. Only run inside an **isolated environment** — container, VM, or dedicated CI runner. Never on a developer's local machine against a live codebase.
2. Always pair with `--max-autopilot-continues` to cap autonomous steps.
3. Review the `.agent.md` definition carefully before granting full permissions. The agent's instructions determine what it will do with unrestricted access.
4. Never commit a script containing `--yolo` to a shared branch without a documented justification and explicit team approval.
```
