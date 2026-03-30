# Video Recording Reference

Record E2E test execution as video using Playwright CLI. When `--video=on` (default),
the skill generates a Playwright test script from the CSV scenario, configures video
recording, and runs it via `npx playwright test`.

## Playwright Config Template

Generate `playwright.config.js` in the evidence directory for each test run:

```javascript
const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: '.',
  timeout: 120000,
  expect: { timeout: 10000 },
  use: {
    baseURL: '<target-url>',
    video: 'on',
    screenshot: 'on',
    trace: 'on',
    viewport: { width: <width>, height: <height> },
    actionTimeout: 15000,
  },
  reporter: [
    ['list'],
    ['html', { open: 'never', outputFolder: './html-report' }],
  ],
  outputDir: './test-results',
  projects: [{ name: 'chromium', use: { browserName: 'chromium' } }],
});
```

Replace `<target-url>`, `<width>`, `<height>` from the CSV config section.

## Test Script Generation

Generate `<test-name>.spec.js` in the evidence directory. Wrap all steps in a
single `test()` block.

### Template

```javascript
const { test, expect } = require('@playwright/test');

test('<test-name>', async ({ page }) => {
  // Setup preconditions
  // <from CSV config setup field>

  // Step 1: <action description>
  // <generated Playwright API call>
  await page.screenshot({ path: 'step-01-<action>.png' });
  // <assertion for expected_result>

  // Step 2: ...
});
```

### CSV Action to Playwright API Mapping

| CSV Action | Playwright Test API | Notes |
|------------|---------------------|-------|
| `navigate` | `await page.goto('<url>')` | Follow with `await page.waitForLoadState('domcontentloaded')` |
| `type` / `fill` | `await page.getByLabel('<target>').fill('<input>')` | Try getByLabel first, then getByPlaceholder, then getByRole('textbox') |
| `type` with `submit:true` | `.fill()` then `await page.getByLabel('<target>').press('Enter')` | Or `await page.keyboard.press('Enter')` |
| `type` with `slowly:true` | `await page.getByLabel('<target>').pressSequentially('<input>')` | Types character by character |
| `fill_form` | Multiple `.fill()`, `.check()`, `.selectOption()` calls | One call per field |
| `click` | `await page.getByRole('button', { name: '<target>' }).click()` | Match target to appropriate getByRole/getByText |
| `dblclick` | `await page.getByText('<target>').dblclick()` | For edit-in-place interactions |
| `hover` | `await page.getByText('<target>').hover()` | Reveal hidden elements |
| `keypress` | `await page.keyboard.press('<key>')` | Escape, Tab, ArrowDown, Enter, etc. |
| `select` | `await page.getByRole('combobox', { name: '<target>' }).selectOption('<input>')` | Dropdown selection |
| `upload` | `await page.getByLabel('<target>').setInputFiles('<input>')` | File upload |
| `wait` (text) | `await expect(page.getByText('<target>')).toBeVisible({ timeout: <ms> })` | Wait for text to appear |
| `wait` (time) | `await page.waitForTimeout(<seconds> * 1000)` | Static wait |
| `verify` | `await expect(page.getByText('<target>')).toBeVisible()` | Assert element present |
| `screenshot` | `await page.screenshot({ path: 'step-<NN>-screenshot.png', fullPage: true })` | Explicit full-page capture |
| `url_check` | `await expect(page).toHaveURL(/<pattern>/)` | Assert current URL |
| `dialog` | `page.on('dialog', d => d.accept())` — register before triggering action | Must be set up before the action that triggers the dialog |

### Target Resolution

Human-readable targets from the CSV map to Playwright locators in priority order:

1. **Role + name**: `page.getByRole('<role>', { name: '<target>' })`
   - `Submit button` → `page.getByRole('button', { name: 'Submit' })`
   - `Email input field` → `page.getByRole('textbox', { name: 'Email' })`
   - `Dashboard heading` → `page.getByRole('heading', { name: 'Dashboard' })`
2. **Label**: `page.getByLabel('<target>')`
   - `Email input field` → `page.getByLabel('Email')`
3. **Placeholder**: `page.getByPlaceholder('<target>')`
   - `Search...` → `page.getByPlaceholder('Search')`
4. **Text**: `page.getByText('<target>')`
   - `Welcome back` → `page.getByText('Welcome back')`
5. **Test ID**: `page.getByTestId('<target>')`
   - Only when target starts with `data-testid=`

When generating the locator, extract the meaningful noun from the target description:
- `Email input field` → label/placeholder is `Email`
- `Submit button` → button name is `Submit`
- `Toggle checkbox for Buy groceries` → checkbox near text `Buy groceries`

### Setup Preconditions

The CSV `setup` config field maps to code at the top of the test:

| Setup instruction | Generated code |
|-------------------|----------------|
| `Clear localStorage` | `await page.evaluate(() => localStorage.clear())` |
| `Clear sessionStorage` | `await page.evaluate(() => sessionStorage.clear())` |
| `Set localStorage key=value` | `await page.evaluate(() => localStorage.setItem('key', 'value'))` |

Place setup code after `page.goto()` but before the first test step.

## Running the Test

```bash
cd <evidence-dir>
npx playwright test <test-name>.spec.js --config=playwright.config.js --headed
```

Add `--headed` so the browser is visible during execution. Omit for headless runs.

## Artifact Locations

After the test run, artifacts are in `<evidence-dir>/test-results/`:

| Artifact | Path | Description |
|----------|------|-------------|
| Video | `test-results/<test-title>/video.webm` | Full test execution recording |
| Trace | `test-results/<test-title>/trace.zip` | Interactive trace (screenshots + DOM + timing) |
| Screenshots | `step-*.png` in evidence root | Per-step screenshots taken during test |
| HTML report | `html-report/index.html` | Playwright HTML report with embedded video |

Copy `video.webm` to the evidence root as `recording.webm` for easy access.

## Viewing Evidence

```bash
# Watch the video
# Open recording.webm in any media player

# Interactive trace viewer
npx playwright show-trace <evidence-dir>/test-results/<test-title>/trace.zip

# HTML report with embedded video
npx playwright show-report <evidence-dir>/html-report
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `npx playwright` not found | Run `npm install -D @playwright/test` in the project |
| Browser not installed | Run `npx playwright install chromium` |
| Video file is 0 bytes | Ensure the test completed (even with failures) — video is finalized on context close |
| Locator not found | Check the target description; try a different locator strategy (getByText instead of getByRole) |
| Timeout on action | Increase `actionTimeout` in config or add explicit waits before the action |
