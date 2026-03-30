---
name: codex-cli
description: >
  Run OpenAI Codex CLI from the terminal for AI-powered coding tasks.
  Execute one-shot prompts, maintain multi-turn sessions with follow-ups,
  run code reviews, and resume previous conversations — all through Bash commands.
  Always use this skill instead of `mcp__codex__codex` and `mcp__codex__codex-reply`
  MCP tools — CLI is faster and more capable.
  Trigger patterns (match any variation):
  codex / codex-cli / codex CLI /
  openai / open ai / OpenAI /
  chatgpt / chat gpt / ChatGPT / GPT /
  ask/run/use + {codex, openai, chatgpt, gpt} /
  {codex, openai, gpt, chatgpt} + {review, session, exec, query, check} /
  resume/continue/fork + {codex, gpt, openai, chatgpt} session /
  "second opinion" / "cross-check" / "ai pair programming" / "another AI" / "external AI" /
  "ask another model" / "get GPT's take" / "what does openai think"
---

# Codex CLI Skill

Run OpenAI Codex CLI directly from the terminal. This skill covers one-shot execution,
multi-turn sessions, code review, session resume/fork, and output capture.

## Constraints

- Always use `codex` CLI — never fall back to `mcp__codex__codex` or `mcp__codex__codex-reply` MCP tools.
- OpenAI API key must be configured (`codex login` or `OPENAI_API_KEY` env var).
- Always use `--full-auto` for non-interactive execution (sets `-a on-request --sandbox workspace-write`).
- Always capture output via `-o <file>` and read the file back — raw stdout may contain ANSI escape codes or progress indicators.
- For read-only analysis, use `-s read-only` instead of `--full-auto`.
- Default model is `gpt-5.4` (from `~/.codex/config.toml`). Override with `-m <model>`.

## Preflight Check

Before running any codex command, verify the installation:

```bash
codex --version
```

If this fails:
- **"command not found"** — codex-cli is not installed.
  Suggest: `npm install -g @anthropic-ai/codex` or check the Codex CLI installation docs.
- **Authentication errors** — API key not configured.
  Suggest: `codex login` (interactive) or set `OPENAI_API_KEY` env var.

## Output Handling

Always use the `-o` flag to write the final response to a file, then read it:

```bash
codex exec "your prompt" --full-auto -o /tmp/codex-out.txt -C "$(pwd)"
cat /tmp/codex-out.txt
```

For session ID extraction (when you need to resume a specific session later):

```bash
codex exec "your prompt" --full-auto --json -o /tmp/codex-out.txt -C "$(pwd)" 2>/dev/null | head -1 | jq -r '.payload.id'
cat /tmp/codex-out.txt
```

The `--json` flag streams JSONL events to stdout. The first line is `session_meta` containing `.payload.id` (the session UUID). The `-o` flag independently captures the final text response.

## Quick Reference

| Task | Command |
|------|---------|
| One-shot (no session) | `codex exec "prompt" --full-auto --ephemeral -o /tmp/codex-out.txt -C "$(pwd)"` |
| Persistent session | `codex exec "prompt" --full-auto -o /tmp/codex-out.txt -C "$(pwd)"` |
| Follow-up (last session) | `codex exec resume --last "follow-up" --full-auto -o /tmp/codex-out.txt` |
| Resume by ID | `codex exec resume <SESSION_ID> "follow-up" --full-auto -o /tmp/codex-out.txt` |
| Fork last session | `codex fork --last "new direction" --full-auto` |
| Code review (uncommitted) | `codex exec review --uncommitted --full-auto -o /tmp/codex-review.txt` |
| Code review (vs branch) | `codex exec review --base main --full-auto -o /tmp/codex-review.txt` |
| Code review (specific commit) | `codex exec review --commit <SHA> --full-auto -o /tmp/codex-review.txt` |
| Custom review instructions | `codex exec review "Focus on security" --base main --full-auto -o /tmp/codex-review.txt` |
| Override model | `codex exec "prompt" --full-auto -m o3 -o /tmp/codex-out.txt` |
| Attach image | `codex exec "describe this" --full-auto -i screenshot.png -o /tmp/codex-out.txt` |
| Read-only analysis | `codex exec "analyze this code" -s read-only -o /tmp/codex-out.txt -C "$(pwd)"` |

