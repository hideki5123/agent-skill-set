---
name: e2e-test
description: Run frontend E2E tests with video evidence. Default mode (--video=on) generates a Playwright test from the scenario CSV and runs it via CLI with video recording. Fallback mode (--video=off) uses Playwright MCP tools interactively with step screenshots. Generates a test report with video, screenshots, and trace. Does NOT modify application code — only creates documents (markdown, CSV, test scripts). Use when the user asks to run E2E tests, verify frontend behavior, do end-to-end testing, check UI flows, or test a web app. Trigger phrases include "e2e", "E2E test", "end-to-end test", "e2e testing", "frontend test", "UI test", "playwright test", "browser test", "verify the UI", "test this page".
version: 1.0.0
---

# E2E Test

Run frontend E2E tests with video and screenshot evidence. Default mode generates a Playwright test script from the scenario CSV and runs it via `npx playwright test` with video recording enabled. Fallback mode uses Playwright MCP tools interactively. Generate a structured test report. Never modify application code.

## Constraints

- **NO code changes**: Do not modify source code files (.ts, .js, .jsx, .tsx, .py, .html, .css, etc.)
- **Documents OK**: May create or update markdown (.md), CSV (.csv), JSON test reports, screenshot files, and generated test scripts
- **Evidence-driven**: Capture video recording and screenshots of every meaningful action
- **Ask before gaps**: If the scenario is insufficient for proper verification, stop and recommend additions before continuing

## Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--video` | `on` | `on`: generate Playwright test script and run via CLI with video recording; `off`: use Playwright MCP tools interactively with screenshots only |

## Workflow

1. **Understand the scenario** — Get the test target and acceptance criteria
2. **Evaluate scenario coverage** — Check if the scenario is sufficient; if not, ask user to update
3. **Generate and run Playwright test** (`--video=on`, default) — Generate test script from CSV, run via CLI with video
4. **Set up browser session** (`--video=off`) — Launch Playwright MCP browser
5. **Execute test steps** (`--video=off`) — Navigate, interact, snapshot, and screenshot at each step
6. **Generate report** — Produce a markdown evidence report with video, screenshots, and trace

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
- `setup` — Precondition action. Maps to `browser_run_code` (e.g., `Clear localStorage` → `async (page) => { await page.evaluate(() => localStorage.clear()); }`)
- `timeout` — Default seconds per wait step (default: `10`)

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

## Step 3: Generate and Run Playwright Test (--video=on)

When `--video=on` (default), generate a Playwright test script from the CSV scenario and run it via CLI with video recording. Read `references/video-recording.md` for the full reference.

### 3.1 Create evidence directory

```bash
mkdir -p ./e2e-evidence/<test-name>-<YYYY-MM-DD-HHMM>
```

### 3.2 Generate playwright.config.js

Create `playwright.config.js` in the evidence directory using the template from `references/video-recording.md`:
- Set `baseURL` to the target URL from the scenario config
- Set `viewport` from scenario config (default `{ width: 1280, height: 720 }`)
- Set `video: 'on'`, `screenshot: 'on'`, `trace: 'on'`
- Set `outputDir` and reporter paths within the evidence directory

### 3.3 Generate test spec

Create `<test-name>.spec.js` in the evidence directory:

1. Import `{ test, expect }` from `@playwright/test`
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

If `npx playwright` is not available, warn the user and offer to fall back to `--video=off` (MCP mode).

If the test run fails, Playwright still captures video and screenshots up to the failure point.

### 3.5 Collect artifacts

After the test run:
1. Find `video.webm` in `test-results/<test-title>/` and copy to evidence root as `recording.webm`
2. Find `trace.zip` in `test-results/<test-title>/` and copy to evidence root
3. Step screenshots (`step-*.png`) are already in the evidence root
4. HTML report is in `html-report/`

Proceed to Step 6 (Generate Report).

---

## Step 4: Set Up Browser Session (--video=off)

**This step is only used when `--video=off`.** When `--video=on`, skip to Step 3 above.

