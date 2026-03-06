# Test Case Design Guide

This guide helps design comprehensive test cases before implementation (TDD RED phase).

## Test Categories

### Category 1: Happy Path Tests

Tests that verify normal, expected behavior.

**Examples**:
- Input valid data → receive expected output
- Successful RPC call → correct data returned
- Valid user action → system state changes correctly

**Design Questions**:
- What is the most common use case?
- What does success look like?
- What output format is expected?

### Category 2: Edge Cases

Tests for boundary conditions and limits.

**Examples**:
- Empty collections (no items to process)
- Single item collections
- Maximum allowed items
- Boundary values (0, 1, max-1, max)
- Null/missing optional parameters

**Design Questions**:
- What are the minimum/maximum values?
- What happens with empty input?
- What happens at boundaries?

### Category 3: Error Handling

Tests for invalid inputs and failure scenarios.

**Examples**:
- Invalid format inputs
- Missing required parameters
- Malformed data
- Network/service failures
- Timeout scenarios

**Design Questions**:
- What inputs should be rejected?
- What errors can external services return?
- How should errors be communicated?

### Category 4: Input Validation

Tests specific to input sanitization and validation.

**Examples**:
- Empty/whitespace strings
- Invalid date formats
- Injection attempts (SQL, command, CSV)
- Over-length inputs
- Invalid characters

**Design Questions**:
- What format is expected for each input?
- What characters are allowed/disallowed?
- What are the length limits?

### Category 5: Integration Points

Tests for external service interactions.

**Examples**:
- RPC/API call parameter verification
- Correct handling of service responses
- Retry behavior on transient failures
- Timeout handling

**Design Questions**:
- What parameters does the external service expect?
- What responses can the service return?
- How should failures be handled?

### Category 6: Output Format

Tests that verify output structure and format.

**Examples**:
- CSV header correctness
- JSON schema compliance
- Date format standards (ISO 8601)
- Character encoding
- Sorting order

**Design Questions**:
- What is the expected output structure?
- What format standards apply?
- How should special characters be handled?

### Category 7: Security Tests

Tests for security-related behavior.

**Examples**:
- Input escaping (CSV injection prevention)
- Error message sanitization (no internal details)
- Authorization enforcement
- Sensitive data handling

**Design Questions**:
- What injection vectors exist?
- What sensitive data is involved?
- What should error messages reveal?

### Category 8: Ordering & Determinism

Tests that verify consistent, deterministic behavior.

**Examples**:
- Same input always produces same output
- Sorting is stable and correct
- Pagination is consistent
- Tie-breaking rules work

**Design Questions**:
- What ordering is expected?
- How are ties broken?
- Is the output deterministic?

### Category 9: Resource Limits

Tests for pagination, truncation, and limits.

**Examples**:
- Maximum result count
- Truncation warnings
- Memory-bounded operations
- Timeout enforcement

**Design Questions**:
- What is the maximum result size?
- How is truncation communicated?
- What are the performance limits?

## BDD Test Format

When using `--bdd`, write tests in Gherkin-style:

```gherkin
Feature: SKU Restock History Export

  Scenario: Export history for valid SKU with matching events
    Given a store "store-001" with the following restock events:
      | date       | sku_ids     | user_id  |
      | 2024-01-15 | SKU-001     | user-123 |
      | 2024-01-16 | SKU-002     | user-456 |
      | 2024-01-17 | SKU-001,002 | user-789 |
    When I export restock history for SKU "SKU-001" at location "loc-001"
    Then the CSV should contain 2 data rows
    And each row should contain "SKU-001"
    And dates should be in descending order

  Scenario: Export history with no matching events
    Given a store with no restock events for SKU "SKU-999"
    When I export restock history for SKU "SKU-999"
    Then the CSV should contain only the header row

  Scenario: Reject invalid date format
    When I export restock history with start date "01/15/2024"
    Then I should see an error about invalid date format
    And the expected format "yyyy-MM-dd" should be shown
```

## TDD Test Naming Convention

Use descriptive names that document behavior:

```
MethodName_StateUnderTest_ExpectedBehavior
```

**Examples**:
- `ExportSkuRestockHistory_WithMatchingSkuInLogs_OutputsCsvWithFilteredResults`
- `ExportSkuRestockHistory_WithEmptyStoreId_ShowsError`
- `ExportSkuRestockHistory_WhenRpcThrows_DisplaysGenericErrorAndPropagates`

## Test Coverage Checklist

Before proceeding to GREEN phase, verify:

- [ ] All happy paths covered
- [ ] All edge cases from team review covered
- [ ] All security concerns have tests
- [ ] All input validation rules tested
- [ ] All error scenarios handled
- [ ] Output format verified
- [ ] Ordering/determinism tested
- [ ] Resource limits tested
- [ ] Tests compile and fail (RED state)

## Mocking Strategy

Decide what to mock vs. use real implementations:

| Component | Mock? | Reason |
|-----------|-------|--------|
| External RPC/API | Yes | Isolate tests, control responses |
| Database | Usually | Speed, isolation |
| File system | Sometimes | Depends on test scope |
| Time/Clock | Yes | Deterministic tests |
| Randomness | Yes | Reproducible tests |
| Internal services | Usually No | Test integration |
