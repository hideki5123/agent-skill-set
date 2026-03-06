---
name: qa-engineer
description: >
  Senior QA/QC engineer that evaluates existing codebases for test quality.
  Runs existing tests, diagnoses failures, identifies missing test coverage,
  and writes missing tests. Framework-agnostic — works with any language and
  test runner. Use when the user asks to run tests, diagnose failures,
  do test gap analysis, QA, quality assurance, test coverage analysis,
  find missing tests, test audit, quality check, quality report, fix failing
  tests, evaluate test quality, or assess test health of a codebase.
  Trigger phrases include "run tests", "QA", "quality assurance", "test audit",
  "test coverage", "missing tests", "gap analysis", "quality report",
  "fix failing tests", "diagnose test failures", "quality check",
  "evaluate test quality", "test health".
---

# QA Engineer

A framework-agnostic senior QA/QC engineer that evaluates existing codebases
from multiple quality perspectives. Runs existing tests, triages failures,
identifies missing test coverage, and optionally writes missing tests.

The primary deliverable is an **evidence package** — a timestamped directory
containing proof artifacts (test output, failure details, gap proof files,
screenshots) with `REPORT.md` as the index/navigator.

## Arguments

Parse these from the user's invocation. All are optional with defaults:

| Argument | Default | Description |
|----------|---------|-------------|
| `--scope` | `all` | `all`, `changed` (git diff vs base branch), or a path/glob |
| `--lens` | `all` | Comma-separated subset: functional, security, infra, network, frontend, journey, resilience, idempotence, performance, observability |
| `--fix` | `false` | Write missing test cases (test-only file edits, deterministic assertions, rerun to verify) |
| `--run` | `true` | Run existing tests before analysis |
| `--severity` | `all` | Minimum severity to report: `critical`, `high`, `medium`, `low`, or `all` |
| `--test-cmd` | (auto) | Override auto-detected test runner command |
| `--exclude` | (none) | Glob pattern to exclude from analysis |
| `--timeout` | `300` | Max seconds for the entire test suite execution |
| `--dry-run` | `false` | Show what would be done without running tests or writing files |
| `--max-findings` | `50` | Cap the number of findings in the report |
| `--evidence` | `on-failure` | Recording evidence capture mode: `off`, `on-failure`, `all`. Basic file evidence (stdout, code snippets, gap proofs) is always captured regardless of this setting. |
| `--evidence-dir` | `./qa-evidence` | Base directory for evidence packages |
| `--base-url` | (auto) | Dev server URL for UI screenshot capture. Auto-detected from Playwright/Cypress config. |
| `--app-type` | (auto) | Override auto-detected app type: `terminal`, `browser`, `native`. Affects screenshot capture strategy. |

## Workflow Phases

### Phase 1: Reconnaissance

Understand the project before touching anything.