Use the Playwright MCP tools to launch a browser. Read `references/playwright-commands.md` for the full tool reference.

```
1. Install browser if needed: mcp__playwright__browser_install
2. Use mcp__playwright__browser_navigate to open the target URL
3. Execute any setup preconditions (e.g., clear localStorage via browser_run_code)
4. Take an initial screenshot with mcp__playwright__browser_take_screenshot (type: "png")
5. Take an initial browser_snapshot to get the accessibility tree
```

Create a directory for evidence artifacts:
```bash
mkdir -p ./e2e-evidence/<test-name>-<YYYY-MM-DD-HHMM>
```

Save all screenshots and accessibility snapshots to this directory.

## Step 5: Execute Test Steps (--video=off)

**This step is only used when `--video=off`.** When `--video=on`, test execution is handled in Step 3.

For each step in the scenario:

1. **Take a snapshot** — Call `mcp__playwright__browser_snapshot` before every interaction to get the current accessibility tree
2. **Find the target** — Parse the accessibility tree to find the element matching the human-readable `target` description. Extract its `ref` identifier
3. **Perform the action** — Use the appropriate Playwright MCP tool, passing the `ref`
4. **Take a screenshot** — Save with descriptive filename: `step-<NN>-<action>.png`
5. **Capture console messages** — Call `mcp__playwright__browser_console_messages` (include in report only when non-empty)
6. **Verify the expected result** — Use `mcp__playwright__browser_snapshot` to read page state
7. **Record pass/fail** — Note the actual result

### Snapshot rules

- **Snapshot before every interaction**: Always call `browser_snapshot` before any action that needs a `ref`. This is the ONLY way to get valid element references
- **Snapshot caching**: Reuse the most recent snapshot if no navigation or DOM-altering action has occurred since the last snapshot (saves tokens on complex pages)
- **Ambiguity resolution**: If multiple elements match the target description, prefer the first visible/in-viewport match. If still ambiguous, present candidates to the user and let them pick
- **No match fallback**: If the target is not found in the accessibility tree, report it as a test infrastructure issue (not a test failure). Suggest the app needs better a11y markup, or offer `browser_run_code` as an escape hatch
- **Stale ref recovery**: If an action fails with a stale ref, take a fresh snapshot, re-locate the element, and retry once

### Retry-on-flaky

Before recording a step as FAIL:
1. Wait 2 seconds (`browser_wait_for` with `time: 2`)
2. Retry the step once
3. If the retry passes, mark as `PASS (retried)`
4. If the retry also fails, record as FAIL with evidence

### Critical steps

If a step is marked as critical and fails, skip subsequent dependent steps and note them as SKIPPED in the report.

### Action-to-Tool Mapping

| Action | Playwright MCP Tool | Notes |
|--------|---------------------|-------|
| `navigate` | `browser_navigate` | Follow with `browser_wait_for` (text) to confirm load |
| `fill` / `type` | `browser_type` | Needs `ref` + `text`. Use `submit: true` for type-then-Enter. `slowly: true` for apps with key handlers |
| `fill_form` | `browser_fill_form` | For multi-field batch fills, checkboxes, radios, comboboxes, sliders (the ONLY tool for non-text fields) |
| `click` | `browser_click` | Needs `ref` |
| `dblclick` | `browser_click` | With `doubleClick: true` (e.g., edit-in-place) |
| `hover` | `browser_hover` | Needs `ref` |
| `keypress` | `browser_press_key` | Global key press (no ref). For standalone keys only (Escape, Tab, arrows). NOT for type-then-Enter |
| `select` | `browser_select_option` | Needs `ref` |
| `upload` | `browser_file_upload` | Needs `paths[]` |
| `wait` | `browser_wait_for` | **Only** supports `text`, `textGone`, `time` (seconds). NOT selectors or URL. For complex waits use `run_code` |
| `verify` | `browser_snapshot` | Read accessibility tree to check page state |
| `screenshot` | `browser_take_screenshot` | **`type` is required** ("png" or "jpeg"). Use `filename` for evidence naming. `fullPage: true` for full page |
| `dialog` | `browser_handle_dialog` | `accept: boolean`, optional `promptText` |
| `url_check` | `browser_evaluate` | `window.location.href` to verify navigation |
| `run_code` | `browser_run_code` | Escape hatch: `async (page) => { ... }`. For localStorage setup, complex waits, iframe interactions, computed style checks |
| `evaluate` | `browser_evaluate` | Run JS in browser context (DOM reads, data checks). Different from `run_code` (which is Node.js/Playwright API) |
| `console` | `browser_console_messages` | Read console log/error |
| `tab` | `browser_tabs` | List, new, close, select tabs |

