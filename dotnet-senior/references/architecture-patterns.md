# .NET Architecture Patterns Reference

Opinionated guide to architecture patterns for .NET 8/10. Covers trade-offs, when to use, when NOT to use, project structures, and recommended NuGet packages.

---

## Decision Matrix

| Scenario | Recommended Pattern |
|----------|-------------------|
| MVP / startup, small team, CRUD-heavy | **Vertical Slices** with Minimal APIs |
| Enterprise app, complex domain, large team | **Clean Architecture** with DDD |
| New product, unsure about boundaries | **Modular Monolith** |
| Financial/audit system requiring full history | **CQRS + Event Sourcing** (Marten + Wolverine) |
| Existing MVC monolith needing modernization | **Strangler Fig** → Modular Monolith → selective extraction |
| Experienced team wanting max velocity | **Vertical Slices + Clean Architecture hybrid** |
| High-traffic read-heavy API | **Simple CQRS** (separate read models, no event sourcing) |

---

## 1. Clean Architecture (Jason Taylor Style)

### Layer Structure

```
Domain  ←  Application  ←  Infrastructure  ←  Presentation (Web/API)
```

- **Domain**: Entities, value objects, enumerations, domain events, exceptions. Zero external dependencies.
- **Application**: Commands/queries (use cases), interfaces (ports), validators, DTOs/mappings. Depends only on Domain.
- **Infrastructure**: EF Core, external services, file I/O, email. Implements Application interfaces.
- **Presentation**: Endpoints, middleware, filters. Orchestrates via Application layer.

**Dependency Rule**: All dependencies point inward. Enforced via project references.

### CQRS with MediatR/Wolverine

Each use case = one command/query + handler. Pipeline behaviors for cross-cutting:

- **Validation** — FluentValidation before handler
- **Logging** — structured logging around requests
- **Authorization** — permission checks as pipeline middleware
- **Performance** — flag slow requests

### When to Use

- Large teams (5+) with clear ownership boundaries
- Long-lived products (3+ year horizon)
- Complex domain justifying abstraction cost
- Regulatory/compliance requirements

### When NOT to Use

- CRUD-heavy APIs with thin business logic — ceremony-to-value ratio is terrible
- Small teams (1-3) building MVPs — layering slows you down
- Short-lived projects or PoCs
- Microservices already small in scope

### Project Structure

```
src/
  Company.Product.Domain/
  Company.Product.Application/
  Company.Product.Infrastructure/
  Company.Product.Web/
tests/
  Company.Product.Domain.UnitTests/
  Company.Product.Application.UnitTests/
  Company.Product.Infrastructure.IntegrationTests/
  Company.Product.Web.FunctionalTests/
```

### Key Packages

| Package | Purpose | Notes |
|---------|---------|-------|
| `Wolverine` | CQRS dispatch, messaging | Apache 2.0, source-generated |
| `MediatR` v13+ | In-process messaging | RPL-1.5 / Commercial (free <$5M revenue) |
| `FluentValidation` | Typed validation rules | Apache 2.0 |
| `Mapperly` | Compile-time mapping | Apache 2.0, zero reflection |
| `Ardalis.GuardClauses` | Defensive programming | MIT |
| `ErrorOr` | Result pattern | MIT |
| `Ardalis.Specification` | Specification pattern | MIT |

---

## 2. Vertical Slice Architecture

### Core Philosophy

Jimmy Bogard (2018). Couple vertically by feature, not horizontally by layer. Each feature is self-contained: endpoint + models + validation + handler + data access.

### Feature-Based Organization

```
Features/
  Products/
    CreateProduct/
      CreateProductEndpoint.cs
      CreateProductCommand.cs
      CreateProductHandler.cs
      CreateProductValidator.cs
    GetProduct/
      GetProductEndpoint.cs
      GetProductQuery.cs
      GetProductHandler.cs
  Orders/
    PlaceOrder/
      ...
```

### Clean Architecture vs Vertical Slices

