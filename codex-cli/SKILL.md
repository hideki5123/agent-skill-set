---
name: codex-cli
description: >
  Run OpenAI Codex CLI from the terminal for batch / one-shot `codex exec`
  invocations with output captured to an `-o` file. Use for fire-and-forget
  runs, scripted CI, code review batches (`codex review`), and resuming a
  specific session by id (`codex exec resume`). Always use this skill
  instead of `mcp__codex__codex` and `mcp__codex__codex-reply` MCP tools —
  CLI is faster and more capable.

  For streaming UX, multi-turn dialogues that need live state, structured
  (JSON schema) output, attaching images, or programmatic event handling
  → **use codex-server instead**. codex-server uses the user's ChatGPT
  subscription via Codex App Server and decoupled async invocation that
  bypasses the Bash 2-minute timeout entirely.

  Trigger patterns (batch-only — chat/streaming triggers belong to codex-server):
  codex-cli / codex CLI /
  codex exec / codex review / codex resume / codex fork /
  batch + {codex, gpt} / one-shot + {codex, gpt} / non-interactive + codex /
  codex {to a file, -o, output file, captured output} /
  CI + {codex, gpt} / scripted + {codex, gpt} /
  fork codex session / resume codex session by id
version: 1.2.0
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
- **Default to background execution.** Codex calls routinely take 2–10 minutes — well past the Bash tool's 2-minute default timeout. Launch with `run_in_background: true` and Monitor the `-o` file, OR pass `timeout: 600000` for foreground. Do NOT rely on default timeouts. See [Adaptive Execution](#adaptive-execution).

## Preflight Check

Before running any codex command, verify the installation:

```bash
codex --version
```

If this fails:
- **"command not found"** — codex-cli is not installed.
  Suggest: `npm install -g @openai/codex` or check the Codex CLI installation docs.
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
# Redirect JSONL to file (do NOT pipe through head — broken pipe kills codex)
codex exec "your prompt" --full-auto --json -o /tmp/codex-out.txt -C "$(pwd)" > /tmp/codex-events.jsonl 2>/dev/null

# Extract thread_id from the first event (jq not required — use grep+cut)
head -1 /tmp/codex-events.jsonl | grep -o '"thread_id":"[^"]*"' | cut -d'"' -f4
cat /tmp/codex-out.txt
```

The `--json` flag streams JSONL events to stdout. The first event is `thread.started` containing `thread_id` (the session UUID). The `-o` flag independently captures the final text response.

**Important**: Do NOT pipe `--json` output through `head` or other commands that close the pipe early — this causes a broken pipe signal that kills the codex process. Always redirect to a file first, then extract.

## Adaptive Execution

Codex CLI calls are slow — typically 2–10 minutes, sometimes longer for complex prompts or `high` reasoning effort. The Bash tool's default timeout is 2 minutes. Without explicit handling, the call gets killed mid-flight and the agent gives up before a response arrives.

**Pick a pattern for every codex call:**

### Pattern A — Background + Monitor (preferred for any non-trivial prompt)

Launch the codex command with the Bash tool's `run_in_background: true`, then wait for the `-o` file to be written before reading.

```bash
# 1. Launch in background — Bash tool param: run_in_background=true
rm -f /tmp/codex-out.txt   # clear stale output if reusing the path
codex exec "your prompt" --full-auto -o /tmp/codex-out.txt -C "$(pwd)"
```

Then use the **Monitor tool** with a **bounded** `for` loop to wait for completion without polling burn AND without infinite-looping if codex crashes:

```bash
# Monitor tool: 120 iterations × 5s = 10 minutes max
for i in $(seq 1 120); do
  [ -s /tmp/codex-out.txt ] && break
  sleep 5
done
[ -s /tmp/codex-out.txt ] || { echo "ERROR: codex produced no output within 10 min" >&2; exit 1; }
```

`-s` is true once the file exists and is non-empty (codex writes the final message at the end). The bound matters: an unbounded `until` loop will hang forever if codex crashes silently (network drop, OOM, killed) — same "agent gives up" failure mode in disguise. Always bound the wait.

If you also need to confirm the codex process has fully exited (e.g., before resuming), pair the success check with a `pgrep` check:

```bash
for i in $(seq 1 120); do
  [ -s /tmp/codex-out.txt ] && ! pgrep -f "codex exec" >/dev/null && break
  sleep 5
