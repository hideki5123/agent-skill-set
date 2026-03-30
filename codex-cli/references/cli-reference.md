# Codex CLI Reference

Full flag-by-flag reference for codex-cli. Read this when you need exact flag names, syntax, or available options.

## Global Options

These options apply to most subcommands:

| Flag | Description |
|------|-------------|
| `-c, --config <key=value>` | Override config from `~/.codex/config.toml`. Dotted path syntax, TOML-parsed values. E.g. `-c model="o3"`, `-c 'sandbox_permissions=["disk-full-read-access"]'` |
| `--enable <FEATURE>` | Enable a feature flag. Equivalent to `-c features.<name>=true` |
| `--disable <FEATURE>` | Disable a feature flag. Equivalent to `-c features.<name>=false` |
| `-i, --image <FILE>...` | Attach image(s) to the prompt |
| `-m, --model <MODEL>` | Override the model (default: from config.toml) |
| `--oss` | Use local open-source model provider (LM Studio or Ollama) |
| `--local-provider <PROVIDER>` | Specify local provider: `lmstudio` or `ollama` |
| `-p, --profile <PROFILE>` | Use a named config profile from config.toml |
| `-s, --sandbox <MODE>` | Sandbox policy: `read-only`, `workspace-write`, `danger-full-access` |
| `-a, --ask-for-approval <POLICY>` | Approval policy: `untrusted`, `on-failure` (deprecated), `on-request`, `never` |
| `--full-auto` | Convenience alias for `-a on-request --sandbox workspace-write` |
| `--dangerously-bypass-approvals-and-sandbox` | Skip all prompts and sandbox. DANGEROUS |
| `-C, --cd <DIR>` | Set working root directory |
| `--search` | Enable live web search tool |
| `--add-dir <DIR>` | Additional writable directories alongside workspace |
| `-h, --help` | Print help |
| `-V, --version` | Print version |

## `codex [PROMPT]` — Interactive Session

Start an interactive TUI session with optional initial prompt.

```
codex [OPTIONS] [PROMPT]
```

Additional options:
- `--remote <ADDR>` — Connect to remote app server (`ws://` or `wss://`)
- `--remote-auth-token-env <ENV_VAR>` — Bearer token env var for remote
- `--no-alt-screen` — Inline mode (preserves terminal scrollback)

## `codex exec [PROMPT]` — Non-Interactive Execution

Run codex non-interactively. This is the primary command for Claude Code integration.

```
codex exec [OPTIONS] [PROMPT] [COMMAND]
```

Subcommands:
- `resume` — Resume a previous session
- `review` — Run a code review

Additional options beyond globals:
- `--skip-git-repo-check` — Allow running outside a git repository
- `--ephemeral` — Don't persist session files to disk
- `--output-schema <FILE>` — JSON Schema for structured response output
- `--color <COLOR>` — Output color: `always`, `never`, `auto` (default: auto)
- `--json` — Print JSONL events to stdout
- `-o, --output-last-message <FILE>` — Write final agent message to file

If `PROMPT` is omitted or `-` is used, instructions are read from stdin.

## `codex exec resume [SESSION_ID] [PROMPT]` — Resume Session

Resume a previous non-interactive session with optional follow-up prompt.

```
codex exec resume [OPTIONS] [SESSION_ID] [PROMPT]
```

Arguments:
- `SESSION_ID` — UUID or thread name. If omitted, use `--last`
- `PROMPT` — Follow-up prompt. Use `-` to read from stdin

Key options:
- `--last` — Resume the most recent session (no ID needed)
- `--all` — Show all sessions (disables CWD filtering)
- `-i, --image <FILE>` — Attach image(s) to the follow-up
- `--ephemeral` — Don't persist this continuation
- `--json` — JSONL events to stdout
- `-o, --output-last-message <FILE>` — Write final message to file
- `--full-auto` — Non-interactive auto-approval
- `--skip-git-repo-check` — Allow outside git repo

## `codex exec review [PROMPT]` — Code Review

Run an automated code review non-interactively.

```
codex exec review [OPTIONS] [PROMPT]
```

