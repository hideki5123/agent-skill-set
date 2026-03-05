---
name: review-pr
description: Self-review loop — request AI reviews (Copilot + Gemini), apply fixes, push, re-request, repeat until clean. Use when the user asks to review their PR, self-review, get AI review, run the review loop, or wants Copilot + Gemini to review their code. Trigger phrases include "review my PR", "self-review", "get AI review", "review loop", "copilot + gemini review", "review PR", "review #123".
---

# Self-Review Loop

Request AI reviews (Copilot + Gemini), apply their fixes, push, re-request reviews, and repeat until clean — or max iterations reached.

## Arguments

- `<pr>` — PR number (`123`, `#123`) or full URL. Default: find the PR for the current branch, or create a draft PR if none exists.
- `--reviewers` — Comma-separated list of AI reviewers. Default: `copilot,gemini`. Supported: `copilot`, `gemini`.
- `--max-iterations` — Max review-fix cycles. Default: `3`.
- `--timeout` — Max wait time per review round in minutes. Default: `5`.
- `--resolve` — Resolve addressed threads on GitHub after replying.
- `--no-draft` — Don't auto-create a draft PR; error if no PR exists.

## Workflow Overview

```
┌─► 1. Resolve/Create PR
│   2. Request AI Reviewers
│   3. Wait for Reviews
│   4. Fetch New Comments (filter already-processed)
│   5. Process & Apply Fixes
│   6. Commit, Push, Reply
│   7. Loop Decision ──► changes made? ─── yes ──┐
│                        no changes? ─── exit     │
│                        max iterations? ─── exit │
└─────────────────────────────────────────────────┘
```

## Step 1: Resolve or Create PR

- If `<pr>` given → use it (`gh pr view <number>`)
- If no `<pr>` → check for existing PR on current branch (`gh pr view`)
- If no PR exists and `--no-draft` is not set → create a draft PR:

```bash
BASE=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')
BRANCH=$(git branch --show-current)

gh pr create --draft --base "$BASE" --head "$BRANCH" \
  --title "$(git log -1 --format=%s)" \
  --body "Draft PR for AI code review."

PR_NUMBER=$(gh pr view --json number --jq '.number')
```

- If `--no-draft` and no PR → error and stop.

Check out the PR branch if not already on it:

```bash
gh pr checkout <number>
```

Pull latest changes:

```bash
git pull --rebase
```

If the rebase fails with merge conflicts, **stop immediately** and inform the user.

Extract owner/repo for API calls:

```bash
OWNER=$(gh repo view --json owner --jq '.owner.login')
REPO=$(gh repo view --json name --jq '.name')
```

Initialize tracking state:

```bash
# Track processed comment IDs across iterations
PROCESSED_IDS=()
ROUND=0
```

## Step 2: Request AI Reviewers

Bot usernames:

| Alias | GitHub Username |
|-------|----------------|
| `copilot` | `copilot-pull-request-reviewer[bot]` |
| `gemini` | `gemini-code-assist[bot]` |

Before requesting, check if a reviewer has already reviewed the current HEAD commit:

```bash
HEAD_SHA=$(gh pr view <number> --json headRefOid --jq '.headRefOid')

# Check if reviewer already submitted a review on this commit
gh api /repos/{owner}/{repo}/pulls/{number}/reviews \
  | jq --arg sha "$HEAD_SHA" '[.[] | select(.user.login == "copilot-pull-request-reviewer[bot]" and .commit_id == $sha)] | length'
```

If already reviewed current HEAD, skip requesting that reviewer.

Otherwise, request via REST API. Read `references/gh-comment-api.md` for full details on requesting and re-requesting reviewers.

```bash
gh api --method POST /repos/{owner}/{repo}/pulls/{number}/requested_reviewers \
  -f "reviewers[]=copilot-pull-request-reviewer[bot]" \
  -f "reviewers[]=gemini-code-assist[bot]"
```

If requesting fails (403 — app not installed), warn and skip that reviewer. Continue with remaining reviewers.

