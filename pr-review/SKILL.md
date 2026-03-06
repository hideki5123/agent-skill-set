---
name: pr-review
description: Review a teammate's pull request — Claude reads the diff, analyzes code across multiple perspectives, and stages review comments for user approval before submission. NOT for self-review of your own PR. Trigger phrases include "review PR #123", "code review PR", "peer review", "check this PR", "give PR feedback", "review pull request", "review someone's PR".
---

# PR Review

Analyze a pull request's diff across multiple review perspectives, stage comments for user approval, and submit a batch review. This skill reviews **someone else's PR** — for self-review of your own PR, use `self-pr-review` instead.

## Arguments

- `<pr>` — PR number (`123`, `#123`) or full URL (required).
- `--lens` — Comma-separated list of review lenses. Options: `bugs`, `security`, `performance`, `style`, `complexity`, `testing`, `docs`. Default: all.
- `--event` — Review event type: `COMMENT` (default), `APPROVE`, `REQUEST_CHANGES`.
- `--severity` — Minimum severity to include: `critical`, `high`, `medium`, `low`, `all`. Default: `all`.
- `--max-comments` — Maximum inline comments to stage. Default: `30`.

## Workflow Overview

```
1. Resolve PR ──► Verify OPEN, fetch metadata
2. Fetch Diff ──► gh pr diff, read changed files for context
3. Analyze ────► Review through each active lens
4. Stage ──────► Display comment table + details (DO NOT POST)
5. Approve ────► User edits/removes/adds/submits/cancels
6. Submit ─────► Batch POST /repos/.../pulls/.../reviews
```

## Step 1: Resolve PR

Accept a PR number, `#number`, or full GitHub URL. Extract owner/repo/number.

```bash
# Verify PR exists and is OPEN
gh pr view <number> --json number,title,state,author,baseRefName,headRefName,isDraft,additions,deletions,changedFiles
```

If PR is not `OPEN`, warn the user and ask whether to proceed (reviewing closed/merged PRs is read-only — skip Step 6).

Extract owner/repo for API calls:

```bash
OWNER=$(gh repo view --json owner --jq '.owner.login')
REPO=$(gh repo view --json name --jq '.name')
```

## Step 2: Fetch Diff and Changed Files

```bash
# Get full diff
gh pr diff <number>

# List changed files
gh pr view <number> --json files --jq '.files[].path'
```

For each changed file, read the full file content (not just the diff) to understand context around the changes. Use the Read tool.

### Large PRs (>30 changed files)

If the PR touches more than 30 files:
1. Warn the user: "This PR has N changed files. Reviewing all of them may take a while."
2. Ask if they want to proceed with all files, or specify a subset.
3. If `--max-comments` is set, prioritize files with the most changes.

### Binary Files

Skip binary files (images, compiled assets). Note them in the summary as "skipped (binary)".

## Step 3: Analyze Code

For each active lens (see `references/review-perspectives.md`), review the diff and generate structured comments.

For each issue found, record:

| Field | Description |
|-------|-------------|
| `path` | File path relative to repo root |
| `line` | Line number in the new file (right side of diff) |
| `start_line` | Start line for multi-line comments (optional) |
| `severity` | `critical`, `high`, `medium`, `low` |
| `lens` | Which lens found the issue |
| `summary` | One-line summary |
| `body` | Full comment body (markdown), may include suggestion blocks |

### Writing Good Comments

- Be specific: reference the exact code, explain why it's an issue.
- Include a suggestion block when a concrete fix exists:

````markdown
This allocates a new array on every render.

```suggestion
const items = useMemo(() => data.filter(Boolean), [data]);
```
````

- For complex issues, explain the impact and link to relevant docs or patterns.
- Avoid vague comments like "this could be better" — say what and why.
- Don't comment on things that are clearly intentional or already explained in the PR description.

### Severity Filtering

After generating all comments, filter by `--severity`. If `--severity medium`, drop `low` severity comments.

### Comment Cap

If total comments exceed `--max-comments`, keep the highest severity comments first, then earliest in file order as tiebreaker. Note dropped comments in the summary.

