# TDD Phases Reference

Detailed guidance for each TDD phase.

## RED Phase: Write Failing Tests

### Objectives
1. Define expected behavior through tests
2. Document acceptance criteria as executable specs
3. Establish clear success criteria

### Steps

1. **Create Test File**
   ```
   <project>.Tests/<feature>/<FeatureName>Tests.cs
   ```

2. **Add Test Dependencies**
   - Testing framework (xUnit, NUnit, etc.)
   - Mocking library (Moq, NSubstitute)
   - Assertion library (FluentAssertions)

3. **Write Test Cases**
   - One test per behavior
   - Clear Arrange/Act/Assert structure
   - Descriptive names

4. **Create Stub Implementation**
   ```csharp
   public Task DoSomething()
   {
       throw new NotImplementedException("RED phase: Implementation not yet complete");
   }
   ```

5. **Run Tests - All Must Fail**
   ```bash
   dotnet test --filter "FullyQualifiedName~FeatureName"
   ```

### RED Phase Commit
```
test: add failing tests for <feature>

Add comprehensive test suite covering:
- Happy path scenarios
- Edge cases
- Error handling
- Input validation

Tests are in RED state - implementation pending.
```

## GREEN Phase: Make Tests Pass

### Objectives
1. Write minimum code to pass tests
2. Don't add unrequested features
3. Focus on correctness, not elegance

### Steps

1. **Pick One Failing Test**
   - Start with simplest test
   - Work incrementally

2. **Write Minimum Code**
   - Just enough to pass that test
   - Don't anticipate future tests

3. **Run Tests**
   - Target test should pass
   - Previous tests still pass
   - Remaining tests still fail (as expected)

4. **Repeat**
   - Pick next failing test
   - Implement minimum code
   - Verify all tests

5. **All Tests Pass**
   - Full test run succeeds
   - No regressions

### GREEN Phase Commit
```
feat: implement <feature>

Implement <brief description> with:
- <key implementation detail 1>
- <key implementation detail 2>
- <security measure from review>

All tests passing.
```

## REFACTOR Phase: Improve Code

### Objectives
1. Improve code quality without changing behavior
2. Remove duplication
3. Enhance readability

### Steps

1. **Identify Improvements**
   - Code duplication
   - Long methods
   - Unclear naming
   - Missing documentation
   - Performance concerns

2. **Make Small Changes**
   - One refactoring at a time
   - Run tests after each change
   - Keep tests green

3. **Common Refactorings**
   - Extract method
   - Rename for clarity
   - Consolidate duplicates
   - Add documentation
   - Optimize hot paths

### REFACTOR Phase Commit (if needed)
```
refactor: improve <aspect> in <feature>

- Extract common logic to helper method
- Improve variable naming for clarity
- Add XML documentation
```

## TDD Rhythm

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   ┌─────┐       ┌───────┐       ┌──────────┐           │
│   │ RED │ ───── │ GREEN │ ───── │ REFACTOR │ ──────┐   │
│   └─────┘       └───────┘       └──────────┘       │   │
│      ▲                                             │   │
│      │                                             │   │
│      └─────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘

RED:      Write a failing test
GREEN:    Make it pass (minimum code)
REFACTOR: Improve code (keep tests green)
REPEAT:   Next test case
```

## Anti-Patterns to Avoid

### In RED Phase
- Writing tests that pass immediately
- Testing implementation details instead of behavior
- Skipping edge cases to save time
- Writing vague test names

### In GREEN Phase
- Writing more code than needed
- Adding features not covered by tests
- Optimizing prematurely
- Ignoring failing tests

### In REFACTOR Phase
- Changing behavior (tests should stay green)
- Big-bang refactoring (keep changes small)
- Skipping the refactor phase entirely
- Adding features during refactoring

## When to Stop Refactoring

The REFACTOR phase is complete when:
- [ ] No obvious code duplication
- [ ] Names clearly express intent
- [ ] Methods are focused (single responsibility)
- [ ] No commented-out code
- [ ] Tests still pass
- [ ] Code is "good enough" for now

Remember: Perfect is the enemy of good. Ship working code!
