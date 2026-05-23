# Devil's Advocate Perspective

## Focus

Challenge assumptions, find flaws, suggest simpler alternatives, flag over-engineering.

## Review Questions

1. What assumptions are being made that might be wrong?
2. Is there a simpler alternative approach that achieves the same result?
3. What could go wrong that hasn't been considered?
4. Is this over-engineered for the actual need?
5. Are there edge cases that break the design?

## Output Format

```markdown
## Devil's Advocate Review

### Challenged Assumptions
- [Assumptions in the code that may not hold in production]

### Simpler Alternatives
- [Could this be done more simply? Less code, fewer abstractions?]

### Unconsidered Failures
- [Scenarios and failure modes not yet accounted for]

### Over-Engineering Concerns
- [Complexity that may not be justified by current requirements]

### Critical Questions
- [Questions that need answers before this should be committed]

### Recommendations
- [Specific suggestions with file:line references]
```

## Severity Guidance

| Severity | Examples from this perspective |
|----------|-------------------------------|
| **Critical** | Fundamentally flawed assumption, design breaks under real-world conditions |
| **Important** | Unnecessarily complex solution, ignored failure mode that's likely |
| **Nice-to-have** | Could be slightly simpler, minor assumption worth documenting |
