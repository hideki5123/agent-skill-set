---
name: address-pr-comments
description: Autonomously fetch and apply AI reviewer comments on a GitHub PR — creating a draft PR and requesting reviewers if needed. Default mode processes Copilot/Gemini bot comments without human intervention. Use when the user asks to address PR comments, fix review comments, handle PR feedback, respond to reviewer comments, apply review suggestions, act on PR feedback, get AI review, run copilot review, auto-review, address review, fix PR feedback.
---

# Address PR Review Comments

Autonomous-first workflow: create or find a PR, request AI reviewers, wait for reviews, apply fixes, commit, push, and reply — all without manual intervention. Pass `--interactive` to fall back to the old human-review flow.

## Arguments

- `<pr>` — PR number (`123`, `#123`) or full URL. Default: find the PR for the current branch, or **create a draft PR** if none exists.
- `--no-draft` — Skip draft PR creation; error if no PR exists.
- `--reviewers` — Comma-separated list of AI reviewers to request. Default: `copilot`. Supported: `copilot`, `gemini`.
- `--timeout` — Max wait time for reviews in minutes. Default: `5`.
- `--interactive` — Switch to interactive mode: process human comments with per-comment approval (old behavior).
- `--reply` — Reply to each comment on GitHub. Default: ON in autonomous mode, OFF in interactive mode.
- `--resolve` — Resolve addressed threads on GitHub.

## Workflow

1. **Resolve or create PR**
2. **Request AI reviewers**
3. **Wait for reviews**
4. **Fetch AI review comments**
5. **Process each comment (autonomous)**
6. **Commit and push**
7. **Reply on GitHub**

## Step 1: Resolve or Create PR

- If `<pr>` given → use it (`gh pr view <number>`)
- If no `<pr>` → check for existing PR on current branch (`gh pr view`)
- If no PR exists → create a draft PR:

```bash
# Determine base branch
BASE=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')
BRANCH=$(git branch --show-current)

# Create draft PR
gh pr create --draft --base "$BASE" --head "$BRANCH" \
  --title "$(git log -1 --format=%s)" \
  --body "Draft PR for AI code review."
```

- If `--no-draft` and no PR → error and stop

Check out the PR branch if not already on it:

```bash
git branch --show-current

# If not on the PR's head branch, check it out
gh pr checkout <number>
```

Pull latest changes:

```bash
git pull --rebase
```

If the rebase fails with merge conflicts, **stop immediately** and inform the user. Do not attempt to resolve merge conflicts automatically.

For fork PRs (`isCrossRepository: true`), `gh pr checkout` handles the remote setup automatically.

## Step 2: Request AI Reviewers

Bot usernames:

| Alias | GitHub Username |
|-------|----------------|
| `copilot` | `copilot-pull-request-reviewer[bot]` |
| `gemini` | `gemini-code-assist[bot]` |

Request via REST API (more reliable than `gh pr edit`):

```bash
gh api --method POST /repos/{owner}/{repo}/pulls/{number}/requested_reviewers \
  -f "reviewers[]=copilot-pull-request-reviewer[bot]"
```

Skip requesting if the reviewer has already submitted a review on the current head commit. Check with:

```bash
gh api /repos/{owner}/{repo}/pulls/{number}/reviews \
  | jq '[.[] | select(.user.login == "copilot-pull-request-reviewer[bot]")]'
```

If requesting a reviewer fails (403 — app not installed), warn and skip that reviewer.

## Step 3: Wait for Reviews

Poll every 15 seconds, up to `--timeout` minutes (default 5):

```bash
# Check pending reviewers
gh api /repos/{owner}/{repo}/pulls/{number}/requested_reviewers \
  | jq '.users[].login'

# Check submitted reviews
gh api /repos/{owner}/{repo}/pulls/{number}/reviews \
  | jq '[.[] | select(.user.login == "copilot-pull-request-reviewer[bot]")] | length'
```

- Reviewer done = no longer in `requested_reviewers` AND has entry in `/pulls/{number}/reviews`
- Once all requested reviewers complete (or timeout): proceed with whatever comments exist
- Show progress: `"Waiting for Copilot review... (30s elapsed)"`

If no comments arrive after timeout, inform the user and suggest checking if the reviewer app is installed.

## Step 4: Fetch AI Review Comments

Fetch line-level review comments and thread resolution status. Read `references/gh-comment-api.md` for full API details, field descriptions, and jq recipes.

```bash
# Fetch all line-level review comments
gh api repos/{owner}/{repo}/pulls/{number}/comments --paginate
```

Fetch thread resolution status via GraphQL:

```bash
gh api graphql -f query='
  query($owner: String!, $repo: String!, $number: Int!) {
    repository(owner: $owner, name: $repo) {
      pullRequest(number: $number) {
        reviewThreads(first: 100) {
          nodes {
            id
            isResolved
            comments(first: 1) {
              nodes {
                databaseId
              }
            }
          }
        }
      }
    }
  }
' -f owner="{owner}" -f repo="{repo}" -F number={number}
```

**Filter IN** (opposite of interactive mode): only comments from known AI reviewer usernames:

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments --paginate \
  | jq '[.[] | select(.user.login == "copilot-pull-request-reviewer[bot]" or .user.login == "gemini-code-assist[bot]")]'
