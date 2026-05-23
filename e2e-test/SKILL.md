---
name: e2e-test
description: Run frontend E2E tests with video evidence. Generates a Playwright test from the scenario CSV and runs it via CLI with video recording. Supports Chrome profile reuse (--chrome-profile) for testing with existing cookies, sessions, and extensions via launchPersistentContext. Generates a test report with video, screenshots, and trace. Does NOT modify application code — only creates documents (markdown, CSV, test scripts). Supports --non-interactive for fork / CI use (fails fast on scenario gaps instead of asking). Use when the user asks to run E2E tests, verify frontend behavior, do end-to-end testing, check UI flows, or test a web app. Trigger phrases include "e2e", "E2E test", "end-to-end test", "e2e testing", "frontend test", "UI test", "playwright test", "browser test", "verify the UI", "test this page".
version: 1.2.0
context: fork
agent: general-purpose
---

# E2E Test

Run frontend E2E tests with video and screenshot evidence. Generates a Playwright test script from the scenario CSV and runs it via `npx playwright test` with video recording enabled. Supports Chrome profile reuse for testing authenticated flows. Generate a structured test report. Never modify application code.

## Constraints

- **NO code changes**: Do not modify source code files (.ts, .js, .jsx, .tsx, .py, .html, .css, etc.)
- **Documents OK**: May create or update markdown (.md), CSV (.csv), JSON test reports, screenshot files, and generated test scripts
- **Evidence-driven**: Capture video recording and screenshots of every meaningful action
- **Ask before gaps**: If the scenario is insufficient for proper verification, stop and recommend additions before continuing

## Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--chrome-profile` | `off` | `off`: normal isolated Chromium context; `on`: use system Chrome with `Default` profile; `<name>`: use named profile (e.g., `Profile 1`). Chrome must be closed before running. |
| `--non-interactive` | `false` | Fail fast on any condition that would otherwise prompt the user (scenario gaps, unknown actions, ambiguous expected results, missing target URL). For use when invoked from a fork / CI / another skill where user prompts cannot be answered. With `context: fork` in this file, the skill runs in a forked subagent context by default; treat that as implicit `--non-interactive` regardless of the flag. |

## Workflow

1. **Understand the scenario** — Get the test target and acceptance criteria
2. **Evaluate scenario coverage** — Check if the scenario is sufficient; if not, ask user to update
3. **Generate and run Playwright test** — Generate test script from CSV, run via CLI with video
4. **Generate report** — Produce a markdown evidence report with video, screenshots, and trace

## Step 1: Understand the Scenario

### Feedback Check

If `feedback/log.md` exists and has 5 or more entries, read the last 10 entries.
If a pattern is apparent (same issue in 3+ entries, or average rating below 3):
- Tell the user: "Recurring feedback detected: [brief pattern]. Consider running `/skill-improve --skill e2e-test`."
- Continue with normal execution.

Determine from the user:
- **Target URL**: The page or app to test (e.g., `http://localhost:3000`)
- **Test scenario**: What user flow to verify (e.g., "login with valid credentials and see dashboard")
- **Expected outcomes**: What constitutes pass/fail for each step

If the user provides a test scenario document (markdown, CSV), read it. If not, ask them to describe the flow.

### Scenario Format

If creating or updating a scenario document, use this CSV structure. Targets are **human-readable descriptions** matched against the accessibility tree (NOT CSS selectors):

```csv
# config
url,https://example.com
viewport,1280x720
setup,Clear localStorage
timeout,10

# steps
step,action,target,input,expected_result
1,navigate,https://example.com,,Page loads with login form visible
2,type,Email input field,user@example.com,Email field populated
3,type,Password input field,secret123,Password field populated (masked); submit:true
4,click,Submit button,,Form submits
5,verify,Dashboard heading,,Dashboard heading visible with welcome text
```

#### Config header

- `url` — The target URL for the test
- `viewport` — Browser viewport dimensions (default: `1280x720`)
- `setup` — Precondition action (e.g., `Clear localStorage` → `await page.evaluate(() => localStorage.clear())`)
- `timeout` — Default seconds per wait step (default: `10`)
- `chrome_profile` — Chrome profile directory name (e.g., `Default`, `Profile 1`). When set, uses `launchPersistentContext` with system Chrome. Overrides `--chrome-profile` argument
- `chrome_profile_path` — Full path to Chrome User Data directory. Optional; auto-detected per platform if omitted

