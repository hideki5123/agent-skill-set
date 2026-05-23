---
name: review-local
version: 2.0.0
description: >
  Review local git changes from 8 expert perspectives by spawning the
  matching reviewer subagents in parallel. Produces a consolidated report
  with Critical/Important/Nice-to-have severity. Lightweight pre-commit or
  pre-push quality gate — no PR or branch push required. Use when the user
  asks to review local changes, check changes before committing, get a team
  review of working tree changes, or run a pre-commit review. Trigger
  phrases include "review local", "review my changes", "review local
  changes", "pre-commit review", "review before commit", "review before
  push", "team review my changes", "check my changes", "review working
  tree", "local code review", "review diff", "review my diff".
---

# Local Review (orchestrator)

Reviewer judgment lives in eight subagents under
`review-local:perspectives:*`. This skill orchestrates them in parallel,
synthesizes findings into a severity-classified report, and (optionally)
writes the report to a timestamped file.

## Reviewer subagents (spawned in parallel)

| Subagent | Lens |
|---|---|
| `review-local:perspectives:architecture` | Software architecture, SOLID, modularity |
| `review-local:perspectives:security` | Input validation, injection, authz, secrets, crypto |
| `review-local:perspectives:infrastructure` | Deployment, observability, resilience, scale |
| `review-local:perspectives:qa` | Testability, coverage, edge cases, regression risk |
| `review-local:perspectives:tdd` | Red/green discipline, scope bound by tests |
| `review-local:perspectives:bdd` | User-observable behaviour, ubiquitous language |
| `review-local:perspectives:idempotence` | Retry safety, dedup, delivery semantics |
| `review-local:perspectives:devils-advocate` | The case against merging |

Each subagent is a focused reviewer that reads the diff + file context
and returns a structured review block. The reviewers do **not** spawn
further subagents — Claude Code does not allow nested subagent spawn.

## Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--staged-only` | `false` | Only review staged changes (`git diff --cached`) |
| `--file` | none | Write report to `review-local-YYYY-MM-DD-HHmm.md` |
| `--lens` | `all` | Comma-separated subset of perspective names (e.g., `architecture,security,qa`). Default: spawn all 8 |
| `--max-files` | `30` | Soft limit on changed-file count. Over this, the skill samples (highest-churn files first) rather than asking the user. Set to `0` to disable the cap |

## Workflow

```
1. Collect Changes ──► 2. Read Context ──► 3. Parallel reviewer subagents ──► 4. Synthesize ──► 5. Report
```

### Phase 1: Collect changes

```bash
git diff --cached                   # staged (always)
git diff                            # unstaged (skip if --staged-only)
git status --porcelain | grep '^??' # untracked (skip if --staged-only)
```

If all are empty: "No local changes detected. Nothing to review." → exit.

For untracked files, read full file content as a pseudo-diff.

### Phase 2: Read context

For each changed file, `Read` the full file so each reviewer has surrounding
context (not just hunk lines). Skip deleted files and binary files.

**Large changesets (>--max-files):** sample by churn — keep the top
`--max-files` files by `git diff --stat | sort -k3 -nr`. Note the
sampled vs total file count in the final report. Do **not** ask the user
whether to proceed — the soft cap is configured by `--max-files`, and the
default `30` already covers most local-changes flows.

### Phase 3: Parallel reviewer subagents

For each lens in `--lens` (default: all eight), spawn the matching
subagent via the Agent tool with `subagent_type` set to the scoped
identifier. Pass each:

- The combined diff from Phase 1.
- The file context from Phase 2 (path → content map).
- Note of any sampled-out files.

Run them in parallel (multiple Agent tool calls in a single message).

Each reviewer returns a structured review block matching its lens's
output format. The reviewers are read-only — they do not edit files.

### Phase 4: Synthesize

Read `references/synthesis-protocol.md` for the full protocol. Briefly:

1. Collect each subagent's block.
2. Categorize each finding by severity: Critical / Important / Nice-to-have.
3. Deduplicate overlapping findings — when two lenses point at the same
   `file:line`, merge into one row that lists both lenses and keeps the
   higher severity.
4. Order Critical → Important → Nice-to-have within each section.

### Phase 5: Present the report

Read `references/report-template.md` for the exact format. Print the
report inline. If `--file` is set, also write
`review-local-YYYY-MM-DD-HHmm.md` in the current directory and confirm
the path.

## Behavior Scenarios

```gherkin
Scenario: Full eight-lens review of local changes
  Given the user has local changes (staged, unstaged, or untracked)
  When /review-local is invoked
  Then the skill spawns 8 reviewer subagents in parallel
       (review-local:perspectives:architecture, security, infrastructure,
       qa, tdd, bdd, idempotence, devils-advocate)
  And synthesizes their structured findings into a single severity report

Scenario: Staged-only review
  Given the user has staged changes ready to commit
  When /review-local --staged-only is invoked
  Then only the staged diff is sent to the reviewer subagents

Scenario: Subset of lenses
  Given the user only wants security + qa coverage
  When /review-local --lens=security,qa is invoked
  Then only those two subagents are spawned, and the report only contains
       findings from those lenses

Scenario: Write report to file
  Given the user wants a persistent record
  When /review-local --file is invoked
  Then the report is written to review-local-YYYY-MM-DD-HHmm.md
       and the path is confirmed

Scenario: No local changes
  Given the working tree is clean
  When /review-local is invoked
  Then the user is told "No local changes detected" and the skill exits

Scenario: Large changeset
  Given more than 30 files are changed
  When /review-local is invoked
  Then the skill samples the top 30 files by churn, notes the sampling
       in the report header, and does not pause for user confirmation
```

## Why this is an orchestrator (not a single reviewer subagent)

Each of the eight lenses has a distinct system prompt and output format.
The cleanest mapping is one subagent per lens. Spawning them must happen
from a context that *can* spawn subagents — i.e., the main session, via
this skill — because subagents cannot spawn further subagents in Claude
Code. So:

- The judgment per lens → eight subagents.
- The parallel-spawn + synthesis + report → this skill.

## References

- `references/perspectives/` — Individual perspective definitions. These
  also serve as the source for each reviewer subagent's system prompt
  (the agent files in `agents/perspectives/` carry the same content
  packaged as subagent definitions).
- `references/synthesis-protocol.md` — How to merge, deduplicate, and
  categorize findings across lenses.
- `references/report-template.md` — Exact markdown format for the
  consolidated report.
