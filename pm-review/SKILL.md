---
name: pm-review
version: 1.0.0
description: >
  Review local git changes from a PMBOK-based product management perspective.
  Analyzes changes against 7 PMBOK knowledge areas: Scope, Risk, Stakeholder,
  Quality, Integration, Schedule, and Resource management. Produces a structured
  report identifying project-level impacts and risks. Standalone skill usable
  independently. Use when the user asks for a PM review, product management
  review, PMBOK analysis, project impact assessment, scope review, risk review,
  or stakeholder impact analysis of local changes. Trigger phrases include
  "pm review", "product management review", "PMBOK review", "project impact",
  "scope review", "risk review", "stakeholder impact", "pm-review",
  "review from PM perspective", "project management review".
---

# PM Review

Review current local git changes from a PMBOK-based product management perspective.

## Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--staged-only` | `false` | Only review staged changes (`git diff --cached`) |
| `--file` | none | Write report to `pm-review-YYYY-MM-DD-HHmm.md` |

## Workflow

```
1. Collect Changes ──► 2. Read Context ──► 3. PMBOK Analysis ──► 4. Report
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

### Feedback Check

If `feedback/log.md` exists and has 5 or more entries, read the last 10 entries.
If a pattern is apparent (same issue in 3+ entries, or average rating below 3):
- Tell the user: "Recurring feedback detected: [brief pattern]. Consider running `/skill-improve --skill pm-review`."
- Continue with normal execution.

### Phase 2: Read Context

For each changed file, read the full file for context. Also look for project-level documents that provide broader context:
- README.md, CHANGELOG.md
- Package manifests (package.json, pyproject.toml, etc.)
- CI/CD configuration files
- Any project roadmap or requirements documents

### Phase 3: PMBOK Analysis

Review the changes against each PMBOK knowledge area. Read `references/pmbok-review-guide.md` for the complete review framework including questions, analysis guidance, and output format for each knowledge area.

The 7 knowledge areas to assess:

1. **Scope Management** — Does this change align with project scope? Feature creep risk?
2. **Risk Management** — What risks does this change introduce or mitigate?
3. **Stakeholder Impact** — Who is affected? Is communication needed?
4. **Quality Management** — Does it meet quality standards and acceptance criteria?
5. **Integration Management** — How does it integrate with other components/systems?
6. **Schedule Impact** — Does this change affect timelines or dependencies?
7. **Resource Management** — Team capacity, skill requirements, tooling needs?

### Phase 4: Present Report

Present the structured report inline. If `--file` is set, write to `pm-review-YYYY-MM-DD-HHmm.md`.

Read `references/report-template.md` for the exact report format.

### Retrospective

After completing the workflow, reflect on the entire execution session:

1. Consider: Were there mid-session corrections? Rejected outputs? Plan changes? Errors?
2. Ask the user: "Quick feedback on this run? (1-5 rating, note any issues, or press enter to skip)"
3. If the user provides feedback OR if corrections/issues occurred during this session:
   a. Create `feedback/` directory if it does not exist
   b. Read `feedback/log.md` (create with `# Feedback Log` header if it does not exist)
   c. Prepend a new entry after the header using the log format from `my-skill-factory/references/skill-improvement-guide.md`
   d. Fill in: current timestamp, skill version from frontmatter, task description, outcome assessment,
      corrections that occurred during the session, issues encountered, user's note
4. If the user skips AND no corrections or issues occurred, end without recording.

## Behavior Scenarios

```gherkin
Scenario: PMBOK review of local changes
  Given the user has local changes (staged, unstaged, or untracked)
  When /pm-review is invoked
  Then changes are analyzed against all 7 PMBOK knowledge areas
  and a structured report with findings and recommendations is presented

Scenario: Staged-only PM review
  Given the user has staged changes ready to commit
  When /pm-review --staged-only is invoked
  Then only staged changes are analyzed

Scenario: Write report to file
  Given the user wants a persistent record
  When /pm-review --file is invoked
  Then the report is written to pm-review-YYYY-MM-DD-HHmm.md
  and the file path is confirmed to the user

Scenario: No local changes
  Given the working tree is clean
  When /pm-review is invoked
  Then the user is told "No local changes detected" and the skill exits
```

## References

- `references/pmbok-review-guide.md` — Complete PMBOK review framework with questions, analysis guidance, and output format per knowledge area
- `references/report-template.md` — Exact markdown format for the PM review report
