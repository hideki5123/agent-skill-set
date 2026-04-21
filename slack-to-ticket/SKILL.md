---
name: slack-to-ticket
version: 1.1.0
description: >
  Create Jira tickets from Slack conversations, optionally with Confluence documentation pages.
  Reads Slack threads/channels/search results via slack-cli, analyzes the conversation to extract
  problems, participants, decisions, and action items, then creates Jira issue(s) via jira-cli
  with the conversation context. A single conversation may produce multiple tickets if it covers
  distinct topics. For long or complex conversations (>15 messages), recommends creating a
  Confluence documentation page via confluence-cli with a context-aware format (postmortem for
  bugs, PRD for features, slim summary for tasks). Supports input as Slack permalink URL,
  channel name, thread timestamp, or search query. Presents drafts for interactive review
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
- **Never create new Jira labels**. Only use labels that already exist on the target project. If a new label seems truly necessary, ask the user for approval first.
- **Always leave the assignee field unassigned**. Do not suggest assignees from conversation participants.
- Use display names (not @account handles) when referencing people in ticket descriptions
- Write ticket content in English unless the user explicitly requests otherwise

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

### Feedback Check

If `feedback/log.md` exists and has 5 or more entries, read the last 10 entries.
If a pattern is apparent (same issue in 3+ entries, or average rating below 3):
- Tell the user: "Recurring feedback detected: [brief pattern]. Consider running `/skill-improve --skill slack-to-ticket`."
- Continue with normal execution.

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

### Resolve Slack mention syntax first

Before extracting anything else, scan every fetched message body for Slack placeholders — `<@UXXX>`, `<#CXXX>`, `<!subteam^SXXX>`, `<!here>`/`<!channel>`/`<!everyone>`, and URL placeholders — and resolve them to human-readable names per `references/slack-mention-resolution.md`. Raw Slack IDs must not reach Phase 3.

For user-group mentions (`<!subteam^SXXX>`) that do not carry a `|@handle` form, ask the user for the handle (e.g., `@biz-cx-team`) once and cache it for reuse.

### Extract

Analyze the resolved messages to extract:

1. **Problem / Request**: The core issue or ask
2. **Key Participants**: Who is involved (display names from messages)
3. **Decisions**: Any conclusions or agreements reached
4. **Action Items**: Explicit or implied next steps with owners
5. **Urgency Signals**: Keywords that indicate priority

Read `references/classification-heuristics.md` for keyword-to-type and keyword-to-priority mapping tables.

Auto-classify:
- **Issue Type**: Bug, Story, Task, or Epic based on conversation keywords
- **Priority**: Highest, High, Medium (default), Low, or Lowest based on urgency signals

### Multi-topic analysis

After initial extraction, determine whether the conversation covers **multiple distinct issues or topics**. Signs of multiple topics:
- Conversation shifts from one problem to another ("also...", "separate issue...", "by the way...")
- Different root causes are identified for different symptoms
- Different owners or teams are involved for different action items
- Investigation reveals distinct sub-problems (e.g., DS7 coordinate drift vs DS4 empty lane issue)

If multiple topics are found:
- Group related messages by topic
- Each topic group becomes a separate ticket candidate
- Each ticket gets its own type/priority classification
- Note relationships between tickets (e.g., "discovered during investigation of...")

If only one topic → single ticket (default behavior).

## Phase 3: Draft Ticket(s)

Compose the ticket draft(s). Before writing, fetch two things from the target Jira project: the project's description template, and its existing labels.

### Fetch the project's description template

Different Jira projects configure different default descriptions per issue type (for example, ROMS Engineering Tasks use `# Motivation / # Requirement / # Acceptance Criterias`). Jira exposes this default directly — always prefer it over the generic template.

Use the Atlassian MCP tool `getJiraIssueTypeMetaWithFields` for the chosen project + issue type:

```
getJiraIssueTypeMetaWithFields:
  cloudId: <CLOUD_ID>
  projectIdOrKey: <PROJECT_KEY>
  issueTypeId: <ISSUE_TYPE_ID>
```

Read `fields[description]`:
- If `hasDefaultValue: true`, take `defaultValue` (ADF JSON), convert to markdown, and use it as the outer skeleton. Map Slack-derived content into the existing heading sections — for example, the user story goes under `# Motivation`, functional requirements under `# Requirement`, acceptance criteria under `# Acceptance Criterias`. Keep all headings from the project default, even ones you have nothing to fill in, so the ticket matches project expectations.
- If `hasDefaultValue` is false or the default is empty, fall back to the generic template in `references/description-template.md`.

