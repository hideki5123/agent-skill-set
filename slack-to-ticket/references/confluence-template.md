# Confluence Documentation Page Template

Use this template when the user approves creating a Confluence page alongside the Jira ticket.
This is for longer/complex conversations that need more documentation than a Jira description allows.

```markdown
# [Issue Summary — matching Jira ticket title]

## Overview
[Extended description of the problem/request. 2-3 paragraphs providing full context
that wouldn't fit in a Jira ticket description.]

## Background
[Why this came up. Prior context, related incidents, or feature requests
that led to this conversation.]

## Discussion Timeline

| Time | Participant | Key Point |
|------|-------------|-----------|
| HH:MM | @user1 | [First significant message] |
| HH:MM | @user2 | [Response or new information] |
| HH:MM | @user3 | [Decision or conclusion] |

## Decisions & Rationale

### Decision 1: [Title]
- **What**: [What was decided]
- **Why**: [Reasoning or constraints that led to this decision]
- **Who**: [Who made or agreed to the decision]

### Decision 2: [Title]
- **What**: [What was decided]
- **Why**: [Reasoning]
- **Who**: [Who decided]

## Action Items

| # | Item | Owner | Priority | Status |
|---|------|-------|----------|--------|
| 1 | [Action description] | @user | High/Med/Low | Pending |
| 2 | [Action description] | @user | High/Med/Low | Pending |

## Open Questions
- [Question 1 — who needs to answer]
- [Question 2]

## Related Resources
- **Jira Ticket**: [PROJ-NNN](<jira-url>)
- **Slack Thread**: [Original conversation](<slack-permalink>)
```

## Section Guidelines

| Section | Include when... | Omit when... |
|---------|----------------|--------------|
| Overview | Always | Never |
| Background | Prior context exists | Conversation is self-contained |
| Discussion Timeline | 5+ messages with distinct phases | Short, single-topic thread |
| Decisions & Rationale | Decisions were made with reasoning | No decisions yet |
| Action Items | Tasks were assigned or implied | Pure discussion |
| Open Questions | Unresolved questions remain | Everything was resolved |
| Related Resources | Always (Jira link is always present) | Never |

## Page Title Convention

Format: `[PROJ-NNN] Issue Summary`
Example: `[BACKEND-456] API Gateway 503 Errors Investigation`

This makes the Confluence page easily searchable by Jira key.
