# Test Outline Generation Rules

Rules for generating test outlines (Phase 2). The outline is a "living document" that serves as a specification — it contains only test structure and descriptive names, never implementation logic.

## Core Principles

1. **No implementation logic** — never write Arrange, Act, Assert, mocks, or setup code in the outline
2. **Names are the spec** — each test case name must fully convey what behavior is being verified
3. **No mock-dependent cases** — do not create test cases that assume mocking of internal modules
4. **Hierarchy = context** — use nesting to represent preconditions and grouping

## Test Case Naming

### Japanese (`--lang=ja`)

Use the pattern: **"[context]の時、[expected behavior]であること"**

Examples:
- "集計期間がデフォルトの7日間の時、過去7日分のデータのみ集計されること"
- "ランキングが20件を超える時、上位20件のみ返却されること"
- "認証されていないユーザーの時、401エラーが返されること"
- "データが0件の時、空の配列が返されること"

### English (`--lang=en`)

Use the pattern: **"should [expected behavior] when [condition]"**

Examples:
- "should aggregate only last 7 days of data when period is default"
- "should return only top 20 results when ranking exceeds 20 items"
- "should return 401 error when user is not authenticated"
- "should return empty array when no data exists"

## Coverage Categories

Every outline must cover these 5 categories. Check each one before presenting to the user.

### 1. Happy Path
Normal expected behavior with valid inputs.
- Primary use case with typical data
- Expected output format and content
- Success response codes / return types

### 2. Edge Cases
Boundary conditions and special values.
- Empty inputs / zero counts / null values
- Exactly-at-limit values (e.g., exactly 20 items for a top-20 ranking)
- Maximum / minimum allowed values
- First / last items in a sequence
- Single-item collections

### 3. Error Handling
Invalid inputs and failure scenarios.
- Missing required fields
- Invalid data types or formats
- Authentication / authorization failures
- External service unavailability
- Concurrent access conflicts

### 4. Constraints Validation
Business rules and limits from the spec.
- Upper / lower bounds specified in requirements
- Default values behave correctly
- Custom parameter overrides work
- Configurable ranges respect their limits

### 5. Data Integrity
State before and after operations, invariants.
- Data is correctly persisted after successful operations
- Data is unchanged after failed operations (rollback)
- Related records are updated consistently
- No orphaned records after deletions
- Timestamps and audit fields are set correctly

## Outline Structure by Framework

### .NET (xUnit)

```csharp
public class TemplateRankingServiceTests
{
    // === Happy Path ===

    [Fact(Skip = "TODO", DisplayName = "should return top 20 templates ranked by usage when period is default 7 days")]
    public void ReturnsTop20TemplatesForDefault7DayPeriod() { }

    [Fact(Skip = "TODO", DisplayName = "should aggregate usage counts correctly when multiple users use the same template")]
    public void AggregatesUsageCountsAcrossMultipleUsers() { }

    // === Edge Cases ===

    [Fact(Skip = "TODO", DisplayName = "should return empty list when no templates have been used in the period")]
    public void ReturnsEmptyListWhenNoUsageData() { }

    [Fact(Skip = "TODO", DisplayName = "should return exactly 20 items when more than 20 templates exist")]
    public void ReturnsExactly20WhenMoreExist() { }

    // === Error Handling ===

    [Fact(Skip = "TODO", DisplayName = "should throw ArgumentException when start date is after end date")]
    public void ThrowsWhenStartDateAfterEndDate() { }

    // === Constraints ===

    [Fact(Skip = "TODO", DisplayName = "should use 7-day default period when no date range is specified")]
    public void UsesDefault7DayPeriodWhenNoneSpecified() { }

    // === Data Integrity ===

    [Fact(Skip = "TODO", DisplayName = "should not modify usage records when aggregating ranking data")]
    public void DoesNotModifySourceDataDuringAggregation() { }
}
```

### .NET (NUnit)

```csharp
[TestFixture]
public class TemplateRankingServiceTests
{
    [Test, Ignore("TODO"), Description("should return top 20 templates ranked by usage when period is default 7 days")]
    public void ReturnsTop20TemplatesForDefault7DayPeriod() { }
    // ... same pattern
}
```

### .NET (MSTest)

```csharp
[TestClass]
public class TemplateRankingServiceTests
{
    [TestMethod("should return top 20 templates ranked by usage when period is default 7 days"), Ignore("TODO")]
    public void ReturnsTop20TemplatesForDefault7DayPeriod() { }
    // ... same pattern
}
```

### pytest (Python)

```python
import pytest

class TestTemplateRankingService:
    """Template usage ranking aggregation for operator dashboard."""

    # === Happy Path ===

    @pytest.mark.skip(reason="TODO")
    def test_returns_top_20_templates_ranked_by_usage_for_default_7_day_period(self):
        """should return top 20 templates ranked by usage when period is default 7 days"""

    @pytest.mark.skip(reason="TODO")
    def test_aggregates_usage_counts_across_multiple_users(self):
        """should aggregate usage counts correctly when multiple users use the same template"""

    # === Edge Cases ===

    @pytest.mark.skip(reason="TODO")
    def test_returns_empty_list_when_no_usage_data(self):
        """should return empty list when no templates have been used in the period"""
```

### Vitest / Jest (TypeScript)

```typescript
describe("TemplateRankingService", () => {
  // === Happy Path ===
  it.todo("should return top 20 templates ranked by usage when period is default 7 days");
  it.todo("should aggregate usage counts correctly when multiple users use the same template");

  // === Edge Cases ===
  it.todo("should return empty list when no templates have been used in the period");
  it.todo("should return exactly 20 items when more than 20 templates exist");

  describe("when custom date range is specified", () => {
    it.todo("should aggregate data only within the specified date range");
    it.todo("should throw error when start date is after end date");
  });

  // === Data Integrity ===
  it.todo("should not modify usage records when aggregating ranking data");
});
```

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Mock-dependent name | "should return data when repository is mocked" | Focus on behavior: "should return data when templates exist" |
| Implementation detail | "should call FindAsync with correct parameters" | Focus on outcome: "should return the matching template" |
| Vague name | "should work correctly" | Specify: "should return top 20 results sorted by usage count descending" |
| Duplicate coverage | Two tests for the same assertion | Merge or pick the more specific one |
| Missing category | All happy path, no edge cases | Check coverage categories checklist |
| Logic in outline | `it("...", () => { expect(...) })` | Use `it.todo("...")` or `[Fact(Skip = "TODO")]` only |
