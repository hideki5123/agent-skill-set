---
name: scenario-gen
description: >
  Generate test scenarios from git branch changes. Compares current branch to
  main/master, identifies changed files, classifies them by type (frontend, API,
  backend, config), and generates test scenarios covering those changes. Produces
  a Markdown report with embedded screenshots for UI changes and CSV files
  compatible with the e2e-test skill for automated execution. Captures live
  browser screenshots via Playwright MCP for frontend changes. Use when the user
  asks to generate test scenarios, create test cases from changes, analyze branch
  for testing, generate test plan from diff, create e2e scenarios from code
  changes, or build test coverage for a branch. Trigger phrases include
  "generate test scenarios", "test scenarios for this branch", "create test
  cases from changes", "what should I test", "generate test plan", "test
  coverage for my changes", "scenario generator", "test scenario generator",
  "generate scenarios from diff", "create e2e scenarios", "test scenario from branch".
---

# Test Scenario Generator

Generate test scenarios from git branch changes. Analyze diffs, classify changes,
capture screenshots for UI changes, and produce both Markdown reports and CSV files
compatible with the e2e-test skill.

## Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--base` | auto-detect | Base branch to diff against (main/master/develop) |
| `--url` | auto-detect | Dev server URL for screenshot capture |
| `--viewport` | `1280x720` | Browser viewport for screenshots |
| `--output-dir` | `./test-scenarios` | Output directory for reports and CSVs |
| `--skip-screenshots` | `false` | Skip browser screenshot capture |
| `--scope` | `all` | Path/glob filter for changed files |

## Constraints

- **NO code changes**: Do not modify source code, config, or test files
- **Documents OK**: Create markdown, CSV, and screenshot files only
- **Branch-based**: Always work from git diff, never analyze unchanged code
- **e2e-test compatible**: CSV output must be directly executable by the e2e-test skill

## Workflow

### Phase 1: Detect Changes

1. Detect base branch:
   - If `--base` provided, use it
   - Otherwise: `git remote show origin | grep 'HEAD branch'` to detect default
   - Fallback order: `main`, `master`, `develop`

2. Get changed files:
   ```bash
   git diff <base>...HEAD --name-only --diff-filter=ACMR
   ```

3. Get diff stats:
   ```bash
   git diff <base>...HEAD --stat
   ```

4. If no changes detected, inform the user:
   > No changes detected between current branch and `<base>`. Verify you are on the correct branch.

5. If more than 50 changed files, warn the user and ask whether to proceed or filter with `--scope`.

6. Apply `--scope` filter if provided.

### Phase 2: Classify Changes

Read `references/change-classification.md` for the full classification rules.

Classify each changed file into categories:

| Category | Examples |
|----------|---------|
| **frontend** | `.tsx`, `.jsx`, `.vue`, `.html`, `.css`, component directories |
| **api** | Route files, controllers, handlers, OpenAPI specs |
| **backend** | Services, models, migrations, middleware |
| **config** | `.env`, config files, `package.json`, CI/CD files |
| **test** | `*.test.*`, `*.spec.*`, `__tests__/` |
| **docs** | `.md`, `docs/`, `README` |

For each file, read the diff to understand what specifically changed:
```bash
git diff <base>...HEAD -- <file>
```

Present the classification table to the user before proceeding.

### Phase 3: Analyze Impact

For each changed file:

1. **Read the changed file** to understand full context
2. **Read the diff hunks** to understand what specifically changed
3. **Identify affected functionality**:
   - Frontend: Which UI components, pages, forms, interactions changed?
   - API: Which endpoints changed? What request/response schemas are affected?
   - Backend: What business logic, data flows, or services are affected?
   - Config: What settings changed and what do they affect?

4. **Check downstream dependencies**: Use grep to find imports/requires referencing the changed module

5. **Build impact map** for each logical change:
   - What changed (function, component, endpoint)
   - What it affects (user-facing behavior, data flow, API contract)
   - What preconditions exist (auth required, specific data state)

### Phase 4: Generate Scenarios

Read `references/scenario-templates.md` for templates by change type.

For each impact from Phase 3, generate test scenarios.

Each scenario must include:
- **ID**: `TS-NNN` (zero-padded sequential)
- **Title**: Descriptive name of what is being tested
- **Type**: `ui` | `api` | `backend` | `config`
- **Priority**: `critical` | `high` | `medium` | `low`
- **Preconditions**: What must be true before the test starts
- **Steps**: Ordered list with step number, action, target, input, expected result
- **Changed files covered**: Which diff files this scenario tests

#### Frontend scenarios
- Navigate to the affected page
- Interact with changed components in the correct order
- Verify visual state and behavior after each interaction
- Cover happy path and one error state
- Note UI components that need screenshot capture

#### API scenarios
- Document endpoint method, path, headers
- Provide example request bodies
- Document expected response codes and bodies
- Cover success, validation error, and auth failure cases

#### Backend scenarios
- Document entry point and expected output
- Trace data through changed components
- Identify state transitions to verify
- Cover error handling paths

#### Config scenarios
- Document what the config controls
- Verify behavior with the new config value
- Note if change requires restart

### Phase 5: Capture Screenshots (Frontend Only)

Skip this phase if `--skip-screenshots` is set or no frontend changes were detected.

#### 5a. Detect dev server

Probe the dev server URL:
- Use `--url` if provided
- Otherwise probe common ports in order:
  - `http://localhost:3000`
  - `http://localhost:5173`
  - `http://localhost:4200`
  - `http://localhost:8080`

