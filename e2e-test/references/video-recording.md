# Video Recording Reference

Record E2E test execution as video using Playwright CLI. The skill generates a Playwright
test script from the CSV scenario, configures video recording, and runs it via
`npx playwright test`.

When `--chrome-profile` is active, the workflow additionally generates a `chrome-fixture.js`
that uses `launchPersistentContext` to reuse an existing Chrome profile (cookies, sessions,
extensions, localStorage, IndexedDB).

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

## Playwright Config Template — Chrome Profile Mode

When Chrome profile mode is active (`--chrome-profile`), generate a stripped-down config.
Video, trace, and screenshot are handled by `chrome-fixture.js`, not by config.

```javascript
const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: '.',
  timeout: 120000,
  expect: { timeout: 10000 },
  workers: 1,       // Required: shared profile cannot parallelize
  retries: 0,       // Shared profile state makes retries unreliable
  use: {
    baseURL: '<target-url>',
    actionTimeout: 15000,
    // video, screenshot, trace — handled by chrome-fixture.js persistent context
    // viewport — handled by chrome-fixture.js launchPersistentContext options
  },
  reporter: [
    ['list'],
    ['html', { open: 'never', outputFolder: './html-report' }],
  ],
  outputDir: './test-results',
});
```

## Chrome Fixture Template (`chrome-fixture.js`)

Generated when Chrome profile mode is active. Overrides `context` and `page` fixtures
to use `launchPersistentContext` with the system Chrome installation.

```javascript
const { test: base, expect } = require('@playwright/test');
const { chromium } = require('playwright');
const path = require('path');

const USER_DATA_DIR = '<chrome-user-data-dir>';
const PROFILE_DIR = '<profile-directory>';
const VIEWPORT = { width: <width>, height: <height> };
const VIDEO_DIR = './test-results/videos';

const test = base.extend({
  context: async ({}, use) => {
    const launchOptions = {
      channel: 'chrome',
      headless: false,
      viewport: VIEWPORT,
      args: [`--profile-directory=${PROFILE_DIR}`],
      recordVideo: { dir: VIDEO_DIR, size: VIEWPORT },
    };

    let context;
    try {
      context = await chromium.launchPersistentContext(USER_DATA_DIR, launchOptions);
    } catch (error) {
      if (error.message.includes('lock') || error.message.includes('already running')
          || error.message.includes('user data directory is already in use')) {
        throw new Error(
          'Chrome profile is locked. Close all Chrome windows and retry.\n'
          + `Profile: ${USER_DATA_DIR} (${PROFILE_DIR})\n`
          + `Original error: ${error.message}`
        );
      }
      throw error;
    }

    await context.tracing.start({ screenshots: true, snapshots: true });
    await use(context);
    await context.tracing.stop({ path: path.join('test-results', 'trace.zip') });
    await context.close();
  },

  page: async ({ context }, use) => {
    const pages = context.pages();
    const page = pages.length > 0 ? pages[0] : await context.newPage();
    await use(page);
  },
});

module.exports = { test, expect };
```

### Template Placeholders

| Placeholder | Source | Example |
|-------------|--------|---------|
| `<chrome-user-data-dir>` | CSV `chrome_profile_path` or platform default | `C:\\Users\\Hideki\\AppData\\Local\\Google\\Chrome\\User Data` |
| `<profile-directory>` | CSV `chrome_profile` or `--chrome-profile` value | `Default`, `Profile 1` |
| `<width>`, `<height>` | CSV `viewport` (default: 1280, 720) | `1280`, `720` |

### Platform Default Chrome User Data Paths

| Platform | Default Path |
|----------|-------------|
| Windows | `%LOCALAPPDATA%\Google\Chrome\User Data` (e.g., `C:\Users\<user>\AppData\Local\Google\Chrome\User Data`) |
| macOS | `~/Library/Application Support/Google/Chrome` |
| Linux | `~/.config/google-chrome` |

The profile directory (`Default`, `Profile 1`, `Profile 2`, etc.) is a subdirectory within
the user data path. Use `--profile-directory` Chrome arg to select it — do NOT append it
to `userDataDir`.

## Test Script Generation

Generate `<test-name>.spec.js` in the evidence directory. Wrap all steps in a
single `test()` block.

### Template

**Normal mode:**
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

**Chrome profile mode** — change only the import line:
```javascript
const { test, expect } = require('./chrome-fixture');

test('<test-name>', async ({ page }) => {
  // Identical test body — page.goto, locators, assertions, screenshots
  // The page fixture comes from chrome-fixture.js persistent context
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

| Artifact | Normal Mode Path | Chrome Profile Mode Path |
|----------|------------------|--------------------------|
| Video | `test-results/<test-title>/video.webm` | `test-results/videos/<guid>.webm` |
| Trace | `test-results/<test-title>/trace.zip` | `test-results/trace.zip` |
| Screenshots | `step-*.png` in evidence root | Same |
| HTML report | `html-report/index.html` | Same |

Copy the video file to the evidence root as `recording.webm` for easy access.
In Chrome profile mode, the video has a GUID filename — copy the most recent `.webm`
from `test-results/videos/`.

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
| Chrome profile locked | Close all Chrome windows using this profile before running the test |
| `channel: 'chrome'` not found | Install Google Chrome (not Chromium). Bundled Chromium does not have profile compatibility |
| Extensions not loading | Extensions only load in headed mode with `channel: 'chrome'`; verify `headless: false` |
| Profile data not persisting | Ensure `userDataDir` points to the Chrome User Data root, NOT the profile subdirectory. Profile is selected via `--profile-directory` arg |
