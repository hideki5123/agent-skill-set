---
name: dev-workflow
description: >
  End-to-end TDD development workflow with multi-agent team review.
  Plans, discusses, and implements features using strict RED-GREEN-REFACTOR
  test-driven development. Handles branch creation, plan-mode exploration,
  team discussion (architecture, security, resource, devil's advocate),
  test case design, TDD implementation, conventional commits, and optional PR creation.
  Use when the user asks to implement a feature, fix a bug, refactor code, add tests,
  or any multi-step development task.
  Triggers on "implement X", "build Y", "add feature Z", "fix bug", "refactor",
  "implement with TDD", "add feature with tests", "build X following TDD",
  or when the user invokes /dev-workflow.
---

# Dev Workflow

End-to-end development with team review and strict TDD discipline.

## Core Principles

1. **Plan Before Code** — Explore the codebase and get approval before writing anything
2. **Team Discussion First** — Never implement without multi-agent review
3. **Tests Before Implementation** — RED -> GREEN -> REFACTOR, always, no exceptions
4. **Clean Commits & Optional PR** — Focused conventional commits, stash-based grouping

## Arguments

All optional with sensible defaults.

| Argument | Default | Description |
|----------|---------|-------------|
| `--bdd` | `false` | Use BDD-style (Given/When/Then) test cases |
| `--skip-team` | `false` | Skip multi-agent team discussion (not recommended) |
| `--skip-approval` | `false` | Skip owner approval step after implementation |
| `--base-branch` | repo default branch | Branch to create feature branch from |
| `--branch` | auto-generated from task | Feature branch name |
| `--pr` | `false` | Create a PR after commits |

## Workflow Overview

```
Setup -> Plan -> Team Discussion -> Test Design -> RED -> GREEN -> REFACTOR -> Approval -> Commit & PR
```

---

### Phase 1: Setup

1. Detect repo's default branch via `git remote show origin | grep 'HEAD branch'` (fallback to `develop`/`main`)
2. Use `--base-branch` if provided, otherwise use the detected default
3. Create feature branch: `git checkout -b <branch-name> <base-branch>`
   - If `--branch` not provided, derive from task description (e.g. `feat/short-description`)

### Phase 2: Plan

1. Enter plan mode with `EnterPlanMode`
2. Understand the user's request thoroughly; ask clarifying questions if ambiguous
3. Explore the codebase: existing patterns, conventions, dependencies, related tests
4. Document acceptance criteria and edge cases
5. Write a clear implementation plan
6. Present the plan via `ExitPlanMode` for user approval
7. If rejected, iterate on the plan until approved

### Phase 3: Team Discussion

Skip if `--skip-team` is set.

Create an agent team to explore this from different angles: one teammate on architecture, one on security, one considering edge device resource, one playing devil's advocate and any other team mate who need to be on this task.

**Setup:**
1. Use `TeamCreate` to create a team named after the feature (e.g. `review-health-check`)
2. Use `SendMessage` to spawn teammates with their role-specific prompts
3. Include the approved plan and relevant codebase context in each spawn prompt

**Teammates:**

| Teammate | Focus |
|----------|-------|
| **Architecture** | Design patterns, modularity, extensibility, existing conventions |
| **Security** | Input validation, injection risks, auth/authz, data exposure |
| **Resource** | Memory, CPU, network constraints, offline scenarios |
| **Devil's Advocate** | Challenge assumptions, find flaws, suggest alternatives |

Add any other teammates needed based on the specific task (e.g. database, UX, performance).

Read `references/team-roles.md` for detailed teammate prompts and output formats.

**Team Discussion Protocol:**
1. Each teammate reviews the plan from their perspective
2. Teammates communicate with each other to challenge findings and debate trade-offs
3. The lead (you) collects and synthesizes all findings
4. Categorize by severity:
   - **Critical** — Blocks implementation, security risk, architectural flaw -> Must address before proceeding
   - **Important** — Should address for quality, but not blocking -> Address during implementation
   - **Nice-to-have** — Improvements that can be deferred -> Document for future
5. Deduplicate overlapping concerns
6. Update the plan with concrete action items
7. Present consolidated feedback to user for approval
8. Clean up the team after discussion is complete

### Phase 4: Test Case Design

Design comprehensive test cases **before writing any implementation code**.

Read `references/test-design.md` for the 9 test categories:
1. Happy Path — Normal expected behavior
2. Edge Cases — Boundary conditions, empty inputs, nulls
3. Error Handling — Invalid inputs, failures, exceptions
4. Input Validation — Sanitization, injection prevention
5. Integration Points — External service interactions
6. Output Format — Structure, schema, encoding
7. Security — Escaping, error sanitization, auth
8. Ordering & Determinism — Consistent, reproducible output
9. Resource Limits — Pagination, truncation, timeouts

**If `--bdd` is set:** Write test cases in Given/When/Then Gherkin format. Read `references/bdd-guide.md` for writing effective scenarios, tables, and backgrounds.

**Test-First Checklist** (all must be true before proceeding):
- [ ] All acceptance criteria have corresponding tests
- [ ] Edge cases identified by team are covered
- [ ] Security concerns from review are tested
- [ ] Error handling scenarios are tested
- [ ] Tests compile but fail (RED state confirmed)

### Phase 5: RED — Write Failing Tests

1. Create test file with all designed test cases
2. Use descriptive test names: `MethodName_StateUnderTest_ExpectedBehavior`
3. Structure each test with clear Arrange/Act/Assert (or Given/When/Then if `--bdd`)
4. Create minimal stub implementation that throws NotImplementedException (or equivalent)
5. Run tests — **ALL MUST FAIL**
6. If any test passes, the stub is too complete — simplify it
7. Commit: `test: add failing tests for <feature>`

**Anti-patterns to avoid:**
- Writing tests that pass immediately
- Testing implementation details instead of behavior
- Skipping edge cases to save time
- Writing vague test names

### Phase 6: GREEN — Make Tests Pass

1. Pick one failing test — start with the simplest
2. Write the minimum code to pass that test
3. Run tests: target passes, previous tests pass, remaining still fail
4. Repeat for each failing test
5. Do NOT add features not covered by tests
6. Apply security measures identified in Phase 3
7. Wire up the implementation to the system (CLI, API, UI) as needed
8. When all tests pass, commit: `feat: implement <feature>`

**Anti-patterns to avoid:**
- Writing more code than needed
- Adding features not covered by tests
- Optimizing prematurely
- Ignoring failing tests

### Phase 7: REFACTOR — Improve Code Quality

1. Review for: duplication, naming clarity, performance, documentation needs
2. Make small changes — one refactoring at a time
3. Run tests after each change — keep them green
4. If changes warrant it, commit: `refactor: improve <aspect> in <feature>`

**Done when:**
- [ ] No obvious code duplication
- [ ] Names clearly express intent
- [ ] Methods are focused (single responsibility)
- [ ] No commented-out code
- [ ] Tests still pass
- [ ] Code is "good enough" for now

**Anti-patterns to avoid:**
- Changing behavior (tests must stay green)
- Big-bang refactoring (keep changes small)
- Skipping the refactor phase entirely
- Adding features during refactoring

### Phase 8: Approval

Skip if `--skip-approval` is set.

1. Present a summary of all changes to the user:
   - Tests added (count and categories)
   - Implementation highlights
   - Refactorings applied
   - Team review items addressed
2. Wait for user approval
3. If rejected, iterate on changes

### Phase 9: Commit & PR

**Commit Strategy:**

Read `references/commit-guide.md` for full conventions.

1. `git stash` all uncommitted changes
2. For each logical group:
   a. `git checkout stash -- <file(s)>` to restore specific files
   b. If a file has multiple logical changes, apply edits manually then stage
   c. `git add <file(s)>` and `git commit`
3. `git stash drop` when done

Key rules:
- One logical change per commit
- Conventional commit prefixes: `feat:`, `fix:`, `refactor:`, `chore:`, `docs:`, `test:`, `ci:`
- Lowercase after prefix, no period at end, max ~72 chars
- Never add `Co-Authored-By` lines
- Use HEREDOC for commit messages

**PR Creation** (only when `--pr` is set):

Read `references/pr-guide.md` for template detection and filling.

1. Push the branch: `git push -u origin <branch-name>`
2. Detect and use the repo's PR template
3. Create PR with `gh pr create`, filling in the template
4. Return the PR URL to the user

---

## BDD vs TDD Test Format

TDD is always enforced. The `--bdd` flag only changes the **test format**:

| Aspect | Default (TDD) | With `--bdd` |
|--------|---------------|-------------|
| Test naming | `Method_State_Expected` | Given/When/Then Gherkin |
| Audience | Developers | Developers + stakeholders |
| Best for | Technical code, utilities, APIs | Business features, user stories |

Use `--bdd` when: stakeholder communication matters, business requirements drive acceptance criteria, or feature documentation has high value.

## Example Invocations

### Standard Development
```
/dev-workflow

Task: Add a health check endpoint
Requirements:
- Return 200 with JSON status
- Include uptime and version info
```

### With BDD for Business Features
```
/dev-workflow --bdd

Task: Implement user authentication flow
Requirements:
- Email/password login
- JWT token generation
- Session management
```

### Quick Solo Mode
```
/dev-workflow --skip-team --skip-approval

Task: Fix date parsing bug in export function
```

### Full Pipeline with PR
```
/dev-workflow --pr --base-branch develop

Task: Add CSV export feature with date range filtering
```

## Behavior Scenarios

```gherkin
Scenario: Full TDD workflow with team review
  Given the user asks to implement a feature
  When the user invokes /dev-workflow
  Then the skill creates a branch, plans in plan-mode, runs team discussion,
       designs tests, executes RED-GREEN-REFACTOR, gets approval, and commits

Scenario: BDD mode for business features
  Given the user needs stakeholder-readable tests
  When the user invokes /dev-workflow --bdd
  Then test cases are written in Given/When/Then format
  And the TDD cycle still applies (RED-GREEN-REFACTOR)

Scenario: Quick fix without team overhead
  Given the user has a simple bug fix
  When the user invokes /dev-workflow --skip-team --skip-approval
  Then team discussion and approval are skipped
  But TDD is still enforced (tests written before implementation)

Scenario: Full pipeline with PR creation
  Given the user wants changes pushed and a PR opened
  When the user invokes /dev-workflow --pr
  Then after commits the branch is pushed and a PR is created using the repo's template

Scenario: Custom branch management
  Given the user specifies a base branch and branch name
  When the user invokes /dev-workflow --base-branch develop --branch feat/new-api
  Then the skill creates the specified branch from the specified base
```

## References

- `references/team-roles.md` — Agent prompts, output formats, and synthesis protocol
- `references/test-design.md` — 9 test categories with examples and mocking strategy
- `references/bdd-guide.md` — Given/When/Then writing guide and BDD decision criteria
- `references/commit-guide.md` — Conventional commits, stash-based grouping, HEREDOC format
- `references/pr-guide.md` — PR template detection and creation with gh CLI
