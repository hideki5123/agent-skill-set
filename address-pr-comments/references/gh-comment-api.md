# GitHub PR Review Comment API Reference

## REST API: Fetch Review Comments

```
GET /repos/{owner}/{repo}/pulls/{number}/comments
```

Paginate with `--paginate` flag in `gh api`.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Unique comment ID (use for replies) |
| `node_id` | string | GraphQL node ID |
| `body` | string | Comment body (markdown) |
| `path` | string | File path relative to repo root |
| `line` | int\|null | Line number in the diff (new file side) |
| `original_line` | int | Line number at time of comment (may differ from `line` if code changed) |
| `start_line` | int\|null | Start line for multi-line comments |
| `position` | int\|null | Deprecated diff position. `null` means the comment is outdated |
| `side` | string | `LEFT` (deletion) or `RIGHT` (addition) |
| `in_reply_to_id` | int\|null | Parent comment ID if this is a reply. `null` for root comments |
| `user.login` | string | Commenter's GitHub username |
| `user.type` | string | `User` or `Bot` |
| `created_at` | string | ISO 8601 timestamp |
| `updated_at` | string | ISO 8601 timestamp |
| `commit_id` | string | The commit SHA the comment was made on |
| `subject_type` | string | `line` or `file` |

## jq Filter Recipes

### Filter out bot comments

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments --paginate \
  | jq '[.[] | select(.user.type != "Bot")]'
```

### Filter out replies (keep only root comments)

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments --paginate \
  | jq '[.[] | select(.in_reply_to_id == null)]'
```

### Group by file path

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments --paginate \
  | jq 'group_by(.path) | map({file: .[0].path, comments: .})'
```

### Exclude outdated comments (no valid position)

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments --paginate \
  | jq '[.[] | select(.line != null or .position != null)]'
```

### Combined filter: active, non-bot, root comments only

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments --paginate \
  | jq '[.[] | select(.user.type != "Bot" and .in_reply_to_id == null and (.line != null or .position != null))]'
```

### Exclude PR author's own comments

```bash
PR_AUTHOR=$(gh pr view {number} --json author --jq '.author.login')
gh api repos/{owner}/{repo}/pulls/{number}/comments --paginate \
  | jq --arg author "$PR_AUTHOR" '[.[] | select(.user.login != $author)]'
```

## GraphQL: Review Thread Resolution Status

```graphql
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
              body
              path
              author {
                login
              }
            }
          }
        }
        pageInfo {
          hasNextPage
          endCursor
        }
      }
    }
  }
}
```

### Pagination

For PRs with >100 threads, use cursor-based pagination:

```graphql
reviewThreads(first: 100, after: $cursor) {
  ...
  pageInfo {
    hasNextPage
    endCursor
  }
}
```

### Mapping REST Comment ID to GraphQL Thread ID

The `databaseId` field in the GraphQL `comments` node corresponds to the REST API `id` field. To find the GraphQL thread ID for a REST comment:

1. Fetch threads via GraphQL (includes `id` and `comments.nodes[0].databaseId`)
2. Match `databaseId` to the REST comment's `id`
3. Use the thread's `id` (node ID) for mutations

## Reply to a Comment

```
POST /repos/{owner}/{repo}/pulls/{number}/comments/{comment_id}/replies
```

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments/{comment_id}/replies \
  --method POST \
  -f body="Fixed in abc1234. Added null check before accessing user.email."
```

The `comment_id` is the REST API `id` of the root comment in the thread.

## Resolve a Review Thread (GraphQL Mutation)

```graphql
mutation($threadId: ID!) {
  resolveReviewThread(input: {threadId: $threadId}) {
    thread {
      isResolved
    }
  }
}
```

```bash
gh api graphql -f query='
  mutation($threadId: ID!) {
    resolveReviewThread(input: {threadId: $threadId}) {
      thread {
        isResolved
      }
    }
  }
' -f threadId="THREAD_NODE_ID"
```

The `threadId` is the GraphQL `id` field from the `reviewThreads` query (not the REST `id`).

## GitHub Suggestion Block Parsing

Reviewers can include code suggestions in their comments using fenced blocks:

````markdown
```suggestion
replacement code here
```
````

### Parsing Rules