## Step 3: Wait for Reviews

Poll every 15 seconds, up to `--timeout` minutes (default 5):

```bash
ELAPSED=0
TIMEOUT_SECS=$((TIMEOUT * 60))
while [ $ELAPSED -lt $TIMEOUT_SECS ]; do
  PENDING=$(gh api /repos/{owner}/{repo}/pulls/{number}/requested_reviewers \
    | jq '[.users[] | select(
      .login == "copilot-pull-request-reviewer[bot]" or
      .login == "gemini-code-assist[bot]"
    )] | length')
  if [ "$PENDING" -eq 0 ]; then
    echo "All reviews complete."
    break
  fi
  echo "Waiting for reviews... (${ELAPSED}s elapsed, $PENDING pending)"
  sleep 15
  ELAPSED=$((ELAPSED + 15))
done
```

- Once all requested reviewers complete (or timeout): proceed with whatever comments exist.
- If one reviewer responds and the other doesn't → proceed with available comments; re-request the missing reviewer in the next round.

## Step 4: Fetch New Comments

Fetch line-level review comments. Read `references/gh-comment-api.md` for full API details, field descriptions, and jq recipes.

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments --paginate \
  | jq '[.[] | select(
    (.user.login == "copilot-pull-request-reviewer[bot]" or .user.login == "gemini-code-assist[bot]")
    and .in_reply_to_id == null
    and (.line != null or .position != null)
  )]'
```

### Filter Out Already-Processed Comments

Each iteration must only process **new** comments. Filter by comment ID against the tracked set:

```bash
# Filter out comments already processed in previous iterations
| jq --argjson seen '[<comma-separated processed IDs>]' \
  '[.[] | select(.id as $id | $seen | index($id) | not)]'
```

### Additional Filters

- **Resolved threads** — skip (check via GraphQL `reviewThreads` query)
- **Outdated comments** — `position: null` and no `line` field → skip
- **Reply comments** — `in_reply_to_id != null` → skip (only process root comments)

Consolidate thread comments — AI reviewers may reply to themselves within a thread. Treat the full thread as one unit.

## Step 5: Process and Apply Fixes

For each new comment:

### 5a. Gather Context

```bash
# Read the file around the commented line (±20 lines for context)
# Use the Read tool

# Get the PR diff for this specific file
gh pr diff <number> -- <file_path>
```

### 5b. Classify the Comment

| Classification | Description | Action |
|---------------|-------------|--------|
| **Clear fix** | Obvious bug, typo, missing check — unambiguous resolution | Auto-apply |
| **Suggestion with code** | Reviewer provided a `suggestion` block | Auto-apply |
| **Style/formatting** | Naming, formatting, convention — low risk | Auto-apply |
| **Design concern** | Architectural feedback, approach question | Ask user only if it conflicts with PR intent |
| **Question** | Reviewer asking for clarification, not requesting a change | Skip with reason |
| **Already addressed** | Current code already handles what the reviewer asked for | Skip with reason |

### 5c. Handle GitHub Suggestion Blocks

If the comment body contains a GitHub suggestion block:

````
```suggestion
replacement code here
```
````

Extract the suggested code and apply it directly to the specified lines. GitHub suggestions map exactly to the `line` (or `start_line`–`line` range) in the comment.

### 5d. Apply or Skip

- **Auto-apply** for: clear fix, suggestion with code, style/formatting
- **Skip with reason** for: questions, already addressed, doesn't make sense in context
- **Ask user** only for: design concerns that conflict with PR intent, conflicting AI feedback

After applying a fix:
- Verify the file still parses (run a syntax check if applicable)
- If multiple comments touch the same file region, process in line-number order and re-read after each edit to avoid offset drift

### 5e. Conflicting Feedback

**Between reviewers (same round):** If Copilot and Gemini give conflicting feedback on the same code:
- Present both comments side by side
- Do not auto-apply either
- Ask the user which direction to take

**Between rounds:** If a new comment in round N reverses a fix applied in round N-1:
- Present the original comment, the fix applied, and the new comment
- Ask the user how to proceed

### 5f. Track Processed Comments

After processing each comment (whether applied or skipped), add its ID to the tracked set:

```bash
PROCESSED_IDS+=(<comment_id>)
```

## Step 6: Commit, Push, Reply

After all comments in this round are processed:

```bash
# Stage changed files (only files actually modified)
git add <file1> <file2> ...

