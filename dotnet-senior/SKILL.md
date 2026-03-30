---
name: dotnet-senior
description: >
  Senior-level .NET development guidance for architecture, code review, scaffolding,
  EF Core, ASP.NET Core, Blazor, and MAUI targeting .NET 8 and .NET 10.
  Provides opinionated best practices, modern C# idioms, security hardening,
  performance optimization, and testing strategies at a staff/senior engineer level.
  Trigger patterns (match any variation):
  .NET / dotnet / dot net / .net /
  C# / csharp / c sharp / c-sharp /
  ASP.NET / aspnet / asp.net core /
  Entity Framework / EF Core / ef core /
  Blazor / MAUI / maui /
  NuGet / nuget /
  Clean Architecture + .NET / CQRS + .NET / DDD + .NET /
  {review, scaffold, create, design, architect, optimize, migrate} + {C#, .NET, dotnet, csharp} /
  "dotnet new" / "dotnet build" / "dotnet test" / "dotnet publish" /
  ".NET best practices" / "C# patterns" / "senior .NET" / ".NET architecture"
version: 1.0.0
---

# .NET Senior Development Skill

Provide senior-level .NET development guidance. Act as a staff engineer with deep .NET expertise
when advising on architecture, reviewing code, scaffolding projects, or optimizing performance.

## Constraints

- Target **.NET 8** (LTS) and **.NET 10** (current). Flag when advice is version-specific.
- Always prefer modern C# idioms (primary constructors, collection expressions, pattern matching, records).
- Default to **minimal APIs** for new web projects unless the user's codebase uses controllers.
- Favor **explicit over implicit** — no magic strings, prefer strongly-typed configuration.
- Security-first: always consider OWASP top 10 for .NET, validate inputs, use parameterized queries.
- Performance-aware: mention allocation impact, async best practices, caching strategies where relevant.
- Test-aware: suggest testing approach alongside implementation (xUnit preferred, NUnit acceptable).

## Version-Specific References

When the user's project targets a specific .NET version, load the corresponding knowledge base:

- **.NET 8 (LTS)** → Read `references/dotnet8-knowledge.md` for C# 12 features, ASP.NET Core 8, EF Core 8, Blazor 8, performance APIs
- **.NET 10** → Read `references/dotnet10-knowledge.md` for C# 14 features, ASP.NET Core 10, EF Core 10, migration path from .NET 8

If the version is unclear, ask. Do not guess — guidance differs between versions.

## Architecture Guidance

When the user asks about architecture, project structure, or design patterns:

1. **Understand scale**: Ask about team size, expected complexity, and timeline if not obvious
2. **Recommend pattern**: Based on scale, suggest the appropriate pattern:
   - **Small API / prototype** → Minimal API with vertical slices
   - **Medium app / single team** → Clean Architecture (Jason Taylor style)
   - **Complex domain / multiple teams** → DDD with bounded contexts
   - **High-read/write asymmetry** → CQRS (with or without event sourcing)
   - **Monolith with future split potential** → Modular Monolith
3. **Explain trade-offs**: Always explain why NOT to use a pattern, not just why to use it
4. **Provide structure**: Show concrete `dotnet sln` / project layout

Read `references/architecture-patterns.md` for detailed pattern descriptions, project templates, and NuGet recommendations.

### Architecture Design Review (Team)

For significant architecture decisions (new project, major refactor, migration), create an agent team to explore from different angles: **Architecture, Security, QA/QC, Devil's Advocate**.

Read `references/team-roles.md` for the detailed perspective prompts and synthesis protocol.

## Code Review

When reviewing C# or .NET code, apply the senior-level review checklist:

### Quick Review (default)

Check these in order of priority:

1. **Correctness** — Does it do what it claims? Edge cases handled?
2. **Security** — Input validation, SQL injection, XSS, auth checks, secrets exposure
3. **Performance** — Unnecessary allocations, async/await misuse, N+1 queries, missing caching
4. **Maintainability** — Naming, single responsibility, appropriate abstractions, testability
5. **Modern idioms** — Using older patterns when modern C# has better alternatives

### Deep Review

For thorough reviews, read `references/review-checklist.md` for the full checklist covering:
- Architecture alignment
- Error handling and resilience
- Concurrency and thread safety
- API design (REST conventions, versioning, pagination)
- EF Core query patterns
- Dependency injection usage
- Logging and observability
- Configuration management

## Project Scaffolding

When creating new .NET projects:

### Solution Structure

```
src/
├── MyApp.Domain/              # Entities, value objects, domain events, interfaces
├── MyApp.Application/         # Use cases, DTOs, validators, mapping
├── MyApp.Infrastructure/      # EF Core, external services, file system
├── MyApp.Api/                 # Minimal APIs or Controllers, middleware, DI setup
└── MyApp.ServiceDefaults/     # Shared Aspire defaults (if using .NET Aspire)
tests/
├── MyApp.UnitTests/           # Domain and Application layer tests
├── MyApp.IntegrationTests/    # Infrastructure tests with real dependencies
└── MyApp.ArchTests/           # Architecture rule enforcement (NetArchTest)
```

Adjust based on chosen architecture pattern. For vertical slices, use feature folders instead.

### Essential NuGet Packages

| Category | Package | Purpose |
|----------|---------|---------|
| Validation | FluentValidation | Request/command validation |
| Mapping | Mapster or Mapperly | DTO mapping (compile-time preferred) |
| CQRS | MediatR or Wolverine | Command/query dispatch |
| Testing | xUnit + FluentAssertions + NSubstitute | Test framework stack |
| Architecture | NetArchTest.Rules | Enforce architecture boundaries |
| API docs | Scalar or Swashbuckle | OpenAPI documentation |
| Resilience | Microsoft.Extensions.Http.Resilience | HTTP retry/circuit breaker |
| Logging | Serilog + Serilog.Sinks.* | Structured logging |
| Health | AspNetCore.HealthChecks.* | Health check endpoints |

### Project Creation Commands

```bash
# Create solution
dotnet new sln -n MyApp

# Create projects
dotnet new classlib -n MyApp.Domain -o src/MyApp.Domain
dotnet new classlib -n MyApp.Application -o src/MyApp.Application
dotnet new classlib -n MyApp.Infrastructure -o src/MyApp.Infrastructure
dotnet new webapi -n MyApp.Api -o src/MyApp.Api --use-minimal-apis
dotnet new xunit -n MyApp.UnitTests -o tests/MyApp.UnitTests
dotnet new xunit -n MyApp.IntegrationTests -o tests/MyApp.IntegrationTests

# Add to solution
dotnet sln add src/**/*.csproj tests/**/*.csproj

# Add project references (dependency rule: outer → inner)
dotnet add src/MyApp.Application reference src/MyApp.Domain
dotnet add src/MyApp.Infrastructure reference src/MyApp.Application
dotnet add src/MyApp.Api reference src/MyApp.Infrastructure
```

## Entity Framework Core

Senior-level EF Core guidance:

- **Always use migrations** — never `EnsureCreated()` in production
- **Prefer `AsNoTracking()`** for read-only queries
- **Avoid lazy loading** — use explicit `Include()` or projection with `Select()`
- **Use split queries** for complex includes: `.AsSplitQuery()`
- **Parameterize everything** — never interpolate user input into raw SQL
- **Use value converters** for enums, strongly-typed IDs
- **Configure in `IEntityTypeConfiguration<T>`** — not in `OnModelCreating`
- **Index strategically** — composite indexes for common query patterns
- **Use compiled queries** for hot paths: `EF.CompileAsyncQuery()`

## ASP.NET Core Patterns

### Minimal API Organization

```csharp
// Group endpoints by feature
public static class OrderEndpoints
{
    public static void MapOrderEndpoints(this IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/api/orders")
            .WithTags("Orders")
            .RequireAuthorization();

        group.MapGet("/", GetOrders);
        group.MapGet("/{id:guid}", GetOrderById);
        group.MapPost("/", CreateOrder)
            .AddEndpointFilter<ValidationFilter<CreateOrderRequest>>();
    }
}

// In Program.cs
app.MapOrderEndpoints();
```

### Middleware Pipeline Order

```csharp
// Correct order matters:
app.UseExceptionHandler();
app.UseHsts();
app.UseHttpsRedirection();
app.UseStaticFiles();
app.UseRouting();
app.UseCors();
app.UseAuthentication();
app.UseAuthorization();
app.UseRateLimiter();
// Map endpoints last
```

### Configuration Pattern

```csharp
// Strongly-typed options
public sealed class DatabaseOptions
{
    public const string SectionName = "Database";
    public required string ConnectionString { get; init; }
    public int MaxRetryCount { get; init; } = 3;
}

// Registration with validation
builder.Services.AddOptionsWithValidateOnStart<DatabaseOptions>()
    .BindConfiguration(DatabaseOptions.SectionName)
    .ValidateDataAnnotations();
```

## Testing Strategy

### Test Pyramid for .NET

1. **Unit Tests** (70%) — Domain logic, application services (mock infrastructure)
2. **Integration Tests** (20%) — EF Core queries, API endpoints (use `WebApplicationFactory`)
3. **Architecture Tests** (10%) — Dependency rules, naming conventions (NetArchTest)

### Integration Test Pattern

```csharp
public class OrderApiTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly HttpClient _client;

    public OrderApiTests(WebApplicationFactory<Program> factory)
    {
        _client = factory.WithWebHostBuilder(builder =>
        {
            builder.ConfigureServices(services =>
            {
                // Replace real DB with test container or in-memory
            });
        }).CreateClient();
    }

    [Fact]
    public async Task CreateOrder_ValidRequest_Returns201()
    {
        var request = new CreateOrderRequest { /* ... */ };
        var response = await _client.PostAsJsonAsync("/api/orders", request);
        response.StatusCode.Should().Be(HttpStatusCode.Created);
    }
}
```

### Architecture Test Example

```csharp
[Fact]
public void Domain_ShouldNotReference_Infrastructure()
{
    var result = Types.InAssembly(typeof(Order).Assembly)
        .ShouldNot()
        .HaveDependencyOn("MyApp.Infrastructure")
        .GetResult();

    result.IsSuccessful.Should().BeTrue();
}
```

## Performance Checklist

- Use `Span<T>` and `Memory<T>` for buffer operations — avoid byte array allocations
- Use `StringComparison.Ordinal` for non-user-facing string comparisons
- Use `ArrayPool<T>.Shared` or `MemoryPool<T>.Shared` for temporary buffers
- Use `FrozenDictionary<K,V>` / `FrozenSet<T>` for read-heavy lookup tables (.NET 8+)
- Use `SearchValues<T>` for character/byte searches (.NET 8+)
- Avoid `async void` — always return `Task` or `ValueTask`
- Use `ValueTask` for hot paths that often complete synchronously
- Use `IAsyncEnumerable<T>` for streaming large result sets
- Use `System.Threading.Channels` instead of `BlockingCollection<T>`
- Profile with `BenchmarkDotNet` before optimizing — measure, don't guess

## Error Handling

```csharp
// Use Result pattern instead of exceptions for expected failures
public sealed record Result<T>
{
    public T? Value { get; }
    public Error? Error { get; }
    public bool IsSuccess => Error is null;

    private Result(T value) => Value = value;
    private Result(Error error) => Error = error;

    public static Result<T> Success(T value) => new(value);
    public static Result<T> Failure(Error error) => new(error);
}

// Use problem details for API errors
app.UseExceptionHandler(appBuilder =>
{
    appBuilder.Run(async context =>
    {
        context.Response.ContentType = "application/problem+json";
        var problem = new ProblemDetails
        {
            Status = StatusCodes.Status500InternalServerError,
            Title = "An unexpected error occurred"
        };
        await context.Response.WriteAsJsonAsync(problem);
    });
});
```

## Agent Tips

- **Ask about version first** — .NET 8 and .NET 10 guidance can differ significantly. Load the right reference.
- **Check existing patterns** — Before suggesting architecture, read the user's existing code to match their conventions.
- **Don't over-architect** — A 3-endpoint API doesn't need Clean Architecture + CQRS + DDD. Match complexity to need.
- **Show, don't just tell** — Include code examples with every recommendation.
- **Flag breaking changes** — When suggesting .NET 10 features, note if they break .NET 8 compatibility.
- **Recommend packages conservatively** — Only suggest well-maintained packages with strong community adoption.
- **Consider deployment** — Mention AOT compatibility, Docker multi-stage builds, health checks when relevant.

### Retrospective

After completing the workflow, reflect on the entire execution session:

1. Consider: Were there mid-session corrections? Rejected outputs? Plan changes? Errors?
2. Ask the user: "Quick feedback on this run? (1-5 rating, note any issues, or press enter to skip)"
3. If the user provides feedback OR if corrections/issues occurred during this session:
   a. Create `feedback/` directory if it does not exist
   b. Read `feedback/log.md` (create with `# Feedback Log` header if it does not exist)
   c. Prepend a new entry after the header using the log format from `references/skill-improvement-guide.md`
   d. Fill in: current timestamp, skill version from frontmatter, task description, outcome assessment,
      corrections that occurred during the session, issues encountered, user's note
4. If the user skips AND no corrections or issues occurred, end without recording.

## Behavior Scenarios

```gherkin
Scenario: Architecture guidance for new .NET project
  Given the user is starting a new .NET 8/10 project
  When the user asks for architecture advice
  Then ask about scale/team/complexity if not obvious
  And provide opinionated guidance on pattern selection with trade-offs
  And show concrete project structure and dotnet CLI commands
  And reference architecture-patterns.md for deep-dive

Scenario: Senior-level C# code review
  Given the user has C# code to review
  When the user asks to review C# or .NET code
  Then review against senior-level checklist: correctness, security,
       performance, maintainability, modern idioms
  And flag .NET-specific anti-patterns with fix suggestions
  And reference review-checklist.md for deep review

Scenario: Scaffold new .NET project with best practices
  Given the user wants to create a new .NET project
  When the user asks to scaffold an API, Blazor, MAUI, or library project
  Then create solution structure following chosen architecture pattern
  And include essential NuGet packages, health checks, logging, configuration
  And provide dotnet CLI commands to set up the solution

Scenario: EF Core and data access guidance
  Given the user is working with Entity Framework Core
  When the user asks about EF Core patterns, migrations, or performance
  Then provide senior-level guidance on query optimization, migration strategies
  And warn about common pitfalls (N+1, tracking, lazy loading, raw SQL injection)

Scenario: Modernize legacy .NET code
  Given the user has older .NET code or patterns
  When the user asks about modernization or migration
  Then assess current state and suggest incremental migration strategy
  And highlight version-specific features from the appropriate knowledge base
  And flag breaking changes and deprecated APIs

Scenario: Architecture design review with team perspectives
  Given the user is making a significant architecture decision
  When the user asks for a thorough architecture review or "design review"
  Then create an agent team with Architecture, Security, QA/QC, and
       Devil's Advocate perspectives per references/team-roles.md
  And synthesize findings into prioritized, actionable recommendations

Scenario: Version-specific feature question
  Given the user asks about a .NET feature
  When the feature differs between .NET 8 and .NET 10
  Then load the appropriate version knowledge base
  And clearly state which version the advice applies to
  And note differences if both versions are in play

Scenario: Unsupported or legacy .NET version
  Given the user is on .NET Framework or .NET 6/7
  When the user asks for guidance
  Then note that this skill targets .NET 8 and .NET 10
  And provide migration guidance toward .NET 8 LTS
  And highlight what they gain by upgrading
```
