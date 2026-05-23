---
name: slack-cli
description: >
  Operate Slack from the terminal via `slack-cli` (@urugus/slack-cli).
  Send messages, check unreads, search history, upload files, manage reactions/pins,
  schedule messages, and manage channels — all through Bash commands.
  Prefer this skill over `mcp__slack__*` MCP tools when you need: scheduling,
  unreads, search with pagination, reactions/pins, file uploads, multi-workspace
  profiles, canvas operations, or jq pipelines for filtered output.
  Trigger phrases include "slack-cli", "slack cli", "send slack message",
  "check slack unreads", "slack history", "search slack", "schedule slack message",
  "slack channel", "upload to slack", "slack reactions", "slack pins",
  "slack canvas", "slack users", "slack unread".
---

# Slack CLI Skill

Interact with Slack workspaces via `slack-cli` in Bash. This skill covers messaging,
channels, history, search, file uploads, reactions, pins, users, scheduled messages,
and canvas operations.

## Constraints

- Always use `slack-cli` — it must be globally installed via npm.
- A Slack Bot Token must already be configured. If not, guide the user through setup.
- Token security: tokens are encrypted with AES-256-GCM at rest. Never log or echo tokens.
- For simple read/post operations where `mcp__slack__*` MCP tools suffice, prefer MCP
  (less overhead, no shell spawning). Switch to CLI for features MCP lacks.

## Preflight Check

Before running any slack-cli command, verify the installation:

```bash
slack-cli --version
```

If this fails:
- **"command not found"** — slack-cli is not installed.
  Suggest: `npm install -g @urugus/slack-cli`
- **"No token configured"** or auth errors — Token not set up.
  Suggest: `slack-cli config set` (interactive) or
  `printf '%s\n' "$SLACK_BOT_TOKEN" | slack-cli config set --token-stdin`

## When to Use CLI vs. MCP

| Capability | `mcp__slack__*` MCP | `slack-cli` CLI |
|------------|---------------------|-----------------|
| Post a message | Yes — `slack_post_message` | Yes — `slack-cli send` |
| Reply to thread | Yes — `slack_reply_to_thread` | Yes — `slack-cli send --thread` |
| Read channel history | Yes — `slack_get_channel_history` | Yes — `slack-cli history` |
| List channels | Yes — `slack_list_channels` | Yes — `slack-cli channels` |
| Get user profile | Yes — `slack_get_user_profile` | Yes — `slack-cli users info` |
| **Edit/delete messages** | No | Yes — `slack-cli edit` / `delete` |
| **Schedule messages** | No | Yes — `slack-cli send --at` / `--after` |
| **Check unreads** | No | Yes — `slack-cli unread` |
| **Mark as read** | No | Yes — `slack-cli unread --mark-read` |
| **Search messages** | No | Yes — `slack-cli search` |
| **Reactions** | Yes — `slack_add_reaction` | Yes — `slack-cli reaction add/remove` |
| **Pins** | No | Yes — `slack-cli pin add/remove/list` |
| **File uploads** | No | Yes — `slack-cli upload` |
| **Canvas read/list** | No | Yes — `slack-cli canvas` |
| **Multi-workspace** | No | Yes — `--profile` flag |
| **JSON output + jq** | No | Yes — `--format json` |

**Rule of thumb:** Use MCP for simple post/read. Use CLI for everything else.

## Output Format Guidance

slack-cli supports three output formats via `--format`:

| Format | Flag | Best for |
|--------|------|----------|
| Table | `--format table` (default) | Human reading in terminal |
| Simple | `--format simple` | Shell pipelines, `grep`, `awk` |
| JSON | `--format json` | Claude processing, `jq` filtering |

When Claude needs to process the output (parse channels, count unreads, extract timestamps),
always use `--format json` and pipe through `jq` for minimal context consumption.

```bash
# Good — filtered JSON, minimal context
slack-cli unread --format json | jq '.[] | select(.count > 5)'

# Avoid — table output wastes tokens on formatting
slack-cli unread --format table
```

## Quick Reference

| Action | Command |
|--------|---------|
| Send message | `slack-cli send -c CHANNEL -m "text"` |
| Send DM | `slack-cli send --user @name -m "text"` |
| Reply to thread | `slack-cli send -c CH -m "text" --thread TS` |
| Edit message | `slack-cli edit -c CH --ts TS -m "new text"` |
| Delete message | `slack-cli delete -c CH --ts TS` |
| Check all unreads | `slack-cli unread --format json` |
| Mark channel read | `slack-cli unread -c CH --mark-read` |
| Channel history | `slack-cli history -c CH --format json` |
| Search messages | `slack-cli search -q "query" --format json` |
| List channels | `slack-cli channels --format json` |
| Upload file | `slack-cli upload -c CH -f ./file.csv` |
| Add reaction | `slack-cli reaction add -c CH -t TS -e emoji` |
| Pin message | `slack-cli pin add -c CH -t TS` |
| Schedule message | `slack-cli send -c CH -m "text" --after 30` |
| List scheduled | `slack-cli scheduled list --format json` |
| List users | `slack-cli users list --format json` |
| Read canvas | `slack-cli canvas read -i CANVAS_ID` |
| Switch profile | `slack-cli config use PROFILE` |

