# Jira Ticket Description Template (fallback)

**This template is the fallback.** Always prefer the target Jira project's configured default description — fetched in Phase 3 via `getJiraIssueTypeMetaWithFields` as `fields[description].defaultValue`. Only use the template below when the project has no default description for the chosen issue type.

When the project has a default, map Slack-derived content into its existing heading sections and keep all project headings (even ones with nothing to fill) so the ticket matches project conventions.

## Fallback template

```markdown
## Context
[1-2 sentence summary of what the conversation is about]

**Source**: [Slack thread](<permalink-url>)
**Channel**: #<channel-name>
**Date**: <YYYY-MM-DD>
**Participants**: Name1, Name2, Name3

## Problem / Request
[Clear statement of the issue or request extracted from conversation.
Focus on the core ask — what needs to happen and why.]

## Key Discussion Points
- [Point 1 — attributed to speaker if relevant]
- [Point 2]
- [Point 3]

## Decisions
- [Decision 1 — who decided, rationale if stated]
- [Decision 2]

## Action Items
- [ ] [Action 1] — Owner: Name
- [ ] [Action 2] — Owner: Name
```

## Section Guidelines

| Section | Include when... | Omit when... |
|---------|----------------|--------------|
| Context | Always | Never |
| Problem / Request | Always | Never |
| Key Discussion Points | 3+ distinct topics discussed | Single-topic, short thread |
| Decisions | Explicit agreement or conclusion reached | No decisions made yet |
| Action Items | Explicit or implied next steps exist | Pure discussion, no actions |
| Conversation Excerpt | **Default: omit.** Include only when a specific quote captures a non-obvious decision, trade-off, or nuance that Decisions / Action Items cannot convey on their own. | Anything else — Decisions and Action Items already summarize the thread. |

Conversation Excerpt is opt-in, not opt-out. It is not part of the default template skeleton; add it only when a quote adds something the summarized sections genuinely cannot.

## Formatting Notes

- Keep the description under 2000 characters for readability
- Use bullet points over paragraphs
- **All Slack placeholders (`<@UXXX>`, `<#CXXX>`, `<!subteam^SXXX>`) must be resolved before inclusion — no raw IDs in ticket text.** See `references/slack-mention-resolution.md`.
- Use display names (e.g., "Miyazaki", "Koike") — NOT @account handles
- For user-group mentions, render as `` `@handle` user group (Slack ID `SXXX`) `` on first mention, then `@handle` thereafter
- Use ISO dates (YYYY-MM-DD)
- The Slack permalink must always appear in the Context section (or the equivalent context section of the project's template)
- Do NOT include an Assignee field — tickets are always created unassigned