| Dimension | Clean Architecture | Vertical Slices |
|-----------|-------------------|----------------|
| Organization | By layer | By feature |
| Adding a feature | Touch 4+ projects | Add one folder |
| Code navigation | Jump across projects | Everything co-located |
| Shared abstractions | Heavy | Minimal |
| Code duplication | Low | Intentionally higher |
| Team scaling | Good with layer ownership | Excellent — no conflicts |
| Domain modeling | Strong | Weaker unless extracted |
| Best for | Complex domains, large teams | CRUD-heavy, rapid delivery |

### Senior-Level Trade-offs

**Duplication concern is overstated.** Most "duplication" across slices is incidental — two features look similar today but diverge tomorrow. Premature extraction creates worse coupling.

**Domain modeling gap is real.** VSA doesn't push toward rich domain models. For complex domains, you'll extract shared logic anyway — effectively hybridizing with Clean Architecture.

**Pragmatic consensus (2025-2026):** Start with vertical slices. Extract shared domain logic into a Domain project only when duplication is proven and stable.

### When NOT to Use

- Junior teams needing "guardrails" of layered architecture
- Deeply shared business rules across many features
- Compliance culture requiring explicit layer traceability

### Project Structure

```
src/
  MyApp.Api/
    Features/
      Products/
        CreateProduct.cs      # Command + Handler + Endpoint in one file
        GetProduct.cs
        ProductDto.cs
      Orders/
        PlaceOrder.cs
    Common/
      Behaviors/
      Middleware/
    Infrastructure/
tests/
  MyApp.Api.Tests/
    Features/
      Products/
        CreateProductTests.cs
```

### Key Packages

| Package | Purpose |
|---------|---------|
| `Carter` | Module-based Minimal API organization |
| `FastEndpoints` | REPR pattern, built-in validation |
| `Wolverine` or `MediatR` | Request dispatch (optional) |
| `Mapperly` | Compile-time mapping |

---

## 3. CQRS + Event Sourcing

### Command/Query Separation

Separate write model (commands) from read model (queries). **Independent of event sourcing.**

**Simple CQRS (recommended starting point):**
- Commands → domain logic → `SaveChanges`
- Queries → optimized read paths (raw SQL, Dapper, denormalized views)
- Same database, different query paths

**Full CQRS + Event Sourcing:**
- Commands → domain events → event store (source of truth)
- Read models built by projecting (replaying) events
- Current state = replay of event stream

### When to Use Full Event Sourcing

- **Audit requirements non-negotiable** — financial, healthcare, legal compliance
- **Temporal queries** — "What was state on March 15?"
- **Complex event-driven workflows** — fine-grained downstream reactions
- **Analytics on behavioral data** — event stream IS the asset

### When NOT to Use Event Sourcing

- **Simple CRUD** — overhead of replay, projections, eventual consistency is enormous
- **Teams without ES experience** — learning curve steep, failure modes non-obvious
- **Simple audit needs** — `AuditEntries` table with before/after JSON covers 95% of cases
- **Strong consistency required everywhere** — ES inherently introduces eventual consistency

### Libraries (2025-2026)

| Library | Type | Notes |
|---------|------|-------|
| **Marten** v8+ | Event Store + Doc DB on PostgreSQL | Pragmatic default. Uses existing PostgreSQL. MIT. |
| **Wolverine** | CQRS + Messaging | Pairs with Marten ("Critter Stack"). Source-generated. Apache 2.0. |
| **EventStoreDB** | Dedicated event store | For very high-throughput. Adds operational complexity. |
| **MassTransit** v8+ | Distributed messaging / sagas | RabbitMQ/Azure Service Bus. Now commercial licensing. |

### Senior Guidance

1. **Start with simple CQRS.** Separate read DTOs from write commands. Different query paths for reads (even raw SQL) vs domain model for writes. Solves 80% of problems.
2. **Add event sourcing only when business demands it.** Operational cost of event versioning, projection rebuilds, and eventual consistency debugging is substantial.
3. **Marten over EventStoreDB for most teams** — one less database to operate.

---

## 4. Domain-Driven Design (DDD) in .NET

### Aggregates

Cluster of entities/value objects as single consistency boundary. All invariants hold after modification. External access through aggregate root only.