## Common Workflows

### Check and summarize unreads

```bash
# Get unread counts as JSON
slack-cli unread --format json

# Filter channels with many unreads
slack-cli unread --format json | jq '.[] | select(.count > 5)'

# Get unread count only
slack-cli unread --count-only
```

After summarizing, mark as read:

```bash
slack-cli unread -c general --mark-read
```

### Send a message and reply to a thread

```bash
# Send to channel
slack-cli send -c general -m "Hello team"

# Send from file content
slack-cli send -c general -f ./announcement.md

# Reply to a specific thread (use the message timestamp)
slack-cli send -c general -m "Noted, thanks!" --thread 1234567890.123456

# Send DM by username or email
slack-cli send --user @alice -m "Quick question..."
slack-cli send --email alice@example.com -m "Check this out"
```

### Search messages

```bash
# Basic search
slack-cli search -q "deployment issue" --format json

# Search with Slack modifiers
slack-cli search -q "in:general from:@alice deploy" --format json

# Paginated search
slack-cli search -q "bug report" -n 20 --page 2 --format json

# Sort by timestamp
slack-cli search -q "release" --sort timestamp --sort-dir desc --format json
```

### Export channel history

```bash
# Recent history
slack-cli history -c general --format json

# History since a date
slack-cli history -c general --since "2026-03-01" --format json

# Last N messages
slack-cli history -c general -n 50 --format json

# Thread history
slack-cli history -c general --thread TS --format json

# Include permalinks
slack-cli history -c general --with-link --format json
```

### Schedule messages

```bash
# Schedule at absolute time (ISO 8601)
slack-cli send -c general -m "Reminder: standup in 5 min" --at "2026-03-14T09:55:00+09:00"

# Schedule relative (N minutes from now)
slack-cli send -c general -m "Follow up on PR" --after 30

# List scheduled messages
slack-cli scheduled list --format json

# Cancel a scheduled message
slack-cli scheduled cancel -c general --id Q12345
```

### Multi-workspace profiles

```bash
# Set up profiles
slack-cli config set --profile work --token-stdin <<< "$WORK_TOKEN"
slack-cli config set --profile personal --token-stdin <<< "$PERSONAL_TOKEN"

# Switch default profile
slack-cli config use work

# Use a profile for a single command
slack-cli send -c general -m "Hello" --profile personal

# List configured profiles
slack-cli config profiles
```

### File uploads and snippets

```bash
# Upload a file
slack-cli upload -c general -f ./report.csv

# Upload to a thread
slack-cli upload -c general -f ./screenshot.png -t TS

# Upload a code snippet
slack-cli upload -c dev --content 'console.log("hello")' --filename hello.js --filetype javascript
```

### Shell pipeline recipes

```bash
# Find channels matching a pattern
slack-cli channels --format json | jq '.[] | select(.name | test("dev"))'

# Get all users' display names
slack-cli users list --format json | jq '.[].display_name'

# Count messages per channel from search results
slack-cli search -q "keyword" --format json | jq 'group_by(.channel) | map({channel: .[0].channel, count: length})'
```

## Error Handling

| Symptom | Cause | Fix |
|---------|-------|-----|
| `command not found` | Not installed | `npm install -g @urugus/slack-cli` |
| `No token configured` | Missing config | `slack-cli config set` |
| `channel_not_found` | Wrong channel name/ID | Verify with `slack-cli channels` |
| `not_in_channel` | Bot not in channel | Invite bot to channel in Slack |
| `invalid_auth` | Token expired/revoked | Re-configure with `slack-cli config set` |
| `missing_scope` | Token lacks required scope | Add scope in Slack app settings |
| Rate limit / timeout | Too many requests | CLI has built-in retry with exponential backoff |

## References

For the full flag-by-flag reference of every subcommand, read `references/command-reference.md`.

## Behavior Scenarios

### Scenario 1: Send a Slack message

```gherkin
Given slack-cli is installed and configured
When the user asks to send a message to a Slack channel
Then run `slack-cli send -c <channel> -m "<message>"`
And report the result (timestamp of sent message)
```

### Scenario 2: Check unreads

```gherkin
Given slack-cli is installed and configured
When the user asks to check Slack unreads
Then run `slack-cli unread --format json`
And summarize channels with unread messages and counts
```

### Scenario 3: Search Slack messages

```gherkin
Given slack-cli is installed and configured
When the user asks to search Slack for a term
Then run `slack-cli search -q "<term>" --format json`
And present matching messages with channel, sender, and timestamp
```

### Scenario 4: slack-cli not installed

```gherkin
Given slack-cli is not installed or not configured
When the user asks to perform any Slack CLI operation
Then check with `slack-cli --version`
And guide the user to install: `npm install -g @urugus/slack-cli`
And guide token setup: `slack-cli config set`
```

### Scenario 5: Multi-workspace operation

```gherkin
Given the user works with multiple Slack workspaces
When the user specifies a workspace or profile
Then use the `--profile <name>` flag on the command
And if no profile exists, guide setup with `slack-cli config set --profile <name>`
```