Fetch once per run and cache in-memory. Do not repeat the call for each draft.

### Fetch existing labels

Fetch the project's existing labels so you only suggest valid ones:

```bash
# Via Atlassian MCP (preferred)
# Use searchJiraIssuesUsingJql to get labels from existing issues

# Via CLI fallback
jira issue list -p <KEY> --plain --columns labels --paginate 0:50 | tr ',' '\n' | sort -u
```

Keep the set of existing labels in-memory — the draft presentation annotates each proposed label as `(existing)` or `(NEW — needs approval)` against this set.

### Present draft(s)

For each ticket candidate, present:

```
## Draft Jira Ticket [N of M]

**Project**: [ask user if unknown — run `jira project list` to show options]
**Type**: <auto-detected> (detected: "<keywords>")
**Priority**: <auto-detected> (detected: "<keywords>")
**Summary**: <generated — under 80 chars>
**Labels**: <label> (existing), <other-label> (NEW — needs approval)  ← annotate each

### Description Preview
[rendered description from template]

### Why this is a separate ticket
[only if M > 1 — brief explanation of why this was split out]

---
[Confluence recommended — conversation has NN messages] ← only if > 15 messages
```

If the Jira project is unknown, run `jira project list` and present options to the user.

Each proposed label must carry a provenance tag:
- `(existing)` — the label appears in the project's existing-label set.
- `(NEW — needs approval)` — the label is not in the existing set and requires explicit user approval before the ticket is created.

If any `(NEW — needs approval)` labels appear, confirm with the user before creating the ticket:
```
Label "<suggested>" does not exist in the project. Create it? (y/n)
```

## Phase 4: User Review

Ask the user to review the draft(s). They can:
1. **Approve** all tickets as-is
2. **Modify** any field on any ticket (type, priority, summary, description, project, labels)
3. **Remove** a ticket from the batch
4. **Merge** tickets back together if they disagree with the split
5. **Add** another ticket manually
6. **Add/skip Confluence page** (if recommended or requested)
7. **Cancel** — clean exit, nothing created

Loop on modifications until the user approves or cancels.

## Phase 5: Create Jira Ticket(s)

For each approved ticket, write the description to a temp file and create the issue.

Prefer using the Atlassian MCP tool (`createJiraIssue`) over the CLI, as it handles custom fields (Impact, Frequency, Sprint) more reliably. Fall back to CLI if MCP is unavailable.

### Via Atlassian MCP (preferred)

```
createJiraIssue:
  projectKey: <KEY>
  issueTypeName: <TYPE>
  summary: <SUMMARY>
  contentFormat: markdown
  description: <DESCRIPTION>
  additional_fields:
    priority: { name: <PRIORITY> }
    labels: [<existing-labels>]
    # Include required custom fields (Impact, Frequency, Sprint) based on project schema
```

Note: Do NOT set `assignee_account_id`. Always leave unassigned.

### Via CLI (fallback)

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
  --label <EXISTING_LABEL> \
  --no-input
```

Note: Do NOT include `--assignee`. Always leave unassigned.

Capture the returned issue key (e.g., `PROJ-456`).

If the command fails due to required custom fields, check the project's field requirements using `getJiraIssueTypeMetaWithFields` and retry with the required fields populated.

### Cross-references (multi-ticket only)

If multiple tickets were created from the same conversation, add a comment to each linking to the others:

```
Related tickets from the same Slack conversation:
- PROJ-456 — <summary>
- PROJ-457 — <summary>
```

## Phase 6: Create Confluence Page (Optional)

Only proceed if the user approved a Confluence page in Phase 4.

### Select document format

Suggest a format based on the conversation type, but **always let the user choose**. Present the three options with a recommendation:

```
Confluence page format?
→ Postmortem (recommended) — timeline, impact, root cause, remediation, lessons learned
→ PRD — problem statement, goals, requirements, constraints, open questions
→ Slim Summary — context, decisions, action items
```

Recommend based on conversation type:
- Bug / Incident → recommend **Postmortem**
- Feature / Story → recommend **PRD**
- Task / General → recommend **Slim Summary**

But the user may override — e.g., an incident investigation that leads to a feature request may be better as a PRD.

Read `references/confluence-template.md` for all three templates.

**All formats MUST include a "Messages" section** that preserves the original Slack conversation messages chronologically. This is the raw data — analysis sections above are interpretation, this section is the source of truth.

### Create the page

```bash
cat > /tmp/slack-ticket-confluence.md << 'CONF_PAGE'
<generated page content from selected template>
CONF_PAGE

