# QA/QC Perspective

## Focus

Test coverage gaps, quality metrics, regression risk, edge case handling, code quality standards.

## Review Questions

1. Are the changes adequately covered by existing tests, or are new tests needed?
2. What regression risks does this change introduce?
3. Are edge cases and boundary conditions handled?
4. Does the code meet quality standards (readability, maintainability, documentation)?
5. Are there any code smells or anti-patterns introduced?

## Output Format

```markdown
## QA/QC Review

### Test Coverage
- [Are changes covered by tests? What new tests are needed?]

### Regression Risk
- [What existing functionality could break?]

### Edge Cases & Boundaries
- [Unhandled edge cases, null/empty/max values, concurrency]

### Code Quality
- [Readability, maintainability, complexity metrics]

### Code Smells
- [Anti-patterns, duplication, dead code, magic numbers]

### Recommendations
- [Specific quality improvements with file:line references]
```

## Severity Guidance

| Severity | Examples from this perspective |
|----------|-------------------------------|
| **Critical** | No tests for critical path, high regression risk with no coverage, data loss edge case |
| **Important** | Missing edge case tests, code complexity too high, duplicated logic |
| **Nice-to-have** | Could improve test names, minor readability improvements |
