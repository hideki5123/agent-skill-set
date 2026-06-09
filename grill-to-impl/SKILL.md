---
name: grill-to-impl
version: 1.0.0
description: >
  Turn a finished grill-me (or any design-finalizing) session into a running
  implementation kickoff. Synthesizes the session's shared understanding into a
  self-contained implementation brief, hardens it with a small agent team and an
  adversarial codex-server review loop (until Codex approves), then launches a
  backgrounded, remote-controllable, autonomous Claude Code session (claude-bg /
  ccb-style: --permission-mode auto --allow-dangerously-skip-permissions --bg
  --remote-control) that runs /prd-council seeded with the brief to produce the
  execution-ready plan and begin implementation. Confirm-before-launch by default.
  Document/prompt generation + session spawning; it does not itself write feature
  code. Use AFTER a grill session when the user wants to hand the agreed design
  off to a fresh autonomous session.
  Trigger patterns (match any variation):
  grill-to-impl / grill to impl / grill→impl / grillの成果を実装へ /
  grillしたセッションから実装 / grillした内容でbriefを作って /
  briefを作ってCodexにレビュー / Codexにレビューさせてからprdーcouncil /
  別セッションでprd-councilを立てる / 新しいセッションでprd-councilを起動 /
  bgセッションで実装を開始 / ccbで実装セッションを起動 /
  ハンドオフして実装開始 / hand off the grill to a new session /
  spawn a background session to start implementation /
  launch prd-council in a new autonomous session / kickoff implementation from a grill /
  /grill-to-impl
---

# grill-to-impl

Bridge a **finished design conversation** to a **running implementation session**.

Pipeline:

```
grilled session  →  synthesize brief  →  team hardening  →  codex-server review loop
                 →  write brief file   →  confirm        →  launch bg prd-council session
```

The terminal action launches a **fresh, autonomous, remote-controllable Claude
Code session** (via the user's `claude-bg` background launcher, ccb-style) that
runs `/prd-council` seeded with the brief. `prd-council` then drafts the PRD,
debates it with Codex, and emits the execution-ready doc set + task list under
`docs/prd/<slug>/` — kicking off implementation.

**This skill generates a prompt/brief and spawns a session. It does NOT write the
feature code itself** — the spawned session does.

## Relationship to neighboring skills

- `grill-me` — runs BEFORE this; produces the shared understanding this consumes.
- `prd-council` — what the spawned session RUNS; it grills + Codex-debates + emits
  `docs/prd/<slug>/`. This skill seeds it so it does not re-grill from scratch.
- `handoff` / `session-handover` — compact a session into a doc; this skill goes
  further: it reviews with Codex and *launches* the next session.
- `to-prd` — publishes a PRD to a tracker; out of scope here (local + spawn only).

Do not duplicate `prd-council`'s heavy debate — the Codex step here is a
**pre-flight hardening** of the brief, not a full PRD debate.

### Feedback Check

If `feedback/log.md` exists and has 5 or more entries, read the last 10. If a
pattern is apparent (same issue in 3+ entries, or average rating below 3):
- Tell the user (in Japanese): 「繰り返しのフィードバックを検出: [簡潔に]。`/skill-improve --skill grill-to-impl` で改善案を分析できます。」
- Continue with normal execution either way.

If `feedback/log.md` does not exist, skip silently.

## Arguments

Parse from the invocation. All optional.

| Argument | Default | Meaning |
|----------|---------|---------|
| `--session <id>` | current session | Source of the grilled content. Default: synthesize from the CURRENT conversation context. Pass an id to pull from a prior session transcript instead. |
| `--target <path>` | current repo root | Project the spawned session runs in (where `docs/prd/<slug>/` lands and code is built). |
| `--slug <slug>` | derived from the brief title | Feature slug for paths / the session label. |
| `--lang <auto\|ja\|en>` | `auto` | Brief + downstream doc language. Commit messages stay English. |
| `--model <opus\|sonnet\|haiku>` | inherit (ccb default) | Model for the spawned bg session. |
| `--rounds <N>` | `3` | Cap on codex-server review rounds before proceeding with the best brief. |
| `--no-codex` | off | Skip the Codex loop; run a Claude-only self-critique and mark the brief degraded. |
| `--no-team` | off | Skip the agent-team hardening pass. |
| `--auto-launch` | off | Skip the confirmation gate and launch immediately after Codex approval. |

## Workflow

### 1. Capture the grilled content

- Default (`--session` unset): synthesize from the CURRENT conversation — extract
  every resolved decision, non-goal, constraint, file/line anchor, risk, and open
  question surfaced during the grill. Do not invent; only capture what was decided.
- `--session <id>` given: load that transcript (use the session search/recap MCP
  tools) and extract the same.
- If the current context shows no finished design discussion AND no `--session`,
  stop and ask the user what to hand off (do not fabricate a brief).

### 2. Synthesize the brief

Read `references/brief-template.md` and write the brief to that structure. The
brief MUST be self-contained — the spawned session has none of this conversation's
context. Mirror the depth of a strong handoff: concrete file:line anchors, a
locked-decisions table, explicit non-goals, branch setup, acceptance criteria,
risks, and a closing **"Seed for prd-council"** block.

### 3. Team hardening (skip if `--no-team`)

Create an agent team to explore the draft brief from different angles:
**Brief Fidelity, Implementability, Idempotence & Safety**. Read
`references/brief-review-team.md` for the teammate prompts and the synthesis
protocol. Fold Critical/Important findings back into the brief before Codex sees it.

### 4. Codex review loop

Read `references/codex-review-loop.md`. Run a codex-server **structured** review of
the brief, looping until Codex approves or `--rounds` is hit. Each round: send the
current brief, get a structured verdict (approved + blocking_issues + suggestions),
and revise the brief from the blocking issues. **The verdict schema must list ALL
properties in `required`** or codex-server returns HTTP 400 on round 1. If Codex is
unavailable or `--no-codex`, degrade to a Claude-only self-critique and mark the
brief `> Codex review: DEGRADED (Claude-only)`.

### 5. Write the brief file

Write the final brief to `<target>/docs/design/<slug>-impl-brief.md` (create dirs).
This file is what the spawned session reads.

### 6. Confirm launch (skip if `--auto-launch`)

Show the user: the brief path, the resolved `--target`/`--slug`/`--model`, and the
EXACT launch command. Get an explicit go-ahead before spawning. Launching an
autonomous, permission-bypassing background agent is consequential — gate it by
default. `--auto-launch` skips this.

### 7. Launch the bg prd-council session

Run `scripts/launch_council_session.sh` (read `references/launch-and-handoff.md`
for the contract). It prefers the user's `claude-bg` (adding ccb flags
`--permission-mode auto --allow-dangerously-skip-permissions`), falls back to a
replicated `claude --bg --remote-control … --permission-mode auto
--allow-dangerously-skip-permissions` invocation, and as a last resort prints the
command for the user to run. The spawned session's initial prompt reads the brief
and invokes `/prd-council --slug <slug> --out docs/prd/<slug>/ --lang <lang>`,
instructing it to treat the brief as already-grilled requirements.