### Screenshot naming convention

```
step-01-navigate-homepage.png
step-02-type-email.png
step-03-type-password.png
step-04-click-submit.png
step-05-verify-dashboard.png
step-04-click-submit-FAIL.png    (failure screenshot)
```

### On failure

If a step fails (expected result doesn't match actual):
1. Take a screenshot named `step-<NN>-<action>-FAIL.png`
2. Capture the current page URL with `browser_evaluate` (`window.location.href`)
3. Capture console messages with `browser_console_messages`
4. Save the accessibility snapshot as `step-<NN>-a11y.md`
5. Log the discrepancy in the report
6. Ask the user whether to continue with remaining steps or stop

## Step 6: Generate Report

After all steps complete, generate a markdown evidence report.

Save to: `./e2e-evidence/<test-name>-<YYYY-MM-DD-HHMM>/REPORT.md`

### Report Template

```markdown
# E2E Test Report: <Test Name>

**Date**: <YYYY-MM-DD HH:MM>
**Duration**: <total time>
**Target**: <URL>
**Browser**: Chromium (Playwright)
**Viewport**: <width>x<height>
**OS**: <platform>
**Scenario file**: `<path>` (modified: <date>)
**Recording mode**: video | screenshots-only
**Preconditions**: <setup actions taken>
**Result**: PASS | FAIL | PARTIAL

## Summary

- Total steps: <N>
- Passed: <N>
- Failed: <N>
- Skipped: <N>
- Retried: <N>

## Video Evidence

*(Include this section when --video=on)*

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

**When --video=on:**
1. Tell the user where the evidence is saved, including:
   - Video: `recording.webm`
   - Trace: `npx playwright show-trace <evidence-dir>/trace.zip`
   - HTML report: `npx playwright show-report <evidence-dir>/html-report`
2. If there were failures, offer to help diagnose the root cause (by examining the app, NOT by modifying code)

**When --video=off:**
1. Close the browser with `mcp__playwright__browser_close`
2. Tell the user where the evidence is saved
3. If there were failures, offer to help diagnose the root cause (by examining the app, NOT by modifying code)

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
  Given a test scenario CSV and --video=on (default)
  When /e2e-test is invoked
  Then generate playwright.config.js with video: 'on',
       generate test spec from CSV scenario mapping actions to Playwright API,
       run via npx playwright test --headed,
       collect recording.webm, step screenshots, and trace.zip,
       generate REPORT.md with Video Evidence section

Scenario: Execution without video (MCP mode)
  Given --video=off is specified
  When /e2e-test is invoked
  Then use Playwright MCP tools for interactive step-by-step testing,
       capture screenshots at each step,
       generate REPORT.md without Video Evidence section

Scenario: Generated test encounters a failure
  Given --video=on and a step assertion fails during the Playwright test run
  When the test finishes (Playwright still captures video up to failure)
  Then collect partial video and failure screenshots,
       report shows which step failed with evidence,
       offer to diagnose the root cause

Scenario: Playwright CLI not available
  Given --video=on but npx playwright is not installed
  When /e2e-test is invoked
  Then warn user that Playwright CLI is required for video mode,
       suggest running npm install -D @playwright/test && npx playwright install chromium,
       offer to fall back to --video=off (MCP mode)

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
