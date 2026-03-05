---
name: playwright-codegen
description: >
  Guided workflow for recording browser interactions with Playwright codegen and transforming
  the raw output into production-quality test suites. Handles the full lifecycle: planning the
  recording session, launching codegen, reviewing captured actions, enhancing with assertions
  and page objects, organizing test files, scaffolding config, and running until green.
  Use when the user wants to create new Playwright tests from browser recordings, turn codegen
  output into structured specs, or bootstrap a test suite for a web application.
  Trigger phrases include "record test", "codegen to test", "generate playwright test",
  "create test from recording", "record and generate test", "playwright codegen workflow",
  "turn recording into test", "bootstrap test suite", "record browser test",
  "generate spec from codegen", "create e2e test from recording".
---

# Playwright Codegen Skill

Guided workflow for recording browser interactions with `npx playwright codegen` and
transforming the raw output into production-quality `.spec.ts` test suites with assertions,
resilient selectors, and optional page objects.

## Why This Skill Exists

Raw codegen output has no assertions, flat action sequences, and fragile selectors.
This skill bridges the gap between a quick recording and a maintainable test suite.

---

## Step 1: Prerequisites

Before starting, verify the environment is ready.

```bash
npx playwright --version
```

If this fails, guide the user:

| Error | Fix |
|-------|-----|
| `npx: command not found` | Install Node.js / npm |
| `Cannot find module '@playwright/test'` | `npm install -D @playwright/test` |
| `Executable doesn't exist` | `npx playwright install` or `npx playwright install chromium` |

Check for an existing config:

```bash
ls playwright.config.ts playwright.config.js 2>/dev/null
```

If no config exists, note it — Step 7 will offer to scaffold one.

---

## Step 2: Plan the Recording

Before launching codegen, gather the following from the user:

1. **Target URL** — The starting page for the recording.
2. **Test scope** — What user flow to record (e.g., "login and add item to cart").
3. **Authentication** — Does the flow require login? If so, plan a two-pass approach:
   - Pass 1: Record login and save storage state.
   - Pass 2: Load storage state and record the actual flow.
4. **Device emulation** — Mobile viewport? Specific device? Default is desktop.
5. **Output language** — Default to `playwright-test` (TypeScript). Can also use `javascript`.

Build the codegen command based on answers:

```bash
# Basic
npx playwright codegen --target=playwright-test -o tests/generated.spec.ts <url>

# With device emulation
npx playwright codegen --target=playwright-test --device="iPhone 13" -o tests/generated.spec.ts <url>

# With custom viewport
npx playwright codegen --target=playwright-test --viewport-size="1280,720" -o tests/generated.spec.ts <url>
```

---

## Step 3: Launch Codegen & Record

### Standard recording

Run the codegen command built in Step 2. The user interacts with the browser while
Playwright records actions.

```bash
npx playwright codegen --target=playwright-test -o <output-file> <url>
```

### Authenticated flows (two-pass)

**Pass 1 — Save auth state:**

```bash
npx playwright codegen --save-storage=auth.json <login-url>
```

Instruct the user to log in, then close the browser. The auth state is saved to `auth.json`.

**Pass 2 — Record with auth:**

```bash
npx playwright codegen --target=playwright-test --load-storage=auth.json -o <output-file> <url>
```

### Headless / remote environments

If the user is in a headless environment (SSH, CI, WSL without display):

- Codegen requires a display. Suggest using a local machine or X11 forwarding.
- As a fallback, the user can write the test manually using patterns from
  `references/test-patterns.md` and selector guidance from `references/selector-strategy.md`.

---

## Step 4: Capture & Review

After the user closes the codegen browser, read the generated file:

```bash
cat <output-file>
```

Review the raw output and identify issues:

1. **Brittle selectors** — Look for `nth-child`, CSS class selectors, XPath, or auto-generated
   `data-testid` values that may change. Flag these for replacement.
2. **Redundant actions** — Duplicate clicks, unnecessary navigations, accidental interactions.
3. **Missing waits** — Codegen may not capture necessary wait conditions.
4. **No assertions** — Raw codegen never includes assertions. This is the biggest gap.
5. **Flat structure** — All actions in a single block, no `describe`/`test` organization.

Present a summary to the user:

- Number of actions recorded
- Pages visited
- Forms filled
- Key interactions (clicks, navigations, form submissions)
- Issues found (list from above)

Ask the user:
- Which actions to **keep** vs **remove** (e.g., accidental clicks)
- What **assertions** to add (what should the test verify?)
- How to **split** the recording into logical test cases (if multiple flows were recorded)

---

## Step 5: Enhance into Test Suite

