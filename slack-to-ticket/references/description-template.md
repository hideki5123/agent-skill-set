# Jira Ticket Description Template

Use this template when composing the Jira ticket description from Slack conversation analysis.
Adapt sections based on what the conversation actually contains — omit empty sections.

```markdown
## Context
[1-2 sentence summary of what the conversation is about]

**Source**: [Slack thread](<permalink-url>)
**Channel**: #<channel-name>
**Date**: <YYYY-MM-DD>
**Participants**: @user1, @user2, @user3

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
- [ ] [Action 1] — Owner: @user
- [ ] [Action 2] — Owner: @user

## Conversation Excerpt
> **@user1** (14:02): [key message]
> **@user2** (14:15): [key response]
> **@user3** (14:30): [key conclusion]
```

## Section Guidelines

| Section | Include when... | Omit when... |
|---------|----------------|--------------|
| Context | Always | Never |
| Problem / Request | Always | Never |
| Key Discussion Points | 3+ distinct topics discussed | Single-topic, short thread |
| Decisions | Explicit agreement or conclusion reached | No decisions made yet |
| Action Items | Explicit or implied next steps exist | Pure discussion, no actions |
| Conversation Excerpt | Thread has key quotes worth preserving | Very short (1-3 messages) — full text is already in Problem section |

## Formatting Notes

- Keep the description under 2000 characters for readability
- Use bullet points over paragraphs
- Attribute quotes to speakers using `@username`
- Use ISO dates (YYYY-MM-DD)
- The Slack permalink must always appear in the Context section
