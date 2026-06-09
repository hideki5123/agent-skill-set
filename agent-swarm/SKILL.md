---
name: agent-swarm
description: Orchestrate multiple coding-agent sessions (Claude Code, Codex, Gemini) over the mcp_agent_mail MCP server, observe their progress on a recurring auto-loop, and prevent inconsistencies (file/edit conflicts and contradictory decisions) between concurrent tasks. Auto-manages the agent-mail server, derives the shared room key from the git repo, and runs either as the orchestrator/observer or as a participating worker. Handles the operational details (server startup, room key, reservation conventions) so the user does not have to remember them. Use when coordinating several agent sessions on different tasks at once, watching a swarm of sessions for conflicts, or wiring already-running sessions into a shared coordination room. Trigger phrases: "agent-swarm", "/agent-swarm", "orchestrate agents", "orchestrate multiple claude sessions", "coordinate sessions", "watch for conflicts between agents", "observe the swarm", "prevent inconsistency between sessions", "multi-agent observe", "複数セッションを協調", "エージェント協調", "セッション間の不整合監視", "スウォーム監視", "複数のClaudeを束ねて".
---

# Agent Swarm

Coordinate several coding-agent sessions working on different tasks at the same
time, observe them, and keep them from stepping on each other. Built on the
`mcp_agent_mail` MCP server (tools appear in-session as
`mcp__mcp-agent-mail__<tool>`).

The skill owns the operational chores so the user does not have to: it starts
the agent-mail server if it is down, derives the shared room key from the repo,
and bakes the reservation conventions into the workflow.

Two modes, auto-selected (Step 2):
- **Orchestrator / observer** — assigns tasks, watches for conflicts, intervenes.
- **Worker** — joins the room, reserves files before editing, reports progress.

`mcp_agent_mail` is **cooperative and advisory**: a session is only visible once
it registers, and file reservations signal intent rather than hard-locking.
Consistency therefore rests on three layers, all handled here: (1) every session
participates, (2) the orchestrator watches the shared lock view, (3) per-task
git worktrees give physical isolation as a backstop.

## Step 0 — Preflight: ensure the server (auto)

1. Check whether `mcp__mcp-agent-mail__health_check` is callable.
   - **If the tool is missing from this session:** the server was not connected
     at session start. Start it in the background:
     ```bash
     nohup bash "${XDG_DATA_HOME:-$HOME/.local/share}/mcp_agent_mail/scripts/run_server_with_token.sh" >/tmp/agent-mail.log 2>&1 &
     ```
     Then tell the user: MCP servers connect only at session startup, so they
     must open a **new session** for the agent-mail tools to load, and re-run
     `/agent-swarm` there. Stop here.
   - **If the tool is present:** call `health_check`. If it errors, the process
     died — restart it with the command above (it re-reads the existing token
     from `.env`, so auth stays consistent), wait a moment, retry once.
2. If the install dir does not exist, the server was never installed — tell the
   user to install `mcp_agent_mail` first and stop.

## Step 1 — Resolve the shared room key (auto)

- `project_key` = the basename of `git rev-parse --show-toplevel` run in the
  user's working directory. All sessions that should talk to each other MUST use
  the **same** `project_key`.
- If not inside a git repo, ask the user for a short room key once.
- State the resolved `project_key` to the user so every session can match it.

## Step 2 — Detect the role

- If the invocation arguments contain `worker` (optionally `worker <name> <task>`),
  use **Worker mode**.
- If they contain `orchestrator`, use **Orchestrator mode**.
- Otherwise read `resource://agents/{project_key}` and ask the user once: run as
  the orchestrator/observer, or join as a worker? Default to orchestrator when no
  agents are registered yet.
- An interval token in the args (e.g. `30s`, `60s`, `2m`) sets the orchestrator
  observe cadence; default `30s`. `off` disables auto-looping (manual cycles
  only). The interval is ignored in worker mode.

## Orchestrator mode

1. **Register**: ensure the room exists first, then register. Call
   `ensure_project(project_key)`, then `register_agent(project_key,
   program="claude-code", model=<this model id>, name="orchestrator",
   task_description="orchestration + consistency watch")` — or equivalently
   `macro_start_session` with no reservation paths, which ensures the project,
   registers, and returns the first inbox snapshot in one call. Keep the
   returned `registration_token` for later calls.
2. **Build the roster**: read `resource://agents/{project_key}`; `whois` each
   worker for its program/model/task. Maintain an internal map of
   task → owner agent → owned file paths, with **non-overlapping** path sets.
3. **Assign tasks**: for each task, `send_message(thread_id=<task-slug>,
   ack_required=true, importance="high")` containing: the goal and done
   criteria, the explicit list of paths the worker owns, and the standing rule —
   "reserve paths with `file_reservation_paths(exclusive=true)` before editing;
   if a reservation is blocked or overlaps, do not edit — message the
   orchestrator." Shared-contract files (types, API schemas, migrations, config,
   shared modules) belong to no one by default and require orchestrator approval.
4. **One observe cycle** — the steps below; Step 7 makes this recur automatically:
   - `fetch_inbox(project_key, "orchestrator", unread_only=true)` — deltas only;
     re-fetch with `include_bodies=true` only for messages that need a decision.
   - Read `resource://tooling/locks` (all active reservations) and flag: two
     exclusive reservations on overlapping paths; a worker reporting an edit to a
     path it never reserved; a reservation on another task's owned path or on a
     shared-contract file.
   - Read `resource://tooling/recent/600` for the last 10 minutes of activity and
     scan for contradictory decisions (the same type/interface/contract changed
     two different ways).
   - Emit a status table: worker / task / progress / reserved paths / blockers /
     conflict flags.
   - `acknowledge_message` everything actionable. Detect non-responders via
     `resource://views/ack-overdue/orchestrator`.
