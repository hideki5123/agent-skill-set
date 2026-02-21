---
name: tdd-team-workflow
description: >
  Test-Driven Development workflow with multi-agent team discussion.
  Ensures thorough planning, team review before implementation, and TDD/BDD best practices.
  Use when implementing features, fixing bugs, or any task that benefits from team perspective
  and test-first approach. Triggers on "implement with TDD", "add feature with tests",
  "build X following TDD", or when the user invokes /tdd-team-workflow.
---

# TDD Team Workflow

A disciplined development workflow that combines multi-agent team discussion with
Test-Driven Development (TDD) and optionally Behavior-Driven Development (BDD) practices.

## Core Principles

1. **Team Discussion First** - Never implement without team review
2. **Tests Before Code** - RED → GREEN → REFACTOR
3. **Human-Readable Tests** - BDD when appropriate for stakeholder communication
4. **Iterative Approval** - User approves at each major phase

## Arguments

Parse these from the user's invocation. All are optional with defaults:

| Argument | Default | Description |
|----------|---------|-------------|
| `--bdd` | `false` | Use BDD-style (Given/When/Then) test cases |
| `--skip-team` | `false` | Skip multi-agent team discussion (not recommended) |
| `--base-branch` | repo default | Branch to create feature branch from |
| `--branch` | auto-generated | Feature branch name |
| `--pr` | `false` | Create a PR after commits |

## Workflow Phases

### Phase 1: Requirements Gathering

1. Understand the user's request thoroughly
2. Ask clarifying questions if requirements are ambiguous
3. Document the acceptance criteria
4. Identify edge cases and error scenarios

### Phase 2: Codebase Exploration

1. Use `EnterPlanMode` to explore systematically
2. Identify existing patterns, conventions, and dependencies
3. Find related code and tests
4. Document findings in the plan

### Phase 3: Team Discussion (Multi-Agent Review)

Spawn parallel agents for diverse perspectives:

| Agent Role | Focus Area |
|------------|------------|
| **Architecture** | Design patterns, modularity, extensibility, existing conventions |
| **Security** | Input validation, injection risks, auth/authz, data exposure |
| **Edge Device / Resource** | Memory, CPU, network constraints, offline scenarios |
| **Devil's Advocate** | Challenge assumptions, find flaws, suggest alternatives |

See [references/team-roles.md](references/team-roles.md) for detailed agent prompts.

**Protocol:**
1. Each agent reviews the plan independently
2. Synthesize feedback into actionable items
3. Update plan based on team input
4. Present consolidated plan to user for approval

### Phase 4: Test Case Design (Before Implementation)

Design test cases with the team. Consider:

1. **Happy Path Tests** - Normal expected behavior
2. **Edge Cases** - Boundary conditions, empty inputs, nulls
3. **Error Handling** - Invalid inputs, failures, exceptions
4. **Integration Points** - RPC calls, database queries, external services
5. **Security Tests** - Input validation, injection prevention
6. **Resource Limits** - Pagination, truncation, timeouts

If `--bdd` is enabled, write tests in Given/When/Then format:
```gherkin
Scenario: Export restock history for valid SKU
  Given a store with restock events for SKU "ABC123"
  When I export restock history for SKU "ABC123"
  Then I should receive CSV with matching events
  And dates should be in ISO 8601 UTC format
```

See [references/test-design.md](references/test-design.md) for test categories.

### Phase 5: TDD RED Phase

1. Create test file with all test cases
2. Create minimal stub implementation (throws NotImplementedException)
3. Run tests - **ALL MUST FAIL**
4. If any test passes, the stub is too complete - simplify it
5. Commit RED phase: `test: add failing tests for <feature>`

### Phase 6: TDD GREEN Phase

1. Implement minimum code to pass each test
2. Run tests frequently - aim for incremental progress
3. Do NOT add features not covered by tests
4. Apply security measures identified in Phase 3
5. When all tests pass, commit: `feat: implement <feature>`

### Phase 7: TDD REFACTOR Phase

1. Review implementation for:
   - Code duplication
   - Naming clarity
   - Performance optimizations
   - Documentation needs
2. Refactor while keeping tests green
3. If needed, commit: `refactor: improve <aspect>`

### Phase 8: Integration & Wiring

1. Wire up the implementation to the system (CLI, API, UI)
2. Add any missing glue code
3. Run full test suite
4. Commit: `feat: wire up <feature> to <system>`

### Phase 9: Final Review & Commit

1. Present summary of all changes to user
2. Wait for approval
3. Create focused, conventional commits
4. Optionally create PR if `--pr` is enabled

## Test-First Checklist

Before writing any implementation code, verify:

- [ ] All acceptance criteria have corresponding tests
- [ ] Edge cases identified by team are covered
- [ ] Security concerns from review are tested
- [ ] Error handling scenarios are tested
- [ ] Tests compile but fail (RED state confirmed)

## BDD vs TDD Decision Guide

Use **BDD** (`--bdd`) when:
- Stakeholders need to understand test cases
- Acceptance criteria come from business requirements
- Documentation value is high

Use **TDD** (default) when:
- Technical implementation details dominate
- Tests are primarily for developers
- Speed of test writing matters

## Example Invocation

### Basic TDD Workflow
```
/tdd-team-workflow

Task: Add a CLI tool to export SKU restock history
Requirements:
- Filter by store_id, location_id, sku_id
- Output CSV format
- Support date range filtering
```

### With BDD for Business Features
```
/tdd-team-workflow --bdd

Task: Implement user authentication flow
Requirements:
- Email/password login
- JWT token generation
- Session management
```

### Quick Mode (Skip Team Discussion)
```
/tdd-team-workflow --skip-team

Task: Fix date parsing bug in export function
```

## Integration with Other Skills

This skill works well with:
- `/multi-agent-council` - For deeper architecture discussions
- `/review-pr` - For final PR review
- `/dev-workflow` - Can be used as the implementation phase

## Output Artifacts

Each run produces:
1. **Test file** - Comprehensive test cases
2. **Implementation** - Code that passes all tests
3. **Plan document** - With team feedback incorporated
4. **Commit history** - Following conventional commits
