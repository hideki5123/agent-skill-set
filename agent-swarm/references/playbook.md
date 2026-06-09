# Agent Swarm Playbook

WHEN TO READ: when assigning tasks, when a conflict appears, or when onboarding
sessions into the room. Not needed for a plain status check.

## Conflict / inconsistency taxonomy

What the orchestrator watches for, and the signal that surfaces it:

1. **Path overlap** — two workers hold exclusive reservations on intersecting
   paths. Signal: `resource://tooling/locks` shows overlapping path sets.
2. **Unreserved edit** — a worker reports (or a commit shows) an edit to a path
   it never reserved. Signal: progress message references a file absent from its
   reservations.
3. **Cross-task trespass** — a worker reserves or edits a path owned by another
   task, or a shared-contract file. Signal: reservation path not in that agent's
   ownership map entry.
4. **Contradictory contract change** — the same type, interface, API schema,
   migration, or config key is changed two different ways by two tasks. Signal:
   `resource://tooling/recent/{seconds}` or thread bodies describe divergent
   edits to the same symbol/contract.
5. **Stale / abandoned reservation** — a reservation past its TTL with no recent
   activity from its owner, blocking others. Signal: lock present but owner
   absent from recent activity / ack-overdue.

## Intervention protocol

1. **Freeze**: `send_message(importance="urgent", ack_required=true)` a HOLD to
   each involved worker — "pause all edits on <paths> until further notice."
2. **Diagnose**: read the relevant thread (`resource://thread/{id}` or
   `summarize_thread`) to learn who needs what and why.
3. **Resolve** with the lightest option that works:
   - Re-assign ownership so paths no longer overlap.
   - Serialize: tell worker B to wait until worker A lands and releases.
   - Funnel a shared contract through one designated owner; others consume it
     after it lands.
4. **Release**: send the all-clear; `force_release_file_reservation` any dead or
   superseded reservation.
5. **Record**: keep the ownership map updated so the same clash does not recur.

## Token discipline

- Default to read-only `resource://...` views — they do not grow context the way
  tool results with bodies do.
- `fetch_inbox(unread_only=true)` for deltas; add `include_bodies=true` only for
  messages that require a decision.
- `summarize_thread` instead of re-reading a long thread.
- Pass large diffs, logs, and generated artifacts as **file paths or git commit
  refs**, never inline in message bodies.
- Keep the assigned tool surface small per worker — they only need join, inbox,
  reservation, and send tools.

## Ready-to-paste worker join prompt

Hand this to each worker session (or a not-yet-joined existing session),
replacing `<project_key>`, `<name>`, and `<task>`:

```text
Join the agent-mail coordination room and work as a swarm worker.

- project_key = "<project_key>"  (must match the orchestrator and all peers)
- Join in one call: macro_start_session with human_key="<project_key>",
  program="claude-code", model="<this model id>", agent_name="<name>",
  task_description="<task>", file_reservation_paths=[the paths you will edit],
  file_reservation_ttl_seconds=3600. Keep the registration_token.
- Then fetch_inbox(unread_only=true) and acknowledge the orchestrator's
  instructions.

Rules while working:
- Before editing any file, reserve it: file_reservation_paths(project_key,
  "<name>", paths=[...], exclusive=true, reason="..."). If a reservation is
  blocked or overlaps another agent's, DO NOT edit — message the orchestrator
  and wait for a grant.
- Stay inside your owned paths / worktree. Never change shared-contract files
  (types, API schemas, migrations, config, shared modules) without orchestrator
  approval.
- Post progress to your task thread; set ack_required=true when you need a
  decision. At the start of every turn, fetch_inbox(unread_only=true); if a HOLD
  (urgent) arrives, stop the affected edits immediately, acknowledge it, and wait.
- Use renew_file_reservations for long work. On completion,
  release_file_reservations and send a completion message.

Initialize now, confirm your task and owned paths with me, then start.
```

## Targeting sessions that already exist — details

**A. Already participating (address by name).** From the orchestrator:
> Read `resource://agents/<project_key>`, list the registered agents, `whois`
> each, then send task instructions to `<name>` and `<name>`.

`resource://agents/{project_key}` is the roster of registered names; `whois`
returns the per-agent profile (task, recent commits). For multiple windows in the
same repo, use `list_window_identities` to see which terminal window maps to
which agent and `rename_window` to label them.

**B. Running but not joined (onboard, then address).** Paste the worker join
prompt above into each existing session with an explicit `agent_name` you choose.
That binds the running session to the room; the orchestrator then sees it in the
roster and addresses it by that name. Assigning the name yourself is the key —
the orchestrator sends to that exact name.

**C. Newcomers appearing later.** At the top of each observe cycle, re-read
`resource://agents/<project_key>` and `resource://tooling/recent/600`; when a new
agent appears, add it to the roster and send it a task-confirmation message if it
is unassigned.

## Physical isolation backstop (recommended)

Reservations are advisory. For real protection against concurrent clobbering,
give each task its own git worktree so even a missed reservation cannot cause a
physical overwrite. This pairs the cooperative coordination layer (agent-mail)
with hard filesystem isolation (worktree per task). The skill recommends this but
does not auto-create worktrees.