#### Target field

Targets describe elements as a human would:
- `Email input field` — matches an input with label/placeholder "Email"
- `Submit button` — matches a button with text "Submit"
- `Toggle checkbox for Buy groceries` — matches a checkbox near the text "Buy groceries"
- For `navigate` action, the target is the URL
- For `verify` action, the target describes what to check in the accessibility tree

## Step 2: Evaluate Scenario Coverage

Before executing, review the scenario for completeness:

### Check for gaps

- Are all critical user interactions covered?
- Are there expected error states that should be tested? (e.g., invalid input, empty fields)
- Are success/failure outcomes clearly defined for each step?
- Is the starting state specified? (e.g., "logged out", "empty database")
- Are wait conditions clear for async operations?
- Are there any **unmapped actions** (actions not in the action-to-tool mapping)? Flag these immediately

### If gaps found

Stop and tell the user what's missing. Provide specific recommendations:

```
The scenario has gaps that may prevent proper verification:

1. **Unknown action**: Step 12 uses "wiggle" which is not a supported action
2. **Missing error case**: No test for invalid login credentials
3. **Ambiguous expected result**: Step 5 says "dashboard visible" but doesn't specify what content to verify

Recommended additions:
- Remove or replace step 12's unknown action
- Add step: type Email input with "bad@email.com", type Password with "wrong", click Submit → expect error message
- Update step 5: verify specific text like "Welcome, User" or a data element

Please update the scenario and I'll proceed with testing.
```

Do NOT proceed with execution until the scenario is adequate or the user explicitly says to continue anyway.

### Non-interactive / fork behavior

