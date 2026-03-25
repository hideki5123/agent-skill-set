---
name: test-scenario
description: >
  Generate test outlines (living documentation) and test code from natural language
  feature descriptions. Supports .NET (xUnit/NUnit/MSTest), Python (pytest),
  TypeScript (Vitest/Jest). Strict mode: no internal module mocking, real DB,
  AAA pattern, Design by Contract (DbC). Use when the user asks to generate tests
  from a feature description, create test cases from requirements, write test outlines,
  scaffold test files, generate test code from spec, convert TODO tests to real tests,
  or create tests for a function. Trigger phrases include "test scenario",
  "テストシナリオ", "generate tests", "テスト生成", "テストケース作成",
  "write tests for", "scaffold tests", "tests from requirements",
  "テストアウトライン", "convert todo tests", "implement test outline",
  "test outline", "test cases from spec".
---

# Test Scenario Generator

Generate exhaustive test outlines and executable test code from natural language feature descriptions. The outline serves as "living documentation" — a specification expressed as test case names.

## Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--framework` | auto-detect | Test framework override (skips auto-detection) |
| `--lang` | auto-detect | Language for test case names: `ja`, `en` |
| `--outline-only` | `false` | Stop after Phase 2 (produce outline only, skip implementation) |
| `--test-file` | auto | Target test file path |
| `--run-cmd` | auto-detect | Override test runner command |

## Constraints

- **NEVER** write implementation or production code — create and modify test files only
- **Never skip the outline** — Phase 2 outline is the "contract" that Phase 3 implements
- **Always ask** when specs, data flows, or edge cases are unclear
- **Strict mode only** — no internal module mocking, real database, AAA pattern, Design by Contract

## Workflow

### Phase 1: Understand & Clarify

1. Parse the user's feature description. Extract:
   - Functional requirements (what the feature does)
   - Constraints (limits, ranges, defaults, permissions)
   - Data flows (input sources, processing, output destinations)
   - UI/API surface (where the feature is exposed)

2. Detect the project's test framework.
   Read `references/framework-profiles.md` for detection logic and syntax mappings.
   - Scan project files to identify the test framework
   - Use `--framework` override if provided
   - Present detection result to user and confirm

3. Determine test file location:
   - If `--test-file` provided, use it
   - Otherwise, infer from the feature description and project conventions
   - If file exists, read it to understand current test coverage

4. Detect test name language:
   - If `--lang` provided, use it
   - Otherwise, check existing test files for Japanese characters
   - Default to `en` if no signal found

5. If anything is unclear, present a numbered question list covering:
   - Input/output contracts
   - Data sources involved (DB tables, APIs, caches)
   - Boundary values and limits
   - Error states to handle
   - Authentication/authorization requirements

   Wait for answers before proceeding. If the user says "use your best judgment", proceed with reasonable assumptions and note them.

### Phase 2: Generate Test Outline

Read `references/outline-rules.md` for the full outline generation rules and per-framework syntax.

1. Generate a test file with only structure and TODO-marked test cases:
   - Use the detected framework's TODO marker syntax
   - Organize tests hierarchically by context/precondition
   - Each test case name must be self-documenting "living documentation"

2. Cover all 5 categories:
   - **Happy Path** — normal expected behavior with valid inputs
   - **Edge Cases** — boundary conditions, empty/null/zero values, at-limit values
   - **Error Handling** — invalid inputs, auth failures, service unavailability
   - **Constraints** — business rules, limits, defaults from the spec
   - **Data Integrity** — state before/after operations, rollback on failure

3. Do NOT create test cases that assume mocking of internal modules.

4. Present the outline to the user in chat. Ask:
   > "Does this outline cover all the behaviors you expect? Should I add, remove, or modify any test cases?"

5. Iterate until the user approves, then write the file.

6. If `--outline-only` is set, stop here and report the file path.

### Phase 3: Implement Test Code

Read `references/implementation-rules.md` for the 6 absolute rules with per-framework code examples.

Convert each TODO-marked test case into an executable test following these rules:

1. **Test Data Lifecycle** — create data in setup, clean up in teardown, using framework-appropriate hooks
2. **AAA Pattern** — visually separate Arrange, Act, Assert with blank lines
3. **No Internal Module Mocking** — use real database, Docker-based mock servers for HTTP
4. **Design by Contract** — assert return value AND database state; in error cases, assert error AND unchanged state
5. **Readability** — each test must be self-explanatory in isolation
6. **Test Utilities** — discover and use existing helpers; create new ones if needed

After implementing all tests, run them:
- Detect or use `--run-cmd` for the runner command
- For each failure, classify:
  - **Test code bug** (wrong assertion, incomplete setup): fix the test and re-run
  - **Spec/implementation mismatch** (real defect or ambiguous spec): skip the test with a comment explaining the issue, and ask the user

Report results:
> "X tests passing, Y tests skipped (awaiting clarification on: [list specific questions])"

Present skipped tests with the specific questions that need answering.

## Behavior Scenarios

```gherkin
Scenario: Generate test outline from natural language description
  Given the user provides a feature description in natural language
  When /test-scenario is invoked
  Then detect framework, ask clarifying questions if needed, generate test outline
       covering all 5 categories, present for user approval, and write the file

Scenario: Implement test code from approved outline
  Given an approved test outline exists
  When Phase 3 proceeds
  Then convert all TODO markers to executable tests following the 6 absolute rules,
       run tests, fix test bugs, skip ambiguous cases for user clarification,
       and report results

Scenario: Outline-only mode
  Given the --outline-only flag is set
  When /test-scenario --outline-only is invoked
  Then produce only the test outline and stop after writing the file

Scenario: Ambiguous feature description
  Given a vague or incomplete feature description
  When Phase 1 parses the input
  Then present a numbered list of specific questions and wait for answers
       before generating the outline

Scenario: Update existing test file
  Given a test file already exists at the target path
  When /test-scenario is invoked for the same feature
  Then read existing tests, identify gaps in coverage, and add only missing
       test cases without duplicating existing ones
```

## Integration with Other Skills

| Skill | How to use together |
|-------|---------------------|
| `dev-workflow` | Use test-scenario to generate the outline (RED state), then dev-workflow to implement production code (GREEN) |
| `orch-qa` | Use orch-qa to identify missing test coverage, then feed gap descriptions to test-scenario as input |
| `scenario-gen` | Different triggers: scenario-gen works from git diffs (change-driven), test-scenario works from natural language (spec-driven) |
