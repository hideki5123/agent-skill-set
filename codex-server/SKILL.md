---
name: codex-server
description: >
  Run OpenAI Codex via the Codex App Server (JSON-RPC-over-stdio) for streaming
  multi-turn chat sessions with persistent threads, structured output, image
  input, and rich event streams. Default entry point for ChatGPT/GPT/Codex-like
  conversations from the terminal. Uses the user's ChatGPT subscription
  (Plus / Pro / Team) exclusively via `codex login` — never consumes
  OPENAI_API_KEY billing, by design. Implementation: TypeScript on deno with
  npm:@openai/codex-sdk; spawns the existing system codex binary.
  Decoupled async invocation: every turn returns turn-id in <1 s; the actual
  SDK work runs in a detached worker that streams to per-turn files under
  ~/.codex-server/turns/<turn-id>/ — Bash's 2-min timeout never applies.
  Prefer this over codex-cli for streaming UX, multi-turn dialogues that need
  live state, structured (JSON schema) output, attaching images, or
  programmatic event handling. Use codex-cli only for one-shot batch
  invocations that pre-capture to an -o file.
  Trigger patterns (match any variation):
  codex / codex-server / codex app server / codex app-server /
  openai / open ai / OpenAI / chatgpt / chat gpt / ChatGPT / GPT /
  ask gpt / chat with gpt / gpt session / codex session /
  streaming chat / multi-turn chat / multi turn chat /
  second opinion / cross-check / cross check /
  ai pair programming / another AI / external AI /
  ask another model / get GPT's take / what does openai think /
  show me what gpt thinks / structured output from gpt / json schema gpt /
  resume codex thread / continue codex conversation / continue codex session /
  /codex-server
version: 1.0.0
---

# Codex Server Skill

Run OpenAI Codex App Server via `@openai/codex-sdk` on deno. Streams multi-turn
chat sessions, structured output, image input, and rich event logs. This is the
**default** ChatGPT/Codex skill — prefer it over `codex-cli` (which is reserved
for batch one-shot `codex exec` use).

## Auth: ChatGPT subscription only

This skill is **ChatGPT-subscription-only by design**. There is no API-key
fallback — `OPENAI_API_KEY` is not in `--allow-env`, so deno cannot read it
even if exported.

- If `~/.codex/auth.json` exists (i.e., `codex login` has been completed),
  the skill works using the user's ChatGPT Plus / Pro / Team subscription. No
  API-key billing is consumed.
- If `~/.codex/auth.json` is missing, every subcommand fails with exit code 2
  and prints the login guide. The user must run `codex login` (browser flow)
  and re-invoke.

For the full login walkthrough (account types, troubleshooting) read
`references/auth-setup.md` — **but only when auth.json is missing**.

## First-run setup

Run once after install. No env vars needed.

```bash
deno run --allow-read --allow-write --allow-env --allow-run=mise,codex,which \
  ~/.claude/plugins/cache/hideki-plugins/codex-server/1.0.0/skills/codex-server/assets/lib/setup.ts
```

setup.ts copies `chat.ts` / `worker.ts` / `helpers.ts` into `~/.codex-server/lib/`,
pins the codex binary path into `~/.codex-server/config.json`, and prepares the
turns directory. After setup, run subsequent invocations from
`~/.codex-server/lib/chat.ts` (stable path, version-independent).

## Operational flow (≤3 lines — this is the whole point)

1. `deno run … chat.ts new "<prompt>"` → returns `{turn_id, out_path, ...}` JSON in <1 s. A detached worker runs the actual turn.
2. Watch progress: use the `Monitor` tool on the returned `out_path` (it grows as deltas arrive).
3. Done when the `done` marker file appears alongside `out.txt`; on `error`, the `error` marker appears instead.

**No `run_in_background: true`. No bounded poll loops. No timeout knobs.** The
deno invocation that Bash spawns exits in <1 s regardless of turn duration.

If you need a blocking call, use `chat.ts wait <turn-id>` — it polls the markers
and prints the final `out.txt` on completion.

## CLI surface

All subcommands of `~/.codex-server/lib/chat.ts`. See `references/examples.md`
for worked examples (only read when an unfamiliar invocation is needed).

- `new "<prompt>" [--model M] [--cwd PATH] [--schema FILE] [--image P]… [--skip-git-check]`
- `continue [--last | --thread <id>] "<prompt>" [same flags]`
- `tail <turn-id> [--follow]`
- `wait <turn-id> [--timeout SECS]`
- `status <turn-id>` — JSON: `running` / `complete` / `failed` / `abandoned` / `missing`
- `list-turns [--limit N]`
- `list` — recent threads from `~/.codex/sessions/`
- `show <thread-id>` — thread metadata + tail

`new` / `continue` always return turn-id in <1 s. `tail` / `wait` are
explicitly blocking; if they exceed 2 min, invoke them with
`run_in_background: true` and use Monitor on the output file instead — same
pattern as any other streaming command.