```

**Filter out** (still applies):
- Resolved threads (already addressed)
- Outdated comments on deleted lines (`position: null` and no `line` field)
- Comments that are replies in a thread (only process the root comment; use `in_reply_to_id` to identify replies)

Consolidate thread comments — AI reviewers may reply to themselves within a thread. Treat the full thread as one unit.

## Step 5: Process Each Comment (Autonomous)

For each comment:

### 5a. Gather context

```bash
# Read the file around the commented line (±20 lines for context)
# Use the Read tool to read the file

# Get the PR diff for this specific file
gh pr diff <number> -- <file_path>
```

### 5b. Classify the comment

| Classification | Description | Default action |
|---------------|-------------|----------------|
| **Clear fix** | Obvious bug, typo, missing check — unambiguous resolution | Auto-apply |
| **Suggestion with code** | Reviewer provided a `suggestion` block | Auto-apply |
| **Style/formatting** | Naming, formatting, convention — low risk | Auto-apply |
| **Design concern** | Architectural feedback, approach question | Ask user only if it conflicts with PR intent |
| **Question** | Reviewer asking for clarification, not requesting a change | Skip with reason |
| **Already addressed** | The current code already handles what the reviewer asked for | Skip with reason |

### 5c. Handle GitHub suggestion blocks

If the comment body contains a GitHub suggestion block:

````
```suggestion
replacement code here
```
````

Extract the suggested code and apply it directly to the specified lines. GitHub suggestions map exactly to the `line` (or `start_line`–`line` range) in the comment.

### 5d. Apply or skip

- **Auto-apply** for: clear fix, suggestion with code, style/formatting
- **Skip with reason** for: questions, already addressed, doesn't make sense in context
- **Ask user** only for: design concerns that conflict with PR intent, conflicting AI feedback

No per-comment approval needed in autonomous mode.

After applying a fix:
- Verify the file still parses (run a syntax check if applicable for the language)
- If multiple comments touch the same file region, process them in line-number order and re-read after each edit to avoid offset drift

### 5e. Conflicting feedback

If two AI reviewers give conflicting feedback on the same code:
- Present both comments side by side
- Do not auto-apply either
- Ask the user which direction to take

## Step 6: Commit and Push

After all comments are processed:

```bash
# Stage changed files (only files that were actually modified)
git add <file1> <file2> ...

# Commit with conventional commit format
git commit -m "$(cat <<'EOF'
fix: address AI review comments from PR #<number>
EOF
)"

# Push to the PR branch
git push
```

If changes fall into logically distinct groups (e.g., security fixes vs. style fixes), split into multiple commits.

## Step 7: Reply on GitHub

Default ON in autonomous mode. For each processed comment:

- **Fixed**: `"Fixed in {short_sha}. {brief description}."`
- **Acknowledged** (no code change needed): `"Acknowledged. {explanation}."`
- **Skipped**: `"Noted — skipping because: {reason}."`

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments/{comment_id}/replies \
  --method POST \
  -f body="Fixed in $(git rev-parse --short HEAD). <brief description>."
```

### Resolve threads (when `--resolve`)

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

Only resolve threads where the comment was actually addressed (fixed), not skipped.

## `--interactive` Mode

When `--interactive` is passed, fall back to the previous human-review behavior:

- **Filter for human comments** (exclude bots — `user.type != "Bot"`)
- Filter out: resolved threads, PR author's own comments, outdated comments, reply comments
- Show summary table, ask user to select which comments to process
- Per-comment approval with diff preview before applying
- `--reply` is OFF by default (user opts in)
- Classification and processing logic is the same as Step 5, but every change requires user confirmation

## Edge Cases

- **No PR for current branch (no `--no-draft`)**: Create a draft PR automatically.
- **No PR for current branch (`--no-draft`)**: Error and stop.
- **AI reviewer not available**: If requesting a reviewer fails (403 — app not installed), warn and skip that reviewer.
- **No comments after timeout**: Inform user, suggest checking if the reviewer app is installed.
- **Re-review**: If comments already exist from a previous review round, process those (don't re-request).
- **No unresolved comments**: If all comments are resolved or filtered out, inform the user and exit.
- **Fork PRs**: `gh pr checkout` handles fork remote setup. Pushing back requires write access to the fork — warn if `isCrossRepository` is true.
- **Merge conflicts on pull**: Stop immediately, inform the user, and do not proceed.
- **>50 comments**: Process in batches grouped by file. Show progress ("Processing file 3/12...").
- **Binary files**: Skip comments on binary files with explanation.
- **Conflicting reviewer feedback**: Present both, ask user (see Step 5e).
- **Outdated comments on deleted files**: Skip with explanation ("File was deleted in this PR").
- **Rate limiting**: If GitHub API returns 403/429, wait and retry with exponential backoff (max 3 retries).
- **Already addressed comments**: Classify as "already addressed" and skip.

## References

- `references/gh-comment-api.md` — REST and GraphQL API details for PR review comments, thread resolution, reply posting, suggestion block parsing, AI reviewer requests, and review polling. Read this before starting.
