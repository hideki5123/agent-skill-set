# Error handling — lookup table

**Read only on error.** Not loaded during normal operation.

## Decision table

| Symptom                                              | Cause                                            | Fix                                                                                                                    |
| ---------------------------------------------------- | ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| `chat.ts` exits 2, prints login guide                | `~/.codex/auth.json` missing                     | Run `codex login`, sign in with ChatGPT account, re-invoke. See `auth-setup.md`.                                       |
| `setup.ts`: "mise is not installed"                  | mise binary missing                              | `brew install mise` (macOS) or `curl https://mise.run \| sh` (Linux). Re-run setup.                                    |
| `setup.ts`: "`codex` is not installed"               | codex binary missing on PATH                     | `brew install codex` or `npm install -g @openai/codex`. Re-run setup.                                                  |
| `chat.ts new`: spawn worker fails                    | deno binary path wrong, or `--allow-run` denied  | Re-run `setup.ts` to refresh `~/.codex-server/config.json`. Ensure caller's `--allow-run` includes the deno path.      |
| `status` reports `state: "abandoned"`                | Worker process crashed before marker write       | Inspect `worker.log` in the turn-dir for `[boot]`/`[fail]` lines (no `[boot]` ⇒ worker never started). Then `new` a fresh turn — no recovery. Turn-dir stays until 7-day GC. |
| Turn hangs: `status` stuck on `running`, `out.txt` not growing for minutes | SDK event stream stalled (network drop, app-server protocol mismatch, wedged child) | The idle watchdog auto-fails it after `CODEX_SERVER_IDLE_SECS` (default 180s) → state flips to `failed`; `worker.log` shows `[watchdog]`. If it never flips, the worker binary predates the watchdog — re-run `setup.ts`. Run `chat.ts doctor`. |
| `status` reports `state: "stalled"`                  | Worker alive but no output progress >5 min and its own watchdog didn't fire | Backstop signal; usually self-heals to `failed` shortly. If persistent, the worker binary is stale — re-run `setup.ts`. |
| Hangs are frequent / intermittent across turns       | Version drift: the codex binary was upgraded since `setup.ts` ran, so the resolved `sdkSpec` no longer matches the binary's app-server protocol | `chat.ts doctor` shows `codex.drift`. Fix: **re-run `setup.ts`** — it re-resolves `sdkSpec` to the current binary minor. (The SDK pin is machine-adaptive, so there's no version to hand-edit.) |
| `wait`/`tail`/`status` says `abandoned` but the turn is really still running | Caller's `--allow-run` omits `kill`, so the `kill -0` liveness probe throws `NotCapable` → the worker reads as not-alive once past the startup grace | Add `kill`: `--allow-run=<codex-path>,<deno-path>,kill`. See SKILL.md "Required deno permissions". |
| `status` reports `state: "missing"`                  | Turn-id has no turn-dir (typo or GC'd)           | Verify the turn-id; check `list-turns` for recent ones.                                                                |
| `out.txt` contains `[turn.failed] sandbox denied...` | codex's sandbox blocked the action               | Inspect the command; consider `--config sandbox_mode=workspace-write` already on; check the SDK's sandbox rules.       |
| `out.txt` contains `[turn.failed] Not inside a trusted directory and --skip-git-repo-check was not specified` (on `continue` / resume) | Resuming into a non-git dir. (Since the v1.2.0 SDK bump the worker passes `skipGitRepoCheck` to `resumeThread`, so `continue --skip-git-check` now handles this — only seen if the worker binary predates the bump.) | Re-run `setup.ts`; pass `--skip-git-check` to `continue`. Or add the cwd to codex's trusted-projects config (`~/.codex/config.toml`). |
| `out.txt` contains `[turn.failed] Not a git repo` on `new`   | Codex requires a git repo by default            | Add `--skip-git-check` (works on both `new` and `continue` since v1.2.0).                                              |
| `wait` exits 2 (timeout)                             | Turn still running past `--timeout` seconds      | Either wait longer (re-invoke wait) or use `tail --follow` for live view.                                              |
| `tail`: out.txt doesn't exist                        | Worker hasn't written anything yet               | tail polls; if it remains empty for many seconds, run `status` — worker may have failed before writing.                |
| ANSI escape codes in output                          | Should not happen — SDK gives structured events  | If it does, file a bug. The worker renders to plain text. Compare `events.jsonl` to `out.txt`.                         |
| "Cannot find module `npm:@openai/codex-sdk`"         | deno cache miss + no network                     | Run a quick connected `chat.ts` invocation to populate deno's npm cache, or `deno cache npm:@openai/codex-sdk@^0.142.4`. |
| Token-cost surprise (e.g., heavy usage)              | Forgot ChatGPT subscription has rate limits      | Check your ChatGPT plan's usage page. Note: this skill never uses `OPENAI_API_KEY`, so no API-key billing is involved. |

## Quick triage commands

```bash
# One-shot health report (auth + version skew + stuck turns) — start here.
deno run --allow-... ~/.codex-server/lib/chat.ts doctor

# Why did a worker die? (boot/fail/watchdog diagnostics)
cat ~/.codex-server/turns/<turn-id>/worker.log

# Auth ready?
ls -la ~/.codex/auth.json

# Workspace healthy?
ls -la ~/.codex-server/lib/ ~/.codex-server/turns/

# codex binary version & path?
cat ~/.codex-server/config.json

# Recent turns and their state?
deno run --allow-... ~/.codex-server/lib/chat.ts list-turns

# Specific turn state?
deno run --allow-... ~/.codex-server/lib/chat.ts status <turn-id>

# Full event log for a turn?
cat ~/.codex-server/turns/<turn-id>/events.jsonl

# Final agent message only?
jq -r 'select(.type=="item.completed" and .item.type=="agent_message") | .item.text' \
  ~/.codex-server/turns/<turn-id>/events.jsonl | tail -1
```

## Escalating

If you can't fix it from this table and the bug is reproducible:

1. Capture `events.jsonl` for the failing turn (it has everything the SDK saw).
2. Note your codex binary version (`cat ~/.codex-server/config.json`) and
   resolved `@openai/codex-sdk` spec (`sdkSpec` in `~/.codex-server/config.json`,
   machine-adaptive — derived from the codex binary minor at setup).
3. File the issue with these artifacts; do **not** include `auth.json`.