done
```

Caveat: `pgrep -f "codex exec"` matches **all** running codex processes. If you have concurrent codex calls in flight, scope it tighter (`pgrep -f "codex exec.*<unique-marker>"`) or skip the pgrep check.

### Pattern B — Foreground with extended timeout (only for short, simple prompts)

When you're confident the call will finish quickly (small prompt, `low` reasoning, no tool use), pass an explicit timeout to the Bash tool:

```bash
# Bash tool param: timeout=600000  (10 minutes — the maximum)
codex exec "short prompt" --full-auto --ephemeral -o /tmp/codex-out.txt -C "$(pwd)"
cat /tmp/codex-out.txt
```

Never rely on the default 2-minute timeout for codex calls.

### Tune for speed

When latency matters more than depth, reduce the work codex does:

| Lever | Flag | Effect |
|-------|------|--------|
| Reasoning effort | `-c model_reasoning_effort="low"` | Fastest. Use `medium` (default) or `high` only when needed. |
| Smaller model | `-m gpt-5.4-mini` (or current mini variant) | Faster, cheaper, less capable. |
| Disable web search | (omit `--search`) | Search adds round-trips. |
| Tighter prompt | — | Less to read = less to think about. |
| Read-only sandbox | `-s read-only` | No tool-use round-trips. Pure analysis. |

Combine for fastest responses:

```bash
codex exec "quick question" --full-auto --ephemeral \
  -c model_reasoning_effort="low" \
  -o /tmp/codex-out.txt -C "$(pwd)"
```

### Decision rule

- **Default**: Pattern A (background + Monitor). Safe for any prompt length.
- **Pattern B**: only when the prompt is small AND you've tuned for speed AND you'd rather block than context-switch.
- **Never**: foreground + default timeout. Codex will outlast it and the agent will give up.

## Quick Reference

> **Note**: For every command below, the Bash tool should use `run_in_background: true` (default) or `timeout: 600000` (foreground). Codex calls outlast the 2-min default timeout. See [Adaptive Execution](#adaptive-execution).

| Task | Command |
|------|---------|
| One-shot (no session) | `codex exec "prompt" --full-auto --ephemeral -o /tmp/codex-out.txt -C "$(pwd)"` |
| Persistent session | `codex exec "prompt" --full-auto -o /tmp/codex-out.txt -C "$(pwd)"` |
| Fast/low-latency query | `codex exec "prompt" --full-auto --ephemeral -c model_reasoning_effort="low" -o /tmp/codex-out.txt -C "$(pwd)"` |
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

`--last` picks the most recent session **filtered by current working directory**. The follow-up inherits the full conversation context.

**CWD filtering caveat**: `--last` only finds sessions started from the same CWD. If resuming from a different directory, use `--all` to disable CWD filtering, and add `--skip-git-repo-check` if the directory is not a git repo:

```bash
codex exec resume --last --all "follow-up" --full-auto -o /tmp/codex-out.txt --skip-git-repo-check
```

### Resume a specific session by ID

When working with multiple sessions, resume by UUID:

```bash
codex exec resume "019d3942-55ab-7ac1-b77f-8d5bcb1cd80c" "What about the edge cases?" --full-auto -o /tmp/codex-out.txt
cat /tmp/codex-out.txt
```

To capture the session ID when starting a session:

```bash
# Start session and capture JSONL events to file
codex exec "Start analyzing the API layer" --full-auto --json -o /tmp/codex-out.txt -C "$(pwd)" > /tmp/codex-events.jsonl 2>/dev/null

# Extract thread_id (no jq needed)
SESSION_ID=$(head -1 /tmp/codex-events.jsonl | grep -o '"thread_id":"[^"]*"' | cut -d'"' -f4)
echo "Session ID: $SESSION_ID"
cat /tmp/codex-out.txt

