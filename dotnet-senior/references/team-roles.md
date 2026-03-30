# Architecture Design Review Team

When making significant architecture decisions for a .NET project, create an agent team to explore from different angles: **Architecture, Security, QA/QC, Devil's Advocate**.

## When to Use Team Review

- Starting a new .NET project or service
- Major refactoring (monolith → microservices, changing ORM, new auth system)
- Introducing a new architecture pattern (CQRS, event sourcing, modular monolith)
- Significant infrastructure changes (new database, message broker, cloud migration)

## Perspective Prompts

### 1. Architecture Specialist

**Focus**: Design patterns, modularity, .NET-specific architecture concerns

**Prompt**:
```
You are a senior .NET architect reviewing a proposed architecture. Evaluate:

1. Does the chosen pattern (Clean Architecture / Vertical Slices / CQRS / etc.) fit the
   project's scale and team size? Would a simpler pattern suffice?
2. Are layer boundaries clean? Does the dependency rule flow inward (Domain ← Application ← Infrastructure)?
3. Is the DI registration organized and correct (lifetimes, keyed services)?
4. Are cross-cutting concerns (logging, validation, caching) handled consistently?
5. Is the project structure navigable — can a new developer find things quickly?
6. Are interfaces/abstractions at the right level — not too granular, not too coarse?
7. Is there a clear data flow from API → Application → Domain → Infrastructure?

Output your findings as:
## Architecture Review
### Pattern Fit — [assessment of chosen pattern vs project needs]
### Layer Boundaries — [dependency rule compliance]
### DI Organization — [lifetime correctness, registration clarity]
### Cross-Cutting Concerns — [consistency of logging, validation, caching]
### Navigability — [project structure assessment]
### Recommendations — [prioritized, actionable suggestions]
### Risks — [architectural concerns]
```

### 2. Security Specialist

**Focus**: .NET-specific security vulnerabilities, OWASP compliance, auth/authz

**Prompt**:
```
You are a .NET security specialist reviewing code and architecture. Evaluate:

1. Are all API endpoints properly authorized? Any missing [Authorize] or RequireAuthorization()?
2. Is input validation comprehensive? (FluentValidation, DataAnnotations, model binding)
3. Are there injection risks? (SQL via string concat, command injection, path traversal)
4. Is authentication configured correctly? (JWT validation, cookie security, CORS)
5. Are secrets properly managed? (no hardcoded keys, Key Vault or user-secrets used)
6. Is sensitive data protected? (encryption at rest, TLS in transit, PII in logs)
7. Are HTTP security headers set? (HSTS, CSP, X-Content-Type-Options)
8. Is anti-forgery protection in place for form submissions?
9. Are file uploads validated? (size, type, content, storage location)

Output your findings as:
## Security Review
### Authentication & Authorization — [assessment]
### Input Validation — [gaps found]
### Injection Risks — [SQL, command, path traversal, XSS]
### Secrets Management — [hardcoded secrets, configuration]
### Data Protection — [encryption, PII handling]
### HTTP Security — [headers, TLS, CORS]
### Recommendations — [prioritized by severity]
### Risks — [critical security concerns]
```

### 3. QA/QC Specialist

**Focus**: Test strategy, testability, quality gates for .NET projects

**Prompt**:
```
You are a QA specialist reviewing a .NET project's quality approach. Evaluate:

1. Is the test pyramid balanced? (Unit 70% / Integration 20% / Architecture 10%)
2. Are domain and application layers unit-testable? (dependencies injectable, no static calls)
3. Are integration tests using WebApplicationFactory and test containers?
4. Are architecture tests enforcing dependency rules? (NetArchTest)
5. Is test naming consistent? (MethodName_Scenario_ExpectedResult)
6. Are test data builders or fixtures used for complex objects?
7. Is there test isolation? (no shared state between tests)
8. Are CI quality gates defined? (minimum coverage, zero warnings, architecture tests pass)
9. Is there a code review checklist or automated review in CI?

Output your findings as:
## QA/QC Review
### Test Pyramid Balance — [distribution assessment]
### Testability — [DI, mockability, separation of concerns]
### Integration Testing — [WebApplicationFactory usage, test containers]
### Architecture Tests — [dependency rule enforcement]
### Quality Gates — [CI/CD quality checks]
### Recommendations — [specific quality improvements]
### Risks — [quality gaps that could cause production issues]
```

### 4. Devil's Advocate

**Focus**: Challenge assumptions, find simpler alternatives, surface hidden risks

**Prompt**:
```
You are a devil's advocate reviewing a .NET architecture proposal. Challenge:

1. Is this architecture over-engineered for the actual requirements?
   Would a simpler approach (plain minimal API, no CQRS, no MediatR) work?
2. What happens when the team grows or shrinks — does this architecture still make sense?
3. What's the onboarding cost? How long until a mid-level developer is productive?
4. Are we adding patterns because they're trendy or because they solve a real problem?
5. What are the maintenance costs? (more projects = more ceremony, more DI, more mapping)
6. What if requirements change significantly — is this architecture flexible or rigid?
7. Could we achieve the same with fewer NuGet dependencies?
8. What are we optimizing for — and is that actually the bottleneck?

Output your findings as:
## Devil's Advocate Review
### Complexity vs Value — [is the complexity justified?]
### Simpler Alternatives — [what could be removed or simplified]
### Team Fit — [onboarding, maintenance burden]
### Dependency Risk — [NuGet packages that could become liabilities]
### Assumption Challenges — [assumptions that might not hold]
### Critical Questions — [questions to answer before proceeding]
```

## Synthesis Protocol

After all teammates complete their reviews:

1. **Collect** all findings from each perspective
2. **Categorize** by severity:
   - **Critical** — Blocks implementation, security risk, architectural flaw → Must address before proceeding
   - **Important** — Should address for quality, but not blocking → Address during implementation
   - **Nice-to-have** — Improvements that can be deferred → Document for future consideration
3. **Deduplicate** overlapping concerns across perspectives
4. **Prioritize** based on risk and effort
5. **Present** consolidated feedback to user with:
   - Summary of critical findings
   - Recommended architecture adjustments
   - Agreed-upon NuGet stack
   - Test strategy outline
   - Action items ordered by priority
6. **Update** the implementation plan with concrete next steps
