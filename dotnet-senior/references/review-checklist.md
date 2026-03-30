# Senior .NET Code Review Checklist

Use this checklist for deep code reviews. For quick reviews, use the abbreviated checklist in SKILL.md.

## 1. Correctness

- [ ] Logic matches requirements / intent
- [ ] Edge cases handled (null, empty, boundary values, overflow)
- [ ] Off-by-one errors checked
- [ ] Correct use of equality comparisons (`==` vs `.Equals()` vs `ReferenceEquals()`)
- [ ] Correct disposal of `IDisposable` / `IAsyncDisposable` resources
- [ ] No swallowed exceptions (empty catch blocks)
- [ ] Cancellation tokens propagated through async call chains

## 2. Security

### Input Validation
- [ ] All external input validated (API parameters, query strings, headers, form data)
- [ ] FluentValidation or DataAnnotations used consistently
- [ ] File upload validation (size, type, content sniffing)
- [ ] Path traversal prevention for file operations

### Injection
- [ ] No string concatenation in SQL — use parameterized queries or EF Core LINQ
- [ ] No raw HTML output — use Razor encoding or explicit `HtmlEncoder`
- [ ] No user input in `Process.Start()` or shell commands
- [ ] No user input in LDAP, XML, or regex without sanitization

### Authentication & Authorization
- [ ] `[Authorize]` or `.RequireAuthorization()` on all non-public endpoints
- [ ] Role/policy-based authorization, not just authentication checks
- [ ] JWT validation includes issuer, audience, and expiry
- [ ] No sensitive data in JWT payload (use claims wisely)
- [ ] CORS policy restricts origins appropriately

### Secrets & Data Protection
- [ ] No hardcoded secrets, connection strings, or API keys
- [ ] Secrets from `IConfiguration` backed by Key Vault, user-secrets, or env vars
- [ ] PII/PHI logged only when necessary, masked in logs
- [ ] `[FromHeader]`, `[FromQuery]` attributes don't expose internal names
- [ ] Anti-forgery tokens for form submissions

### HTTP Security Headers
- [ ] HSTS enabled (`UseHsts()`)
- [ ] Content-Security-Policy set
- [ ] X-Content-Type-Options: nosniff
- [ ] X-Frame-Options or frame-ancestors CSP directive

## 3. Performance

### Allocations
- [ ] No unnecessary `ToList()` / `ToArray()` — use `IEnumerable<T>` when streaming
- [ ] `Span<T>` / `Memory<T>` used for parsing and buffer operations
- [ ] `StringBuilder` for string concatenation in loops
- [ ] `ArrayPool<T>.Shared` or `MemoryPool<T>.Shared` for temporary buffers
- [ ] `FrozenDictionary` / `FrozenSet` for immutable lookup tables (.NET 8+)
- [ ] `SearchValues<T>` for character set searches (.NET 8+)

### Async/Await
- [ ] No `async void` (except event handlers)
- [ ] No `.Result` or `.Wait()` on tasks (deadlock risk)
- [ ] `ConfigureAwait(false)` in library code (not needed in ASP.NET Core app code)
- [ ] `ValueTask` for hot paths that often complete synchronously
- [ ] No `Task.Run()` wrapping async methods in ASP.NET Core (wastes thread pool threads)
- [ ] `IAsyncEnumerable<T>` for streaming large collections

### Database
- [ ] No N+1 queries — check `Include()` usage or use projection
- [ ] `AsNoTracking()` for read-only queries
- [ ] `AsSplitQuery()` for complex multi-level includes
- [ ] Compiled queries for hot paths: `EF.CompileAsyncQuery()`
- [ ] Pagination implemented (no unbounded `SELECT *`)
- [ ] Indexes exist for frequently queried columns
- [ ] No `ToListAsync()` before filtering — filter in database

### Caching
- [ ] Appropriate caching strategy (in-memory, distributed, output caching)
- [ ] Cache invalidation strategy defined
- [ ] Cache key collision prevention
- [ ] No caching of user-specific data in shared cache without user key

### HTTP
- [ ] `IHttpClientFactory` used (not `new HttpClient()`)
- [ ] Resilience policies (retry, circuit breaker) via `Microsoft.Extensions.Http.Resilience`
- [ ] Response compression enabled for applicable content types
- [ ] HTTP/2 or HTTP/3 considered for high-throughput scenarios

## 4. Architecture & Design