## Step 4: Stage Comments

**CRITICAL: Do NOT submit anything to GitHub at this point.** Display all comments for user review.

### Summary Table

```
## Staged Review for PR #<number>: <title>

| # | File | Line | Severity | Lens | Summary |
|---|------|------|----------|------|---------|
| 1 | src/api.ts | 42 | high | bugs | Null dereference on optional field |
| 2 | src/db.ts | 15 | critical | security | SQL injection via string concat |
| 3 | src/app.tsx | 88 | medium | performance | Re-render on every state change |
...

**Total: N comments** (X critical, Y high, Z medium, W low)
```

### Detail View

For each comment, show the full body:

```
### Comment #1 — src/api.ts:42 [high/bugs]

`user.email` is accessed without a null check. If the user object is missing
the email field, this will throw a TypeError.

\```suggestion
const email = user?.email ?? 'unknown';
\```

---
```

### Overall Review Body

Draft the top-level review summary:

```
**Review body:**
> Reviewed N files across K lenses. Found X issues (C critical, H high, M medium, L low).
> Key concerns: [brief list of critical/high items].
```

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

Wait for the user's decision. Loop until the user chooses `submit` or `cancel`.

### `edit N`
Re-display the comment, accept new body text from the user, update the staged comment.

### `remove N`
Remove the comment from the staged list. Renumber remaining comments.

### `add file:line body`
Add a manual comment. Parse file path and line number, accept body text.

### `change-event EVENT`
Change the review event type. Warn if changing to `APPROVE` or `REQUEST_CHANGES` (these have stronger implications).

### `submit`
Proceed to Step 6.

### `cancel`
Exit without submitting. Print "Review cancelled. No comments were posted."

## Step 6: Submit Review

Build the API payload and submit as a single batch review. Read `references/gh-review-api.md` for full API details.

```bash
# Get HEAD SHA for the review
HEAD_SHA=$(gh pr view <number> --json headRefOid --jq '.headRefOid')

# Build review JSON
REVIEW_JSON=$(cat <<'ENDJSON'
{
  "commit_id": "$HEAD_SHA",
  "event": "$EVENT",
  "body": "Review summary.",
  "comments": [
    {
      "path": "src/api.ts",
      "line": 42,
      "side": "RIGHT",
      "body": "Comment body here."
    }
  ]
}
ENDJSON
)

# Submit
echo "$REVIEW_JSON" | gh api --method POST \
  /repos/{owner}/{repo}/pulls/{number}/reviews \
  --input -
```

After submission:
1. Confirm success: "Review submitted with N comments."
2. Print the review URL if available.
3. If any comments failed (422 on specific paths/lines), report which ones failed and why.

### Error Recovery

- **403** — User lacks permission. Inform and abort.
- **404** — PR not found (may have been deleted). Inform and abort.
- **422** — Validation error. Report the specific field/comment that failed. Offer to retry without the invalid comments.
- **429** — Rate limited. Wait for `Retry-After` header duration, then retry once.

## Edge Cases

- **Closed/merged PR** — Warn at Step 1. Allow read-only review (skip submission) or proceed if user confirms.
- **Draft PR** — Note that it's a draft. Review normally.
- **No diff** — PR has no changes (e.g., empty commits). Report and exit.
- **Binary files** — Skip with note in summary.
- **Large PR (>30 files)** — Warn and ask user before proceeding (see Step 2).
- **Zero issues found** — Report "No issues found across N lenses." Offer to submit an approval or exit.
- **API rate limiting** — Check `X-RateLimit-Remaining` header. If low, warn before submitting.
- **Reviewer is PR author** — Cannot use `APPROVE` or `REQUEST_CHANGES` on own PR. Fall back to `COMMENT` with warning.
- **Fork PRs** — Diff may not include all context. Note if `isCrossRepository` is true.

## References

- `references/gh-review-api.md` — Full REST API reference for creating batch reviews, error handling, and suggestion blocks.
- `references/review-perspectives.md` — Detailed review lens definitions with what-to-look-for and severity guidance.
