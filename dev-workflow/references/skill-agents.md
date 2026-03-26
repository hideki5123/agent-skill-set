# Skill Agent Invocation Guide

How dev-workflow spawns other installed skills as agents within workflow phases.

## Core Rule: Always Confirm with User

Before spawning any agent at any phase, present the proposed agent list to the user:

> **[Phase Name] Agents:**
> - agent-1 — purpose [enabled/disabled]
> - agent-2 — purpose [enabled/disabled]
>
> **Proceed with these agents?** (you can add/remove)

Wait for user confirmation. The user may adjust which agents run.

## Invocation Mechanism

Use the **Agent tool** to spawn skill-based agents. This provides genuine parallelism — multiple agents can run simultaneously in separate subprocesses.

### Single Agent Pattern

```
Agent tool:
  description: "Run review-local skill"
  prompt: "You are in worktree at [WORKTREE_PATH]. Run the /review-local skill on the code changes. Return the full output including severity levels."
```

### Parallel Agent Pattern

To run agents in parallel, issue multiple Agent tool calls in a **single message**:

```
Agent tool call 1:
  description: "Run review-local"
  prompt: "You are in worktree at [WORKTREE_PATH]. Run /review-local. Return full output."

Agent tool call 2:
  description: "Run pm-review"
  prompt: "You are in worktree at [WORKTREE_PATH]. Run /pm-review. Return full output."
```

Both agents execute concurrently. Wait for both to complete before proceeding.

### Background Agent Pattern

For agents whose results you don't need immediately:

```
Agent tool:
  description: "Run scenario-gen"
  run_in_background: true
  prompt: "..."
```

You'll be notified when it completes.

## Phase 0a: PRD Team Discussion

**Agents**: pm-review, devil's advocate, domain-specific (user confirms)

Each agent receives:
- The draft PRD text
- The user's original task description

Each agent reviews the PRD from their perspective and returns findings categorized as Critical/Important/Nice-to-have.

Synthesize all findings, update the PRD, present to user.

## Phase 0b: Technical Requirements Team Discussion

**Agents**: Architecture, Security, Resource, devil's advocate (user confirms)

Each agent receives:
- The approved PRD
- Relevant codebase context (file structure, existing patterns)

Each agent produces their section of the Technical Requirements Document. Synthesize into a single document.

## Phase 2: Plan Team Discussion

**Agents**: Architecture, Security, Resource, Devil's Advocate (user confirms)

Same as existing team discussion, but now embedded in the Plan phase. Each agent receives:
- The approved PRD and Tech Req Doc
- The draft implementation plan
- Relevant codebase context

Read `references/team-roles.md` for detailed teammate prompts and output formats.

Protocol:
1. Spawn confirmed agents via Agent tool (parallel)
2. Collect findings from all agents
3. Categorize by severity (Critical/Important/Nice-to-have)
4. Deduplicate overlapping concerns
5. Update the plan with concrete action items
6. Present consolidated feedback to user

## Phase 3, Step 4a: test-scenario (Generate)

**Agent**: test-scenario (mandatory, user confirms before spawning)

```
Agent tool:
  description: "Generate test outline"
  prompt: |
    You are in worktree at [WORKTREE_PATH].
    Run the /test-scenario skill to generate a test outline for this feature:

    Feature: [feature description from PRD]
    Acceptance Criteria: [from PRD]
    Technical Requirements: [from Tech Req Doc]
    BDD mode: [true/false based on --bdd flag]

    Generate a structured test outline covering:
    - Happy path
    - Edge cases
    - Error handling
    - Constraints
    - Data integrity

    Return the full test outline.
```

**Output handling**:
- Always show the generated test cases to the user
- Merge with team discussion findings from prior phases (security tests, edge cases)

## Phase 3, Step 4c: test-scenario (Verify)

**Agent**: test-scenario (mandatory, user confirms before spawning)

```
Agent tool:
  description: "Verify test design"
  prompt: |
    You are in worktree at [WORKTREE_PATH].
    Run the /test-scenario skill to verify this combined test design:

    [combined test outline from 4a + 4b]

    Acceptance Criteria: [from PRD]

    Evaluate:
    - Coverage against acceptance criteria
    - Missing edge cases or categories
    - Test quality (naming, structure, assertions)
    - Alignment with security and resource findings

    Report any gaps or quality issues.
```