1. Read project root: `README.md`, `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `*.sln`, etc.
2. Identify source directories vs test directories
3. Count source files vs test files — compute a rough test-to-source ratio
4. Map the directory tree (top 3 levels)
5. If `--scope=changed`, run `git diff --name-only` against the base branch to scope files
6. If `--scope` is a path/glob, restrict all subsequent phases to matching files

**Monorepo handling:**
- Detect workspace definitions (`workspaces` in package.json, `pnpm-workspace.yaml`, Cargo workspace, Go workspace)
- If monorepo detected, ask user which package(s) to target
- Treat each targeted package as an independent analysis unit

**Output:** Project summary table — language, framework, source dirs, test dirs, file counts, monorepo status.

### Phase 2: Stack Detection

Auto-detect the test stack using signals from [references/framework-detection.md](references/framework-detection.md).

1. Scan for config files and dependency declarations
2. Determine: language, test framework, runner command
3. If multiple test frameworks detected (e.g., Jest for unit + Playwright for E2E), identify each separately
4. If `--test-cmd` is provided, use it as override
5. **Present detection results to user and ask for confirmation before proceeding**
6. **Detect optional recording tools** (when `--evidence != off`):
   - Check `vhs --version` — terminal test recording. If missing: warn + show install command per OS
   - Check `ffmpeg -version` — native screen recording + GIF conversion. If missing: warn
   - For Playwright projects: note that video can be enabled via config (`video: 'retain-on-failure'`)
   - These are optional enhancements — baseline file evidence is always captured without tools
7. **Determine app type** (or use `--app-type` override):
   - `terminal` — Jest, Vitest, Mocha, Pytest, Go test, Cargo test, etc. (default for most)
   - `browser` — Playwright or Cypress detected as test framework
   - `native` — WinAppDriver, XCUITest, Appium, Robot Framework detected, or `--app-type=native`
   - Present tool availability and app type in the detection summary
8. **Detect coverage tooling** — check for existing coverage infrastructure:
   - Pre-commit hooks: `.husky/pre-commit` containing coverage commands, `lint-staged` with coverage
   - CI pipelines: `.github/workflows/*.yml`, `.gitlab-ci.yml`, `Jenkinsfile` — look for coverage gates/thresholds
   - Runner config: Jest `coverageThreshold`, pytest `--cov-fail-under`, Go `-coverprofile` in scripts
   - Third-party: Codecov config (`codecov.yml`), Coveralls, SonarQube
   - If none detected, flag for recommendation in the report's "Next Steps"

**Output:** Detection summary — runner command, detected frameworks, app type, recording tools, coverage tooling status.

### Phase 3: Preflight Safety

Before running any tests, check for potential side effects.

1. Scan test configuration files for:
   - Database connection strings (check for prod-like URLs)
   - Environment variable requirements (`process.env`, `os.environ`, etc.)
   - API keys / secrets references
   - Network calls to external services
   - File system write operations outside temp dirs
2. Scan test files in scope for:
   - Direct HTTP calls to non-localhost URLs
   - Database mutation operations (INSERT, UPDATE, DELETE, DROP)
   - Payment/billing API references
   - Email/SMS sending functions
3. Classify risks:
   - **Safe**: Mocked/stubbed, localhost only, in-memory DB
   - **Warn**: External API calls, real DB mutations, file writes
   - **Block**: Production URLs, payment APIs, destructive operations

**If any Warn/Block risks found:**
- List each risk with file:line evidence
- Ask user for explicit confirmation to proceed
- Suggest mitigations (e.g., "set `DATABASE_URL` to test DB", "mock the payment client")

**If `--run=false`:** Skip this phase entirely.
**If `--dry-run`:** Show the safety report but do not prompt for confirmation.

### Phase 4: Test Execution

Run the existing test suite and capture results into the evidence package.

**If `--run=false`, skip to Phase 6.**
**If `--dry-run`, show the commands that would run and skip to Phase 6.**

1. **Create evidence directory structure:**
   ```
   <evidence-dir>/<YYYY-MM-DD-HHmm>/
     execution/
     failures/
     gaps/
     remediation/
     recordings/
   ```
2. Run the test command detected in Phase 2 (or `--test-cmd`)
3. **Always capture stdout+stderr** to `execution/test-output.txt` (use `2>&1 | tee`)
4. **Always generate `execution/test-summary.json`** by parsing the test output — see [references/evidence-tools.md](references/evidence-tools.md) for the format spec
5. Apply `--timeout` — if execution exceeds the limit, kill the process tree and report partial results
6. Parse from output:
   - Total tests, passed, failed, skipped, duration
   - Full failure output for each failing test
7. If tests fail to start (missing deps, config error), diagnose the setup issue and report it. Do not proceed to Phase 5 failure triage — instead report the setup issue and ask user how to proceed.
8. **Recording capture** (when `--evidence != off`). Strategy depends on app type detected in Phase 2. See [references/evidence-tools.md](references/evidence-tools.md) Tier 2 section for tool details.

   **Terminal tests:**
   - Generate a VHS tape file wrapping the test command
   - Run `vhs <tape-file>` instead of the raw command — outputs `.gif` to `recordings/`
   - If VHS unavailable: fall back to raw command (stdout/stderr still captured in `execution/`)

   **Browser UI tests:**
   - Playwright: temporarily set `video: 'retain-on-failure'` (or `video: 'on'` if `--evidence=all`)
   - Cypress: enable `video: true` in config
   - After test run: collect `.webm` files into `recordings/`
   - For failed tests with a known URL: `npx playwright screenshot <base-url><route> <output>.png --full-page`

   **Native desktop app tests:**
   - Before test: start ffmpeg screen recording as background process (platform-specific: `gdigrab`/`avfoundation`/`x11grab`)
   - Run the test command normally
   - After test: stop ffmpeg (SIGINT / `taskkill` on Windows), save to `recordings/`
   - If ffmpeg unavailable: fall back to platform-native screenshot

**Output:** Test execution summary table. Evidence artifacts listed if captured.

### Phase 5: Failure Triage

Classify every failure from Phase 4. For each failing test:

1. **Create evidence folder** `failures/NNN-<test-name>/` containing:
   - `error-output.txt` — full error message + stack trace extracted from test output
   - `source-context.txt` — source code around the failing line (+/- 10 lines)
   - `test-code.txt` — the complete failing test function/block
   - `rerun-output.txt` — output from rerunning the single test (flaky check)
   - `screenshot.png` — for browser tests, capture the page under test

2. **Classify the failure:**

| Category | Signal | Action |
|----------|--------|--------|
| **env/infra** | Missing deps, DB connection refused, file not found, permission denied, port in use | Report the infra issue. Do not rerun. |
| **flaky** | Passes on 2nd or 3rd rerun of the same test (use `--retry` flag if runner supports it, else rerun manually up to 2 times) | Mark as flaky. Report but deprioritize. |
| **real defect** | Fails consistently across reruns. Assertion mismatch indicates the code under test is wrong. | Report as product bug. Include expected vs actual. |
| **test bug** | Assertion logic is wrong, mock is stale/incorrect, test uses removed API, test has race condition | Report as test bug. If `--fix` enabled, queue for remediation. |

3. **For each failure, produce:**
   - Category label
   - Confidence (high/medium/low)
   - Evidence link: `[evidence](failures/NNN-<test-name>/)`
   - Suggested fix (one sentence)

**Output:** Failure triage table with evidence links.

### Phase 6: Gap Analysis

The core value of this skill. Identify untested or under-tested code.

**Method — Source-to-test mapping + pattern scanning:**

1. Build a source-file-to-test-file mapping:
   - Convention-based: `src/foo.ts` -> `test/foo.test.ts`, `src/foo.py` -> `tests/test_foo.py`
   - Config-based: check `testMatch`, `testPathPattern`, pytest `testpaths`
2. Find source files with NO corresponding test file
3. For each source file, scan for patterns per the active `--lens` perspectives

**Apply QA lenses** per [references/qa-perspectives.md](references/qa-perspectives.md):
- For each active lens (all 10 by default, or `--lens` subset):
  - Grep source files for the lens-specific patterns
  - For each match, check if there's a corresponding test covering that pattern
  - A pattern is "uncovered" if no test file explicitly references the function/class containing the pattern

**For each finding, generate a proof file** `gaps/gap-NNN-<lens>-<severity>.md` containing:
- Full source code snippet (the function/method, not just file:line)
- Explanation of why this is a gap
- The specific pattern matched
- Suggested test description

See [references/evidence-tools.md](references/evidence-tools.md) Tier 1 section for the gap proof template.

**For browser apps** (`--app-type=browser` or auto-detected): capture a screenshot of the related UI page/component and save as `gaps/gap-NNN-screenshot.png`.

**For each finding, also produce a summary row:**
- Lens category
- Severity: `critical` / `high` / `medium` / `low`
- Confidence: `high` / `medium` / `low`
- Source location: `file:line`
- Pattern matched (what was detected)
- Proof link: `[proof](gaps/gap-NNN-<lens>-<severity>.md)`
- Suggested test description (what a test should verify)

**Apply `--severity` filter** — drop findings below the minimum severity.
**Apply `--max-findings` cap** — keep highest severity findings first.
**Apply `--exclude` pattern** — skip matching files.

**Output:** Gap analysis findings list, grouped by lens, with proof links.

### Phase 7: Remediation & Report

#### 7a: Write Missing Tests (only if `--fix` is enabled)

For each gap finding queued for remediation:

1. **Determine the target test file:**
   - Use the source-to-test mapping from Phase 6
   - If no test file exists, create one following the project's test naming convention
2. **Write the test:**
   - Follow existing test patterns in the project (imports, describe/it structure, fixtures)
   - Use deterministic assertions only — no random data, no timing-dependent checks
   - Mock external dependencies (network, DB, file system) following existing mock patterns
   - Include a comment: `// QA-ENGINEER: covers <lens> gap in <source-file>:<line>`
3. **Run the impacted test file** to verify the new test passes
4. **Capture evidence** to `remediation/NNN-<test-file>/`:
   - `added-tests.diff` — diff of the test file changes
   - `test-output.txt` — output from running the new tests
5. **If the test fails:**
   - If it's a test bug (assertion wrong), fix it and rerun once
   - If it's a real defect (code is actually broken), keep the test but mark it with `// TODO: real defect — <description>`
   - If it's flaky after 2 reruns, delete it and report the issue
6. **Constraints:**
   - Only edit test files — NEVER edit source/production code
   - Only add new test cases — never modify or delete existing tests
   - Maximum 10 new test files per run (ask user to continue if more needed)

#### 7b: Generate Quality Report

Generate a markdown report following [references/report-template.md](references/report-template.md).

1. Save the report as `REPORT.md` inside the evidence package directory (`<evidence-dir>/<timestamp>/REPORT.md`)
2. The evidence directory was created in Phase 4 (or create it now if `--run=false`)
3. Add `qa-evidence/` to `.gitignore` if not already present (ask user first)

**Report contents:**
- Evidence Package manifest table (directory -> contents -> count)
- Executive summary with health verdict
- Test execution results from Phase 4 (linked to `execution/` files)
- Failure triage from Phase 5 (linked to `failures/NNN/` folders)
- Gap analysis findings from Phase 6, organized by lens and by severity (linked to `gaps/` proof files)
- Remediation summary from Phase 7a (linked to `remediation/NNN/` folders, if `--fix` was used)
- Coverage Tooling section — detected tools or recommendation to set up coverage gates
- Recommended next steps (include coverage tooling setup if none detected)

4. **Present the executive summary to the user in chat** — include:
   - Health verdict and key metrics
   - Evidence package path and file counts: "Evidence package: `./qa-evidence/<timestamp>/` — N failure folders, N gap proofs, N recordings"
   - Don't make them open the file for the headline result

#### 7c: Recording Conversion (only when recording artifacts exist in `recordings/`)

1. Present recording summary: list all captured artifacts with type, size, duration
2. Ask user: "Which recording artifacts should be converted to GIF for PR?"
3. For user-approved items:
   - `.webm` / `.mp4` -> GIF via ffmpeg palette method (see [references/evidence-tools.md](references/evidence-tools.md))
   - VHS `.gif` output — copy as-is (already GIF)
   - `.png` screenshots — keep as-is
4. Save GIFs to `recordings/gif/`
5. Output: "Ready for PR: N GIFs saved to `recordings/gif/`"

## Monorepo Behavior

When a monorepo is detected:

1. Ask user which packages to target (or accept `--scope=packages/foo`)
2. Run Phases 2-7 independently per package
3. Generate one evidence package per package, plus a combined executive summary
4. Cross-package integration gaps are noted but not deeply analyzed (suggest using `--lens=network` for API boundaries)

## Error Handling

| Situation | Behavior |
|-----------|----------|
| No test files found | Skip Phase 4-5. Run Phase 6 gap analysis. Report "no test suite detected". |
| Test runner not detected | Ask user for `--test-cmd`. If still unknown, skip Phase 4-5. |
| Tests time out | Kill after `--timeout` seconds. Report partial results. Suggest increasing timeout or scoping. |
| Permission denied on test dir | Report the issue. Ask user to fix permissions. |
| Git not available | `--scope=changed` falls back to `--scope=all` with a warning. |
| Evidence dir not writable | Fall back to report-only mode — generate REPORT.md in the current directory without evidence subdirectories. Warn user. |

## Integration with Other Skills

| Skill | When to use instead / together |
|-------|-------------------------------|
| `tdd-team-workflow` | Use TDD to **build** new features with tests. Use `qa-engineer` to **audit** existing code. |
| `e2e-test` | Use for interactive Playwright browser testing. `qa-engineer` evaluates E2E test coverage but uses the project's own test runner. |
| `review-pr` | Use for line-by-line PR review. `qa-engineer` focuses on test quality across the codebase, not PR diff review. |
| `playwright-cli` / `playwright-codegen` | Use to create/run Playwright tests. `qa-engineer` may detect E2E gaps and recommend using these skills. |

## Example Invocations

### Full QA audit
```
Run a full QA analysis on this project
```

### Security-focused audit, no test execution
```
Analyze test gaps --run=false --lens=security
```

### Fix failing tests and fill gaps
```
QA this codebase --fix
```

### Audit only changed files
```
Run QA on changed files --scope=changed --lens=functional,security
```

### Dry run to preview
```
QA audit --dry-run
```

### Custom test command with timeout
```
Run tests and analyze gaps --test-cmd="npm run test:unit" --timeout=120
```

### QA with recording evidence for all tests
```
QA this project --evidence=all
```

### Native desktop app testing
```
Run QA --app-type=native --evidence=on-failure
```

### Browse evidence after a run
```
# Evidence package structure:
./qa-evidence/2026-03-07-1430/
  REPORT.md                          # Start here — index into all evidence
  execution/test-output.txt          # Full test output
  execution/test-summary.json        # Parsed results
  failures/001-auth-login/           # Failure evidence folder
    error-output.txt
    source-context.txt
    test-code.txt
    rerun-output.txt
  gaps/gap-001-security-critical.md  # Gap proof with source snippet
  gaps/gap-001-screenshot.png        # UI screenshot (browser apps)
  remediation/001-auth-test/         # Added test diff + output
    added-tests.diff
    test-output.txt
```