# Later, resume with explicit ID (works across any CWD):
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
- **`run_in_background` by default**: Codex routinely takes 2–10 minutes, exceeding the Bash tool's 2-minute default timeout. Launch every non-trivial codex call with `run_in_background: true` and use the Monitor tool to wait on the `-o` file. Foreground calls require explicit `timeout: 600000`. See [Adaptive Execution](#adaptive-execution).
- **Tune reasoning effort for latency**: For quick queries, pass `-c model_reasoning_effort="low"`. The default (`medium`) is balanced; reserve `high` for genuinely hard problems where you're willing to wait.
- **`-s read-only` for safe analysis**: When codex only needs to read and analyze (not write), use read-only sandbox mode.
- **`-m` for model override**: Switch models per-query without changing config: `-m o3`, `-m gpt-5.4`, etc.
- **`-i` for image input**: Attach screenshots or diagrams: `-i screenshot.png`.
- **`--search` for web search**: Enable web search capability: `codex exec "what's new in React 19" --search --full-auto -o /tmp/codex-out.txt`.
- **Pipe from stdin**: Use `-` as prompt to read from stdin: `echo "explain this" | codex exec - --full-auto -o /tmp/codex-out.txt`.
- **`--json` + `-o` together**: `--json` streams JSONL events to stdout (redirect to file, do NOT pipe through `head`); `-o` independently captures the final message. First event's `thread_id` is the session UUID.
- **`--all` for cross-CWD resume**: `codex exec resume --last` filters sessions by CWD. Add `--all` to find sessions started from any directory.
- **`--skip-git-repo-check`**: Required when running codex from a directory that is not a git repository.
- **Config overrides**: Use `-c key=value` for one-off config changes: `-c model_reasoning_effort="low"`.
- **`--add-dir`**: Grant write access to additional directories beyond the workspace: `--add-dir /tmp/output`.
- **`--output-schema`**: Constrain the response shape with a JSON Schema file for structured output.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `command not found: codex` | codex-cli not installed | Install via npm or check PATH |
| `Authentication required` / `invalid API key` | OpenAI API key missing or expired | Run `codex login` or set `OPENAI_API_KEY` |
| `No sessions found` | No session to resume, or CWD mismatch | Start a new session, or add `--all` to disable CWD filtering |
| `Session not found: <ID>` | Invalid or deleted session UUID | Check `~/.codex/sessions/` for valid IDs |
| `timed out` / agent gives up before response | Bash 2-min default timeout shorter than typical codex latency (2–10 min) | Default to `run_in_background: true` + Monitor on the `-o` file. For foreground, set `timeout: 600000`. Tune speed via `-c model_reasoning_effort="low"` or a smaller `-m`. See Adaptive Execution. |
| `Permission denied` / sandbox error | Sandbox policy too restrictive | Use `--full-auto` or `-s workspace-write` / `-s danger-full-access` |
| `Not a git repository` | codex exec requires git repo by default | Use `--skip-git-repo-check` or `cd` to a git repo |
| ANSI escape codes in output | Reading stdout instead of `-o` file | Always use `-o <file>` and read the file |
| Broken pipe / empty `-o` file | Piping `--json` stdout through `head` or other early-close commands | Redirect `--json` to a file (`> events.jsonl`), then extract from the file |
| Resume finds wrong session | `--last` filtered by CWD, picked a different session | Use explicit session ID, or add `--all` to search all sessions |

Read `references/cli-reference.md` for the full flag-by-flag reference of all subcommands.

## Retrospective

After completing the workflow, reflect on the entire execution session:

1. Consider: Were there mid-session corrections? Rejected outputs? Plan changes? Errors? Did codex calls time out or hang?
2. Ask the user: "Quick feedback on this run? (1-5 rating, note any issues, or press enter to skip)"
3. If the user provides feedback OR if corrections/issues occurred during this session:
   a. Create `feedback/` directory if it does not exist
   b. Read `feedback/log.md` (create with `# Feedback Log` header if it does not exist)
   c. Prepend a new entry after the header using the log format from `my-skill-factory/references/skill-improvement-guide.md`
   d. Fill in: current timestamp, skill version from frontmatter, task description, outcome assessment,
      corrections that occurred during the session, issues encountered, user's note
4. If the user skips AND no corrections or issues occurred, end without recording.

## Behavior Scenarios

```gherkin
Scenario: One-shot Codex query
  Given codex CLI is installed and authenticated
  When the user asks to run a quick Codex prompt
  Then run `codex exec "<prompt>" --full-auto --ephemeral -o /tmp/codex-out.txt -C "$(pwd)"`
  And read the output file and present the result

Scenario: Multi-turn session with follow-up (same CWD)
  Given a Codex session was started with `codex exec` from directory X
  When the user asks to continue from the same directory X
  Then run `codex exec resume --last "<follow-up>" --full-auto -o /tmp/codex-out.txt`
  And present the continued conversation result with prior context preserved

Scenario: Multi-turn session with follow-up (different CWD)
  Given a Codex session was started from directory X
  When the user asks to continue from a different directory Y
  Then run `codex exec resume --last --all "<follow-up>" --full-auto --skip-git-repo-check -o /tmp/codex-out.txt`
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

Scenario: Long-running Codex query without timing out
  Given a Codex prompt is expected to take longer than 2 minutes
  When the user asks to run any non-trivial codex command
  Then launch with the Bash tool's `run_in_background: true` and `-o /tmp/codex-out.txt`
  And use the Monitor tool with a bounded `for i in $(seq 1 120); do [ -s /tmp/codex-out.txt ] && break; sleep 5; done`
  And after the loop, verify the file is non-empty (codex may have crashed) and surface an error if not
  And read /tmp/codex-out.txt only after the loop exits with a non-empty file
  And never rely on the default 2-minute Bash timeout

Scenario: Latency-sensitive Codex query
  Given the user wants a fast answer and depth is not critical
  When running codex exec
  Then add `-c model_reasoning_effort="low"` and consider a smaller `-m` model
  And still use background execution (Pattern A) unless the prompt is trivially short
```