Use `mcp__playwright__browser_navigate` to attempt connection.

If no server is reachable:
> No dev server detected. Frontend screenshots will be skipped. Start your dev server and re-run, or use `--url=<your-url>`.

Continue with text-based scenarios (mark screenshots as "pending" in report).

#### 5b. Capture screenshots

For each UI scenario from Phase 4:

1. Navigate to the relevant page: `mcp__playwright__browser_navigate`
2. Take accessibility snapshot: `mcp__playwright__browser_snapshot`
3. Identify the changed UI component in the accessibility tree
4. Take a full-page screenshot: `mcp__playwright__browser_take_screenshot`
5. Save as `scenario-NNN-<component-name>.png` in the output directory

If a specific element needs highlighting:
- Use `browser_snapshot` to find the element's ref
- Use `browser_hover` on the element to visually indicate it
- Then take the screenshot

#### 5c. Close browser

After all screenshots are captured: `mcp__playwright__browser_close`

### Phase 6: Write Output

Create the output directory:
```bash
mkdir -p <output-dir>/<YYYY-MM-DD-HHmm>
```

#### 6a. Generate Markdown Report

Save as `<output-dir>/<YYYY-MM-DD-HHmm>/REPORT.md`.

Read `references/report-template.md` for the full template structure.

Report must include:
1. **Header**: Date, branch, base, change count, scenario count
2. **Executive Summary**: Overview of changes and testing needs
3. **Changes Analyzed**: Table of all changed files with classification
4. **Test Scenarios**: Grouped by feature/component, with full step details and embedded screenshots
5. **Coverage Matrix**: Map of changed files to scenario IDs
6. **Generated CSV Files**: List with descriptions and execution instructions
7. **Recommendations**: Actionable suggestions for additional testing

Embed screenshots inline with their scenarios:
```markdown
![Contact form before submission](scenario-001-contact-form.png)
```

#### 6b. Generate CSV Files

Read `references/csv-format.md` for the exact format specification.

For each UI test scenario (or group of related UI scenarios), generate a CSV file compatible with the e2e-test skill.

File naming: `scenario-NNN-<feature-slug>.csv`

Key CSV rules:
- Targets are human-readable descriptions (NOT CSS selectors)
- Actions use the e2e-test action vocabulary (navigate, click, type, verify, etc.)
- One CSV per logical user flow
- Include `screenshot` action steps at key verification points

Only generate CSVs for **frontend/UI scenarios**. API and backend scenarios are documented in REPORT.md only (e2e-test is browser-only).

#### 6c. Summary to User

After writing all files, present in chat:
- Number of scenarios generated by type (UI, API, Backend, Config)
- Number of CSV files created with their paths
- Number of screenshots captured
- Output directory path
- How to execute: `Run e2e test with scenario <path-to-csv>`

## Edge Cases

| Situation | Behavior |
|-----------|----------|
| No changes on branch | Inform user, suggest checking branch |
| Only test files changed | Note tests changed, suggest running orch-qa instead |
| Only docs changed | Minimal report noting documentation changes only |
| Only config changed | Config impact scenarios, no screenshots |
| Dev server not running | Text-only scenarios, suggest starting dev server |
| Very large diff (>50 files) | Warn user, ask to filter with `--scope` |
| Binary files in diff | Skip binary files, note in report |
| Deleted files only | Regression scenarios for code that depended on deleted files |
| Branch has merge conflicts | Warn and stop -- resolve conflicts first |

## Integration with Other Skills

| Skill | How to use together |
|-------|-------------------|
| **e2e-test** | CSV output is directly executable: `Run e2e test with scenario <path>.csv` |
| **orch-qa** | Complementary: orch-qa audits existing tests, this skill creates new scenarios from changes |
| **dev-workflow** | After implementing a feature via dev-workflow, use this skill to create E2E scenarios |

## Behavior Scenarios

```gherkin
Scenario: Generate test scenarios for frontend changes
  Given the current branch has UI component changes and a dev server is running
  When the user invokes the skill
  Then it analyzes the diff, launches the app in a browser, captures screenshots
  of affected UI components, and generates REPORT.md with embedded screenshots
  plus CSV scenarios compatible with e2e-test

Scenario: Generate test scenarios for API changes
  Given the current branch has API endpoint changes
  When the user invokes the skill
  Then it analyzes the diff, documents affected endpoints with request/response
  examples, and generates test scenarios in REPORT.md

Scenario: Generate test scenarios for mixed changes
  Given the current branch has both frontend and backend changes
  When the user invokes the skill
  Then it classifies each change, generates appropriate scenarios for each type,
  captures screenshots for UI changes, and produces a unified report

Scenario: No dev server running for frontend changes
  Given the current branch has frontend changes but no dev server is accessible
  When the user invokes the skill
  Then it generates text-based scenarios without screenshots and suggests how to
  start the dev server for screenshot capture

Scenario: No changes on branch
  Given the current branch has no diff from main
  When the user invokes the skill
  Then it informs the user that no changes were detected and suggests checking
  the branch
```

## References

- `references/change-classification.md` -- File extension and path patterns for categorizing changes as frontend, API, backend, config, test, or docs
- `references/scenario-templates.md` -- Templates for generating scenarios by change type (UI, API, backend, config) with worked examples
- `references/report-template.md` -- REPORT.md template with all sections and placeholder instructions
- `references/csv-format.md` -- CSV format reference ensuring e2e-test skill compatibility, including action vocabulary and target description conventions
