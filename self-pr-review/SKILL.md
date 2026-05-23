---
name: self-pr-review
description: Self-review loop for YOUR OWN PR — request AI reviews (Copilot + Gemini), apply their fixes, push, re-request, and repeat until clean. NOT for reviewing someone else's PR. Use when the user asks to self-review their PR, run the AI review loop, or wants Copilot + Gemini to review their own code. Trigger phrases include "self-review", "self-pr-review", "review my PR", "AI review my PR", "review loop", "copilot + gemini review", "run self-review on my PR".
version: 1.1.0
context: fork
agent: general-purpose
disable-model-invocation: true
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

### Feedback Check

If `feedback/log.md` exists and has 5 or more entries, read the last 10 entries.
If a pattern is apparent (same issue in 3+ entries, or average rating below 3):
- Tell the user: "Recurring feedback detected: [brief pattern]. Consider running `/skill-improve --skill self-pr-review`."
- Continue with normal execution.

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
```

  Before creating, check for a PR template in the repo:

  1. Read `.github/pull_request_template.md` (or `PULL_REQUEST_TEMPLATE.md` at repo root)
  2. **Detect selector templates** — if the file contains `?template=<name>.md` links instead of actual form sections (Motivation, Description, etc.), it is a selector pointing to sub-templates in `.github/PULL_REQUEST_TEMPLATE/`
  3. **If selector detected:** read the selector text to understand which sub-template maps to which scenario. Check `git diff --name-only $BASE..HEAD` to determine which sub-template applies, then read and use that sub-template.
  4. **If not a selector:** use it directly as the template.
  5. **If no template file exists:** check `.github/PULL_REQUEST_TEMPLATE/` for `.md` files and use `default.md` or the first one found.
  6. **If no template at all:** fall back to `"Draft PR for AI code review."`.

  **Filling the template:** read the template, then populate each section based on `git diff $BASE..HEAD` and `git log --oneline $BASE..HEAD`.
  - Fill Motivation, Existing/New Behavior, or Description sections with concise explanations of the changes.
  - **Checklists: preserve the exact structure verbatim** — same items, same sub-bullets, same order, same wording. Only change `[ ]` to `[x]` where the item is satisfied. Never add, remove, reword, or restructure checklist items.

```bash
gh pr create --draft --base "$BASE" --head "$BRANCH" \
  --title "$(git log -1 --format=%s)" \
  --body "<filled template or fallback>"

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
REPLIED_IDS=()    # comment_id values we already replied to (one reply per comment max)
OUR_REPLY_IDS=()  # IDs of replies WE posted (to detect reviewer follow-ups)
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

### Detect Reviewer Follow-ups

After processing root comments, also fetch reviewer replies to OUR previous replies. These are comments where `in_reply_to_id` matches one of `OUR_REPLY_IDS` (IDs of replies we posted in earlier rounds). This captures cases where a reviewer responds to our fix with further feedback.

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments --paginate \
  | jq --argjson ours '[<comma-separated OUR_REPLY_IDS>]' \
  '[.[] | select(
    (.user.login == "copilot-pull-request-reviewer[bot]" or .user.login == "gemini-code-assist[bot]")
    and (.in_reply_to_id as $rid | $ours | index($rid) | . != null)
  )]'
```

Merge these follow-up comments into the processing queue alongside the root comments. Each follow-up is treated as a new actionable comment — process it through Steps 5a–5f as usual.

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

### 5g. Conflicting feedback under `context: fork` (fail-fast)

This skill ships with `context: fork`. In a forked subagent context the
user cannot answer prompts — any tool call that would prompt is
auto-denied. The "ask the user which direction to take" branches above
therefore cannot complete inside a fork.

Under fork, when conflicting feedback is detected:

- Do **not** auto-pick a side and do **not** silently skip.
- Stop the loop, record both comments with full context in the round
  report, and exit with status `conflict-requires-user`.
- The next run of this skill (inline, no fork) sees the conflict in the
  open thread and the user can resolve it via interactive prompts.

The skill is also marked `disable-model-invocation: true` because every
iteration commits and pushes — Claude must not auto-trigger this skill
from a generic phrase. The user explicitly types
`/self-pr-review` to start a loop.

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

Reply to each processed comment on GitHub — **one reply per comment maximum**. Before posting, check `REPLIED_IDS`: if the comment was already replied to in a previous round, skip the reply (the fix is still applied, but no duplicate notification is sent).

- **Fixed**: `"Fixed in {short_sha}. {brief description}."`
- **Acknowledged** (no code change needed): `"Acknowledged. {explanation}."`
- **Skipped**: `"Noted — skipping because: {reason}."`

```bash
# Only reply if we haven't replied to this comment before
if ! echo "${REPLIED_IDS[@]}" | grep -qw "$COMMENT_ID"; then
  REPLY_RESPONSE=$(gh api repos/{owner}/{repo}/pulls/{number}/comments/{comment_id}/replies \
    --method POST \
    -f body="Fixed in $(git rev-parse --short HEAD). <brief description>.")

  # Track that we replied, and record our reply ID for follow-up detection
  REPLIED_IDS+=("$COMMENT_ID")
  OUR_REPLY_ID=$(echo "$REPLY_RESPONSE" | jq '.id')
  OUR_REPLY_IDS+=("$OUR_REPLY_ID")
fi
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

## References

- `references/gh-comment-api.md` — REST and GraphQL API details for PR review comments, thread resolution, reply posting, suggestion block parsing, AI reviewer requests, review polling, re-requesting reviews, and commit-based filtering. Read this before starting.
