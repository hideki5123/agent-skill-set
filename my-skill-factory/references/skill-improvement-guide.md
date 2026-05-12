# Skill Improvement Guide

The Observe/Inspect/Amend/Evaluate (OIAE) cycle for making skills self-improving. Read this reference when creating a skill with feedback loop support or when running the "Improve an Existing Skill" workflow.

## Overview

Skills are living system components, not static prompt files. The OIAE cycle allows skills to improve based on real execution data:

1. **Observe** — After each execution, record what happened (Retrospective step)
2. **Inspect** — At the start of each execution, check for recurring patterns (Feedback Check)
3. **Amend** — The factory proposes targeted changes based on accumulated evidence
4. **Evaluate** — Verify amendments actually improved outcomes; rollback if not

Skills observe and record. The factory analyzes and amends. Skills never self-modify during execution.

## Feedback Directory Structure

```
skill-name/
└── feedback/              (git-tracked, NOT copied to marketplace)
    ├── log.md             (append-only observation log)
    └── amendments.md      (amendment history with outcomes)
```

- `feedback/` is created at runtime on the first observation
- It is git-tracked (institutional memory), but excluded from marketplace copies by `install_skill.py`
- `log.md` is append-only — never edit existing entries
- `amendments.md` is maintained by the factory's "Improve" workflow

## Log Format (`feedback/log.md`)

New entries go at the top (newest first). Each entry is a self-contained record.

```markdown
# Feedback Log

<!-- Append new entries at the top. Do not edit previous entries. -->

## <ISO-8601 timestamp>
- **Skill Version**: <version from frontmatter>
- **Task**: <1-line description of what the user asked for>
- **Outcome**: success | partial-success | failure | error
- **Rating**: <N>/5 (or "—" if not provided)
- **Rating reason**: <user's verbatim response to "why this rating?", or "—" if rating was 5 or not provided>
- **Corrections**: <mid-session corrections/pivots the user made, or "none">
- **Issues**: <specific problems encountered, or "none">
- **User Note**: <user's verbatim feedback, or "—">
---
```

Field definitions:

| Field | Description |
|-------|-------------|
| **Skill Version** | From SKILL.md frontmatter `version` field |
| **Task** | What the user originally asked for (1 line) |
| **Outcome** | `success` (completed as expected), `partial-success` (completed with workarounds), `failure` (could not complete), `error` (crashed/broke) |
| **Rating** | User's optional 1-5 rating |
| **Rating reason** | If `Rating` is 1-4, the user's verbatim answer to the "why?" follow-up. ALWAYS ask the follow-up when rating < 5 — the "why" is where the actionable improvement signal lives. Set to "—" if rating was 5 or not provided. |
| **Corrections** | Mid-session course corrections — rejected outputs, approach changes, user redirections. This is the strongest improvement signal. |
| **Issues** | Technical problems: errors, tool failures, missing data, unexpected behavior |
| **User Note** | User's verbatim feedback, quoted exactly |

## Amendment Format (`feedback/amendments.md`)

Created by the factory's "Improve" workflow. Tracks what was changed and why.

```markdown
# Amendment History

## AMD-<NNN> — <YYYY-MM-DD>
- **Pattern**: <recurring issue description>
- **Evidence**: <dates of log entries that motivated this change>
- **Change**: <what was modified — human-readable summary>
- **Files Modified**: <file paths and sections changed>
- **Version Bump**: <old version> → <new version>
- **Git Commit**: <short hash>
- **Status**: applied — monitoring
---
```

Status values:
- `applied — monitoring` — just applied, waiting for post-amendment data
- `effective` — post-amendment feedback confirms improvement
- `ineffective` — issue persists after amendment
- `rolled-back` — reverted via `git revert`

## Retrospective Step Template

Embed this at the end of generated skill workflows (after the last phase):

```markdown
### Retrospective

After completing the workflow, reflect on the entire execution session:

1. Consider: Were there mid-session corrections? Rejected outputs? Plan changes? Errors?
2. Ask the user: "Quick feedback on this run? (1-5 rating, note any issues, or press enter to skip)"
   **If the user provides a rating < 5, ALWAYS follow up**: "Why this rating? (concrete details help me improve)" — record the response verbatim as `Rating reason`. Never skip this follow-up, even in auto-mode; the "why" is where the actionable signal lives.
3. If the user provides feedback OR if corrections/issues occurred during this session:
   a. Create `feedback/` directory if it does not exist
   b. Read `feedback/log.md` (create with `# Feedback Log` header if it does not exist)
   c. Prepend a new entry after the header using the log format from `references/skill-improvement-guide.md`
   d. Fill in: current timestamp, skill version from frontmatter, task description, outcome assessment, rating + rating reason (if rating < 5),
      corrections that occurred during the session, issues encountered, user's note
4. If the user skips AND no corrections or issues occurred, end without recording.
```

## Feedback Check Template

Embed this near the top of generated skill workflows (before the main work begins):

```markdown
### Feedback Check

If `feedback/log.md` exists and has 5 or more entries, read the last 10 entries.
If a pattern is apparent (same issue in 3+ entries, or average rating below 3):
- Tell the user: "Recurring feedback detected: [brief pattern]. Consider running `/my-skill-factory improve <skill-name>`."
- Continue with normal execution.
```

## Pattern Detection Heuristics

When analyzing `feedback/log.md` during the "Improve" workflow:

| Signal | Threshold | What it means |
|--------|-----------|---------------|
| Same issue keyword in Corrections/Issues | 3+ entries | Recurring problem — skill instructions need fixing |
| Average rating | Below 3.0 over last 10 | General underperformance |
| Declining ratings | Trend downward over time | Skill degrading (environment shift) |
| Outcome distribution | >30% partial-success or failure | Workflow has structural issues |
| Version-correlated | Issues cluster after a version bump | Recent amendment may have introduced problems |

## Evaluation Criteria

After an amendment is applied (`applied — monitoring`), evaluate on the next "Improve" run:

1. Read log entries dated after the amendment
2. Check if the specific issue pattern recurred
3. Check if average rating improved
4. Update amendment status:
   - **effective** — issue did not recur AND ratings stable or improved (over 3+ post-amendment entries)
   - **ineffective** — issue recurred OR ratings declined
   - **insufficient data** — fewer than 3 post-amendment entries; keep monitoring

For ineffective amendments:
- Suggest `git revert <commit>` to roll back
- Update status to `rolled-back` if reverted
- Consider a different approach in the next improvement cycle

## When NOT to Use the Improvement Loop

Skip the feedback loop (opt-in level: None) for:
- **One-shot skills** — run once and work forever (e.g., session-handover, install hooks)
- **Simple utility skills** — deterministic, no workflow, always produces the same kind of output
- **Skills with fewer than 5 expected uses** — not enough data to detect patterns
- **Wrapper skills** — thin CLI wrappers that just format commands (e.g., jira-cli, slack-cli)
