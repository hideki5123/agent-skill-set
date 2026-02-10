---
name: review-pr
description: Perform detailed code review on a GitHub pull request. Analyzes every changed file for bugs, security vulnerabilities, performance issues, design problems, and style nits. Produces a structured report with line-level comments tagged by category and severity, then optionally posts the review to GitHub. Use when the user asks to review a PR, review a pull request, do a code review on a PR, check a PR for issues, or mentions a GitHub PR URL or number in the context of reviewing. Trigger phrases include "review PR", "review pull request", "code review", "check this PR", "review #123", "review github.com/.../pull/...".
---

# PR Review

Perform a thorough, line-level code review of a GitHub pull request. Produce a detailed report categorizing each finding, then optionally post review comments to GitHub.

## Workflow

1. **Resolve the PR** — Determine the repo and PR number
2. **Fetch PR metadata and diff** — Get the full diff, description, and context
3. **Analyze each changed file** — Review every hunk for issues
4. **Generate the report** — Structured markdown with line-level findings
5. **Post to GitHub** (if requested) — Submit as a PR review with inline comments

## Step 1: Resolve the PR

Accept either format:
- **Full URL**: `https://github.com/owner/repo/pull/123` — extract owner, repo, PR number
- **PR number only**: `123` or `#123` — use the current git remote to determine owner/repo

To resolve from the current repo:
```bash
gh pr view <number> --json number,title,url,baseRefName,headRefName,body,author,files,additions,deletions,changedFiles
```

If neither is provided, ask the user.

## Step 2: Fetch PR Data

Fetch all required data in parallel:

```bash
# Full diff
gh pr diff <number>

# PR metadata (title, body, base branch, head branch, author)
gh pr view <number> --json title,body,baseRefName,headRefName,author,labels,reviewDecision,commits

# Changed file list with stats
gh pr view <number> --json files

# PR comments and existing reviews (to avoid duplicating feedback)
gh pr view <number> --json comments,reviews
```

For large PRs (>20 files or >1000 lines changed), inform the user and offer to focus on specific files or directories.

## Step 3: Analyze Each Changed File

For every file in the diff, review each hunk. Read `references/review-categories.md` for the full category and severity definitions, security checklist, and comment format examples.

### Review Checklist

For each changed line/block, check:

**Correctness (bug)**
- Logic errors, off-by-one, wrong operator, incorrect condition
- Null/undefined dereference, unhandled promise rejection
- Wrong variable used, copy-paste errors
- Missing `break`/`return`, incorrect loop bounds
- Race conditions, deadlocks, missing synchronization

**Security**
- Injection flaws (SQL, command, XSS, etc.)
- Hardcoded secrets, API keys, passwords
- Missing authentication/authorization checks
- Insecure crypto, weak randomness
- Path traversal, SSRF, open redirects

**Performance (perf)**
- N+1 queries, unnecessary re-renders
- O(n^2) or worse where O(n) is feasible
- Missing memoization for expensive computations
- Unbounded growth (memory leaks, missing cleanup)
- Blocking the event loop / main thread

**Design**
- Violation of project conventions (check existing patterns)
- Tight coupling, missing abstraction, god objects
- Breaking backward compatibility without migration
- Missing or inadequate error handling
- Wrong layer (business logic in controller, SQL in UI, etc.)

**Better-to-have**
- Missing test coverage for new/changed code
- Missing or misleading documentation for public APIs
- Edge cases not handled (empty input, max values, unicode)
- Magic numbers/strings that should be constants
- Error messages that don't help debugging

**Nitpick**
- Style inconsistencies with rest of codebase
- Unnecessary `let` where `const` suffices
- Verbose code that could be simplified
- Comment/naming improvements

**Question**
- Unclear intent — ask before assuming
- Suspicious patterns that might be intentional

### Context-Aware Review

- Check the PR description for context — understand the author's intent
- Look at the base branch to understand existing patterns and conventions
- Consider the broader changeset — a change in one file may affect another
- Don't flag issues in unchanged code unless the PR makes them worse

## Step 4: Generate the Report

Use this report structure:

```markdown
# PR Review: <PR title> (#<number>)

**Author**: @<author>
**Branch**: `<head>` → `<base>`
**Files changed**: <N> | **Additions**: +<N> | **Deletions**: -<N>

## Summary

<2-4 sentence overview of the PR's purpose and overall quality.
Mention the most important findings upfront.>

## Verdict

<APPROVE | REQUEST_CHANGES | COMMENT>

- **Critical**: <count>
- **Major**: <count>
- **Minor**: <count>
- **Trivial**: <count>
- **Questions**: <count>

## Findings

### <filename> (lines X-Y)

#### 1. [category|severity] Short title

**Line(s)**: `<file>#L<start>-L<end>`

```<lang>
// the problematic code from the diff
```

**Issue**: Explanation of what's wrong and what impact it has.

**Suggested fix**:
```<lang>
// corrected code
```

---

(repeat for each finding, grouped by file)

## Files with No Issues

- `path/to/clean/file.ts` — Looks good
- `path/to/another.ts` — Clean

## General Observations

<Optional section for cross-cutting concerns, patterns across files,
or architectural feedback that doesn't tie to a specific line.>
```

### Verdict Logic

- **REQUEST_CHANGES** if any `critical` finding exists
- **REQUEST_CHANGES** if 3+ `major` findings exist
- **COMMENT** if only `major` (1-2), `minor`, or `trivial` findings exist
- **APPROVE** if only `trivial`/`nitpick` findings and no questions

## Step 5: Post to GitHub (Optional)

Ask the user before posting. When confirmed, post the review:

```bash
# Submit the overall review
gh pr review <number> --<approve|request-changes|comment> --body "<summary>"
```

For inline comments, post each as a review comment on the specific file and line:

```bash
# Post inline comment on specific line
gh api repos/<owner>/<repo>/pulls/<number>/comments \
  --method POST \
  -f body="<comment body>" \
  -f commit_id="<head_sha>" \
  -f path="<file_path>" \
  -F line=<line_number> \
  -f side="RIGHT"
```

To post multiple inline comments as a single review (preferred — avoids notification spam):

```bash
gh api repos/<owner>/<repo>/pulls/<number>/reviews \
  --method POST \
  -f body="<overall summary>" \
  -f event="<APPROVE|REQUEST_CHANGES|COMMENT>" \
  -f commit_id="<head_sha>" \
  --input <json_file_with_comments>
```

The JSON input for `--input` should have a `comments` array:
```json
{
  "body": "Overall review summary",
  "event": "COMMENT",
  "comments": [
    {
      "path": "src/foo.ts",
      "line": 42,
      "side": "RIGHT",
      "body": "[bug|critical] Off-by-one in pagination\n\n..."
    }
  ]
}
```

Get the head commit SHA with:
```bash
gh pr view <number> --json headRefOid --jq '.headRefOid'
```

## References

- `references/review-categories.md` — Full category definitions, severity levels, security checklist, and comment format examples. Read this before starting the review.
