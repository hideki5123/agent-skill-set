---
name: pm-review
version: 1.1.0
description: >
  Review local git changes from a PMBOK-based product management perspective.
  Analyzes changes against 7 PMBOK knowledge areas: Scope, Risk, Stakeholder,
  Quality, Integration, Schedule, and Resource management. Produces a structured
  report identifying project-level impacts and risks. The PMBOK analyst role
  itself lives in the `pm-review:pm-review` subagent; this skill is a thin
  orchestrator that gathers the change set and project context before delegating.
  Use when the user asks for a PM review, product management review, PMBOK
  analysis, project impact assessment, scope review, risk review, or stakeholder
  impact analysis of local changes. Trigger phrases include "pm review",
  "product management review", "PMBOK review", "project impact", "scope review",
  "risk review", "stakeholder impact", "pm-review", "review from PM perspective",
  "project management review".
---

# PM Review

Orchestrator skill for PMBOK-based review of local git changes. Gathers the
change set + project context, then hands off to the
`@agent-pm-review:pm-review` subagent for the analysis itself.

## Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--staged-only` | `false` | Only review staged changes (`git diff --cached`) |
| `--file` | none | Write report to `pm-review-YYYY-MM-DD-HHmm.md` |

## Workflow

```
1. Collect Changes ──► 2. Read Context ──► 3. Delegate to subagent ──► 4. Surface report
```

### Phase 1: Collect changes

```bash
git diff --cached                  # staged (always)
git diff                           # unstaged (skip if --staged-only)
git status --porcelain | grep '^??' # untracked (skip if --staged-only)
```

If everything is empty: tell the user "No local changes detected. Nothing to
review." and exit.

### Feedback Check

If `feedback/log.md` exists and has 5+ entries, read the last 10. If a pattern
is apparent (same issue in 3+ entries, or avg rating < 3): tell the user
"Recurring feedback detected: [brief]. Consider running `/skill-improve
--skill pm-review`." Continue with normal execution.

### Phase 2: Read project context

For each changed file, read the full file. Also gather project-level docs that
inform PM judgment:

- `README.md`, `CHANGELOG.md`
- Package manifests (`package.json`, `pyproject.toml`, etc.)
- CI/CD configuration files
- Any roadmap or requirements docs the repo carries

### Phase 3: Delegate to the subagent

Hand the change set + the context bundle to `@agent-pm-review:pm-review`. Pass
through the `--staged-only` and `--file` flags so the subagent can write the
report file directly.

The subagent applies the PMBOK lens across the 7 knowledge areas (Scope,
Risk, Stakeholder, Quality, Integration, Schedule, Resource) and returns a
structured report.

### Phase 4: Surface the report

Print the subagent's report inline. If `--file` was passed and the subagent
already wrote the file, confirm the path. Otherwise, write the report to
`pm-review-YYYY-MM-DD-HHmm.md`.

## Retrospective

After completing the workflow, reflect on the entire execution session:

1. Were there mid-session corrections, rejected outputs, plan changes, or
   errors?
2. Ask the user: "Quick feedback on this run? (1-5 rating, note any issues,
   or press enter to skip)"
3. If the user provides feedback OR if corrections/issues occurred:
   a. Create `feedback/` if it does not exist.
   b. Read or create `feedback/log.md` (header: `# Feedback Log`).
   c. Prepend a new entry using the format in
      `my-skill-factory/references/skill-improvement-guide.md`. Fill
      timestamp, skill version (1.1.0), task description, outcome,
      corrections, issues, user note.
4. If the user skips AND no corrections / issues occurred, end without
   recording.

## Behavior Scenarios

```gherkin
Scenario: PMBOK review of local changes
  Given the user has local changes (staged, unstaged, or untracked)
  When /pm-review is invoked
  Then the skill collects the change set and project context, delegates to
       @agent-pm-review:pm-review, and surfaces the structured report

Scenario: Staged-only PM review
  Given the user has staged changes ready to commit
  When /pm-review --staged-only is invoked
  Then only staged changes are gathered and analyzed by the subagent

Scenario: Write report to file
  Given the user wants a persistent record
  When /pm-review --file is invoked
  Then the subagent writes the report to pm-review-YYYY-MM-DD-HHmm.md
       and the skill confirms the path to the user

Scenario: No local changes
  Given the working tree is clean
  When /pm-review is invoked
  Then the user is told "No local changes detected" and the skill exits
       without invoking the subagent
```

## References

- `references/pmbok-review-guide.md` — Complete PMBOK review framework (read
  by the subagent, available here for direct human reference).
- `references/report-template.md` — Exact markdown format for the report.
