# Classification Heuristics

## Issue Type Auto-Classification

Analyze the conversation content for keyword patterns to suggest an issue type.
Use the **first match** from highest to lowest specificity.

### Bug

Conversation mentions errors, failures, regressions, or broken behavior.

**Keywords**: error, bug, crash, broken, not working, regression, 500, 503, 404, exception,
stack trace, traceback, null pointer, undefined, NaN, timeout, failing, failed, outage,
incident, degraded, down, "doesn't work", "stopped working", "used to work"

### Story

Conversation discusses user needs, feature requests, or new capabilities.

**Keywords**: feature, "as a user", "I want", "we need", "it would be nice", "can we add",
request, enhancement, improvement, "new feature", user story, requirement, "would be great",
proposal, suggestion, "how about", "what if we"

### Task (default)

Conversation discusses work items, maintenance, or action items without fitting Bug or Story.

**Keywords**: task, TODO, "we should", "need to", refactor, cleanup, update, migrate,
upgrade, configure, setup, deploy, maintenance, chore, "action item", investigate,
research, spike, document, review

### Epic

Use only when explicitly suggested by the user or when the conversation clearly spans
multiple workstreams or teams.

## Priority Auto-Classification

Scan for urgency signals. Use the **highest matching priority**.

### Highest
**Keywords**: outage, P0, "production down", "site down", "service down",
"data loss", "security breach", "critical vulnerability", SEV-1, SEV1

### High
**Keywords**: urgent, ASAP, blocking, blocker, critical, P1, "needs immediate",
"high priority", "can't proceed", "release blocker", SEV-2, SEV2,
"customers affected", "revenue impact"

### Medium (default)
No urgency signals detected, or ambiguous urgency.
This is the safe default — let the user adjust in the review step.

### Low
**Keywords**: "nice to have", "when you get a chance", backlog, "low priority",
"not urgent", "whenever", "no rush", P3, P4, "someday", "minor"

### Lowest
**Keywords**: "if we ever", "maybe someday", "wishlist", "far future"

## Classification Output Format

Present the classification to the user with reasoning:

```
**Type**: Bug (detected: "503 errors", "not working", "regression")
**Priority**: High (detected: "blocking", "customers affected")
```

If no strong signals are detected:
```
**Type**: Task (default — no strong bug/story signals)
**Priority**: Medium (default — no urgency signals)
```

## Override Rules

- User's explicit statement always overrides auto-classification
- If the conversation contains mixed signals (e.g., both bug keywords and feature keywords), present both options and let the user choose
- When in doubt, default to Task/Medium — the user can adjust during review