5. **Intervene on conflict**: send an `importance="urgent"`, `ack_required=true`
   HOLD to each involved worker (pause edits on the contested paths), then either
   re-assign ownership or serialize the work (land A, then B). Funnel shared
   contracts through a single worker while others wait. After resolution, send
   the release, and `force_release_file_reservation` any dead reservation.
6. **Never edit code** — this session coordinates and observes only.
7. **Run continuously (auto-loop)** — after the first cycle, start the recurring
   watch yourself; do not make the user run `/loop` manually. Invoke the `/loop`
   skill with the chosen interval and an observe-cycle prompt, e.g.
   `/loop 30s run one agent-swarm observe cycle: fetch unread inbox, read
   resource://tooling/locks and resource://tooling/recent/600, update the status
   table, and intervene on any conflict per the playbook`. Use the interval from
   the args (default `30s`). If the args say `off`, skip auto-looping and run
   cycles manually instead. The loop ends when the user says stop or when all
   tasks are completed and acknowledged — say so and stop scheduling.

Read `references/playbook.md` for the conflict taxonomy, the full intervention
protocol, token-discipline rules, and the ready-to-paste worker join prompt.
WHEN TO READ: when assigning tasks, when a conflict appears, or when onboarding
sessions.

## Worker mode

1. **Join in one call**: `macro_start_session(human_key=<project_key>,
   program="claude-code", model=<this model id>, agent_name=<assigned name>,
   task_description=<task>, file_reservation_paths=[paths to edit],
   file_reservation_ttl_seconds=3600)`. Keep the `registration_token`.
2. Immediately `fetch_inbox(unread_only=true)` and `acknowledge_message` the
   orchestrator's instructions.
3. **Reserve before editing**: `file_reservation_paths(exclusive=true)` for the
   paths you are about to touch. If blocked or overlapping, do not edit — message
   the orchestrator and wait for a grant.
4. Stay inside your owned paths / worktree. Never change shared-contract files
   without orchestrator approval.
5. Report progress to your task thread; set `ack_required=true` when you need a
   decision. At the start of every turn `fetch_inbox(unread_only=true)`; obey any
   HOLD immediately and acknowledge it. Use `renew_file_reservations` for long
   work.
6. On completion: `release_file_reservations` and send a completion message.

## Targeting sessions that already exist

- **Already participating** → discover with `resource://agents/{project_key}`,
  inspect with `whois`, address by `name`. `list_window_identities` /
  `rename_window` disambiguate multiple windows in one repo.
- **Running but not joined** → hand each session the worker join prompt (with an
  explicit `agent_name`) from `references/playbook.md`, then address it by name.
- **Appearing later** → re-read `resource://agents/{project_key}` at the top of
  each observe cycle and onboard newcomers.

## Observe cadence and token discipline

- MCP is pull-based: cadence = effective latency. The orchestrator starts its
  own recurring watch (orchestrator mode Step 7) via the `/loop` skill at the
  interval from the args (default `30s`) — the user does not invoke `/loop`
  manually. Pass `off` to run cycles by hand instead, or a larger interval
  (`2m`, `5m`) for calmer watching.
- Prefer read-only `resource://...` views and `unread_only=true`; condense long
  threads with `summarize_thread`; pull full bodies only when a decision needs
  them; pass large diffs/logs as file paths or git commits, never inline.

## Tool / resource cheat sheet

- Join: `register_agent`, `macro_start_session`
- Talk: `send_message`, `fetch_inbox`, `acknowledge_message`, `reply_message`,
  `search_messages`, `summarize_thread`, `fetch_topic`
- Conflicts: `file_reservation_paths`, `renew_file_reservations`,
  `release_file_reservations`, `force_release_file_reservation`
- Discover/observe (read-only): `resource://agents/{project_key}`,
  `resource://tooling/locks`, `resource://tooling/recent/{seconds}`,
  `resource://thread/{id}`, `resource://views/ack-overdue/{agent}`

## Feedback Check

Before starting, if `feedback/log.md` exists next to this SKILL.md and has 5+
entries, read the last 10. If a pattern is apparent (same keyword in 3+ entries,
or average rating below 3), tell the user (in Japanese):
「過去のフィードバックで類似パターンを検出: [簡潔に]。`/skill-improve --skill agent-swarm` で改善案を分析できます。」
Otherwise proceed silently.

## Retrospective

After an orchestration/observe session ends or the user wraps up:
1. Note any mid-session corrections, conflicts that slipped through, or surprises.
2. Ask the user (in Japanese): 「今回のフィードバック (1-5の評価、気になった点、または何もなければEnter)」. If the rating is < 5, follow up: 「なぜその評価ですか？」 and record the answer verbatim.
3. If feedback is given OR issues occurred, create `feedback/log.md` if missing
   (header `# Feedback Log`, blank line, then
   `<!-- Append new entries at the top. Do not edit previous entries. -->`) and
   prepend an entry: ISO-8601 timestamp, Skill Version, Task, Outcome, Rating,
   Rating reason, Corrections, Issues, User Note.
4. If the user skips and nothing went wrong, end without recording.

## References

- `references/playbook.md` — conflict taxonomy, intervention protocol, token
  discipline, the ready-to-paste worker join prompt, and detailed targeting of
  existing sessions. WHEN TO READ: when assigning tasks, on conflict, or when
  onboarding sessions; not needed for a plain status check.
- `references/scenarios.feature` — BDD spec. WHEN TO READ: only when auditing or
  amending the skill; never during normal execution.
