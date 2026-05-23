---
name: pr-review
version: 1.1.0
description: >
  Review a teammate's pull request. The reviewer role (multi-lens analysis,
  severity calibration, suggestion writing) lives in the `pr-review:pr-review`
  subagent; this skill is the orchestrator — it resolves the PR, fetches diff
  and changed files, delegates analysis to the subagent, stages the resulting
  comments for user approval, then submits a batch review via the GitHub API.
  NOT for self-review of your own PR (use `self-pr-review` instead).
  Trigger phrases include "review PR #123", "code review PR", "peer review",
  "check this PR", "give PR feedback", "review pull request", "review someone's PR".
---

# PR Review

Orchestrator skill for reviewing someone else's PR. The reviewer judgment
itself lives in the `@agent-pr-review:pr-review` subagent. This skill handles
PR lookup, diff fetching, staging UI, user interaction, and GitHub submission.

This skill reviews **someone else's PR** — for self-review of your own PR,
use `self-pr-review` instead.

## Arguments

- `<pr>` — PR number (`123`, `#123`) or full URL (required).
- `--lens` — Comma-separated list of review lenses. Options: `bugs`,
  `security`, `performance`, `style`, `complexity`, `testing`, `docs`.
  Default: all.
- `--event` — Review event type: `COMMENT` (default), `APPROVE`,
  `REQUEST_CHANGES`.
- `--severity` — Minimum severity to include: `critical`, `high`, `medium`,
  `low`, `all`. Default: `all`.
- `--max-comments` — Maximum inline comments to stage. Default: `30`.

## Workflow Overview

```
1. Resolve PR ──► Verify OPEN, fetch metadata
2. Fetch Diff ──► gh pr diff + read changed files
3. Delegate ────► @agent-pr-review:pr-review analyses with active lenses
4. Stage ───────► Display comment table + details (DO NOT POST)
5. Approve ─────► User edits / removes / adds / submits / cancels
6. Submit ──────► Batch POST /repos/.../pulls/.../reviews
```

## Step 1: Resolve PR

Accept a PR number, `#number`, or full GitHub URL. Extract owner/repo/number.

```bash
gh pr view <number> --json number,title,state,author,baseRefName,headRefName,isDraft,additions,deletions,changedFiles
```

If PR is not `OPEN`, warn and ask whether to proceed read-only (skip Step 6).

```bash
OWNER=$(gh repo view --json owner --jq '.owner.login')
REPO=$(gh repo view --json name --jq '.name')
```

## Step 2: Fetch Diff and Changed Files

```bash
gh pr diff <number>
gh pr view <number> --json files --jq '.files[].path'
```

For each changed file, `Read` the full content (not just the diff) so the
subagent has surrounding context.

### Large PRs (>30 changed files)

1. Warn: "This PR has N changed files. Reviewing all of them may take a
   while."
2. Ask whether to proceed with all files, or specify a subset.
3. If `--max-comments` is set, prioritize files with the most changes.

### Binary files

Skip and note them in the summary as "skipped (binary)".

## Step 3: Delegate to the reviewer subagent

Hand the bundle to `@agent-pr-review:pr-review`:

- `diff` (text)
- `files` (path → content map for non-binary files)
- `active_lenses` (from `--lens`, default all)
- `severity_floor` (from `--severity`, default `low`)
- `max_comments` (from `--max-comments`, default 30)
- PR metadata (title, author, body — for context)

The subagent returns a structured object with `summary`, `files_reviewed`,
`files_skipped`, `comments`, and `dropped_by_cap`.

## Step 4: Stage Comments

**CRITICAL: Do NOT submit anything to GitHub yet.** Display the staged review
inline.

### Summary Table

```
## Staged Review for PR #<number>: <title>

| # | File | Line | Severity | Lens | Summary |
|---|------|------|----------|------|---------|
| 1 | src/api.ts | 42 | high | bugs | Null dereference on optional field |
| 2 | src/db.ts | 15 | critical | security | SQL injection via string concat |
| 3 | src/app.tsx | 88 | medium | performance | Re-render on every state change |

**Total: N comments** (X critical, Y high, Z medium, W low)
```

### Detail View

For each comment, show path:line, severity/lens, and the full body (including
any ` ```suggestion ` block).

### Overall Review Body

Use the subagent's `summary` as the top-level review body.

### Action Menu

```
**Actions:**
- `submit` — Submit all staged comments as a review
- `edit N` — Edit comment #N (provide new body text)
- `remove N` — Remove comment #N from the review
- `add file:line body` — Add a new comment manually
- `change-event EVENT` — Change review event (COMMENT/APPROVE/REQUEST_CHANGES)
- `cancel` — Abort without submitting
```

## Step 5: User Approval

Wait for the user's decision. Loop until `submit` or `cancel`.

- `edit N` — re-display, accept new body, update staged comment.
- `remove N` — drop from list, renumber.
- `add file:line body` — parse and append manual comment.
- `change-event EVENT` — warn if changing to `APPROVE` / `REQUEST_CHANGES`.
- `submit` — proceed to Step 6.
- `cancel` — print "Review cancelled. No comments were posted." and exit.

## Step 6: Submit Review

Build the API payload and submit as one batch review. See
`references/gh-review-api.md`.

```bash
HEAD_SHA=$(gh pr view <number> --json headRefOid --jq '.headRefOid')

# Build review JSON with commit_id, event, body, and comments[]
# Then submit:
echo "$REVIEW_JSON" | gh api --method POST \
  /repos/{owner}/{repo}/pulls/{number}/reviews \
  --input -
```

After submission:

1. "Review submitted with N comments."
2. Print the review URL if available.
3. If any comments failed (422 on specific path/line), report which and why.

### Error Recovery

- **403** — no permission. Inform and abort.
- **404** — PR not found. Inform and abort.
- **422** — validation. Report the failing field/comment. Offer retry without
  invalid comments.
- **429** — rate limited. Wait for `Retry-After`, retry once.

## Edge Cases

- **Closed/merged PR** — warn at Step 1. Allow read-only (skip Step 6) on
  confirmation.
- **Draft PR** — note it, review normally.
- **No diff** — empty PR. Report and exit.
- **Binary files** — skip, note in summary.
- **Large PR (>30 files)** — warn at Step 2.
- **Zero issues** — "No issues found across N lenses." Offer to submit an
  approval or exit.
- **API rate limiting** — check `X-RateLimit-Remaining` before submitting.
- **Reviewer is PR author** — cannot use `APPROVE` / `REQUEST_CHANGES` on
  own PR. Fall back to `COMMENT` with warning.
- **Fork PRs** — diff may not include all context; note if
  `isCrossRepository` is true.

## References

- `references/gh-review-api.md` — Full REST API reference for batch
  reviews, error handling, suggestion blocks.
- `references/review-perspectives.md` — Detailed lens definitions used by
  the subagent.