### SOLID Principles
- [ ] Single Responsibility — class/method does one thing
- [ ] Open/Closed — extensible without modifying existing code
- [ ] Liskov Substitution — subtypes substitutable for base types
- [ ] Interface Segregation — no fat interfaces forcing unused implementations
- [ ] Dependency Inversion — depend on abstractions, not concretions

### Dependency Injection
- [ ] Services registered with correct lifetime (Scoped for DB contexts, Singleton for stateless)
- [ ] No service locator pattern (`IServiceProvider.GetService()` in business logic)
- [ ] No captive dependency (Singleton holding Scoped service reference)
- [ ] Keyed services used where multiple implementations exist (.NET 8+)

### API Design
- [ ] RESTful conventions (proper HTTP verbs, status codes, resource naming)
- [ ] Consistent error responses using ProblemDetails (RFC 7807)
- [ ] API versioning strategy (URL, header, or query string)
- [ ] Pagination for collection endpoints (cursor-based preferred)
- [ ] Request/response DTOs separate from domain models
- [ ] No over-posting — bind only expected properties

### Error Handling
- [ ] Global exception handler configured
- [ ] Domain exceptions mapped to appropriate HTTP status codes
- [ ] Result pattern for expected failures (not exceptions for flow control)
- [ ] Retry logic for transient failures (Polly or built-in resilience)
- [ ] Circuit breaker for external service calls

## 5. Maintainability

### Code Organization
- [ ] Feature-based or layer-based organization (consistent, not mixed)
- [ ] No god classes (>500 lines is a smell)
- [ ] No god methods (>50 lines is a smell)
- [ ] Private methods extracted when logic is reusable or complex

### Naming
- [ ] PascalCase for public members, camelCase for locals/parameters
- [ ] `Async` suffix on async methods
- [ ] `I` prefix on interfaces
- [ ] Meaningful names — no abbreviations, no single-letter variables (except LINQ lambdas)
- [ ] Boolean names are questions: `IsValid`, `HasAccess`, `CanExecute`

### Modern C# Idioms
- [ ] Records for immutable DTOs and value objects
- [ ] Primary constructors for DI in .NET 8+ classes
- [ ] Collection expressions `[1, 2, 3]` instead of `new List<int> { 1, 2, 3 }` (C# 12+)
- [ ] Pattern matching over type checks + casts
- [ ] `required` modifier for mandatory properties
- [ ] `file`-scoped types for implementation details
- [ ] `global using` for common namespaces
- [ ] Raw string literals for multi-line strings
- [ ] `using` declarations (no braces) for scoped disposables

## 6. Testing

- [ ] Unit tests for domain logic and application services
- [ ] Integration tests for API endpoints (`WebApplicationFactory`)
- [ ] Architecture tests for dependency rules (NetArchTest)
- [ ] Test naming follows convention: `MethodName_Scenario_ExpectedResult`
- [ ] Arrange-Act-Assert pattern clear in each test
- [ ] No test interdependencies (each test is independent)
- [ ] Mocks/stubs only for infrastructure boundaries (not for domain types)
- [ ] Test data builders or fixtures for complex object creation

## 7. Observability

### Logging
- [ ] Structured logging with Serilog or `ILogger<T>`
- [ ] Log levels used correctly (Debug, Information, Warning, Error, Critical)
- [ ] Correlation IDs propagated across service calls
- [ ] No sensitive data in logs (passwords, tokens, PII)
- [ ] Request/response logging with appropriate redaction

### Health Checks
- [ ] Liveness check at `/health/live`
- [ ] Readiness check at `/health/ready` (includes DB, external services)
- [ ] Health check UI or dashboard configured

### Metrics & Tracing
- [ ] OpenTelemetry configured for distributed tracing (if microservices)
- [ ] Custom metrics for business-critical operations
- [ ] Correlation with logs for end-to-end request tracing

## 8. Configuration & Deployment

- [ ] Strongly-typed options with validation (`AddOptionsWithValidateOnStart`)
- [ ] Environment-specific settings via `appsettings.{Environment}.json`
- [ ] No secrets in `appsettings.json` — use Secret Manager, env vars, or Key Vault
- [ ] Docker multi-stage build for minimal image size
- [ ] `.dockerignore` excludes unnecessary files
- [ ] AOT compatibility checked if targeting Native AOT
- [ ] Global.json pins SDK version for team consistency
