# GitHub PR Review API Reference

## Create a Pull Request Review

Submit a batch review with inline comments in a single API call.

```
POST /repos/{owner}/{repo}/pulls/{number}/reviews
```

### Request Body

```json
{
  "commit_id": "HEAD_SHA",
  "body": "Overall review summary.",
  "event": "COMMENT",
  "comments": [
    {
      "path": "src/api.ts",
      "line": 42,
      "side": "RIGHT",
      "body": "Consider adding error handling here."
    },
    {
      "path": "src/db.ts",
      "start_line": 10,
      "line": 15,
      "side": "RIGHT",
      "body": "This query may be vulnerable to SQL injection.\n\n```suggestion\nconst result = await db.query('SELECT * FROM users WHERE id = $1', [userId]);\n```"
    }
  ]
}
```

### Key Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `commit_id` | string | No | SHA of the commit to review. Defaults to latest. |
| `body` | string | No | Top-level review body (summary). |
| `event` | string | Yes | `COMMENT`, `APPROVE`, or `REQUEST_CHANGES`. |
| `comments` | array | No | Inline review comments (see below). |

### Comment Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `path` | string | Yes | File path relative to repo root. |
| `line` | int | Yes | Line number in the diff (end line for multi-line). |
| `side` | string | No | `LEFT` (old) or `RIGHT` (new). Default: `RIGHT`. |
| `start_line` | int | No | Start line for multi-line comments. |
| `start_side` | string | No | Side for start_line. Default: matches `side`. |
| `body` | string | Yes | Comment body (markdown). Supports suggestion blocks. |

### Event Types

| Event | Effect |
|-------|--------|
| `COMMENT` | Neutral review — no approval or rejection. |
| `APPROVE` | Approve the PR. Requires write access. |
| `REQUEST_CHANGES` | Block merge until resolved. Requires write access. |

## Submitting via `gh api`

Use `--input -` to pipe JSON for complex request bodies:

```bash
# Build the JSON payload
REVIEW_JSON=$(cat <<'ENDJSON'
{
  "event": "COMMENT",
  "body": "Review summary here.",
  "comments": [
    {
      "path": "src/api.ts",
      "line": 42,
      "side": "RIGHT",
      "body": "Consider adding error handling."
    }
  ]
}
ENDJSON
)

echo "$REVIEW_JSON" | gh api --method POST \
  /repos/{owner}/{repo}/pulls/{number}/reviews \
  --input -
```

## Fetching the PR Diff

```bash
# Full diff
gh pr diff <number>

# Diff for a specific file
gh pr diff <number> -- <file_path>
```

## Fetching PR Metadata

```bash
# Basic info
gh pr view <number> --json number,title,state,author,baseRefName,headRefName,isDraft,additions,deletions,changedFiles

# Changed files list
gh pr view <number> --json files --jq '.files[].path'
```

## Fetching Existing Reviews (for dedup)

```bash
gh api /repos/{owner}/{repo}/pulls/{number}/reviews \
  | jq '[.[] | {id: .id, user: .user.login, state: .state, submitted_at: .submitted_at}]'
```

## Error Handling

| Status | Meaning | Recovery |
|--------|---------|----------|
| 200 | Success | Review submitted. |
| 403 | No permission | User lacks write access or is not a collaborator. |
| 404 | PR not found | Check owner/repo/number. |
| 422 | Validation error | Invalid `path`, `line` outside diff range, or bad `event`. |
| 429 | Rate limited | Retry with exponential backoff (check `Retry-After` header). |

### Common 422 Causes

- `path` does not exist in the PR diff
- `line` is outside the hunk range for the given file
- `start_line` > `line`
- `event` is `APPROVE`/`REQUEST_CHANGES` but user is the PR author
- Empty `comments` array with no `body`

## Suggestion Block Format

Include code suggestions in comment bodies:

````markdown
This could be simplified:

```suggestion
const result = items.filter(Boolean);
```
````

GitHub renders this as an "Apply suggestion" button for the PR author.
