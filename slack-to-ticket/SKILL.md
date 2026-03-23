---
name: slack-to-ticket
description: >
  Create Jira tickets from Slack conversations, optionally with Confluence documentation pages.
  Reads Slack threads/channels/search results via slack-cli, analyzes the conversation to extract
  problems, participants, decisions, and action items, then creates a Jira issue via jira-cli
  with the conversation context. For long or complex conversations (>15 messages), recommends
  creating a Confluence documentation page via confluence-cli. Supports input as Slack permalink
  URL, channel name, thread timestamp, or search query. Presents a draft for interactive review
  before creating. Trigger phrases include "slack to ticket", "slack-to-ticket",
  "create ticket from slack", "jira ticket from slack", "create ticket from #channel",
  "create ticket from thread", "slack conversation to jira", "ticket from slack thread",
  "jira from slack", "slack to jira", "create issue from slack".
---

# Slack to Ticket

Create Jira tickets from Slack conversations with optional Confluence documentation.

## Constraints

- Never create a ticket without user review and approval
- Always include the Slack permalink in the ticket description
- Always offer to post a summary back to the Slack thread after ticket creation
- Recommend Confluence page when conversation exceeds 15 messages, but always ask for approval
- Use `--format json` for all slack-cli output and pipe through `jq` when filtering

## Phase 0: Preflight

Check required tools. Stop if any required tool is missing.

```bash
# Required
slack-cli --version
jira --version

# Optional — warn if missing, don't stop
confluence --version
```

If a tool is missing, report:
- `slack-cli`: Install with `npm install -g @urugus/slack-cli`, then configure with `slack-cli config set`
- `jira`: Install with `npm install -g @pchuri/jira-cli`, then configure with `jira config --server URL --token TOKEN`
- `confluence`: Install with `npm install -g @urugus/confluence-cli`, then configure with `confluence config set`

## Phase 1: Parse Input & Fetch Conversation

Determine the input mode from the user's message. Read `references/input-parsing.md` for URL pattern details.

### Mode A: Slack Permalink URL (primary)

Parse the URL to extract channel ID and thread timestamp:

```bash
# URL: https://myteam.slack.com/archives/C0123ABCDEF/p1711234567890123
# channel_id = C0123ABCDEF
# thread_ts = 1711234567.890123 (insert dot before last 6 digits, strip 'p')

slack-cli history -c C0123ABCDEF --thread 1711234567.890123 --with-link --format json
```

If the URL contains `?thread_ts=`, use that as the thread root instead.

### Mode B: Channel Name

```bash
slack-cli history -c <channel-name> -n 30 --with-link --format json
```

Present the messages and ask the user to confirm scope or narrow with a count/date.

### Mode C: Search Query

```bash
slack-cli search -q "<query>" --format json
```

Present matching messages grouped by channel/thread. Ask user to select relevant ones.

### Mode D: Channel + Date Range

```bash
slack-cli history -c <channel-name> --since "<YYYY-MM-DD>" --with-link --format json
```

### After fetching

Count the messages. If count > 15, set `confluence_recommended = true` for Phase 3.

Extract the first message's permalink as the canonical Slack link for the ticket.

## Phase 2: Analyze Conversation

Analyze the fetched messages to extract:

1. **Problem / Request**: The core issue or ask
2. **Key Participants**: Who is involved (names from messages)
3. **Decisions**: Any conclusions or agreements reached
4. **Action Items**: Explicit or implied next steps with owners
5. **Urgency Signals**: Keywords that indicate priority

Read `references/classification-heuristics.md` for keyword-to-type and keyword-to-priority mapping tables.

Auto-classify:
- **Issue Type**: Bug, Story, Task, or Epic based on conversation keywords
- **Priority**: Highest, High, Medium (default), Low, or Lowest based on urgency signals

## Phase 3: Draft Ticket

Compose the ticket draft. Read `references/description-template.md` for the description template.

Present to the user:

```
## Draft Jira Ticket

**Project**: [ask user if unknown — run `jira project list` to show options]
**Type**: <auto-detected> (detected: "<keywords>")
**Priority**: <auto-detected> (detected: "<keywords>")
**Summary**: <generated — under 80 chars>
**Assignee**: [suggest from participants, or leave blank]

### Description Preview
[rendered description from template]

---
[Confluence recommended — conversation has NN messages] ← only if > 15 messages
```

If the Jira project is unknown, run `jira project list` and present options to the user.

## Phase 4: User Review

Ask the user to review the draft. They can:
1. **Approve** as-is
2. **Modify** any field (type, priority, summary, description, project, assignee)
3. **Add/skip Confluence page** (if recommended or requested)
4. **Cancel** — clean exit, nothing created

