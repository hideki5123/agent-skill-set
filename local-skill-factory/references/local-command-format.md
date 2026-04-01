# Local Command Format Reference

Claude Code project commands live in `.claude/commands/` as markdown files. Each file becomes a slash command scoped to that project.

## File Location

```
<project-root>/
└── .claude/
    └── commands/
        ├── review.md          → /project:review
        ├── test.md            → /project:test
        └── deploy.md          → /project:deploy
```

- Filename (without `.md`) = command name
- Invoked as `/project:<name>` or just `/<name>` when in the project
- Files are plain markdown — no YAML frontmatter needed

## File Structure

```markdown
<Description line — shown in command picker>

<Prompt body — the full instructions Claude receives when the command is invoked>

$ARGUMENTS
```

### Key Elements

| Element | Description |
|---------|-------------|
| **First line** | Brief description shown in autocomplete/picker |
| **Body** | Full prompt template — imperative instructions |
| **`$ARGUMENTS`** | Replaced with whatever the user types after the command |

## Minimal Example

```markdown
Review the code changes in this project for issues and improvements.

Look at the current git diff and review for:
1. Bugs or logic errors
2. Security issues
3. Performance concerns
4. Code style violations

Provide findings as a prioritized list.

Focus on: $ARGUMENTS
```

Usage: `/project:review the authentication module`

## Full Example (with project-specific knowledge)

```markdown
Create a new API endpoint following this project's conventions.

## Project Conventions
- Endpoints go in `src/Features/<Feature>/` as vertical slices
- Each endpoint file contains: Request DTO, Validator, Handler, Endpoint mapping
- Use FluentValidation for input validation
- Use Mapperly for DTO mapping
- Return ProblemDetails for errors

## Steps
1. Ask for: HTTP method, route, request/response shape, business logic description
2. Create the endpoint file at `src/Features/<Feature>/<Verb><Resource>Endpoint.cs`
3. Include: request record, FluentValidation validator, handler with error handling
4. Register in the feature's endpoint mapping extension
5. Create a test file at `tests/Features/<Feature>/<Verb><Resource>Tests.cs`

## Naming
- File: `<Verb><Resource>Endpoint.cs` (e.g., `CreateProductEndpoint.cs`)
- Request: `<Verb><Resource>Request`
- Response: `<Verb><Resource>Response`
- Validator: `<Verb><Resource>Validator`

Create endpoint for: $ARGUMENTS
```

## Writing Good Local Commands

### DO

- **Be project-specific** — encode conventions, paths, patterns unique to THIS project
- **Use imperative form** — "Review the code", not "This command reviews code"
- **Include concrete paths** — `src/Features/`, `tests/`, `migrations/`
- **Reference project tools** — the actual test runner, linter, build system
- **Keep focused** — one command per responsibility
- **Use `$ARGUMENTS`** — let users parameterize the command

### DON'T

- Don't include generic knowledge Claude already has (language syntax, common patterns)
- Don't make overly long commands (>200 lines) — split into multiple commands
- Don't hardcode values that change (versions, URLs) — reference config files instead
- Don't duplicate CLAUDE.md content — reference it, or put shared context there

## Patterns by Use Case

### Code Generation

```markdown
Scaffold a new [component/endpoint/module] following project conventions.

## Conventions
[Project-specific patterns, naming, file locations]

## Steps
1. [Gather input]
2. [Create files at correct locations]
3. [Wire up registration/routing]
4. [Create test file]

Create: $ARGUMENTS
```

### Code Review

```markdown
Review code against this project's standards.

## Standards
[Project-specific linting rules, patterns, anti-patterns]

## Review Checklist
[Project-specific quality gates]

## Output
Prioritized list: Critical > Important > Nice-to-have

Review: $ARGUMENTS
```

### Build & Test

```markdown
Run the project's test suite with context.

## Test Commands
- Unit tests: [exact command]
- Integration tests: [exact command]
- Full suite: [exact command]

## On Failure
- Read the error output
- Identify the failing test
- Suggest a fix based on the project's patterns

Run: $ARGUMENTS
```

### Documentation

```markdown
Generate or update documentation for the specified area.

## Doc Locations
- API docs: [path]
- Architecture docs: [path]
- README: [path]

## Style
[Project's documentation style and conventions]

Document: $ARGUMENTS
```

### Deployment / DevOps

```markdown
Guide through the deployment checklist for this project.

## Pre-deploy
- [ ] All tests pass
- [ ] [Project-specific checks]

## Deploy Steps
[Environment-specific deployment commands]

## Post-deploy
- [ ] [Verification steps]

Deploy: $ARGUMENTS
```

## Relationship to CLAUDE.md

| Concern | Where |
|---------|-------|
| Project-wide coding standards | `CLAUDE.md` |
| Specific slash command workflow | `.claude/commands/<name>.md` |
| Tech stack and tools | `CLAUDE.md` |
| One-off task automation | `.claude/commands/<name>.md` |

A command can reference CLAUDE.md content implicitly — Claude loads CLAUDE.md every session. So commands don't need to repeat what's already there.

## Multiple Related Commands

For a project needing several commands, create them as individual files:

```
.claude/commands/
├── review.md       # Code review
├── test.md         # Run tests
├── endpoint.md     # Scaffold API endpoint
├── migration.md    # Database migration workflow
└── deploy.md       # Deployment checklist
```

Each is independent and focused. Users discover them via autocomplete.