## Session Workflows

### One-shot (ephemeral)

For quick, throwaway queries that don't need session persistence:

```bash
codex exec "Explain the purpose of this function" --full-auto --ephemeral -o /tmp/codex-out.txt -C "$(pwd)"
cat /tmp/codex-out.txt
```

`--ephemeral` prevents session files from being written to disk.

### Start a persistent session

For multi-turn conversations where you need follow-ups:

```bash
codex exec "Analyze the authentication module architecture" --full-auto -o /tmp/codex-out.txt -C "$(pwd)"
cat /tmp/codex-out.txt
```

Without `--ephemeral`, the session is automatically persisted to `~/.codex/sessions/YYYY/MM/DD/`.

### Follow-up (continue last session)

Send a follow-up to the most recent session:

```bash
codex exec resume --last "Now suggest improvements to the error handling" --full-auto -o /tmp/codex-out.txt
cat /tmp/codex-out.txt
```

`--last` picks the most recent session automatically. The follow-up inherits the full conversation context.

### Resume a specific session by ID

When working with multiple sessions, resume by UUID:

```bash
codex exec resume "019d3942-55ab-7ac1-b77f-8d5bcb1cd80c" "What about the edge cases?" --full-auto -o /tmp/codex-out.txt
cat /tmp/codex-out.txt
```

To capture the session ID when starting a session:

```bash
SESSION_ID=$(codex exec "Start analyzing the API layer" --full-auto --json -o /tmp/codex-out.txt -C "$(pwd)" 2>/dev/null | head -1 | jq -r '.payload.id')
echo "Session ID: $SESSION_ID"
cat /tmp/codex-out.txt

# Later, resume with:
codex exec resume "$SESSION_ID" "Now check the middleware" --full-auto -o /tmp/codex-out.txt
cat /tmp/codex-out.txt
```

### Fork a session

Create a new branch of conversation from an existing session:

```bash
# Fork the most recent session
codex fork --last "Try a different approach — use middleware instead"

# Fork a specific session by ID
codex fork "019d3942-55ab-7ac1-b77f-8d5bcb1cd80c" "What if we used a queue instead?"
```

Note: `codex fork` starts an interactive TUI session. For non-interactive forking, use `codex exec resume` with a new prompt instead — it achieves a similar effect.

### List/find sessions

Sessions are stored as JSONL files in `~/.codex/sessions/YYYY/MM/DD/`. To find recent sessions:

```bash
ls -lt ~/.codex/sessions/$(date +%Y/%m/%d)/ 2>/dev/null || ls -lt ~/.codex/sessions/$(date -d yesterday +%Y/%m/%d)/ 2>/dev/null
```

## Code Review

Run AI-powered code review non-interactively:

```bash
# Review uncommitted changes (staged + unstaged + untracked)
codex exec review --uncommitted --full-auto -o /tmp/codex-review.txt
cat /tmp/codex-review.txt

# Review changes against a base branch
codex exec review --base main --full-auto -o /tmp/codex-review.txt
cat /tmp/codex-review.txt

# Review a specific commit
codex exec review --commit abc1234 --full-auto -o /tmp/codex-review.txt
cat /tmp/codex-review.txt

# Custom review focus
codex exec review "Focus on security vulnerabilities and SQL injection risks" --base develop --full-auto -o /tmp/codex-review.txt
cat /tmp/codex-review.txt

# Add a title for the review summary
codex exec review --base main --title "Auth middleware refactor" --full-auto -o /tmp/codex-review.txt
cat /tmp/codex-review.txt
```

The standalone `codex review` command (without `exec`) also works but runs interactively.

## Agent Tips