**Output handling**:
- Always show the verified test cases to the user
- User must approve before proceeding to RED

## Phase 6a Gate 1: review-local + pm-review

**Agents**: review-local (default on), pm-review (opt-in via `--pm-review true`)

Spawn in parallel:

```
Agent 1 (review-local):
  description: "Run review-local"
  prompt: "You are in worktree at [WORKTREE_PATH]. Run /review-local on the local changes. Return the full review report with severity levels."

Agent 2 (pm-review, if enabled):
  description: "Run pm-review"
  prompt: "You are in worktree at [WORKTREE_PATH]. Run /pm-review on the local changes. Return the full PMBOK analysis."
```

**Critical finding gate**:
- Parse review-local output for "Critical" severity findings
- If Critical findings exist:
  1. Present to user with details
  2. Ask: "Address critical findings before continuing?"
  3. If yes: return to REFACTOR phase, fix, re-run gate
  4. If no: proceed with acknowledgment

## Phase 6a Gate 2: orch-qa + scenario-gen

**Agents**: orch-qa + scenario-gen (default on via `--qa true`)

Spawn in parallel:

```
Agent 1 (orch-qa):
  description: "Run QA analysis"
  prompt: "You are in worktree at [WORKTREE_PATH]. Run /orch-qa to analyze test quality, run existing tests, diagnose any failures, and identify coverage gaps. Return the full quality report."

Agent 2 (scenario-gen):
  description: "Generate test scenarios"
  prompt: "You are in worktree at [WORKTREE_PATH]. Run /scenario-gen to generate test scenarios from the branch changes. Return the report and any CSV files generated."
```

**Output handling**:
- Present both reports to user
- If scenario-gen produces CSV files, make them available for Gate 3 (e2e-test)

## Phase 6a Gate 3: e2e-test

**Agent**: e2e-test (opt-in via `--e2e true`, only when frontend changes detected)

**Frontend detection**: Check changed files for: .tsx, .jsx, .vue, .svelte, .html, .css, .scss
If none found, skip even if `--e2e true` (inform user).

```
Agent (e2e-test):
  description: "Run E2E tests"
  prompt: "You are in worktree at [WORKTREE_PATH]. Run /e2e-test. [If CSV from scenario-gen]: Use these test scenarios: [CSV path]. Return the test report with screenshots."
```

## Phase 7a: Implementation Review

**Agent**: Fresh general-purpose agent (mandatory, user confirms)

```
Agent tool:
  description: "Review implementation diff"
  prompt: |
    Review the actual code changes (not a plan) for quality and correctness.

    Git diff of all changes:
    [full git diff output]

    Original requirements:
    [acceptance criteria from PRD]

    Team discussion findings:
    [synthesized findings from prior phases]

    Review for:
    - Bugs or logic errors
    - Missed edge cases or security concerns
    - Code quality (naming, duplication, complexity)
    - Whether implementation matches acceptance criteria
    - Discrepancies between plan and actual code

    Categorize findings as Critical/Important/Nice-to-have.
```

**Output handling**:
- Present findings to user
- If Critical issues: return to REFACTOR, fix, re-run
- Proceed to Commit & PR only when clean or user approves

## Phase 8a: Post-PR Review

**Agents**: self-pr-review (default on), address-pr-comments (opt-in)

These run **sequentially** (address-pr-comments depends on self-pr-review results):

```
Step 1 (self-pr-review, if --self-review true):
  Skill tool:
    skill: "self-pr-review"
    args: "[PR number]"

Step 2 (address-pr-comments, if --address-comments true and comments remain):
  Skill tool:
    skill: "address-pr-comments"
    args: "[PR number]"
```

Post-PR agents use the Skill tool (not Agent tool) since they run sequentially and need direct PR context.

## Error Handling

| Situation | Behavior |
|-----------|----------|
| Skill not installed | Warn user: "Skill [name] not available, skipping" |
| Skill fails/errors | Log the error, present to user, continue workflow |
| Skill times out | After 10 minutes, warn user and ask: wait or skip? |
| User cancels agent | Skip that agent, continue workflow at next step |
| All agents in a gate fail | Present errors, ask user whether to proceed or retry |
