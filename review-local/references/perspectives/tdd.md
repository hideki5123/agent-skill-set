# TDD Perspective

## Focus

Red-green-refactor adherence, test-first patterns, test quality, test isolation, mocking strategy.

## Review Questions

1. Were tests written before or alongside the implementation (test-first evidence)?
2. Do test names follow `MethodName_StateUnderTest_ExpectedBehavior` convention?
3. Are tests isolated — no shared mutable state, no order dependency?
4. Is the mocking strategy appropriate (mock external dependencies, not internals)?
5. Does each test verify exactly one behavior (single assertion principle)?

## Output Format

```markdown
## TDD Review

### Test-First Evidence
- [Signs that tests were written before/with implementation, or after]

### Test Naming & Structure
- [Naming convention adherence, arrange-act-assert structure]

### Test Isolation
- [Shared state, order dependencies, flaky test risks]

### Mocking Strategy
- [What is mocked, what should/shouldn't be mocked]

### Single Responsibility
- [Does each test verify one behavior? Over-assertion?]

### Recommendations
- [Specific TDD improvements with file:line references]
```

## Severity Guidance

| Severity | Examples from this perspective |
|----------|-------------------------------|
| **Critical** | Implementation with no tests at all, tests that pass regardless of implementation |
| **Important** | Tests written after implementation with gaps, shared mutable state between tests |
| **Nice-to-have** | Test naming inconsistencies, could extract test helpers |
