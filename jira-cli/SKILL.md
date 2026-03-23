---
name: jira-cli
description: >
  Use @pchuri/jira-cli to view, search, create, update, and delete
  Jira issues, comments, sprints, and projects from the terminal.
  Prefer this skill over `mcp__claude_ai_Atlassian__*` MCP tools when you need:
  JQL search, sprint/board management, markdown export, file-based descriptions,
  issue deletion, comment management, or shell pipelines.
  Trigger phrases include "jira", "jira-cli", "jira issue",
  "create jira issue", "search jira", "jira sprint", "jira board",
  "jira project", "jira comment", "jira JQL", "list jira issues",
  "view jira issue", "jira backlog".
---

# jira-cli Skill

A CLI tool for Atlassian Jira. Lets you view, search, create, update, and delete issues, manage comments, sprints, and projects from the terminal or from an agent.

## Installation

```sh
npm install -g @pchuri/jira-cli
jira --version   # verify install
```

## Configuration

**Preferred for agents — environment variables (no interactive prompt):**

| Variable | Description | Example |
|---|---|---|
| `JIRA_HOST` | Your Jira hostname | `company.atlassian.net` |
| `JIRA_API_TOKEN` | API token or personal access token | `ATATT3x...` |
| `JIRA_USERNAME` | Email address (Basic auth only) | `user@company.com` |
| `JIRA_API_VERSION` | API version: `auto` (default), `2`, or `3` | `auto` |

Legacy env vars (`JIRA_DOMAIN`, `JIRA_USERNAME`, `JIRA_API_TOKEN`) are also supported.

**Bearer token authentication (recommended):**

```sh
jira config --server https://company.atlassian.net --token your-api-token
```

**Basic authentication (legacy):**

```sh
jira config --server https://company.atlassian.net --username user@company.com --token your-api-token
```

**View / modify config:**

```sh
jira config --show                    # display current settings
jira config set <key> <value>         # set individual config value
```