When invoked under `context: fork` (the default in this skill's frontmatter)
or with explicit `--non-interactive`, do not prompt. Instead:

- If any gap above is detected, **fail fast** with a structured error
  summarising the gaps (unknown actions, ambiguous expected results,
  missing target URL, etc.). Return exit code / status `scenario-incomplete`.
- Do not generate a Playwright script, do not run any tests, and do not
  produce a report.
- The orchestrator that invoked you (or the user, on the next inline run)
  fixes the scenario and re-invokes.

This matches the official guidance for background subagents: any tool
call that would prompt is auto-denied, so a fork-invoked skill must
fail-fast rather than appear to hang.

## Step 3: Generate and Run Playwright Test

Generate a Playwright test script from the CSV scenario and run it via CLI with video recording. Read `references/video-recording.md` for the full reference.

### 3.0 Chrome profile mode detection

Determine if Chrome profile mode is active:
1. Check `--chrome-profile` argument (CLI)
2. Check `chrome_profile` field in CSV config (overrides CLI)
3. If either is set (and not `off`), activate Chrome profile mode

If Chrome profile mode is active:
- Profile directory = the value (`Default` if `on` was specified without a name)
- User data path = `chrome_profile_path` from CSV, or auto-detect per platform:
  - Windows: `%LOCALAPPDATA%\Google\Chrome\User Data`
  - macOS: `~/Library/Application Support/Google/Chrome`
  - Linux: `~/.config/google-chrome`

> **Privacy warning**: Chrome profile mode exposes real accounts, personal data, and extensions in test evidence (video, screenshots, trace). Extensions and service workers from the profile may affect test determinism.

### 3.1 Create evidence directory

```bash
mkdir -p ./e2e-evidence/<test-name>-<YYYY-MM-DD-HHMM>
```

### 3.2 Generate playwright.config.js

Create `playwright.config.js` in the evidence directory using the template from `references/video-recording.md`:

**Normal mode:**
- Set `baseURL` to the target URL from the scenario config
- Set `viewport` from scenario config (default `{ width: 1280, height: 720 }`)
- Set `video: 'on'`, `screenshot: 'on'`, `trace: 'on'`
- Set `outputDir` and reporter paths within the evidence directory

**Chrome profile mode:**
- Use the Chrome Profile Config Template from `references/video-recording.md`
- Set `workers: 1` (shared profile cannot parallelize)
- Set `retries: 0` (shared state makes retries unreliable)
- Do NOT set `use.video`, `use.trace`, `use.screenshot` (handled by `chrome-fixture.js`)
- Do NOT set `projects` (fixture handles browser selection)

### 3.2b Generate chrome-fixture.js (Chrome profile mode only)

When Chrome profile mode is active, generate `chrome-fixture.js` in the evidence directory using the Chrome Fixture Template from `references/video-recording.md`:
- Replace `<chrome-user-data-dir>` with the resolved user data path
- Replace `<profile-directory>` with the profile directory name
- Replace `<width>`, `<height>` from scenario config viewport

### 3.3 Generate test spec

Create `<test-name>.spec.js` in the evidence directory:

1. **Normal mode**: `const { test, expect } = require('@playwright/test');`
   **Chrome profile mode**: `const { test, expect } = require('./chrome-fixture');`
2. Wrap all steps in a single `test('<test-name>', async ({ page }) => { ... })` block
3. Add setup preconditions (e.g., `localStorage.clear()`) after the first `page.goto()`
4. For each CSV step, generate the corresponding Playwright API call:
   - Use Playwright locators (`getByRole`, `getByLabel`, `getByText`, `getByPlaceholder`) to resolve human-readable targets — see `references/video-recording.md` for the mapping
   - Add `await page.screenshot({ path: 'step-<NN>-<action>.png' })` after each action
   - Add `await expect(...)` assertions for each `expected_result`
5. Handle `dialog` actions by registering `page.on('dialog', ...)` before the triggering action

### 3.4 Run the test

```bash
cd <evidence-dir>
npx playwright test <test-name>.spec.js --config=playwright.config.js --headed
```

If `npx playwright` is not available, warn the user. Suggest: `npm install -D @playwright/test && npx playwright install chromium`.

If the test run fails, Playwright still captures video and screenshots up to the failure point.

### 3.5 Collect artifacts

After the test run:

**Normal mode:**
1. Find `video.webm` in `test-results/<test-title>/` and copy to evidence root as `recording.webm`
2. Find `trace.zip` in `test-results/<test-title>/` and copy to evidence root

**Chrome profile mode:**
1. Find the video file (`.webm`) in `test-results/videos/` and copy to evidence root as `recording.webm`
2. Find `trace.zip` in `test-results/` (saved by fixture) and copy to evidence root

**Both modes:**
3. Step screenshots (`step-*.png`) are already in the evidence root
4. HTML report is in `html-report/`

Proceed to Step 4 (Generate Report).

## Step 4: Generate Report

After all steps complete, generate a markdown evidence report.

Save to: `./e2e-evidence/<test-name>-<YYYY-MM-DD-HHMM>/REPORT.md`

### Report Template

```markdown
# E2E Test Report: <Test Name>

**Date**: <YYYY-MM-DD HH:MM>
**Duration**: <total time>
**Target**: <URL>
**Browser**: Chromium (Playwright) | Chrome (profile: <name>)
**Viewport**: <width>x<height>
**OS**: <platform>
**Scenario file**: `<path>` (modified: <date>)
**Recording mode**: video
**Preconditions**: <setup actions taken>
**Result**: PASS | FAIL | PARTIAL

## Summary

- Total steps: <N>
- Passed: <N>
- Failed: <N>
- Skipped: <N>
- Retried: <N>

## Video Evidence

- **Video**: [recording.webm](recording.webm)
- **Trace**: [trace.zip](trace.zip) — open with `npx playwright show-trace trace.zip`
- **HTML Report**: [Full Report](html-report/index.html) — open with `npx playwright show-report html-report`

*(If video was requested but recording failed, note: "Video recording was requested but Playwright tracing failed. Screenshots are available as step evidence below.")*

## Test Steps

### Step 1: <Action Description>
- **Action**: <what was done>
- **Target**: <human-readable description>
- **Expected**: <expected result>
- **Actual**: <actual result>
- **Status**: PASS | FAIL | PASS (retried) | SKIPPED
- **Screenshot**: ![Step 1](step-01-<action>.png)
- **Console**: <console output if non-empty>

---

(repeat for each step)

## Failed Steps Detail

### Step <N>: <Action Description>
- **Error**: <what went wrong>
- **Page URL**: <URL at time of failure>
- **Console Errors**: <any relevant console output>
- **Screenshot**: ![Failure](step-<NN>-<action>-FAIL.png)
- **Accessibility snapshot**: [step-<NN>-a11y.md](step-<NN>-a11y.md)

## Recommendations

<If any failures occurred, provide actionable recommendations.>
<If scenario gaps were identified during testing, note them here.>
```

## Cleanup

After generating the report:

1. Tell the user where the evidence is saved, including:
   - Video: `recording.webm`
   - Trace: `npx playwright show-trace <evidence-dir>/trace.zip`
   - HTML report: `npx playwright show-report <evidence-dir>/html-report`
2. If there were failures, offer to help diagnose the root cause (by examining the app, NOT by modifying code)

### Retrospective

After completing the workflow, reflect on the entire execution session:

1. Consider: Were there mid-session corrections? Rejected outputs? Plan changes? Errors?
2. Ask the user: "Quick feedback on this run? (1-5 rating, note any issues, or press enter to skip)"
3. If the user provides feedback OR if corrections/issues occurred during this session:
   a. Create `feedback/` directory if it does not exist
   b. Read `feedback/log.md` (create with `# Feedback Log` header if it does not exist)
   c. Prepend a new entry after the header using the log format from `my-skill-factory/references/skill-improvement-guide.md`
   d. Fill in: current timestamp, skill version from frontmatter, task description, outcome assessment,
      corrections that occurred during the session, issues encountered, user's note
4. If the user skips AND no corrections or issues occurred, end without recording.

## Re-running a Test Scenario

1. Open the scenario file (e.g., `test-scenarios/todomvc-sample.csv`)
2. Invoke: "Run e2e test with scenario test-scenarios/todomvc-sample.csv"
3. A new timestamped evidence directory is created each run
4. Compare reports across runs with diff to detect regressions

## Behavior Scenarios

```gherkin
Scenario: Default execution with video evidence
  Given a test scenario CSV
  When /e2e-test is invoked
  Then generate playwright.config.js with video: 'on',
       generate test spec from CSV scenario mapping actions to Playwright API,
       run via npx playwright test --headed,
       collect recording.webm, step screenshots, and trace.zip,
       generate REPORT.md with Video Evidence section

Scenario: Chrome profile mode with persistent context
  Given --chrome-profile is set (or chrome_profile in CSV) and Chrome is not running
  When /e2e-test is invoked
  Then generate chrome-fixture.js with launchPersistentContext using the specified profile,
       generate playwright.config.js with workers: 1, retries: 0, no video/trace config,
       generate test spec importing from ./chrome-fixture instead of @playwright/test,
       run via npx playwright test --headed,
       collect video from test-results/videos/ and trace from test-results/trace.zip,
       generate REPORT.md with Chrome profile noted in Browser field

Scenario: Chrome profile is locked by running Chrome instance
  Given --chrome-profile is active and Chrome is open with the same profile
  When /e2e-test launches the persistent context
  Then the fixture catches the profile lock error,
       displays a clear message: "Chrome profile is locked. Close all Chrome windows and retry.",
       the test fails with an actionable error (not a cryptic Playwright internal error)

Scenario: Generated test encounters a failure
  Given a step assertion fails during the Playwright test run
  When the test finishes (Playwright still captures video up to failure)
  Then collect partial video and failure screenshots,
       report shows which step failed with evidence,
       offer to diagnose the root cause

Scenario: Playwright CLI not available
  Given npx playwright is not installed
  When /e2e-test is invoked
  Then warn user that Playwright CLI is required,
       suggest running npm install -D @playwright/test && npx playwright install chromium

Scenario: Scenario has gaps before execution
  Given a test scenario with missing steps or ambiguous expected results
  When /e2e-test evaluates the scenario (Step 2)
  Then stop and recommend specific additions,
       do not proceed until user updates the scenario or says to continue

Scenario: Re-running a previous test scenario
  Given a previously used scenario CSV file
  When /e2e-test is invoked with the same scenario
  Then create a new timestamped evidence directory,
       run the test fresh, generate new report,
       user can diff reports across runs to detect regressions
```