### 8. Report

Tell the user: the brief path, the spawned session's remote-control label
(`<slug>-<sid8>`), and how to attach — the Claude app's Remote Control list, or
`ccon <sid8>` / `claude --resume <sessionId>`. Note that `prd-council`'s residual
questions will surface there for the user to answer remotely.

### Retrospective

After step 8, reflect on the run:
1. Consider: mid-session corrections, rejected briefs, Codex/launcher errors, missing anchors discovered late?
2. Ask the user (in Japanese): 「今回のハンドオフのフィードバック (1-5、気になった点、なければEnter)」
3. If the user gives feedback OR corrections/issues occurred:
   a. Create `feedback/` next to this SKILL.md if missing.
   b. Read/create `feedback/log.md` (`# Feedback Log` header + the append-at-top comment).
   c. Prepend an entry using the log format in `references/skill-improvement-guide.md`
      of the my-skill-factory skill (timestamp, version, task, outcome, corrections, issues, user note).
   d. Confirm in one short Japanese sentence.
4. If the user skips AND nothing went wrong, end without recording.

## Dependencies

- **codex-server** skill (preferred) for the structured review loop — uses the
  user's ChatGPT subscription via `codex login`. Degrade gracefully if absent.
- **claude-bg** on PATH (the user's background launcher) for spawning. Degrade to
  `claude --bg` or to printing the command if absent.
- **prd-council** skill — invoked by the spawned session.
- Optional: session search/recap MCP tools when `--session <id>` is used.

## Behavior Scenarios

```gherkin
Scenario: Hand off the current grill to a new implementation session
  Given the current conversation just finished a grill-me design with locked decisions
  When the user runs /grill-to-impl
  Then it synthesizes a self-contained brief, hardens it with the agent team,
       loops codex-server review until approval, writes the brief file, shows the
       launch command for confirmation, and on go-ahead spawns a claude-bg
       prd-council session, then reports the remote-control label

Scenario: Codex is unavailable
  Given codex login / codex-server is not available
  When the review step runs
  Then it degrades to a Claude-only self-critique, marks the brief DEGRADED,
       and continues without silently skipping review

Scenario: claude-bg is not installed
  Given the launcher cannot find claude-bg or claude --bg fails
  When step 7 runs
  Then it prints the exact launch command for the user to run manually
       instead of failing the whole workflow

Scenario: Fully automatic launch
  Given the user passes --auto-launch
  When Codex approves the brief
  Then the session is spawned immediately without the confirmation gate

Scenario: Source is a prior session
  Given the user passes --session <id>
  When capturing content
  Then it loads that transcript via session tools and synthesizes the brief from it
       rather than the current context

Scenario: Nothing to hand off
  Given the current context has no finished design discussion and no --session
  When the user runs /grill-to-impl
  Then it stops and asks what to hand off instead of fabricating a brief

Scenario: Brief fidelity gap found by the team
  Given the draft brief dropped a non-goal or constraint decided during the grill
  When the team hardening pass runs
  Then the Brief Fidelity teammate flags the omission and it is restored before Codex review
```

## References

- `references/brief-template.md` — structure of the self-contained implementation brief.
- `references/codex-review-loop.md` — codex-server structured review protocol, verdict schema (all-required), round cap, graceful degradation.
- `references/brief-review-team.md` — the Brief Fidelity / Implementability / Idempotence & Safety teammate prompts + synthesis protocol.
- `references/launch-and-handoff.md` — claude-bg / ccb launch semantics, the prd-council seed prompt, fallbacks, attach instructions.
