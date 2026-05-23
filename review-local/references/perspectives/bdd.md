# BDD Perspective

## Focus

Given/When/Then coverage, acceptance criteria alignment, stakeholder-readable specifications, scenario completeness.

## Review Questions

1. Do the changes map to clearly defined acceptance criteria or user stories?
2. Are there Given/When/Then scenarios that cover the changed behavior?
3. Are scenarios written in stakeholder-readable language (no implementation details)?
4. Are both happy paths and error paths covered by scenarios?
5. Are Scenario Outlines used where multiple data variations apply?

## Output Format

```markdown
## BDD Review

### Acceptance Criteria Alignment
- [Do changes map to defined acceptance criteria?]

### Scenario Coverage
- [Which behaviors have Given/When/Then scenarios? Which are missing?]

### Scenario Quality
- [Stakeholder readability, appropriate abstraction level]

### Happy & Error Paths
- [Are both success and failure scenarios covered?]

### Suggested Scenarios
- [Specific Given/When/Then scenarios that should exist for these changes]

### Recommendations
- [Specific BDD improvements with file:line references]
```

## Severity Guidance

| Severity | Examples from this perspective |
|----------|-------------------------------|
| **Critical** | User-facing behavior change with no acceptance criteria or scenarios |
| **Important** | Missing error path scenarios, scenarios too implementation-specific |
| **Nice-to-have** | Could use Scenario Outline for data variations, minor wording improvements |