Transform the raw codegen output into a structured test file. Follow the patterns in
`references/test-patterns.md`.

### 5a. Structure with describe/test blocks

Wrap actions in `test.describe` and `test()` blocks:

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/start-page');
  });

  test('should do the first thing', async ({ page }) => {
    // actions...
    // assertions...
  });

  test('should do the second thing', async ({ page }) => {
    // actions...
    // assertions...
  });
});
```

### 5b. Add assertions

Every test must verify something. Common assertion patterns:

```typescript
// URL changed after navigation
await expect(page).toHaveURL('/dashboard');

// Element is visible
await expect(page.getByRole('heading', { name: 'Welcome' })).toBeVisible();

// Text content
await expect(page.getByText('Success')).toBeVisible();

// Element count
await expect(page.getByRole('listitem')).toHaveCount(5);

// Page title
await expect(page).toHaveTitle(/Dashboard/);

// Input value
await expect(page.getByLabel('Email')).toHaveValue('user@example.com');
```

See `references/test-patterns.md` for the full assertion catalog.

### 5c. Improve selectors

Replace fragile codegen selectors with resilient ones following the priority order
in `references/selector-strategy.md`:

| Priority | Locator | Example |
|----------|---------|---------|
| 1 | `getByRole` | `page.getByRole('button', { name: 'Submit' })` |
| 2 | `getByText` | `page.getByText('Welcome back')` |
| 3 | `getByLabel` | `page.getByLabel('Email address')` |
| 4 | `getByPlaceholder` | `page.getByPlaceholder('Enter email')` |
| 5 | `getByTestId` | `page.getByTestId('submit-btn')` |
| 6 | CSS (last resort) | `page.locator('.btn-primary')` |

### 5d. Add waits where needed

If the app has async loading, add explicit waits:

```typescript
await page.waitForLoadState('networkidle');
await expect(page.getByRole('table')).toBeVisible();
```

### 5e. Extract beforeEach for shared setup

If multiple tests share navigation or setup, move it to `beforeEach`.

---

## Step 6: Organize Files

### Naming and placement

Place the test file in the project's `testDir` (default: `tests/`):

```
tests/
  <feature>.spec.ts      # e.g., checkout.spec.ts, login.spec.ts
```

Use descriptive names matching the feature under test.

### Page objects (optional)

For complex pages with many interactions, or when 3+ tests share the same page,
extract a page object. See `references/page-object-pattern.md`.

```
tests/
  pages/
    <feature>.page.ts    # Page object class
  <feature>.spec.ts      # Test file using the page object
```

---

## Step 7: Scaffold Config

If no `playwright.config.ts` exists (detected in Step 1), offer to create one.

Use the template from `references/config-template.md` as a starting point. Customize:

- `baseURL` — Set to the app's base URL
- `testDir` — Set to the test directory (default `./tests`)
- `projects` — Start with Chromium, optionally add Firefox and WebKit

```bash
# Verify the config is valid
npx playwright test --list
```

---

## Step 8: Run & Verify

Run the generated test to verify it passes:

```bash
npx playwright test <file> --project=chromium
```

### If tests fail

1. Read the error output carefully.
2. Common issues and fixes:
   - **Timeout** — Add `await page.waitForLoadState()` or increase timeout.
   - **Element not found** — Selector is wrong. Check the page and fix the locator.
   - **Assertion failed** — Expected value is incorrect. Verify against actual app behavior.
   - **Navigation error** — URL or route changed. Update `goto()` calls.
3. Fix the issue in the test file.
4. Re-run until green.

### Run headed for debugging

```bash
npx playwright test <file> --project=chromium --headed
```

### Use trace on failure

```bash
npx playwright test <file> --project=chromium --trace=on
# Then view:
npx playwright show-trace test-results/<test-folder>/trace.zip
```

---

## Step 9: Next Steps

After the test passes, suggest:

- **Multi-browser**: `npx playwright test <file>` (runs all configured projects)
- **CI integration**: Add `npx playwright install --with-deps && npx playwright test` to CI pipeline
- **Visual comparison**: Add `await expect(page).toHaveScreenshot()` for visual regression
- **Tracing**: Set `trace: 'on-first-retry'` in config for debugging flaky tests
- **More tests**: Record additional flows using this same workflow
- **Test tagging**: Use `test.describe('feature', { tag: '@smoke' }, ...)` for selective runs

---

## Related Skills

- **`playwright-cli`** — CLI reference for all `npx playwright` commands. Use for running
  tests, managing browsers, viewing reports, and other CLI operations.
- **`e2e-test`** — Interactive browser automation using Playwright MCP tools with screenshot
  evidence. Use for step-by-step manual browser testing, not CLI test suites.