# Commit with round number
git commit -m "$(cat <<'EOF'
fix: address AI review (round N) for PR #<number>
EOF
)"

# Push
git push
```

Reply to each processed comment on GitHub:

- **Fixed**: `"Fixed in {short_sha}. {brief description}."`
- **Acknowledged** (no code change needed): `"Acknowledged. {explanation}."`
- **Skipped**: `"Noted — skipping because: {reason}."`

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments/{comment_id}/replies \
  --method POST \
  -f body="Fixed in $(git rev-parse --short HEAD). <brief description>."
```

### Resolve Threads (when `--resolve`)

Only resolve threads where the comment was actually addressed (fixed), not skipped:

```bash
gh api graphql -f query='
  mutation($threadId: ID!) {
    resolveReviewThread(input: {threadId: $threadId}) {
      thread {
        isResolved
      }
    }
  }
' -f threadId="<thread_node_id>"
```

## Step 7: Loop Decision

After committing and pushing, decide whether to loop:

| Condition | Action |
|-----------|--------|
| Changes were made this round | Increment `ROUND`, go to Step 2 |
| No changes (all comments skipped/acknowledged) | Exit with summary |
| `ROUND >= --max-iterations` | Exit with summary of remaining unaddressed comments |
| PR closed or merged | Exit immediately |

Check PR state before each new iteration:

```bash
gh pr view <number> --json state --jq '.state'
```

If state is not `OPEN`, exit the loop.

## Final Summary

After exiting the loop (for any reason), print a summary table:

```
## Self-Review Summary for PR #<number>

| Round | Comments Received | Changes Applied | Skipped |
|-------|------------------|-----------------|---------|
| 1     | 8                | 6               | 2       |
| 2     | 3                | 2               | 1       |
| 3     | 0                | 0               | 0       |

**Total**: 11 comments processed, 8 fixes applied, 3 skipped.
**Exit reason**: No new comments in round 3 — PR is clean.
```

If exiting due to max iterations with remaining comments, list them:

```
**Remaining unaddressed comments (max iterations reached):**
- `src/api.ts:42` — [copilot] Consider adding rate limiting
- `src/db.ts:15` — [gemini] Index may improve query performance
```

## Edge Cases

- **One reviewer responds, other doesn't** — proceed with available comments; re-request the missing reviewer next round.
- **Conflicting reviews between reviewers** — present both, ask user (see Step 5e).
- **Conflicting reviews between rounds** — present original fix + new comment, ask user (see Step 5e).
- **Reviewer bot uninstalled mid-loop** — warn on 403, continue with remaining reviewers.
- **PR closed/merged during loop** — check state each iteration (Step 7), exit if not open.
- **Rate limiting** — if GitHub API returns 403/429, wait and retry with exponential backoff (max 3 retries).
- **Merge conflicts on pull** — stop immediately, inform user.
- **>50 comments per round** — batch by file with progress ("Processing file 3/12...").
- **No PR for current branch (`--no-draft`)** — error and stop.
- **No PR for current branch (default)** — create draft PR automatically.
- **Fork PRs** — `gh pr checkout` handles fork remote setup. Warn if `isCrossRepository` is true (pushing requires write access to fork).
- **Binary files** — skip comments on binary files with explanation.
- **Outdated comments on deleted files** — skip with explanation ("File was deleted in this PR").

## References

- `references/gh-comment-api.md` — REST and GraphQL API details for PR review comments, thread resolution, reply posting, suggestion block parsing, AI reviewer requests, review polling, re-requesting reviews, and commit-based filtering. Read this before starting.
