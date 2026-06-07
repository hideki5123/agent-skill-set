# Execution patterns — decoupled async architecture

**Read only when the SKILL.md 3-line summary is not enough, or when hitting an
edge case.** Not loaded during normal operation.

## Why "decoupled async"?

Claude Code's `Bash` tool has a 2-minute default timeout. Codex turns can take
2-10 minutes. The naive approach — running the SDK call synchronously inside
the deno script Bash invokes — would either:

- die at 2 min (lost work)
- require every caller to remember `run_in_background: true` plus a bounded
  poll loop (codex-cli's pattern — error-prone)

Instead, `chat.ts new` / `continue` always returns in <1 s by **forking a
detached worker** that owns the long-running SDK call. The worker streams
its output to per-turn files; Claude observes progress via the `Monitor`
tool on those files. The Bash 2-min timeout never applies to the actual
turn because the Bash invocation has already exited.

## Component lifecycles

```
  chat.ts new (Bash invocation)             worker.ts (detached)
  ────────────────────────────             ─────────────────────
  1. Auth check (~1 ms)                    (not yet running)
  2. Generate turn_id (~1 ms)
  3. Create turn-dir (~5 ms)
  4. Write prompt.txt + initial meta.json
  5. Spawn worker via Deno.Command + unref
  6. Print {turn_id, out_path, ...} JSON
  7. Exit 0                                 spawned, writes its pid to meta.json
                                            opens SDK, sends turn
                                            iterates AsyncIterable<ThreadEvent>
                                              appends events.jsonl line-by-line
                                              appends out.txt human-readable
                                            on turn.completed → touch done
                                            on turn.failed     → touch error
                                            on uncaught error  → touch error
                                            exit
```

Total `new` invocation latency: typically 100-500 ms on a warm machine.

## Marker contract

`turn-dir/<id>/done` and `error` are empty marker files. Their presence is the
authoritative "turn state" signal. Always check markers, not parse out.txt or
events.jsonl tail-line.

State decision tree (used by `status` and `wait`):

```
if turn-dir does not exist                          → state="missing"
else if done marker exists                          → state="complete"
else if error marker exists                         → state="failed"
else if meta.json missing or unparsable             → state="missing"
else if within ~10s startup grace of started_at     → state="running"
else if worker pid > 0 and alive (kill -0)          → state="running"
else                                                → state="abandoned"
```

The startup-grace step covers the brief window between `new` creating the
turn-dir and the worker recording its real pid; without it a poll in that gap
would see no marker and a not-yet-live pid and wrongly report "abandoned".

The `kill -0` liveness check requires `kill` in the caller's `--allow-run`
(see SKILL.md "Required deno permissions"). Without it the probe throws
`NotCapable` and the turn reads as not-alive — so a turn outliving the grace
window would falsely report "abandoned". pid 0 is treated as not-alive because
`kill -0 0` targets the caller's process group and spuriously succeeds.

`abandoned` means the worker crashed before writing a marker. Treat it as
failed; no recovery is attempted (just start a new turn). The 7-day GC will
sweep stale dirs.

## When to use `wait` vs `tail` vs Monitor

| You need                                | Use                                              |
| --------------------------------------- | ------------------------------------------------ |
| Final text only, ok to block            | `chat.ts wait <id>`                              |
| Live streaming in your terminal         | `chat.ts tail <id> --follow`                     |
| Claude Code to observe streaming        | `Monitor` on the returned `out_path`             |
| Programmatic JSON event consumption     | Read `events.jsonl` directly                     |
| Just check current state                | `chat.ts status <id>`                            |

`wait` and `tail --follow` can themselves exceed Bash's 2-minute timeout for
long turns. If you invoke them from Claude Code, use `run_in_background: true`
+ Monitor on the file — same pattern as any other long-running command.
`new` and `continue` never need this because they return <1 s by design.

## Concurrency

Multiple turns can run concurrently — each gets its own turn-id and turn-dir
and its own codex app-server subprocess. There is no shared state in deno;
the only shared state is `~/.codex/sessions/` which the codex binary itself
manages.

## Cleanup

`setup.ts` runs a 7-day GC on every invocation: any turn-dir whose mtime is
older than 7 days is `Deno.remove(..., { recursive: true })`-d. Run setup
manually if your `~/.codex-server/turns/` is taking up too much disk; or
simply `rm -rf ~/.codex-server/turns/<turn-id>` for a specific turn.

## What can go wrong

- **Worker spawn fails** (e.g., deno binary not at the path we expected):
  `chat.ts new` itself errors and exits non-zero. No turn-dir is left behind
  beyond the partial meta.json.
- **Worker crashes during SDK call**: the unhandledrejection handler tries
  to write the `error` marker. If even that fails, the turn becomes
  `abandoned`.
- **codex binary crashes**: the SDK throws on its own; worker catches in the
  outer try/catch and writes `error`.
- **Disk full**: writes throw; falls into the abandoned path.

In all failure modes, a future `new` is independent — there is no skill-level
state that needs cleanup.
