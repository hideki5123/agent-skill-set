---
name: review-local
description: >
  Review local git changes from 8 expert perspectives using multi-agent team
  orchestration. Produces a consolidated report with Critical/Important/Nice-to-have
  severity levels. Lightweight pre-commit or pre-push quality gate — no PR or
  branch push required. Use when the user asks to review local changes, check
  changes before committing, get a team review of working tree changes, or run
  a pre-commit review. Trigger phrases include "review local", "review my changes",
  "review local changes", "pre-commit review", "review before commit",
  "review before push", "team review my changes", "check my changes",
  "review working tree", "local code review", "review diff", "review my diff".
---

# Local Review

Review current local git changes from multiple expert perspectives using team orchestration.

## Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--staged-only` | `false` | Only review staged changes (`git diff --cached`) |
| `--file` | none | Write report to `review-local-YYYY-MM-DD-HHmm.md` |

## Workflow

```
1. Collect Changes ──► 2. Read Context ──► 3. Team Review ──► 4. Synthesize ──► 5. Report
```

### Phase 1: Collect Changes

Gather local changes:

```bash
# Staged changes (always collected)
git diff --cached

# Unstaged changes (skip if --staged-only)
git diff

# Untracked files (skip if --staged-only)
git status --porcelain | grep '^??'
```

If all produce empty results, inform the user: "No local changes detected. Nothing to review." and exit.

For untracked files, read the full file content as a pseudo-diff.

If more than 30 files changed, warn the user and ask whether to proceed or narrow scope.

### Phase 2: Read Context

For each changed file, read the full file to give reviewers surrounding context. Skip deleted files and binary files.

### Phase 3: Team Review

Create an agent team to explore this from different angles: one teammate on software architecture, one on security, one on infrastructure design, one on QA/QC, one on TDD, one on BDD, one on idempotence, and one playing devil's advocate.

Each teammate receives:
1. The combined diff from Phase 1
2. The file context from Phase 2
3. Their perspective-specific prompt — read from `references/perspectives/<perspective>.md`

Read `references/perspectives/` for each teammate's detailed review prompt, questions, output format, and severity guidance.

### Phase 4: Synthesize Findings

After all teammates complete their reviews, synthesize findings. Read `references/synthesis-protocol.md` for the full protocol:

1. Collect all findings from each teammate
2. Categorize by severity: Critical, Important, Nice-to-have
3. Deduplicate overlapping concerns
4. Prioritize by risk and effort

### Phase 5: Present Report

Present the consolidated report inline. If `--file` is set, write to `review-local-YYYY-MM-DD-HHmm.md` in the current directory.

Read `references/report-template.md` for the exact report format.

## Behavior Scenarios

```gherkin
Scenario: Full team review of local changes
  Given the user has local changes (staged, unstaged, or untracked)
  When /review-local is invoked
  Then a team is created with all 8 perspectives, each reviews the diff,
  findings are synthesized into a consolidated severity report inline

Scenario: Staged-only review
  Given the user has staged changes ready to commit
  When /review-local --staged-only is invoked
  Then only the staged diff is reviewed by the team

Scenario: Write report to file
  Given the user wants a persistent record
  When /review-local --file is invoked
  Then the report is written to review-local-YYYY-MM-DD-HHmm.md
  and the file path is confirmed to the user

Scenario: No local changes
  Given the working tree is clean
  When /review-local is invoked
  Then the user is told "No local changes detected" and the skill exits

Scenario: Large changeset warning
  Given more than 30 files are changed
  When /review-local is invoked
  Then the user is warned and asked whether to proceed or narrow scope
```

## References

- `references/perspectives/` — One file per review perspective with prompts, questions, output format, and severity guidance
- `references/synthesis-protocol.md` — How to merge, deduplicate, and categorize findings
- `references/report-template.md` — Exact markdown format for the consolidated report
