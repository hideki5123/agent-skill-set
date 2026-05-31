---
name: dev-workflow
deprecated: true
description: >
  End-to-end TDD development workflow with multi-agent team review and skill-based
  quality gates. Plans, discusses, and implements features using strict RED-GREEN-REFACTOR
  test-driven development. Handles worktree-based branch isolation (from latest remote),
  PRD and technical requirements creation, plan-mode exploration,
  embedded team discussion at every deliverable phase,
  skill-agent quality gates (review-local, orch-qa, scenario-gen, pm-review, e2e-test),
  mandatory test case design via test-scenario skill, TDD implementation,
  fresh agent implementation review, conventional commits,
  optional PR creation with self-pr-review and address-pr-comments.
  Use when the user asks to implement a feature, fix a bug, refactor code, add tests,
  or any multi-step development task.
  Triggers on "implement X", "build Y", "add feature Z", "fix bug", "refactor",
  "implement with TDD", "add feature with tests", "build X following TDD",
  or when the user invokes /dev-workflow.
---

> [!WARNING]
> **DEPRECATED (2026-06-01).** Superseded by the upstream
> [mattpocock/skills](https://github.com/mattpocock/skills) workflow:
> `grill-me` / `grill-with-docs` → `to-prd` → `tdd` →
> `improve-codebase-architecture` (plus `diagnose`, `triage`, `zoom-out`,
> `prototype`, `handoff`). This plugin is **disabled globally** and kept here
> for reference only. Re-enable by flipping
> `dev-workflow@hideki-plugins` back to `true` in `~/.claude/settings.json`.
>
> Not covered by the upstream replacement: multi-agent team review and
> automated PR creation (`self-pr-review` / `address-pr-comments`).

# Dev Workflow

End-to-end development with team review, skill agents, and strict TDD discipline.

## Core Principles

1. **Requirements First** — PRD and Tech Req before any code
2. **Team Discussion at Every Deliverable** — Each phase that produces a deliverable gets its own agent team review
3. **Always Confirm Agents** — Present which agents will run, get user feedback before spawning
4. **Tests Before Implementation** — RED -> GREEN -> REFACTOR, always, no exceptions
5. **Clean Commits & Optional PR** — Focused conventional commits, stash-based grouping

## Arguments

All optional with sensible defaults. Flags use positive names with boolean values.

| Argument | Default | Description |
|----------|---------|-------------|
| `--bdd` | `false` | Use BDD-style (Given/When/Then) test cases |
| `--team` | `true` | Run agent team discussion at each deliverable phase |
| `--approval` | `true` | Run owner approval step after implementation |
| `--review` | `true` | Run review-local quality gate |
| `--qa` | `true` | Run orch-qa + scenario-gen quality gate |
| `--pm-review` | `false` | Run pm-review alongside review-local (opt-in) |
| `--e2e` | `false` | Run e2e-test for frontend changes (opt-in) |
| `--self-review` | `true` | Run self-pr-review after PR creation |
| `--address-comments` | `false` | Run address-pr-comments after self-pr-review (opt-in) |
| `--quality-gate` | `standard` | Preset: `none` / `standard` / `full` |
| `--base-branch` | repo default | Branch to create feature branch from |
| `--branch` | auto-generated | Feature branch name (also worktree directory name) |
| `--pr` | `false` | Create a PR after commits |

**Quality gate presets** (override individual flags):
- `none` = `--review false --qa false --self-review false`
- `standard` = default (review + qa + self-review enabled)
- `full` = enables everything (pm-review, e2e, address-comments also enabled)

## Workflow Overview

```
Phase 0a: PRD [+team review]
  -> Phase 0b: Tech Req [+team review]
  -> Phase 1: Branch Setup
  -> Phase 2: Plan [+team review]
  -> Phase 3: Test Design [+test-scenario agents]
  -> Phase 4: RED -> Phase 5: GREEN -> Phase 6: REFACTOR
  -> Phase 6a: Quality Gates (skill agents)
  -> Phase 7: Approval
  -> Phase 7a: Implementation Review (fresh agent)
  -> Phase 8: Commit & PR
  -> Phase 8a: Post-PR Review (skill agents)
```

---

### Phase 0a: PRD (Product Requirements Document)

Before any technical work, create a PRD from the user's request.

1. Analyze the user's task description, requirements, and context
2. Draft a PRD covering:
   - **Problem Statement** — What problem does this solve?
   - **Goals & Non-Goals** — What's in scope and explicitly out of scope
   - **User Stories / Use Cases** — Who benefits and how
   - **Acceptance Criteria** — Measurable conditions for success
   - **Constraints & Assumptions** — Known limitations
   - **Success Metrics** — How to measure if this was done right

3. **Team Discussion on PRD** (skip if `--team false`):

   Present agent team to user:
   > **PRD Review Agents:**
   > - pm-review — product management perspective, scope validation
   > - Devil's Advocate — challenge assumptions, find gaps
   > - [additional agents based on task domain]
   >
   > **Proceed with these agents?**

   Spawn confirmed agents. Synthesize findings (Critical/Important/Nice-to-have). Update PRD.

4. Present the final PRD to the user for approval
5. Iterate until approved

The PRD drives all subsequent phases.

### Phase 0b: Technical Requirements Document

Based on the approved PRD, create a Technical Requirements Document.

Present agent team to user:
> **Tech Req Agents:**
> - Architecture — system design, component boundaries, data flow
> - Security — threat model, auth requirements, data protection
> - Resource — memory, CPU, network constraints
> - Devil's Advocate — challenge assumptions
> - [additional agents based on PRD scope]
>
> **Proceed with these agents?**

1. Spawn confirmed agents in parallel to analyze the PRD
2. Synthesize into a Technical Requirements Document:
   - **Architecture Overview** — Components, interfaces, data flow
   - **Technical Constraints** — Language, framework, performance requirements
   - **API / Interface Contracts** — Inputs, outputs, error handling
   - **Data Model Changes** — Schema updates, migrations needed
   - **Security Requirements** — Authentication, authorization, validation rules
   - **Testing Strategy** — What types of tests are needed, coverage targets
   - **Dependencies** — External services, libraries, tools needed
3. Present to user for approval

The Tech Req Doc informs all subsequent phases.

### Phase 1: Branch Setup

1. Detect repo's default branch via `git remote show origin | grep 'HEAD branch'` (fallback to `develop`/`main`)
2. Use `--base-branch` if provided, otherwise use the detected default
3. **Fetch the latest base branch from remote:**
   ```bash
   git fetch origin <base-branch>
   ```
   - If fetch fails (network error, auth failure), warn and continue with local branch
4. If `--branch` not provided, derive from task description (e.g. `feat/short-description`)
5. Record the main repo root: `REPO_ROOT=$(git rev-parse --show-toplevel)`
6. Create worktree with feature branch from the fetched remote ref:
   ```bash
   git worktree add "$REPO_ROOT/.worktrees/<branch-name>" -b <branch-name> origin/<base-branch>
   ```
   - If fetch failed in step 3, fall back to local `<base-branch>` instead of `origin/<base-branch>`
   - If the worktree path already exists (stale), clean up first: `git worktree remove <path>` then retry
   - If the branch already exists, omit `-b`: `git worktree add "$REPO_ROOT/.worktrees/<branch-name>" <branch-name>`
7. Change working directory to the worktree: `cd "$REPO_ROOT/.worktrees/<branch-name>"`
   - **All subsequent phases operate inside the worktree directory**
   - The main checkout remains on its original branch, undisturbed

### Phase 2: Plan

1. Enter plan mode with `EnterPlanMode`
2. Understand the user's request thoroughly; ask clarifying questions if ambiguous
3. Explore the codebase: existing patterns, conventions, dependencies, related tests
4. Document acceptance criteria and edge cases
5. Write a clear implementation plan

6. **Team Discussion on Plan** (skip if `--team false`):

   Present agent team to user:
   > **Plan Review Agents:**
   > - Architecture — design patterns, modularity, testability
   > - Security — input validation, injection risks, data exposure
   > - Resource — memory, CPU, network constraints
   > - Devil's Advocate — challenge assumptions, find flaws
   > - [additional agents based on task]
   >
   > **Proceed with these agents?**

   Spawn confirmed agents. Read `references/team-roles.md` for detailed prompts.
   Synthesize findings (Critical/Important/Nice-to-have). Update plan.

7. Present the plan via `ExitPlanMode` for user approval
8. If rejected, iterate until approved

### Phase 3: Test Case Design

Design comprehensive test cases **before writing any implementation code**.

**Step 3a: Automated Test Outline** (mandatory)

Present to user:
> **Test Design Agent:** /test-scenario — generate rough test outline from plan
> **Proceed?**

Invoke `/test-scenario` skill to generate a test outline from the approved plan.
**Always show the generated test cases to the user.**
- Pass the feature description, acceptance criteria, and `--bdd` flag if set
- The skill generates structured test cases covering happy path, edge cases, error handling, constraints, and data integrity
- Merge with team discussion findings from prior phases

Read `references/skill-agents.md` for invocation details.

**Step 3b: Manual Test Design** (always)

Read `references/test-design.md` for the 9 test categories. Fill gaps not covered by the test-scenario outline, particularly categories 5-9 (Integration Points, Output Format, Security, Ordering, Resource Limits).

If `--bdd` is set, write test cases in Given/When/Then Gherkin format. Read `references/bdd-guide.md`.

**Step 3c: Test Design Verification** (mandatory)

Present to user:
> **Test Verification Agent:** /test-scenario — verify combined test design for completeness
> **Proceed?**

Invoke `/test-scenario` again to validate the combined test design.
**Always show the verified test cases to the user.**
- Evaluates coverage against acceptance criteria, missing categories, test quality
- User must approve the test design before proceeding to RED
- If gaps found, iterate on the test design

**Test-First Checklist** (all must be true before proceeding):
- [ ] All acceptance criteria have corresponding tests
- [ ] Edge cases from team discussion are covered
- [ ] Security concerns are tested
- [ ] Error handling scenarios are tested
- [ ] Tests compile but fail (RED state confirmed)

### Phase 4: RED — Write Failing Tests

1. Create test file with all designed test cases
2. Use descriptive test names: `MethodName_StateUnderTest_ExpectedBehavior`
3. Structure each test with clear Arrange/Act/Assert (or Given/When/Then if `--bdd`)
4. Create minimal stub implementation that throws NotImplementedException (or equivalent)
5. Run tests — **ALL MUST FAIL**
6. If any test passes, the stub is too complete — simplify it
7. Commit: `test: add failing tests for <feature>`

### Phase 5: GREEN — Make Tests Pass

1. Pick one failing test — start with the simplest
2. Write the minimum code to pass that test
3. Run tests: target passes, previous tests pass, remaining still fail
4. Repeat for each failing test
5. Do NOT add features not covered by tests
6. Apply security measures identified in prior phases
7. Wire up the implementation to the system (CLI, API, UI) as needed
8. When all tests pass, commit: `feat: implement <feature>`

### Phase 6: REFACTOR — Improve Code Quality

1. Review for: duplication, naming clarity, performance, documentation needs
2. Make small changes — one refactoring at a time
3. Run tests after each change — keep them green
4. If changes warrant it, commit: `refactor: improve <aspect> in <feature>`

**Done when:** No duplication, clear names, focused methods, no commented-out code, tests pass.

### Phase 6a: Quality Gates

Post-refactor quality checks using skill agents. Read `references/skill-agents.md` for details.

Skip all gates if `--quality-gate none` or both `--review false` and `--qa false`.

**Step 1: Present agent plan to user**

> **Quality Gate Agents:**
> - review-local — 8-perspective code review [enabled/disabled]
> - pm-review — PMBOK analysis [enabled/disabled]
> - orch-qa — test coverage & gap analysis [enabled/disabled]
> - scenario-gen — test scenarios from branch diff [enabled/disabled]
> - e2e-test — frontend E2E tests [enabled/disabled]
>
> **Proceed with these agents?** (you can add/remove)

**Gate 1: Code Review** (when user confirms review-local)

Spawn in parallel via Agent tool:
- `/review-local` — 8-perspective review of worktree changes
- `/pm-review` (if `--pm-review true`) — PMBOK analysis

**Critical finding gate**: If Critical findings exist, present to user. If user wants to fix, return to Phase 6 (REFACTOR), then re-run gate.

**Gate 2: QA Analysis** (when user confirms orch-qa)

Spawn in parallel via Agent tool:
- `/orch-qa` — run tests and gap analysis on changed files
- `/scenario-gen` — generate test scenarios from branch diff

**Gate 3: E2E Testing** (when `--e2e true` AND frontend changes detected)

Invoke `/e2e-test` with CSV scenarios from scenario-gen if available.

### Phase 7: Approval

Skip if `--approval false`.

1. Present a summary of all changes:
   - Tests added (count and categories)
   - Implementation highlights
   - Refactorings applied
   - Quality gate findings addressed
2. Wait for user approval
3. If rejected, iterate on changes

### Phase 7a: Implementation Review

**Always spawn a fresh agent to review actual code changes before making the PR.**

Present to user:
> **Implementation Review Agent:** A fresh agent will review the actual code diff for bugs, missed edge cases, security issues, and code quality.
> **Proceed?**

Spawn a new general-purpose agent with:
- The full `git diff` of all worktree changes
- Original acceptance criteria from PRD
- Team discussion findings from prior phases

The agent reviews the **actual implementation** (not the plan) and reports:
- Bugs or logic errors
- Missed edge cases or security concerns
- Code quality issues
- Whether implementation matches acceptance criteria

If Critical issues found: return to Phase 6 (REFACTOR), fix, re-run.
Proceed only when clean or user explicitly approves.

### Phase 8: Commit & PR

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

**Post-PR AI Review** (only when PR created successfully):

Present to user:
> **Post-PR Agents:**
> - self-pr-review — AI review loop (Copilot + Gemini) [enabled/disabled]
> - address-pr-comments — auto-apply reviewer comments [enabled/disabled]
>
> **Proceed with these agents?**

1. If confirmed: invoke `/self-pr-review` with PR number
2. If `--address-comments true` and comments remain: invoke `/address-pr-comments`
3. Report final PR status

Read `references/skill-agents.md` for invocation details.

**Worktree Cleanup** (always, as final step):

1. Change back to the main repo root: `cd "$REPO_ROOT"`
2. Remove the worktree: `git worktree remove "$REPO_ROOT/.worktrees/<branch-name>"`
   - If uncommitted changes remain, use `--force`
3. Verify cleanup: `git worktree list`

---

## BDD vs TDD

TDD is always enforced. `--bdd` only changes test format: `Method_State_Expected` (TDD) vs Given/When/Then Gherkin (BDD). Use BDD when stakeholder communication matters.

## Example Invocations

### Standard Development
```
/dev-workflow

Task: Add a health check endpoint
Requirements:
- Return 200 with JSON status
- Include uptime and version info
```

### BDD Mode
```
/dev-workflow --bdd true
Task: Implement user authentication flow
```

### Quick Solo Mode
```
/dev-workflow --team false --approval false
Task: Fix date parsing bug
```

### Full Pipeline
```
/dev-workflow --quality-gate full --pr true --base-branch develop
Task: Add payment processing integration
```

## Behavior Scenarios

```gherkin
Scenario: Full workflow with PRD, tech req, and team review
  Given the user asks to implement a feature
  When the user invokes /dev-workflow
  Then the skill creates a PRD, gets tech requirements, creates a worktree,
       plans with team review, designs tests with /test-scenario,
       executes RED-GREEN-REFACTOR, runs quality gates, gets approval,
       reviews implementation with a fresh agent, commits, and cleans up

Scenario: PRD created from user request
  Given the user invokes /dev-workflow with a task description
  When Phase 0a runs
  Then a PRD is created covering problem, goals, user stories, acceptance criteria
  And the user reviews and approves the PRD before any technical work begins

Scenario: Technical requirements derived from PRD
  Given the PRD is approved
  When Phase 0b runs
  Then the user is shown which agents will analyze the PRD
  And agents produce a Technical Requirements Document
  And the user approves the Tech Req Doc

Scenario: Branch created from latest remote
  Given the user invokes /dev-workflow
  When Phase 1 runs
  Then git fetch origin <base-branch> runs before worktree creation
  And the feature branch is based on origin/<base-branch> (latest remote state)

Scenario: Fetch failure falls back to local branch
  Given the remote is unreachable
  When Phase 1 attempts git fetch
  Then the skill warns and branches from local <base-branch> instead

Scenario: Team discussion embedded in Plan phase
  Given Phase 2 Plan is drafted
  When --team true (default)
  Then agents review the plan from architecture, security, resource, devil's advocate perspectives
  And findings are synthesized and the plan is updated before user approval

Scenario: Test scenario skill generates and verifies tests
  Given Phase 2 Plan is approved
  When Phase 3 runs
  Then /test-scenario generates a rough test outline (Step 3a, shown to user)
  And manual test design fills gaps (Step 3b)
  And /test-scenario verifies the combined design (Step 3c, shown to user)
  And the user approves before RED

Scenario: Quality gates run with standard preset
  Given Phase 6 REFACTOR completes
  When Phase 6a runs (default --quality-gate standard)
  Then user is shown which agents will run and confirms
  And review-local and orch-qa+scenario-gen are spawned as parallel agent pairs
  And Critical findings block progression until addressed

Scenario: Fresh agent reviews actual implementation before PR
  Given Phase 7 Approval completes
  When Phase 7a runs
  Then a new agent reviews the actual code diff (not the plan)
  And findings are presented to the user before Commit & PR

Scenario: Quality gates skipped with --quality-gate none
  Given the user invokes /dev-workflow --quality-gate none
  When Phase 6 completes
  Then no quality gate skills are invoked

Scenario: Quick fix without team overhead
  Given the user invokes /dev-workflow --team false --approval false
  Then team discussion and approval are skipped but TDD and test-scenario still run

Scenario: Worktree isolation and cleanup
  Given the workflow completes
  Then the worktree is removed and git worktree list confirms no orphans

Scenario: Agent confirmation at every phase
  Given any phase is about to spawn agents
  Then the user is always shown which agents will run and can adjust before confirming
```

## References

- `references/skill-agents.md` — Skill agent invocation guide: Agent tool patterns, context passing, error handling
- `references/team-roles.md` — Agent prompts, output formats, and synthesis protocol
- `references/test-design.md` — 9 test categories with examples and mocking strategy
- `references/bdd-guide.md` — Given/When/Then writing guide and BDD decision criteria
- `references/commit-guide.md` — Conventional commits, stash-based grouping, HEREDOC format
- `references/pr-guide.md` — PR template detection, creation with gh CLI, post-PR skill agents