## Required deno permissions

The setup script pins the codex binary path. After setup, every
`chat.ts` invocation needs these flags:

- `--allow-read` and `--allow-write` — workspace + working dir + turn files
- `--allow-env=PATH,HOME,USERPROFILE` — only; deliberately omits `OPENAI_API_KEY`
- `--allow-run=<codex-path>,<deno-path>,kill` — `<codex-path>` from `~/.codex-server/config.json`; `<deno-path>` (`Deno.execPath()`) because `new`/`continue` fork a detached deno worker; `kill` because `wait`/`tail`/`status` liveness-check the worker via `kill -0`
- `--allow-net=api.openai.com` — defensive

## Streaming and events

The worker writes one JSON event per line to `events.jsonl` and a
human-readable rendering to `out.txt`. Item types observed:
`agent_message`, `reasoning`, `command_execution`, `file_change`, `todo_list`.
For deep parsing or extending event rendering read
`references/streaming-protocol.md` — only when the default rendering is
insufficient.

## Per-turn directory layout

`~/.codex-server/turns/<turn-id>/` contains:

- `prompt.txt` — the user prompt
- `meta.json` — `{ turn_id, thread_id, started_at, cwd, model, pid, resumed_from }`
- `events.jsonl` — every `ThreadEvent` (one JSON per line)
- `out.txt` — streamed human-readable text
- `done` (marker) — present once `turn.completed` fires
- `error` (marker) — present on `turn.failed` or uncaught worker errors

`setup.ts` GCs turn-dirs older than 7 days on every invocation.

## Error handling

On unexpected behavior read `references/error-handling.md`. Common cases:

- `~/.codex/auth.json` missing → run `codex login`
- `codex` not on PATH → install via `brew install codex` or `npm install -g @openai/codex`
- worker crashed → `status` reports `abandoned`; safe to abandon, just `new` again

## Deferred features

These are intentionally out of scope for v1.0.0. Pull them in only on demand.

- [ ] Interactive tool-approval flow (`turn/approve` / `turn/reject`) via raw JSON-RPC. Currently auto-approved via `approval_policy: on-failure`.
- [ ] WebSocket transport (`--listen ws://IP:PORT`).
- [ ] In-skill ChatGPT login orchestration (`account/login/start`, device code) — users complete `codex login` externally.
- [ ] Persistent app-server (warm process) — amortize ~500ms–2 s startup per turn.
- [ ] Per-session model upgrade detection à la openai-cli's `resolveModel.ts`. Currently defers to `~/.codex/config.toml`.
- [ ] Raw JSON-RPC sub-mode using `codex app-server generate-ts` bindings.

## Behavior Scenarios

BDD spec lives in `references/scenarios.feature`. Read only when auditing or
amending the skill (e.g., via `/skill-improve`); **not needed for normal
execution**.

## Feedback Check

Before doing any work, if `feedback/log.md` exists next to this SKILL.md and
has ≥5 entries, read the last 10. If a pattern is apparent (the same keyword
in 3+ entries, or average rating below 3), tell the user (in Japanese):
「過去のフィードバックで類似パターンを検出: [簡潔に]。`/skill-improve --skill codex-server` で改善案を分析できます。」
Otherwise proceed silently.

## Retrospective

After completing a session, reflect:

1. Were there mid-session corrections, errors, or surprises?
2. Ask the user (in Japanese): 「今回のセッションのフィードバック (1-5の評価、気になった点、または何もなければEnter)」
3. If the user provides feedback OR if corrections/issues actually occurred:
   - Create `feedback/log.md` next to this SKILL.md if missing (header: `# Feedback Log` + blank line + `<!-- Append new entries at the top. Do not edit previous entries. -->`).
   - Prepend a new entry:
     ```markdown
     ## <ISO-8601 timestamp>
     - **Skill Version**: 1.0.0
     - **Task**: <brief description>
     - **Outcome**: success | partial-success | failure | error
     - **Rating**: <N>/5 (or "—" if not provided)
     - **Corrections**: <mid-session corrections, or "none">
     - **Issues**: <specific problems, or "none">
     - **User Note**: <user's verbatim feedback, or "—">
     ---
     ```
4. If the user skips AND no corrections/issues occurred, end without recording.

## References

Read these on-demand only — they are not auto-loaded.

- `references/scenarios.feature` — Gherkin BDD spec. **Only for skill-improve / audit. Never during normal execution.**
- `references/auth-setup.md` — `codex login` walkthrough. Only when auth.json is missing.
- `references/sdk-reference.md` — `Codex` / `Thread` / `Turn` API quick-ref. Only when extending or debugging.
- `references/streaming-protocol.md` — event/item types. Only when default rendering is insufficient.
- `references/execution-patterns.md` — full rationale for decoupled async. Only when this 3-line summary is not enough.
- `references/examples.md` — worked invocations. Only when an unfamiliar pattern is needed.
- `references/error-handling.md` — error-to-fix lookup. Only on error.
