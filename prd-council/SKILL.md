---
name: prd-council
version: 1.0.0
description: >
  Turn a feature idea into an execution-ready document set through an
  adversarial PRD "council": grill the user for requirements, draft a PRD,
  then debate it with OpenAI Codex round-by-round until BOTH sides approve,
  and finally emit a Technical PRD (one overall summary + one per UseCase)
  plus a task list with agent assignments, dependencies, and acceptance
  criteria — designed so a PdM-role agent could later distribute the work to
  specialist agents. Document-generation only (no agent execution). Writes
  local files under docs/prd/<slug>/; never publishes to external trackers.
  Uses codex-server (the user's ChatGPT subscription) for the debate loop.
  Use when the user wants a PRD reviewed/approved by Codex, a "PRD council",
  a Technical PRD for task distribution, or a task breakdown from a PRD.
  Trigger patterns (match any variation):
  prd-council / prd council / PRD council /
  PRD + {Codex, GPT, ChatGPT} + {議論, 相互承認, レビュー, 承認, debate, review, approve} /
  CodexとPRDを議論 / CodexとPRDを相互承認 / PRDをCodexと詰める /
  technical prd / technical product requirement document /
  全体サマリー + UseCase + PRD / ユースケース別PRD /
  タスク振り分けドキュメント / PdM agent task distribution doc /
  PRDからタスクリスト / break a PRD into tasks / task breakdown from PRD /
  /prd-council
---

# PRD Council

Produce an **execution-ready document set** from a feature idea, hardened by an
adversarial debate with OpenAI Codex. This skill is **document-generation only** —
it never runs the specialist agents; it produces the artifacts that *would let* a
PdM-role agent distribute and drive the work later.

Deliverables (all local files under `docs/prd/<slug>/`):

| File | What it is |
|------|------------|
| `prd.md` | The Codex-approved PRD (problem / solution / user stories / decisions). |
| `debate-log.md` | Full round-by-round Claude↔Codex transcript + final verdicts. |
| `technical-prd-summary.md` | Overall Technical PRD: architecture, agent roster, cross-cutting concerns, UseCase index, dependency graph. |
| `technical-prd-<usecase>.md` | One per UseCase: scope, assigned agents + responsibilities, interfaces, test seams, done criteria. |
| `tasks.md` | Task list grouped by UseCase; each task tagged with assigned agent role, dependencies, and acceptance criteria. |

This skill **does not publish** to Jira / Notion / Confluence / GitHub. Output is
local files only.

## Dependencies

- **codex-server** skill (the debate engine) — runs Codex via the user's ChatGPT
  subscription (`codex login`). prd-council shells out to
  `~/.codex-server/lib/chat.ts`.
- If Codex is unavailable (no `~/.codex/auth.json`, or `codex` not installed, or
  `--no-codex`), **degrade gracefully**: run a Claude-only self-critique council
  instead and clearly mark `debate-log.md` as degraded. See
  `references/codex-loop.md` → "Graceful degradation". Never silently skip the loop.

## Arguments

Parse from the invocation. All optional.

| Argument | Default | Meaning |
|----------|---------|---------|
| `--out <dir>` | `docs/prd/<slug>/` | Output directory (relative to the target project cwd). |
| `--slug <slug>` | derived from PRD title | Feature slug used in paths/filenames. |
| `--agents <csv>` | auto (see roster) | Override the role roster, e.g. `frontend,backend,qa,infra`. |
| `--council <default\|heavy>` | `default` | `default` = structured Codex approval handshake; `heavy` = multi-lens panel (Codex + Claude self-critique across lenses). See `references/codex-loop.md`. |
| `--rounds <N>` | `4` | Hard cap on debate rounds before escalating to the user. |
| `--model <M>` | from `~/.codex/config.toml` | Codex model override. |
| `--no-codex` | off | Skip Codex; run degraded Claude-only council. |
| `--lang <auto\|ja\|en\|…>` | `auto` | Document body language. `auto` = the session/invocation language. Commit messages are ALWAYS English regardless. |
| `--grill <auto\|full\|skip>` | `auto` | Phase-1 depth. `auto` = assess existing context and grill only unresolved branches (confirm-only if already grilled). `full` = force a complete re-grill. `skip` = trust context as-is (still shows the summary for one confirm). |

## Feedback Check

Before any work: if `feedback/log.md` exists next to this SKILL.md and has ≥5
entries, read the last 10. If a pattern is apparent (same keyword in 3+ entries,
or average rating below 3), tell the user (in Japanese):
「過去のフィードバックで類似パターンを検出: [簡潔に]。`/skill-improve --skill prd-council` で改善案を分析できます。」
Otherwise proceed silently. If the file does not exist, skip silently.

## Workflow

The work product is hardened by an adversarial council, so order matters: lock
requirements first (grill), draft, then debate to mutual approval, then derive
the technical docs and tasks from the approved PRD — never the other way around.

### Phase 0 — Setup & recon

1. Resolve the target project cwd. Detect the primary stack/language (build files,
   manifests) — this drives stack-aware agent binding in Phase 4.
2. Resolve the doc language (`--lang auto` → session language).
3. Check Codex availability: `test -f ~/.codex/auth.json` and `codex` on PATH. If
   missing and not `--no-codex`, tell the user how to enable it (run `codex login`)
   and offer to proceed degraded. Read `references/codex-loop.md` only if you need
   the setup/degradation detail.
4. Determine `<slug>` and create the output dir.

### Phase 1 — Grill (always a checkpoint; depth adapts to existing context)

There is **always** a user-facing requirements checkpoint before drafting — this
skill never silently synthesizes like to-prd. But its *depth adapts to what's
already known*, so a user who was just grilled is not re-interrogated.

Read `references/grill-protocol.md` and run the **shared-understanding assessment
first**: scan what the available context already resolves (this conversation, any
prior `grill-me`/`grill-with-docs` output, a passed-in draft/ticket, the codebase),
then act on coverage:

- **Already grilled / context-rich** (decision tree largely resolved): do NOT
  re-walk the tree. Present a consolidated requirements summary and ask for a
  single confirm-or-correct pass; grill only the genuinely-unresolved branches.
- **Thin context**: run the full one-question-at-a-time grill (recommend an answer
  each, explore the codebase for what you can answer yourself).
- `--grill full` forces a complete re-grill; `--grill skip` trusts the context
  as-is but still shows the summary for one confirm. `auto` (default) decides by
  coverage.

Either way, stop only when you and the user share an understanding of problem,
solution, scope, UseCases, and constraints.

### Phase 2 — Draft the PRD

Synthesize the grilled requirements + codebase understanding into `prd.md` using
the PRD template in `references/templates.md` (PRD section). Use the project's
domain vocabulary; respect ADRs in the area you touch. Identify the **UseCases**
explicitly here — they become the per-UseCase Technical PRDs in Phase 4.

### Phase 3 — Codex council loop (to mutual approval)

Read `references/codex-loop.md` and run the loop. In short (`default` mode):

1. Send the current PRD to Codex via `chat.ts new … --schema <verdict-schema>`,
   asking for a **structured verdict** `{verdict: approve|revise, blocking_issues[],
   suggestions[], rationale}`.
2. Resolve every blocking issue, revise `prd.md`, and re-send with a changelog via
   `chat.ts continue --last …` (same thread).
3. **Mutual approval** = Codex returns `approve` AND you have no unresolved
   objection to Codex's remaining points. Then stop.
4. If `--rounds` is hit without convergence, **stop and escalate**: surface the
   open disagreements to the user for a decision. Do not loop forever.
5. Append every round (prompt, verdict, changelog) to `debate-log.md`.

`--council heavy` runs a multi-lens panel each round (Codex + Claude self-critique
across correctness / feasibility / security / testability / UX); see the reference.

### Phase 4 — Technical PRD (summary + per-UseCase)

Acting as the **PdM role**, derive the technical docs from the approved PRD:

1. **Resolve the agent roster.** Read `references/role-taxonomy.md`. Start from the
   generic capability taxonomy, select only the roles the PRD actually needs, then
   opportunistically bind each role to an installed, stack-appropriate subagent if
   one exists (else keep the generic role). `--agents` overrides selection.
2. Write `technical-prd-summary.md` (overall) using the Technical PRD summary
   template: architecture, the resolved roster + each agent's responsibilities and
   I/O interfaces, cross-cutting concerns, a UseCase index, and the cross-UseCase
   dependency graph (Mermaid — never ASCII art).
3. Write one `technical-prd-<usecase>.md` per UseCase using the per-UseCase
   template: scope, assigned agent(s), interfaces, test seams, and done criteria.

### Phase 5 — Task list

From the Technical PRDs, write `tasks.md` using the tasks template: grouped by
UseCase, every task tagged with its assigned agent role, dependencies (by task id),
and acceptance criteria, linking back to the relevant Technical PRD section. This
is the artifact a PdM agent would consume to distribute work.

### Phase 6 — Finalize

Write all files under the output dir. Print a clickable index of what was created
and a one-line summary (rounds to approval, UseCase count, task count). Do **not**
publish anywhere. If the repo is git-tracked and the user asks to commit, use an
English commit message (per project convention).

## Roster resolution (summary)

Layered, portable-first (full rules in `references/role-taxonomy.md`):

1. **Stable layer** — generic capability roles: `PdM`, `Frontend`, `Backend`,
   `Data`, `QA`, `DevOps`, `Security`, `Docs`. Select only what the PRD needs.
2. **Opportunistic binding** — if the detected stack has a matching installed
   subagent (e.g. .NET backend → `dotnet-senior`, test gaps → `orch-qa`), bind the
   role to it; otherwise keep the generic role label. Never hard-depend on a
   specific subagent being installed.
3. **Override** — `--agents` wins.

## Retrospective

After Phase 6, reflect:

1. Were there mid-session corrections, Codex/auth errors, non-convergence
   escalations, or surprises?
2. Ask the user (in Japanese): 「今回のPRD councilのフィードバック (1-5の評価、気になった点、または何もなければEnter)」
3. If the user gives feedback OR corrections/issues occurred:
   - Create `feedback/log.md` next to this SKILL.md if missing (header
     `# Feedback Log` + blank line + `<!-- Append new entries at the top. Do not edit previous entries. -->`).
   - Prepend an entry:
     ```markdown
     ## <ISO-8601 timestamp>
     - **Skill Version**: 1.0.0
     - **Task**: <feature/slug, mode, rounds-to-approval>
     - **Outcome**: success | partial-success | failure | error
     - **Rating**: <N>/5 (or "—")
     - **Corrections**: <mid-session corrections, or "none">
     - **Issues**: <specific problems, or "none">
     - **User Note**: <verbatim feedback, or "—">
     ---
     ```
   - For any rating < 5, follow up by asking WHY before writing the entry.
4. If the user skips AND nothing went wrong, end without recording.

## Behavior Scenarios

BDD spec lives in `references/scenarios.feature`. Read it only when auditing or
amending this skill (e.g. via `/skill-improve`) — **not needed for normal
execution**.

## References

Read on-demand only — none are auto-loaded. Each is loaded as its phase begins,
keeping this body light.

- `references/grill-protocol.md` — the Phase 1 interview protocol. Read at the start of Phase 1.
- `references/codex-loop.md` — Codex debate mechanics: verdict schema, `default` vs `heavy`, round cap/escalation, debate-log format, graceful degradation. Read at Phase 3 (or Phase 0 if Codex setup is in question).
- `references/templates.md` — PRD + Technical PRD (summary & per-UseCase) + tasks.md templates. Read at Phases 2, 4, 5.
- `references/role-taxonomy.md` — generic roles + stack-aware subagent binding rules. Read at Phase 4.
- `references/scenarios.feature` — Gherkin BDD spec. **Only for audit / skill-improve. Never during normal execution.**