Loop on modifications until the user approves or cancels.

## Phase 5: Create Jira Ticket

Write the description to a temp file and create the issue:

```bash
cat > /tmp/slack-ticket-desc.md << 'JIRA_DESC'
<generated description from template>
JIRA_DESC

jira issue create \
  --project <KEY> \
  --type <TYPE> \
  --summary "<SUMMARY>" \
  --description-file /tmp/slack-ticket-desc.md \
  --priority <PRIORITY> \
  [--assignee <EMAIL>]
```

Capture the returned issue key (e.g., `PROJ-456`).

If the command fails, report the error and preserve the draft so the user can retry or fix.

## Phase 6: Create Confluence Page (Optional)

Only proceed if the user approved a Confluence page in Phase 4.

Read `references/confluence-template.md` for the page template.

```bash
cat > /tmp/slack-ticket-confluence.md << 'CONF_PAGE'
<generated page content from template>
CONF_PAGE

confluence create "[ISSUE-KEY] <Summary>" <SPACEKEY> \
  --file /tmp/slack-ticket-confluence.md --format markdown
```

If Confluence space key is unknown, run `confluence spaces` and present options.

After creating the page, update the Jira ticket to include the Confluence link:

```bash
# Append Confluence link to description
echo -e "\n\n## Documentation\n[Confluence Page](<confluence-url>)" >> /tmp/slack-ticket-desc.md

jira issue edit <ISSUE-KEY> --description-file /tmp/slack-ticket-desc.md
```

## Phase 7: Summary & Slack Notification

Report the results:

```
## Created

- **Jira**: [PROJ-456](<jira-url>) — <summary>
- **Confluence**: [Page title](<confluence-url>) ← only if created
- **Source**: [Slack thread](<permalink>)
```

Then **always offer** to post a summary back to the Slack thread:

```
Post summary to the Slack thread?
→ "Jira ticket created: PROJ-456 — <summary>"
```

If the user approves:

```bash
slack-cli send -c <channel> \
  -m "Jira ticket created: <ISSUE-KEY> — <summary>\n<jira-url>" \
  --thread <thread_ts>
```

## Edge Cases

| Situation | Behavior |
|-----------|----------|
| Empty thread (no messages) | Inform user, suggest checking the URL |
| Single message (no thread) | Create ticket from that message, skip Discussion sections |
| >100 messages | Summarize in chunks, strongly recommend Confluence |
| Messages with file attachments | Note attachment references in description (files cannot transfer) |
| Private channel access denied | Report the permission error, suggest checking bot token scopes |
| User cancels at review | Clean exit, no ticket created |
| Jira project unknown | Run `jira project list`, present options |
| Confluence space unknown | Run `confluence spaces`, present options |
| jira create fails | Report error, preserve draft for retry |
| Unrecognized URL format | Ask user to provide channel + thread TS manually |

## Behavior Scenarios

```gherkin
Scenario 1: Create ticket from a Slack permalink (primary path)
  Given slack-cli and jira-cli are installed and configured
  And the user pastes a Slack permalink URL
  When the user invokes the skill
  Then it parses the URL, fetches the thread via slack-cli
  And analyzes the conversation, presents a draft ticket for review
  And after user approval, creates the Jira issue with Slack permalink in description
  And offers to post a summary back to the Slack thread

Scenario 2: Create ticket from channel name (secondary)
  Given the user says "create ticket from #channel-name"
  When the skill fetches recent channel history
  Then it summarizes, auto-suggests type/priority, presents draft for review
  And upon approval creates the Jira issue

Scenario 3: Long conversation triggers Confluence recommendation
  Given the conversation has more than 15 messages
  When the skill finishes analyzing
  Then it recommends creating a Confluence page alongside the Jira ticket
  And if user approves, creates both with cross-links

Scenario 4: Create ticket with Confluence documentation
  Given confluence-cli is installed and the user requests a Confluence page
  When the skill creates the Jira ticket
  Then it also creates a Confluence documentation page
  And cross-links them (Confluence link in Jira, Jira key in Confluence)

Scenario 5: Missing prerequisites
  Given one or more required CLIs are not installed
  When the user invokes the skill
  Then it reports which tools are missing with install instructions and stops
```

## References

- `references/description-template.md` — Read when composing the Jira ticket description
- `references/confluence-template.md` — Read when creating a Confluence documentation page
- `references/input-parsing.md` — Read when parsing the user's Slack URL or input
- `references/classification-heuristics.md` — Read when auto-classifying issue type and priority