```csharp
public class Order : AggregateRoot
{
    private readonly List<OrderLine> _lines = new();
    public IReadOnlyCollection<OrderLine> Lines => _lines.AsReadOnly();

    public void AddLine(ProductId productId, int quantity, Money unitPrice)
    {
        Guard.Against.NegativeOrZero(quantity, nameof(quantity));
        var line = new OrderLine(productId, quantity, unitPrice);
        _lines.Add(line);
        AddDomainEvent(new OrderLineAddedEvent(Id, line));
    }
}
```

### Value Objects

Immutable, identity-less, structural equality. Use C# `record` types.

```csharp
public record Money(decimal Amount, string Currency)
{
    public Money Add(Money other)
    {
        if (Currency != other.Currency) throw new CurrencyMismatchException();
        return this with { Amount = Amount + other.Amount };
    }
}
```

### EF Core Implementation Patterns

**Value Objects → Complex Types (EF Core 8+)**

```csharp
modelBuilder.ComplexProperty<Order>(o => o.ShippingAddress);
```

**Strongly-Typed IDs:**

```csharp
public readonly record struct OrderId(Guid Value);

modelBuilder.Entity<Order>()
    .Property(o => o.Id)
    .HasConversion(id => id.Value, v => new OrderId(v));
```

**Encapsulated Collections:**

```csharp
public class Order
{
    public OrderId Id { get; private set; }
    private readonly List<OrderLine> _lines = new();
    public IReadOnlyCollection<OrderLine> Lines => _lines.AsReadOnly();
}
```

### Rich vs Anemic Models

| Dimension | Anemic | Rich |
|-----------|--------|------|
| Logic lives in | Service/manager classes | Inside aggregate |
| Testing | Mock dependencies | Pure unit tests |
| EF Core friction | Low | Moderate (private setters, backing fields) |
| Best for | Simple CRUD | Complex invariants |

**Senior take:** Most .NET codebases are anemic by default (EF tutorials teach data-first). Cost compounds — rules scatter across services, controllers, stored procs. Invest in rich models for genuine domain complexity.

### Key Packages

| Package | Purpose |
|---------|---------|
| `Vogen` | Source-generated value objects |
| `StronglyTypedId` | Source-generated typed IDs |
| `Ardalis.GuardClauses` | Guard clauses for invariants |
| `ErrorOr` / `FluentResults` | Domain results without exceptions |

---

## 5. Minimal API Patterns

### Organization Strategies

**Extension Methods (small-medium):**

```csharp
public static class ProductEndpoints
{
    public static void MapProductEndpoints(this WebApplication app)
    {
        var group = app.MapGroup("/api/products").WithTags("Products");
        group.MapGet("/", GetProducts);
        group.MapPost("/", CreateProduct).RequireAuthorization();
    }
}
// Program.cs: app.MapProductEndpoints();
```

**Carter Modules (medium-large):**

```csharp
public class ProductModule : ICarterModule
{
    public void AddRoutes(IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/api/products").WithTags("Products");
        group.MapGet("/", GetProducts);
        group.MapPost("/", CreateProduct);
    }
}
```

**FastEndpoints / REPR (large):**

```csharp
public class CreateProductEndpoint : Endpoint<CreateProductRequest, CreateProductResponse>
{
    public override void Configure()
    {
        Post("/api/products");
        AllowAnonymous();
    }

    public override async Task HandleAsync(CreateProductRequest req, CancellationToken ct)
    {
        await SendAsync(response);
    }
}
```

### Controllers vs Minimal APIs

| Factor | Controllers | Minimal APIs |
|--------|------------|-------------|
| Performance | Baseline | ~15-35% faster |
| Team familiarity | Most devs know MVC | Newer pattern |
| Scale organization | Built-in | Needs Carter/FastEndpoints |
| OpenAPI | Mature | Good with `.WithOpenApi()` |

**Recommendation:** Minimal APIs with Carter or FastEndpoints for new .NET 8+ projects. Controllers not deprecated — two can coexist.

### Key Packages

| Package | Purpose |
|---------|---------|
| `Carter` | Module-based Minimal APIs + FluentValidation |
| `FastEndpoints` | REPR, built-in validation, ~45k req/s over MVC |
| `Asp.Versioning.Http` | API versioning |
| `Scalar.AspNetCore` | Modern API docs (Swagger UI replacement) |