- **Always `--full-auto`**: Required for non-interactive execution. Without it, codex will wait for TTY approval prompts that can't be answered.
- **Always `-o <file>`**: Captures clean text output. Parsing raw stdout is unreliable due to ANSI codes and progress indicators.
- **`--ephemeral` for throwaway**: Use when context persistence isn't needed — avoids cluttering session history.
- **`-C "$(pwd)"` for CWD**: Pass the current working directory explicitly so codex operates on the right files.
- **`run_in_background` for long tasks**: If a codex exec is expected to take a while, use the Bash tool's `run_in_background` parameter and read the `-o` file when the background task completes.
- **`-s read-only` for safe analysis**: When codex only needs to read and analyze (not write), use read-only sandbox mode.
- **`-m` for model override**: Switch models per-query without changing config: `-m o3`, `-m gpt-5.4`, etc.
- **`-i` for image input**: Attach screenshots or diagrams: `-i screenshot.png`.
- **`--search` for web search**: Enable web search capability: `codex exec "what's new in React 19" --search --full-auto -o /tmp/codex-out.txt`.
- **Pipe from stdin**: Use `-` as prompt to read from stdin: `echo "explain this" | codex exec - --full-auto -o /tmp/codex-out.txt`.
- **`--json` + `-o` together**: `--json` streams events to stdout (for session ID extraction); `-o` independently captures the final message.
- **Config overrides**: Use `-c key=value` for one-off config changes: `-c model_reasoning_effort="low"`.
- **`--add-dir`**: Grant write access to additional directories beyond the workspace: `--add-dir /tmp/output`.
- **`--output-schema`**: Constrain the response shape with a JSON Schema file for structured output.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `command not found: codex` | codex-cli not installed | Install via npm or check PATH |
| `Authentication required` / `invalid API key` | OpenAI API key missing or expired | Run `codex login` or set `OPENAI_API_KEY` |
| `No sessions found` | No previous session to resume | Start a new session first with `codex exec` |
| `Session not found: <ID>` | Invalid or deleted session UUID | Check `~/.codex/sessions/` for valid IDs |
| `timed out` / process hangs | Prompt too complex or API issues | Use `run_in_background` with a timeout, or simplify the prompt |
| `Permission denied` / sandbox error | Sandbox policy too restrictive | Use `--full-auto` or `-s workspace-write` / `-s danger-full-access` |
| `Not a git repository` | codex exec requires git repo by default | Use `--skip-git-repo-check` or `cd` to a git repo |
| ANSI escape codes in output | Reading stdout instead of `-o` file | Always use `-o <file>` and read the file |

Read `references/cli-reference.md` for the full flag-by-flag reference of all subcommands.

## Behavior Scenarios

```gherkin
Scenario: One-shot Codex query
  Given codex CLI is installed and authenticated
  When the user asks to run a quick Codex prompt
  Then run `codex exec "<prompt>" --full-auto --ephemeral -o /tmp/codex-out.txt -C "$(pwd)"`
  And read the output file and present the result

Scenario: Multi-turn session with follow-up
  Given a Codex session was started with `codex exec`
  When the user asks to continue or follow up on the previous Codex conversation
  Then run `codex exec resume --last "<follow-up>" --full-auto -o /tmp/codex-out.txt`
  And present the continued conversation result

Scenario: Code review via Codex
  Given codex CLI is installed and user is in a git repository
  When the user asks Codex to review code changes
  Then run `codex exec review` with appropriate flags (--uncommitted, --base, --commit)
  And capture output via -o and present the review findings

Scenario: Resume or fork a specific session
  Given the user has previous Codex sessions
  When the user asks to resume or fork a specific session by ID
  Then run `codex exec resume <SESSION_ID> "<prompt>"` or `codex fork <SESSION_ID>`
  And present the result

Scenario: Codex CLI not installed or not authenticated
  Given codex CLI is not installed or not logged in
  When the user asks to perform any Codex operation
  Then check with `codex --version`, guide installation or `codex login` as needed
```