Arguments:
- `PROMPT` — Custom review instructions. Use `-` to read from stdin

Key options:
- `--uncommitted` — Review staged + unstaged + untracked changes
- `--base <BRANCH>` — Review changes against a base branch
- `--commit <SHA>` — Review changes from a specific commit
- `--title <TITLE>` — Commit title for the review summary
- `--json` — JSONL events to stdout
- `-o, --output-last-message <FILE>` — Write final review to file
- `--full-auto` — Non-interactive auto-approval
- `--ephemeral` — Don't persist session
- `--skip-git-repo-check` — Allow outside git repo

## `codex resume [SESSION_ID] [PROMPT]` — Resume Interactive Session

Resume a previous session in interactive TUI mode.

```
codex resume [OPTIONS] [SESSION_ID] [PROMPT]
```

Arguments:
- `SESSION_ID` — UUID or thread name
- `PROMPT` — Optional initial prompt

Key options:
- `--last` — Continue most recent session
- `--all` — Show all sessions (disables CWD filtering)
- `--include-non-interactive` — Include `exec` sessions in picker/`--last`

Note: This opens the interactive TUI. For non-interactive resume, use `codex exec resume` instead.

## `codex fork [SESSION_ID] [PROMPT]` — Fork Session

Create a new conversation branch from an existing session.

```
codex fork [OPTIONS] [SESSION_ID] [PROMPT]
```

Arguments:
- `SESSION_ID` — UUID to fork
- `PROMPT` — Optional initial prompt for the forked session

Key options:
- `--last` — Fork the most recent session
- `--all` — Show all sessions (disables CWD filtering)

Note: This opens the interactive TUI. For non-interactive forking, use `codex exec resume` with a new prompt — similar effect without the TUI.

## `codex review [PROMPT]` — Standalone Code Review

Non-interactive code review (top-level alias).

```
codex review [OPTIONS] [PROMPT]
```

Same options as `codex exec review`:
- `--uncommitted`, `--base <BRANCH>`, `--commit <SHA>`, `--title <TITLE>`

## `codex apply` — Apply Diffs

Apply the latest diff produced by the Codex agent as `git apply` to the local working tree.

```
codex apply
```

Aliases: `codex a`

## `codex login` / `codex logout` — Authentication

```
codex login       # Configure API key (interactive)
codex logout      # Remove stored credentials
```

## `codex mcp` — MCP Server Management

```
codex mcp list              # List configured MCP servers
codex mcp add <name> ...    # Add an MCP server
codex mcp remove <name>     # Remove an MCP server
```

## `codex mcp-server` — Run as MCP Server

Start codex as an MCP server over stdio, allowing other tools to use codex as a tool provider.

```
codex mcp-server
```

## Config File

Location: `~/.codex/config.toml`

Key settings:
```toml
model = "gpt-5.4"
model_reasoning_effort = "high"    # low | medium | high

[mcp_servers.<name>]
command = "..."
args = ["..."]

[projects.'<path>']
trust_level = "trusted"

[windows]
sandbox = "elevated"
```

Override any config value at runtime with `-c`:
```bash
codex exec "prompt" -c model="o3" -c model_reasoning_effort="low"
```

## Session Storage

- Location: `~/.codex/sessions/YYYY/MM/DD/<timestamp>-<uuid>.jsonl`
- Format: JSONL with `type` and associated fields per line
- First event: `{"type":"thread.started","thread_id":"<UUID>"}` — the `thread_id` is the session UUID
- Subsequent events: `turn.started`, `item.completed` (with `item.text` for agent messages)
- Sessions are filtered by CWD by default; use `--all` to see all
- **Do NOT pipe `--json` stdout through `head`** — broken pipe kills the process. Redirect to file first, then extract.
- Extract thread_id without jq: `head -1 events.jsonl | grep -o '"thread_id":"[^"]*"' | cut -d'"' -f4`

## Skills Directory

- Location: `~/.codex/skills/`
- Skills are auto-loaded by codex from this directory
- Synced from source via `python scripts/sync_skills.py --targets codex`
