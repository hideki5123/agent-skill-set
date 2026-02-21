# BDD Guide

When to use Behavior-Driven Development (BDD) and how to write effective scenarios.

## When to Use BDD

### Use BDD When:

1. **Stakeholder Communication**
   - Business requirements need validation
   - Non-technical stakeholders review test cases
   - Acceptance criteria need documentation

2. **User-Facing Features**
   - User stories drive development
   - Behavior is more important than implementation
   - Feature documentation is valuable

3. **Complex Business Logic**
   - Multiple scenarios per feature
   - Edge cases need business validation
   - Rules are complex and need clarity

### Use TDD (not BDD) When:

1. **Technical Implementation**
   - Internal APIs or utilities
   - Performance optimizations
   - Infrastructure code

2. **Developer-Only Audience**
   - No stakeholder review needed
   - Quick iteration preferred
   - Technical details dominate

3. **Simple Features**
   - Single obvious behavior
   - Minimal edge cases
   - Not worth the BDD overhead

## BDD Structure

### Given-When-Then

```gherkin
Given [initial context/state]
When [action is performed]
Then [expected outcome]
```

### Extended Keywords

```gherkin
Given [context]
  And [additional context]
When [action]
  And [additional action]
Then [outcome]
  And [additional outcome]
  But [exception to outcome]
```

## Writing Good Scenarios

### DO:
- Write from user's perspective
- Use domain language (ubiquitous language)
- Keep scenarios focused (one behavior each)
- Make scenarios independent
- Use concrete examples

### DON'T:
- Include implementation details
- Use technical jargon
- Combine multiple behaviors
- Create scenario dependencies
- Use vague language

## Examples

### Good Scenario
```gherkin
Scenario: Customer receives loyalty points for purchase
  Given a customer with Gold status
  And a shopping cart totaling $100
  When the customer completes checkout
  Then the customer should earn 200 loyalty points
  And a confirmation email should be sent
```

### Bad Scenario (Too Technical)
```gherkin
Scenario: Update database with points
  Given a customer record in PostgreSQL
  When POST /api/checkout is called with JSON payload
  Then UPDATE customers SET points = points + 200
  And SendGrid API is called with email template
```

### Bad Scenario (Too Vague)
```gherkin
Scenario: Points work correctly
  Given a customer
  When they buy something
  Then points are updated
```

## Scenario Tables

Use tables for data-driven scenarios:

```gherkin
Scenario Outline: Loyalty points vary by status
  Given a customer with <status> status
  And a shopping cart totaling $<amount>
  When the customer completes checkout
  Then the customer should earn <points> loyalty points

  Examples:
    | status   | amount | points |
    | Bronze   | 100    | 100    |
    | Silver   | 100    | 150    |
    | Gold     | 100    | 200    |
    | Platinum | 100    | 300    |
```

## Background

Use Background for common setup:

```gherkin
Feature: SKU Restock History Export

  Background:
    Given a connected RPC gateway
    And a store "store-001" exists

  Scenario: Export history with matching events
    Given restock events exist for SKU "SKU-001"
    When I export restock history for SKU "SKU-001"
    Then I should receive a CSV with matching events

  Scenario: Export history with no matches
    Given no restock events exist for SKU "SKU-999"
    When I export restock history for SKU "SKU-999"
    Then I should receive a CSV with only headers
```

## Converting BDD to Test Code

### Gherkin Scenario
```gherkin
Scenario: Export restock history for valid SKU
  Given a store with restock events for SKU "SKU-001"
  When I export restock history for SKU "SKU-001"
  Then the CSV should contain matching events
  And dates should be in ISO 8601 format
```

### xUnit Test (C#)
```csharp
[Fact]
public async Task ExportRestockHistory_WithMatchingSku_ReturnsFilteredCsv()
{
    // Given: a store with restock events for SKU "SKU-001"
    var response = new GetLocationAuditLogResponse
    {
        Log = new List<LocationAuditLog>
        {
            CreateRestockedLog(DateTime.UtcNow, new[] { "SKU-001" })
        }
    };
    _mockRpcGateway.Setup(x => x.GetStockLocationAuditLog(...))
        .ReturnsAsync(response);

    // When: I export restock history for SKU "SKU-001"
    await _sut.ExportSkuRestockHistory("store-001", "loc-001", "SKU-001",
        null, null, _outputWriter);

    // Then: the CSV should contain matching events
    var csv = _outputWriter.ToString();
    var lines = csv.Split(Environment.NewLine, StringSplitOptions.RemoveEmptyEntries);
    lines.Should().HaveCount(2); // Header + 1 event

    // And: dates should be in ISO 8601 format
    var dataLine = lines[1];
    var dateField = dataLine.Split(',')[0];
    dateField.Should().MatchRegex(@"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}");
}
```

## Team Discussion for BDD Scenarios

When using BDD with team discussion:

1. **Draft Scenarios** - Initial feature understanding
2. **Team Review** - Each agent reviews scenarios for their domain
3. **Refine** - Update based on feedback
4. **Approve** - User validates scenarios match expectations
5. **Implement** - Write test code from scenarios

### Team Review Focus

| Agent | Scenario Review Focus |
|-------|----------------------|
| Architecture | Are scenarios complete? Missing behaviors? |
| Security | Are security scenarios included? Edge cases? |
| Resource | Performance scenarios? Limit scenarios? |
| Devil's Advocate | Missing failure scenarios? False assumptions? |
