# Launch & Handoff

How step 7 spawns the autonomous prd-council session. Driven by
`scripts/launch_council_session.sh`; this file explains the mechanism and the
seed prompt so you can verify/override it.

## The launch mechanism (ccb / claude-bg)

The user runs background Claude sessions via a `claude-bg` launcher and `cc*b`
aliases. Observed semantics (do not hardcode any absolute path — resolve
`claude-bg` on `PATH`):

- `claude-bg [--label <name>] <claude flags/args…>` generates a fresh session
  UUID, then `exec claude --session-id <uuid> --remote-control "<label>-<sid8>"
  --bg <flags> "<initial prompt>"`.
  - `--bg` backgrounds the session.
  - `--remote-control "<label>-<sid8>"` makes it **interactive but remotely
    drivable** — it appears in the Claude app's Remote Control list and is
    revivable with `ccon <sid8>` or `claude --resume <sessionId>`.
  - `--label` defaults to the cwd basename; we pass `--label <slug>` so the
    session is identifiable by feature.
- The `ccb` alias = `claude-bg --permission-mode auto --allow-dangerously-skip-permissions`.
  Aliases do NOT expand in non-interactive scripts, so the launcher passes these
  two flags explicitly to emulate `ccb`.
- `--permission-mode auto` + `--allow-dangerously-skip-permissions` make the
  session autonomous (auto-accept, permission bypass). This is why step 6 gates
  the launch behind explicit confirmation by default.

Because the session is `--remote-control`, prd-council's residual grill questions
surface in the Claude app for the user to answer remotely — the brief minimizes
them but does not have to eliminate them.

## Fallback ladder

1. **Preferred:** `claude-bg --label <slug> --permission-mode auto
   --allow-dangerously-skip-permissions [--model <m>] "<seed>"` (run from `<target>`).
2. **Fallback** (no `claude-bg`): replicate it — generate a uuid, then
   `claude --session-id <uuid> --remote-control "<slug>-<sid8>" --bg
   --permission-mode auto --allow-dangerously-skip-permissions [--model <m>] "<seed>"`.
3. **Last resort** (no `claude`, or `--print-only`, or launch errors): print the
   exact command and ask the user to run it. Never fail the whole workflow silently.

## The seed prompt (initial message to the spawned session)

Run from `<target>` so paths are relative to the target repo:

```
Read the implementation brief at docs/design/<slug>-impl-brief.md — it is the
finalized, already-grilled and Codex-reviewed design. Treat it as the complete
requirements: do NOT re-grill from scratch. Then run
/prd-council --slug <slug> --out docs/prd/<slug>/ --lang <lang>, using the brief as
the agreed requirements; only ask if a genuine blocking gap remains. Emit the
execution-ready doc set + tasks.md, then begin implementation per tasks.md,
following the brief's Branch setup (fresh feature branch — never a design/doc/PR branch).
```

## Reporting back

After launch, tell the user:
- Brief path: `<target>/docs/design/<slug>-impl-brief.md`
- Spawned session label: `<slug>-<sid8>` (find it in the Claude app's Remote Control list)
- Attach via: `ccon <sid8>` or `claude --resume <sessionId>`
- That prd-council's questions will appear in that session for remote answering.

## Path discipline

The launcher resolves `claude-bg` / `claude` via `command -v`. It must NOT embed
any operator-specific absolute path (an operator home directory or a Nix per-user
profile bin path) — always resolve tools on `PATH`. The `<slug>`, `<target>`,
`<lang>`, `<m>` values come from arguments.