Config is stored in platform-specific directories (e.g. `~/.config/jira-cli/` on Linux/macOS, `%APPDATA%\jira-cli\` on Windows).

**Cloud vs Server/DC:**
- Atlassian Cloud (`*.atlassian.net`): use Bearer token auth with email + API token
- Self-hosted / Data Center: use Bearer token auth with a personal access token
- API version auto-detection tries v3 first, falls back to v2

**Non-interactive setup for agents:**

```sh
export JIRA_HOST="company.atlassian.net"
export JIRA_API_TOKEN="your-api-token"
# Optional for Basic auth:
export JIRA_USERNAME="user@company.com"
```

---

## Constraints

- Always use `jira` CLI — it must be globally installed via npm (`@pchuri/jira-cli`).
- Configuration must already be set up (env vars or `jira config`). If not, guide the user through setup.
- For simple Jira issue view/create/edit operations where `mcp__claude_ai_Atlassian__*` MCP tools suffice, prefer MCP (less overhead, no shell spawning). Switch to CLI for features MCP lacks.

## Preflight Check

Before running any jira command, verify the installation:

```bash
jira --version
```

If this fails:
- **"command not found"** — jira-cli is not installed.
  Suggest: `npm install -g @pchuri/jira-cli`
- **"No configuration found"** / connection errors — Config not set up.
  Suggest: `jira config --server <url> --token <token>` or set env vars (`JIRA_HOST`, `JIRA_API_TOKEN`)

## When to Use CLI vs. MCP

| Capability | `mcp__claude_ai_Atlassian__*` MCP | `jira` CLI |
|------------|-----------------------------------|------------|
| View issue | Yes — `getJiraIssue` | Yes — `jira issue view` |
| Search (JQL) | Yes — `searchJiraIssuesUsingJql` | Yes — `jira issue list --jql` |
| Create issue | Yes — `createJiraIssue` | Yes — `jira issue create` |
| Edit issue | Yes — `editJiraIssue` | Yes — `jira issue edit` |
| Add comment | Yes — `addCommentToJiraIssue` | Yes — `jira issue comment add` |
| Transition issue | Yes — `transitionJiraIssue` | No |
| Get transitions | Yes — `getTransitionsForJiraIssue` | No |
| Add worklog | Yes — `addWorklogToJiraIssue` | No |
| Issue links | Yes — `createIssueLink` | No |
| **Delete issue** | No | Yes — `jira issue delete` |
| **List comments** | No | Yes — `jira issue comment list` |
| **Edit comment** | No | Yes — `jira issue comment edit` |
| **Delete comment** | No | Yes — `jira issue comment delete` |
| **Sprint management** | No | Yes — `jira sprint list/active` |
| **Board listing** | No | Yes — `jira sprint boards` |
| **Project components** | No | Yes — `jira project components` |
| **Project versions** | No | Yes — `jira project versions` |
| **Markdown export** | No | Yes — `--format markdown` |
| **File-based descriptions** | No | Yes — `--description-file` |
| **Internal comments** | No | Yes — `--internal` flag |
| **Shell pipelines** | No | Yes — pipe to `jq`, `grep`, etc. |
| **API version control** | No | Yes — `JIRA_API_VERSION` env var |

**Rule of thumb:** Use MCP for simple view/create/edit and transitions. Use CLI for delete, comments management, sprints, boards, project details, markdown export, and shell pipelines.

## Quick Reference

| Action | Command |
|--------|---------|
| View issue | `jira issue view PROJ-123` |
| List issues | `jira issue list --project PROJ --limit 20` |
| Search with JQL | `jira issue list --jql "assignee = currentUser() AND status != Done"` |
| Create issue | `jira issue create --project PROJ --type Bug --summary "Fix login"` |
| Edit issue | `jira issue edit PROJ-123 --summary "Updated title"` |
| Delete issue | `jira issue delete PROJ-123 --force` |
| Add comment | `jira issue comment add PROJ-123 "Looks good"` |
| List comments | `jira issue comment list PROJ-123` |
| Edit comment | `jira issue comment edit <commentId> "Updated text"` |
| Delete comment | `jira issue comment delete <commentId> --force` |
| List projects | `jira project list` |
| View project | `jira project view PROJ` |
| Project components | `jira project components PROJ` |
| Project versions | `jira project versions PROJ` |
| List boards | `jira sprint boards` |
| List sprints | `jira sprint list --board <boardId>` |
| Active sprint | `jira sprint active --board <boardId>` |
| Show config | `jira config --show` |

---

## Commands Reference

### `config`

Configure authentication and connection settings.

**Bearer token (recommended):**

```sh
jira config --server https://company.atlassian.net --token your-api-token
```

**Basic auth:**

```sh
jira config --server https://company.atlassian.net --username user@company.com --token your-api-token
```

**View config:**

```sh
jira config --show
```

**Set individual value:**

```sh
jira config set <key> <value>
```

---

### `issue view <key>`

View issue details. Alias: `issue show`.

```sh
jira issue view <KEY> [--format terminal|markdown] [--output <path>]
```

| Option | Default | Description |
|---|---|---|
| `--format` | `terminal` | Output format: `terminal` or `markdown` |
| `--output` | — | Export to file |

```sh
jira issue view PROJ-123
jira issue view PROJ-123 --format markdown
jira issue view PROJ-123 --format markdown --output ./issue.md
```

---

### `issue list`

List issues with filters. Alias: `issue ls`, `issue --list`.

```sh
jira issue list [--project <key>] [--assignee <user>] [--status <status>] [--jql <query>] [--limit <number>]
```

| Option | Default | Description |
|---|---|---|
| `--project` | — | Filter by project key |
| `--assignee` | — | Filter by assignee |
| `--status` | — | Filter by status |
| `--jql` | — | JQL query for advanced filtering |
| `--limit` | — | Maximum number of results |

```sh
jira issue list --project PROJ
jira issue list --project PROJ --status "In Progress" --limit 10
jira issue list --jql "assignee = currentUser() AND sprint in openSprints()"
jira issue list --assignee user@company.com --status Done
```

---

### `issue create`

Create a new issue.

```sh
jira issue create --project <KEY> --type <TYPE> --summary <TEXT> [--description <text>] [--description-file <path>] [--assignee <user>] [--priority <level>]
```

| Option | Required | Description |
|---|---|---|
| `--project` | Yes | Project key |
| `--type` | Yes | Issue type (Bug, Task, Story, Epic, etc.) |
| `--summary` | Yes | Issue summary/title |
| `--description` | No | Issue description (inline text) |
| `--description-file` | No | Load description from file |
| `--assignee` | No | Assign to user |
| `--priority` | No | Priority level (Highest, High, Medium, Low, Lowest) |

```sh
jira issue create --project PROJ --type Bug --summary "Login button broken"
jira issue create --project PROJ --type Story --summary "Add search" --description "As a user, I want to search..."
jira issue create --project PROJ --type Task --summary "Refactor auth" --description-file ./spec.md --assignee user@company.com --priority High
```

Outputs the new issue key on success.

---

### `issue edit <key>`

Edit/update an existing issue. Alias: `issue update`.

At least one of `--summary`, `--description`, `--description-file`, `--assignee`, or `--priority` is required.

```sh
jira issue edit <KEY> [--summary <text>] [--description <text>] [--description-file <path>] [--assignee <user>] [--priority <level>]
```

| Option | Description |
|---|---|
| `--summary` | New summary/title |
| `--description` | New description (inline text) |
| `--description-file` | Load description from file |
| `--assignee` | Reassign to user |
| `--priority` | Change priority |

```sh
jira issue edit PROJ-123 --summary "Updated title"
jira issue edit PROJ-123 --description-file ./updated-spec.md
jira issue edit PROJ-123 --assignee user@company.com --priority High
```

---

### `issue delete <key>`

Delete an issue.

```sh
jira issue delete <KEY> --force
```

| Option | Description |
|---|---|
| `--force` | Required — skip confirmation prompt |

```sh
jira issue delete PROJ-123 --force
```

---

### `issue comment add <key> <text>`

Add a comment to an issue. Alias: `issue c add`.

```sh
jira issue comment add <KEY> "<text>" [--file <path>] [--internal]
```

| Option | Description |
|---|---|
| `--file` | Load comment content from file |
| `--internal` | Mark as internal/restricted comment |

```sh
jira issue comment add PROJ-123 "This looks good, merging now"
jira issue comment add PROJ-123 "" --file ./review-notes.md
jira issue comment add PROJ-123 "Internal note" --internal
```

---

### `issue comment list <key>`

List comments for an issue. Alias: `issue c list`.

```sh
jira issue comment list <KEY> [--format table|json]
```

| Option | Default | Description |
|---|---|---|
| `--format` | `table` | Output format: `table` or `json` |

```sh
jira issue comment list PROJ-123
jira issue comment list PROJ-123 --format json
```

---

### `issue comment edit <commentId> <text>`

Edit an existing comment.

```sh
jira issue comment edit <ID> "<text>" [--file <path>]
```

| Option | Description |
|---|---|
| `--file` | Load updated content from file |

```sh
jira issue comment edit 12345 "Updated comment text"
```

---

### `issue comment delete <commentId>`

Delete a comment.

```sh
jira issue comment delete <ID> --force
```

| Option | Description |
|---|---|
| `--force` | Required — skip confirmation prompt |

```sh
jira issue comment delete 12345 --force
```

---

### `project list`

List all accessible Jira projects.

```sh
jira project list [--type <type>] [--category <category>]
```

| Option | Description |
|---|---|
| `--type` | Filter by project type |
| `--category` | Filter by project category |

```sh
jira project list
jira project list --type software
```

---

### `project view <key>`

View project details.

```sh
jira project view <KEY>
```

```sh
jira project view PROJ
```

---

### `project components <key>`

List components of a project.

```sh
jira project components <KEY>
```

```sh
jira project components PROJ
```

---

### `project versions <key>`

List versions/releases of a project.

```sh
jira project versions <KEY>
```

```sh
jira project versions PROJ
```

---

### `sprint boards`

List all Scrum/Kanban boards.

```sh
jira sprint boards
```

---

### `sprint list`

List sprints for a board.

```sh
jira sprint list [--board <id>] [--state <state>] [--active]
```

| Option | Description |
|---|---|
| `--board` | Board ID (required when multiple boards exist) |
| `--state` | Filter by sprint state (active, closed, future) |
| `--active` | Show only active sprints |

```sh
jira sprint list --board 42
jira sprint list --board 42 --state active
jira sprint list --active
```

---

### `sprint active`

Show the active sprint and its issues.

```sh
jira sprint active [--board <id>]
```

| Option | Description |
|---|---|
| `--board` | Board ID (required when multiple boards exist) |

```sh
jira sprint active
jira sprint active --board 42
```

---

## Common Agent Workflows

### Search and filter issues

```sh
# Find all bugs assigned to me in the current sprint
jira issue list --jql "assignee = currentUser() AND sprint in openSprints() AND type = Bug"

# Find unresolved issues in a project
jira issue list --project PROJ --status "To Do" --limit 50

# Find issues updated recently
jira issue list --jql "project = PROJ AND updated >= -7d ORDER BY updated DESC"
```

### Create issue with file-based description

```sh
# Write description to a temp file, then create
cat > /tmp/issue-desc.md << 'EOF'
## Problem
The login page crashes on mobile Safari.

## Steps to Reproduce
1. Open the app on iOS Safari
2. Tap the login button
3. App crashes

## Expected Behavior
Login form should appear.
EOF

jira issue create --project PROJ --type Bug --summary "Mobile Safari crash on login" --description-file /tmp/issue-desc.md --priority High
```

### Sprint review workflow

```sh
# 1. Find the active sprint
jira sprint active --board 42

# 2. List all issues in the sprint
jira issue list --jql "sprint in openSprints() AND project = PROJ"

# 3. Export each issue as markdown for review
jira issue view PROJ-123 --format markdown --output ./sprint-review/PROJ-123.md
```

### Bulk comment on issues

```sh
# Add the same comment to multiple issues
for key in PROJ-101 PROJ-102 PROJ-103; do
  jira issue comment add "$key" "Reviewed and approved for release"
done
```

### Process issues as JSON

```sh
jira issue comment list PROJ-123 --format json | jq '.[].body'
```

---

## Agent Tips

- **Always use `--force`** on destructive commands (`delete`, `comment delete`) to avoid interactive prompts blocking the agent.
- **Prefer `--format markdown`** when exporting issues for agent processing.
- **Use `--format json`** on comment lists for machine-parseable output.
- **Use `--description-file`** for longer descriptions — write to a temp file first, then reference it.
- **JQL tips**: Use `currentUser()` for assignee, `openSprints()` for active sprint, `-7d` for relative dates. Wrap JQL in double quotes.
- **ANSI color codes**: stdout may contain ANSI escape sequences. Pipe through `| cat` or use `NO_COLOR=1` if your downstream tool doesn't handle them.
- **API version**: If you get unexpected errors, try setting `JIRA_API_VERSION=2` — some self-hosted instances only support v2.
- **Issue types**: Common types are `Bug`, `Task`, `Story`, `Epic`, `Sub-task`. Use `jira project view <KEY>` to see available types for a project.

## Error Patterns

| Error | Cause | Fix |
|---|---|---|
| `No configuration found` | No config and no env vars set | Set env vars or run `jira config --server ... --token ...` |
| `401 Unauthorized` | Invalid or expired token | Regenerate API token and reconfigure |
| `404 Not Found` | Issue key doesn't exist or no permissions | Verify the issue key and user permissions |
| `Field 'issuetype' required` | Missing `--type` on create | Add `--type Bug/Task/Story` |
| `Field 'summary' required` | Missing `--summary` on create | Add `--summary "..."` |
| `Board not found` | Invalid board ID for sprint commands | Run `jira sprint boards` to list available boards |
| `API v3 not supported` | Self-hosted instance on older Jira | Set `JIRA_API_VERSION=2` |
| `command not found: jira` | CLI not installed | Run `npm install -g @pchuri/jira-cli` |

## Behavior Scenarios

### Scenario 1: View a Jira issue

```gherkin
Given jira-cli is installed and configured
When the user asks to view a Jira issue (by key like PROJ-123)
Then run `jira issue view PROJ-123 --format markdown`
And present the issue details
```

### Scenario 2: Search Jira issues

```gherkin
Given jira-cli is installed and configured
When the user asks to search Jira for issues
Then build a JQL query or use filter flags
And run `jira issue list --jql "<query>" --limit 20`
And present matching issues with keys, summaries, and statuses
```

### Scenario 3: Create or update an issue

```gherkin
Given jira-cli is installed and configured
When the user asks to create or update a Jira issue
Then use `--description-file` for longer content (write to a temp file first)
And report the issue key on success
```

### Scenario 4: Manage sprint/backlog

```gherkin
Given jira-cli is installed and configured
When the user asks about sprints or backlog
Then run `jira sprint boards` to find the board
And run `jira sprint active --board <id>` or `jira sprint list --board <id>`
And present sprint details and issue lists
```

### Scenario 5: jira-cli not installed

```gherkin
Given jira-cli is not installed or not configured
When the user asks to perform any Jira CLI operation
Then check with `jira --version`
And guide the user to install: `npm install -g @pchuri/jira-cli`
And guide config setup: `jira config --server <url> --token <token>` or set env vars
```

### Scenario 6: Comment management

```gherkin
Given jira-cli is installed and configured
When the user asks to add, list, edit, or delete comments
Then use `jira issue comment add/list/edit/delete` accordingly
And use `--force` on destructive operations to avoid interactive prompts
And use `--file` for longer comment content
```
