# Confluence Documentation Templates

Select the template based on the conversation type classified in Phase 2.
**All templates MUST include a "Messages" section** preserving the original Slack messages.

---

## Template Selection

| Conversation Type | Template | When to use |
|---|---|---|
| Bug / Incident | Postmortem | Conversation involves errors, outages, misplacements, regressions, or operational incidents |
| Feature / Story | PRD | Conversation discusses new capabilities, user needs, feature requests, or enhancements |
| Task / General | Slim Summary | Conversation is about maintenance, chores, investigations, or doesn't fit above categories |

---

## 1. Postmortem Template (Bug / Incident)

```markdown
# [Issue Summary]

## Incident Summary
- **What happened**: [1-2 sentence description of the incident]
- **When**: [Date and time range]
- **Where**: [System, service, store, environment affected]
- **Severity**: [Impact level]
- **Status**: [Resolved / Monitoring / Ongoing]

## Impact
- **Who was affected**: [Users, customers, stores, internal teams]
- **Duration**: [How long the impact lasted]
- **Scope**: [How widespread — single store, region, all stores, etc.]

## Timeline

| Time | Event |
|------|-------|
| HH:MM | [First sign of issue — how it was detected] |
| HH:MM | [Investigation started — who was involved] |
| HH:MM | [Key finding or diagnosis] |
| HH:MM | [Mitigation action taken] |
| HH:MM | [Resolution confirmed] |

## Root Cause Analysis
[Detailed explanation of what went wrong and why. Include technical details such as
coordinate values, error codes, configuration states, or log excerpts from the conversation.]

### Contributing Factors
- [Factor 1 — e.g., no validation on input data]
- [Factor 2 — e.g., missing monitoring for edge case]

## Remediation
### Immediate Fix
[What was done to resolve the incident right away]

### Systemic Fixes Required
[Longer-term fixes to prevent recurrence — these should map to the Jira action items]

## Lessons Learned
- [Lesson 1 — what we should do differently]
- [Lesson 2 — what worked well and should be repeated]

## Messages
[Preserve ALL original Slack messages chronologically. This is the source of truth.]

| Time | From | Message |
|------|------|---------|
| HH:MM | Name | [message text] |
| HH:MM | Name | [message text] |

## Related Resources
- **Jira Ticket**: [PROJ-NNN](<jira-url>)
- **Slack Thread**: [Original conversation](<slack-permalink>)
```

### Section Guidelines (Postmortem)

| Section | Include when... | Omit when... |
|---------|----------------|--------------|
| Incident Summary | Always | Never |
| Impact | Impact is known or estimable | Impact is unclear (note "TBD" instead) |
| Timeline | 3+ events with distinct phases | Very short incident |
| Root Cause Analysis | Cause was identified in conversation | Still under investigation (note status) |
| Remediation | Fix was applied or proposed | No fix discussed yet |
| Lessons Learned | Conversation includes reflections | Too early for lessons |
| Messages | Always | Never |
| Related Resources | Always | Never |

---

## 2. PRD Template (Feature / Story)

```markdown
# [Feature/Request Summary]

## Problem Statement
[What problem is being solved? Why does it matter?
Extract from the conversation — who raised it and what pain point they described.]

## Goals & Success Metrics
- **Goal 1**: [What should be achieved]
- **Goal 2**: [Secondary goal if any]
- **Success metric**: [How we know it worked — extracted from conversation or inferred]

## Requirements
### Functional Requirements
- [Requirement 1 — extracted from conversation decisions/asks]
- [Requirement 2]
- [Requirement 3]

### Non-Functional Requirements
- [Performance, security, compatibility constraints mentioned in conversation]

## Constraints & Dependencies
- [Constraint 1 — technical, timeline, or resource limitations mentioned]
- [Dependency 1 — other teams, systems, or features required]

## Open Questions
- [Question 1 — unresolved in conversation, who needs to answer]
- [Question 2]

## Messages
[Preserve ALL original Slack messages chronologically. This is the source of truth.]

| Time | From | Message |
|------|------|---------|
| HH:MM | Name | [message text] |
| HH:MM | Name | [message text] |

## Related Resources
- **Jira Ticket**: [PROJ-NNN](<jira-url>)
- **Slack Thread**: [Original conversation](<slack-permalink>)
```

### Section Guidelines (PRD)

| Section | Include when... | Omit when... |
|---------|----------------|--------------|
| Problem Statement | Always | Never |
| Goals & Success Metrics | Goals were discussed or can be inferred | Pure brainstorm with no clear goals |
| Requirements | Specific asks or decisions were made | Still in discovery phase (note status) |
| Constraints & Dependencies | Mentioned in conversation | None discussed |
| Open Questions | Unresolved items remain | Everything was decided |
| Messages | Always | Never |
| Related Resources | Always | Never |

---

## 3. Slim Summary Template (Task / General)

```markdown
# [Summary]

## Context
[Brief description of what the conversation was about and why it happened.]

## Decisions
- [Decision 1 — who decided, brief rationale]
- [Decision 2]

## Action Items

| # | Item | Owner | Status |
|---|------|-------|--------|
| 1 | [Action] | Name | Pending |
| 2 | [Action] | Name | Pending |

## Messages
[Preserve ALL original Slack messages chronologically. This is the source of truth.]

| Time | From | Message |
|------|------|---------|
| HH:MM | Name | [message text] |
| HH:MM | Name | [message text] |

## Related Resources
- **Jira Ticket**: [PROJ-NNN](<jira-url>)
- **Slack Thread**: [Original conversation](<slack-permalink>)
```

### Section Guidelines (Slim Summary)

| Section | Include when... | Omit when... |
|---------|----------------|--------------|
| Context | Always | Never |
| Decisions | Decisions were made | Pure discussion |
| Action Items | Tasks were assigned or implied | No actions |
| Messages | Always | Never |
| Related Resources | Always | Never |

---

## Page Title Convention

Format: `[PROJ-NNN] Issue Summary`
Examples:
- `[ROMS-3666] Auto-annotation Coordinate Drift — Shibamata Store Postmortem`
- `[ROMS-1234] Empty Lane Detection UI — Product Requirements`
- `[ROMS-5678] Sprint Planning Notes — Q3 Priorities`
