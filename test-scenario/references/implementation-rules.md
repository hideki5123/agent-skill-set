# Test Implementation Rules

The 6 absolute rules for converting test outlines into executable test code (Phase 3). These rules are non-negotiable — strict mode only.

## Rule 1: Test Data Lifecycle Management

Test data creation and cleanup must be colocated to guarantee test isolation regardless of pass/fail.

### .NET (xUnit) — IAsyncLifetime

```csharp
public class OrderServiceTests : IAsyncLifetime
{
    private readonly AppDbContext _db;
    private User _testUser = null!;
    private Product _testProduct = null!;

    public OrderServiceTests(DatabaseFixture fixture)
    {
        _db = fixture.CreateContext();
    }

    public async Task InitializeAsync()
    {
        // Create test data
        _testUser = new User { Name = "Test User", Email = "test@example.com" };
        _testProduct = new Product { Name = "Widget", Price = 9.99m };
        _db.Users.Add(_testUser);
        _db.Products.Add(_testProduct);
        await _db.SaveChangesAsync();
    }

    public async Task DisposeAsync()
    {
        // Cleanup — runs regardless of test outcome
        _db.Users.Remove(_testUser);
        _db.Products.Remove(_testProduct);
        await _db.SaveChangesAsync();
        _db.Dispose();
    }
}
```

### .NET (NUnit) — SetUp / TearDown

```csharp
[TestFixture]
public class OrderServiceTests
{
    private AppDbContext _db = null!;
    private User _testUser = null!;

    [SetUp]
    public async Task SetUp()
    {
        _db = TestDbFactory.CreateContext();
        _testUser = new User { Name = "Test User" };
        _db.Users.Add(_testUser);
        await _db.SaveChangesAsync();
    }

    [TearDown]
    public async Task TearDown()
    {
        _db.Users.Remove(_testUser);
        await _db.SaveChangesAsync();
        _db.Dispose();
    }
}
```

### .NET (MSTest) — TestInitialize / TestCleanup

```csharp
[TestClass]
public class OrderServiceTests
{
    private AppDbContext _db = null!;
    private User _testUser = null!;

    [TestInitialize]
    public async Task Initialize()
    {
        _db = TestDbFactory.CreateContext();
        _testUser = new User { Name = "Test User" };
        _db.Users.Add(_testUser);
        await _db.SaveChangesAsync();
    }

    [TestCleanup]
    public async Task Cleanup()
    {
        _db.Users.Remove(_testUser);
        await _db.SaveChangesAsync();
        _db.Dispose();
    }
}
```

### pytest — Fixture with yield

```python
@pytest.fixture(autouse=True)
def setup_test_data(db_session):
    # Create test data
    user = User(name="Test User", email="test@example.com")
    product = Product(name="Widget", price=9.99)
    db_session.add_all([user, product])
    db_session.commit()

    yield {"user": user, "product": product}

    # Cleanup — runs regardless of test outcome
    db_session.delete(user)
    db_session.delete(product)
    db_session.commit()
```

### Vitest — beforeEach with onTestFinished

```typescript
describe("OrderService", () => {
  let testUser: User;
  let testProduct: Product;

  beforeEach(async () => {
    // Create test data
    testUser = await db.user.create({ data: { name: "Test User", email: "test@example.com" } });
    testProduct = await db.product.create({ data: { name: "Widget", price: 9.99 } });

    onTestFinished(async () => {
      // Cleanup — runs regardless of test outcome
      await db.product.delete({ where: { id: testProduct.id } });
      await db.user.delete({ where: { id: testUser.id } });
    });
  });
});
```

### Jest — beforeEach with afterEach

```typescript
describe("OrderService", () => {
  let testUser: User;
  let testProduct: Product;

  beforeEach(async () => {
    testUser = await db.user.create({ data: { name: "Test User" } });
    testProduct = await db.product.create({ data: { name: "Widget", price: 9.99 } });
  });

  afterEach(async () => {
    await db.product.delete({ where: { id: testProduct.id } });
    await db.user.delete({ where: { id: testUser.id } });
  });
});
```

## Rule 2: AAA Pattern (Arrange-Act-Assert)

Visually separate the three phases with blank lines and optional comments. Never mix phases.

```csharp
[Fact]
public async Task ReturnsTop20TemplatesForDefaultPeriod()
{
    // Arrange
    var service = new TemplateRankingService(_db);
    var endDate = DateTime.UtcNow;
    var startDate = endDate.AddDays(-7);

    // Act
    var result = await service.GetRankingAsync(startDate, endDate);

    // Assert
    Assert.Equal(20, result.Count);
    Assert.True(result.First().UsageCount >= result.Last().UsageCount);

    var dbRecords = await _db.TemplateUsages
        .Where(u => u.UsedAt >= startDate && u.UsedAt <= endDate)
        .GroupBy(u => u.TemplateId)
        .OrderByDescending(g => g.Count())
        .Take(20)
        .ToListAsync();
    Assert.Equal(dbRecords.Count, result.Count);
}
```

**Rules:**
- **Arrange**: Set up preconditions, create service instances, prepare inputs. Shared setup goes in `beforeEach`/`SetUp`/`InitializeAsync`; test-specific setup stays in the test method.
- **Act**: Execute exactly ONE behavior. A single method call or operation.
- **Assert**: Verify postconditions and invariants. Can have multiple assertions, but they should all relate to the single Act.

## Rule 3: No Internal Module Mocking

**Absolutely prohibited** — do not mock internal modules:

| Framework | Prohibited |
|-----------|-----------|
| .NET | `Mock<IRepository>`, `Substitute.For<IService>()` (Moq, NSubstitute, FakeItEasy) for internal services |
| pytest | `monkeypatch`, `unittest.mock.patch` for internal modules |
| Vitest | `vi.mock("./repository")`, `vi.spyOn(internalModule, "method")` |
| Jest | `jest.mock("./repository")`, `jest.spyOn(internalModule, "method")` |

### What to use instead

| Scenario | Approach |
|----------|----------|
| Database operations | Use a real test database. Verify state with ORM queries after operations. |
| External HTTP APIs | Use a Docker-based mock server (WireMock, Prism, MockServer) instead of code-level mocking. |
| File system operations | Use a real temporary directory, clean up after test. |
| Time-dependent logic | Use injectable clock abstractions (e.g., `IClock`, `TimeProvider` in .NET 8+). These are NOT mocks — they are designed injection points. |

### Boundary: what counts as "internal"

- Internal: repositories, services, API clients, database connections — code you own
- External injection points: `IClock`, `IOptions<T>`, configuration — these are designed to be swapped and are acceptable

## Rule 4: Design by Contract (DbC)

### Postcondition Verification (success cases)

Assert BOTH the return value AND the database state:

```csharp
[Fact]
public async Task CreatesOrderAndReturnsOrderId()
{
    // Arrange
    var service = new OrderService(_db);

    // Act
    var orderId = await service.CreateOrderAsync(_testUser.Id, _testProduct.Id, quantity: 2);

    // Assert — return value
    Assert.NotEqual(Guid.Empty, orderId);

    // Assert — database state
    var order = await _db.Orders.FindAsync(orderId);
    Assert.NotNull(order);
    Assert.Equal(_testUser.Id, order.UserId);
    Assert.Equal(_testProduct.Id, order.ProductId);
    Assert.Equal(2, order.Quantity);
    Assert.Equal(19.98m, order.TotalPrice);
}
```

### Invariant Verification (error cases)

Assert BOTH that the error occurs AND that the database state is unchanged:

```csharp
[Fact]
public async Task ThrowsWhenInsufficientStockAndDoesNotCreateOrder()
{
    // Arrange
    var service = new OrderService(_db);
    var orderCountBefore = await _db.Orders.CountAsync();
    var stockBefore = await _db.Products.Where(p => p.Id == _testProduct.Id).Select(p => p.Stock).FirstAsync();

    // Act & Assert — error is thrown
    await Assert.ThrowsAsync<InsufficientStockException>(
        () => service.CreateOrderAsync(_testUser.Id, _testProduct.Id, quantity: 999)
    );

    // Assert — database state unchanged (invariant)
    var orderCountAfter = await _db.Orders.CountAsync();
    var stockAfter = await _db.Products.Where(p => p.Id == _testProduct.Id).Select(p => p.Stock).FirstAsync();
    Assert.Equal(orderCountBefore, orderCountAfter);
    Assert.Equal(stockBefore, stockAfter);
}
```

Equivalent pattern for pytest:

```python
def test_raises_when_insufficient_stock_and_does_not_create_order(self, db_session, test_data):
    # Arrange
    service = OrderService(db_session)
    order_count_before = db_session.query(Order).count()
    stock_before = db_session.query(Product).get(test_data["product"].id).stock

    # Act & Assert — error is raised
    with pytest.raises(InsufficientStockError):
        service.create_order(test_data["user"].id, test_data["product"].id, quantity=999)

    # Assert — database state unchanged (invariant)
    order_count_after = db_session.query(Order).count()
    stock_after = db_session.query(Product).get(test_data["product"].id).stock
    assert order_count_before == order_count_after
    assert stock_before == stock_after
```

## Rule 5: Readability & Maintainability

Each test method must be self-explanatory when read in isolation.

**Guidelines:**
- Test name describes the behavior being verified (see outline-rules.md for naming)
- Even when `beforeEach`/`SetUp` handles shared setup, the test body should make clear what scenario is being tested
- Use descriptive variable names: `expectedTopTemplate`, `invalidDateRange`, not `x`, `data`
- If a test needs context from setup, add a brief comment: `// Given: 25 templates with usage data exist (created in SetUp)`
- Avoid magic numbers: use named constants or variables that convey meaning

**Anti-patterns:**
- A test that requires reading 3 other methods to understand
- Assert-only tests with no clear Act phase
- Shared helper methods that obscure what is actually being tested

## Rule 6: Test Utility Usage

### Discovery

1. Check for existing test utility directories:
   - .NET: `TestHelpers/`, `TestFixtures/`, `TestUtilities/`
   - Python: `conftest.py`, `test_utils/`, `tests/helpers/`
   - TypeScript: `src/test-utils/`, `tests/helpers/`, `__tests__/utils/`
2. Read existing utilities to understand available helpers
3. Use existing utilities wherever applicable

### Creation

When useful utilities are missing, create them:
- Database factory methods: `CreateTestUser()`, `CreateTestProduct()`
- Common assertion helpers: `AssertDatabaseUnchanged()`, `AssertOrderCreatedCorrectly()`
- Fixture builders: fluent APIs for complex test data setup

### Refactoring

As the test suite grows, watch for:
- Repeated setup patterns across test classes → extract to shared fixtures
- Duplicate assertion sequences → extract to assertion helpers
- Complex data creation → extract to builder/factory pattern

When better utilities would improve the suite, propose a zero-base rebuild of the relevant utility module rather than patching incrementally.