1. A suggestion block replaces the lines specified by the comment's `line` (single-line) or `start_line`–`line` range (multi-line)
2. The content inside the block is the exact replacement text (no extra newlines)
3. A single comment can contain multiple suggestion blocks — each one is a separate replacement
4. Suggestion blocks use the `` ```suggestion `` fence — do not confuse with regular code fences
5. The replacement preserves the indentation as written in the suggestion block

### Extracting Suggestions

To extract suggestion content from a comment body:

```bash
# Using sed to extract content between ```suggestion and ``` fences
echo "$COMMENT_BODY" | sed -n '/^```suggestion$/,/^```$/{ /^```/d; p }'
```

### Applying Suggestions

1. Read the target file
2. Identify the line range: single line (`line`) or range (`start_line` to `line`)
3. Replace those lines with the suggestion block content
4. Write the file back

For multi-line suggestions where `start_line` is set:
- `start_line` is the first line to replace (inclusive)
- `line` is the last line to replace (inclusive)
- The suggestion content replaces this entire range

## Requesting AI Reviewers

Request an AI reviewer on a PR via the REST API:

```
POST /repos/{owner}/{repo}/pulls/{number}/requested_reviewers
```

```bash
gh api --method POST /repos/{owner}/{repo}/pulls/{number}/requested_reviewers \
  -f "reviewers[]=copilot-pull-request-reviewer[bot]"
```

For multiple reviewers:

```bash
gh api --method POST /repos/{owner}/{repo}/pulls/{number}/requested_reviewers \
  -f "reviewers[]=copilot-pull-request-reviewer[bot]" \
  -f "reviewers[]=gemini-code-assist[bot]"
```

If the reviewer app is not installed on the repo, the API returns `403`. Handle this gracefully by warning and skipping the reviewer.

## AI Reviewer Bot Usernames

| Alias | GitHub Username | Notes |
|-------|----------------|-------|
| `copilot` | `copilot-pull-request-reviewer[bot]` | GitHub Copilot code review |
| `gemini` | `gemini-code-assist[bot]` | Google Gemini Code Assist |

## Checking Review Completion

To determine if a requested AI reviewer has finished:

1. **Check pending reviewers** — a reviewer that is still pending appears in `requested_reviewers`:

```bash
gh api /repos/{owner}/{repo}/pulls/{number}/requested_reviewers \
  | jq '.users[].login'
```

2. **Check submitted reviews** — once the reviewer submits, it appears here:

```bash
gh api /repos/{owner}/{repo}/pulls/{number}/reviews \
  | jq '[.[] | select(.user.login == "copilot-pull-request-reviewer[bot]")]'
```

A reviewer is **done** when it is no longer in `requested_reviewers` AND has at least one entry in `/reviews`.

### Polling Pattern

```bash
# Poll every 15 seconds, up to TIMEOUT minutes
ELAPSED=0
TIMEOUT_SECS=$((TIMEOUT * 60))
while [ $ELAPSED -lt $TIMEOUT_SECS ]; do
  PENDING=$(gh api /repos/{owner}/{repo}/pulls/{number}/requested_reviewers \
    | jq '[.users[] | select(.login == "copilot-pull-request-reviewer[bot]")] | length')
  if [ "$PENDING" -eq 0 ]; then
    echo "Review complete."
    break
  fi
  echo "Waiting for review... (${ELAPSED}s elapsed)"
  sleep 15
  ELAPSED=$((ELAPSED + 15))
done
```

## Draft PR Creation

Create a draft PR for AI review when no PR exists on the current branch:

```bash
# Determine base branch
BASE=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')
BRANCH=$(git branch --show-current)

# Create draft PR
gh pr create --draft --base "$BASE" --head "$BRANCH" \
  --title "$(git log -1 --format=%s)" \
  --body "Draft PR for AI code review."
```

After creation, extract the PR number:

```bash
PR_NUMBER=$(gh pr view --json number --jq '.number')
```

## jq Filter: AI-Only Comments

Keep only comments from known AI reviewer bot usernames (opposite of the bot-exclusion filter):

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments --paginate \
  | jq '[.[] | select(
    (.user.login == "copilot-pull-request-reviewer[bot]" or .user.login == "gemini-code-assist[bot]")
    and .in_reply_to_id == null
    and (.line != null or .position != null)
  )]'
```

This filters to:
- Only AI reviewer comments (by username)
- Root comments only (excludes replies within threads)
- Active comments only (excludes outdated ones with no valid position)
