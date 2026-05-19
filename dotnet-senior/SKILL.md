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
version: 1.1.0
---

# .NET Senior Development Skill

This skill delegates to the `dotnet-senior:dotnet-senior` subagent
(`@agent-dotnet-senior:dotnet-senior`), which carries the full role definition,
constraints, and senior-level review/scaffolding/EF/ASP.NET guidance.

## How to invoke

When invoked, hand the user's request off to the subagent so the role's
system prompt, constraints, and judgment criteria apply. Example:

```text
@agent-dotnet-senior:dotnet-senior <user request>
```

The subagent system prompt covers:

- Modern C# idioms (primary constructors, collection expressions, pattern
  matching, records) and version targeting (.NET 8 LTS / .NET 10).
- Architecture pattern selection (Minimal API, Clean Architecture, DDD, CQRS,
  Modular Monolith) with trade-off explanation.
- Senior-level code review checklist (correctness, security, performance,
  maintainability, modern idioms).
- Project scaffolding (solution layout, essential NuGet packages, `dotnet` CLI
  commands).
- EF Core, ASP.NET Core, performance, error handling, and testing patterns.

## When to skip the subagent

Only skip the subagent and answer inline if the user's request is purely a
one-line factual lookup (e.g., "what's the default port for Kestrel?") where
the full role context adds no value. Otherwise, delegate.

## Version-specific references

The subagent reads version knowledge bases on demand. The skill's
`references/` directory ships:

- `references/dotnet8-knowledge.md` — .NET 8 (LTS) features and APIs
- `references/dotnet10-knowledge.md` — .NET 10 features and .NET 8 migration
- `references/architecture-patterns.md` — pattern descriptions and templates
- `references/review-checklist.md` — full code review checklist
- `references/team-roles.md` — perspectives for architecture team review

These files are shared between the skill and the subagent (the subagent
reads them via `Read` from the plugin's `skills/dotnet-senior/references/`
location).

## Retrospective

After completing a `/dotnet-senior` flow, reflect on the entire execution:

1. Were there mid-session corrections, rejected outputs, plan changes, or
   errors?
2. Ask the user: "Quick feedback on this run? (1-5 rating, note any issues,
   or press enter to skip)"
3. If the user provides feedback OR if corrections/issues occurred:
   a. Create `feedback/` if it does not exist.
   b. Read or create `feedback/log.md` (header: `# Feedback Log`).
   c. Prepend a new entry using the format in
      `references/skill-improvement-guide.md`. Fill timestamp, skill version
      (1.1.0), task description, outcome, corrections, issues, user note.
4. If the user skips AND no corrections or issues occurred, end without
   recording.
