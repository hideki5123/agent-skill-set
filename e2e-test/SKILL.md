---
name: e2e-test
description: Run frontend E2E tests using Playwright MCP browser tools. Takes screenshots at each step as verification evidence and generates a test report. If the test scenario has gaps, recommends updates before proceeding. Does NOT modify application code — only updates documents (markdown, CSV). Use when the user asks to run E2E tests, verify frontend behavior, do end-to-end testing, check UI flows, or test a web app. Trigger phrases include "e2e", "E2E test", "end-to-end test", "e2e testing", "frontend test", "UI test", "playwright test", "browser test", "verify the UI", "test this page".
---

# E2E Test

Run frontend E2E tests interactively using Playwright browser automation. Capture screenshots at every step as verification evidence. Generate a structured test report. Never modify application code.

## Constraints

- **NO code changes**: Do not modify source code files (.ts, .js, .jsx, .tsx, .py, .html, .css, etc.)
- **Documents OK**: May create or update markdown (.md), CSV (.csv), JSON test reports, and screenshot files
- **Evidence-driven**: Take a screenshot after every meaningful action
- **Ask before gaps**: If the scenario is insufficient for proper verification, stop and recommend additions before continuing

## Workflow

1. **Understand the scenario** — Get the test target and acceptance criteria
2. **Evaluate scenario coverage** — Check if the scenario is sufficient; if not, ask user to update
3. **Set up browser session** — Launch Playwright browser
4. **Execute test steps** — Navigate, interact, snapshot, and screenshot at each step
5. **Generate report** — Produce a markdown evidence report with all screenshots

## Step 1: Understand the Scenario

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

## Step 3: Set Up Browser Session

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

## Step 4: Execute Test Steps

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

## Step 5: Generate Report

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
**Preconditions**: <setup actions taken>
**Result**: PASS | FAIL | PARTIAL

## Summary

- Total steps: <N>
- Passed: <N>
- Failed: <N>
- Skipped: <N>
- Retried: <N>

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
1. Close the browser with `mcp__playwright__browser_close`
2. Tell the user where the evidence is saved
3. If there were failures, offer to help diagnose the root cause (by examining the app, NOT by modifying code)

## Re-running a Test Scenario

1. Open the scenario file (e.g., `test-scenarios/todomvc-sample.csv`)
2. Invoke: "Run e2e test with scenario test-scenarios/todomvc-sample.csv"
3. A new timestamped evidence directory is created each run
4. Compare reports across runs with diff to detect regressions