---

## 6. Modular Monolith

### Concept

Single deployable with strictly enforced module boundaries. Each module owns its data, logic, and API surface. Microservice-style boundaries without distributed systems cost.

### Module Structure

```
src/
  Host/                          # Bootstrapper
  Modules/
    Ordering/
      Ordering.Contracts/        # Public: interfaces, DTOs, integration events
      Ordering.Core/             # Internal: domain + application
      Ordering.Infrastructure/   # Internal: data access
    Catalog/
      Catalog.Contracts/
      Catalog.Core/
      Catalog.Infrastructure/
  Shared/
    Shared.Kernel/               # Base classes, common value objects
    Shared.Infrastructure/       # Auth, logging, event bus
```

### Boundary Enforcement

- **Project references**: Only reference `.Contracts`, never `.Core`/`.Infrastructure`
- **Separate DbContexts**: Each module owns its schema. No cross-module joins.
- **Architecture tests**: NetArchTest/ArchUnitNET in CI

### Inter-Module Communication

| Pattern | Mechanism | When |
|---------|-----------|------|
| Sync (in-process) | Interface via DI, MediatR/Wolverine | Need immediate response |
| Async (in-process) | In-memory event bus | React to changes, no immediate consistency |
| Async (durable) | Outbox + message broker | Guaranteed delivery, microservice prep |

### Migration to Microservices

1. Start monolithic — all modules in one deployable
2. Prove boundaries — modules communicate only via events
3. Extract module — replace in-process bus with broker, own database, deploy independently
4. Repeat selectively — most modules stay in monolith

**Critical insight:** Teams starting with microservices often get distributed monolith (worst of both worlds). Modular monolith forces proven boundaries first.

### Key Packages

| Package | Purpose |
|---------|---------|
| `Wolverine` | In-process messaging, outbox, sagas |
| `MassTransit` | Distributed messaging (RabbitMQ, Azure SB) |
| `NetArchTest.Rules` | Architecture boundary enforcement |
| `ArchUnitNET` | Alternative architecture testing |

---

## NuGet Licensing Alert (2025-2026)

Several popular packages changed to commercial licensing:

| Package | New License | Free Tier |
|---------|------------|-----------|
| `MediatR` v13+ | RPL-1.5 / Commercial | <$5M revenue, education, non-profit |
| `AutoMapper` v13+ | RPL-1.5 / Commercial | Same as MediatR |
| `MassTransit` v8+ | Commercial | Limited |

**Alternatives:**
- MediatR → **Wolverine** (Apache 2.0) or **Mediator** by martinothamar (MIT)
- AutoMapper → **Mapperly** (Apache 2.0) or **Mapster** (MIT)
- MassTransit → **Wolverine** for simpler cases, **Brighter** (MIT)

---

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Solution | `Company.Product` | `Acme.OrderSystem` |
| Projects | `Company.Product.Layer` | `Acme.OrderSystem.Domain` |
| Test projects | `...Layer.TestType` | `...Domain.UnitTests` |
| Commands | `{Verb}{Noun}Command` | `PlaceOrderCommand` |
| Queries | `Get/List{Noun}Query` | `GetOrderQuery` |
| Handlers | `{CommandOrQuery}Handler` | `PlaceOrderCommandHandler` |
| Validators | `{CommandOrQuery}Validator` | `PlaceOrderCommandValidator` |
| Integration events | `{Noun}{PastVerb}IntegrationEvent` | `OrderPlacedIntegrationEvent` |

---

## Testing Stack

| Package | Purpose | License |
|---------|---------|---------|
| `xUnit` v2.9+ | Test framework | Apache 2.0 |
| `FluentAssertions` v8+ | Readable assertions | Apache 2.0 |
| `NSubstitute` v5+ | Mocking (preferred over Moq) | BSD |
| `Testcontainers` | Real containers for integration tests | MIT |
| `Bogus` | Fake data generation | MIT |
| `Respawn` | Fast DB reset between tests | Apache 2.0 |
| `NetArchTest.Rules` | Architecture boundary enforcement | MIT |
| `Verify` | Snapshot testing | MIT |