confluence create "[ISSUE-KEY] <Summary>" <SPACEKEY> \
  --file /tmp/slack-ticket-confluence.md --format markdown
```

If Confluence space key is unknown, ask the user (they may provide a URL like `https://site.atlassian.net/wiki/spaces/KEY/overview`).

After creating the page, update the Jira ticket to include the Confluence link:

```bash
echo -e "\n\n## Documentation\n[Confluence Page](<confluence-url>)" >> /tmp/slack-ticket-desc.md

jira issue edit <ISSUE-KEY> --description-file /tmp/slack-ticket-desc.md
```

## Phase 7: Summary & Slack Notification

Report the results:

```
## Created

- **Jira**: [PROJ-456](<jira-url>) — <summary>
- **Jira**: [PROJ-457](<jira-url>) — <summary>  ← if multiple
- **Confluence**: [Page title](<confluence-url>) ← only if created
- **Source**: [Slack thread](<permalink>)
```

Then **always offer** to post a summary back to the Slack thread:

```
Post summary to the Slack thread?
→ "Jira ticket(s) created:
  PROJ-456 — <summary>
  PROJ-457 — <summary>
  <jira-urls>"
```

If the user approves:

```bash
slack-cli send -c <channel> \
  -m "Jira ticket(s) created:\n<ISSUE-KEY> — <summary>\n<jira-url>" \
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
| User cancels at review | Clean exit, nothing created |
| Jira project unknown | Run `jira project list`, present options |
| Confluence space unknown | Ask user for space URL or key |
| jira create fails | Report error, preserve draft for retry. Check required custom fields |
| Unrecognized URL format | Ask user to provide channel + thread TS manually |
| Conversation covers multiple topics | Split into multiple ticket candidates, present all for review |
| No existing labels match | Ask user before creating any new label |
| Required custom fields (Impact, Frequency, Sprint) | Fetch field metadata, prompt user or use sensible defaults |

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

## Behavior Scenarios

```gherkin
Scenario 1: Create ticket from a Slack permalink (primary path)
  Given slack-cli and jira-cli are installed and configured
  And the user pastes a Slack permalink URL
  When the user invokes the skill
  Then it parses the URL, fetches the thread via slack-cli
  And analyzes the conversation, presents a draft ticket for review
  And the ticket is always unassigned with only existing labels
  And after user approval, creates the Jira issue with Slack permalink in description
  And offers to post a summary back to the Slack thread

Scenario 2: Multiple tickets from one conversation
  Given a Slack conversation covers two or more distinct issues
  When the skill finishes analyzing
  Then it identifies each distinct issue as a separate ticket candidate
  And presents all drafts numbered (1 of N, 2 of N) for review
  And the user can approve, modify, merge, or remove any of them
  And approved tickets are created with cross-reference comments

Scenario 3: Labels — only existing labels used
  Given the target Jira project has a set of existing labels
  When the skill composes a ticket draft
  Then it only selects from existing project labels
  And if no label fits, it asks the user before creating a new one

Scenario 4: Long conversation triggers Confluence recommendation
  Given the conversation has more than 15 messages
  When the skill finishes analyzing
  Then it recommends creating a Confluence page alongside the Jira ticket(s)
  And presents format options (Postmortem, PRD, Slim Summary) with a recommendation
  And the user chooses the format
  And the page always includes a Messages section preserving the original conversation

Scenario 5: User overrides recommended Confluence format
  Given the conversation is classified as a Bug/incident
  And the skill recommends Postmortem format
  When the user chooses PRD format instead
  Then the skill creates the Confluence page using the PRD template

Scenario 7: Missing prerequisites
  Given one or more required CLIs are not installed
  When the user invokes the skill
  Then it reports which tools are missing with install instructions and stops
```

## References

- `references/description-template.md` — Fallback ticket description template, used when the Jira project has no configured default description
- `references/slack-mention-resolution.md` — Read at the start of Phase 2 to resolve `<@UXXX>`, `<#CXXX>`, `<!subteam^SXXX>`, and URL placeholders before drafting
- `references/confluence-template.md` — Read when creating a Confluence documentation page (contains postmortem, PRD, and slim summary templates)
- `references/input-parsing.md` — Read when parsing the user's Slack URL or input
- `references/classification-heuristics.md` — Read when auto-classifying issue type and priority
