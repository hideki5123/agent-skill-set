---
name: playwright-cli
description: >
  Run Playwright CLI commands via Bash for test execution, code generation, browser management,
  reporting, and debugging. Covers the full `npx playwright` surface: test, codegen, install,
  show-report, show-trace, screenshot, pdf, open, clear-cache, merge-reports, and more.
  Use when the user asks to run playwright tests, generate test code, install browsers,
  view a test report or trace, take a page screenshot or PDF, open a URL in a specific browser,
  clear the playwright cache, merge shard reports, debug tests, or use playwright UI mode.
  Trigger phrases include "playwright test", "run playwright", "npx playwright", "codegen",
  "install browsers", "show report", "show trace", "playwright screenshot", "playwright pdf",
  "open in chromium", "open in firefox", "open in webkit", "clear playwright cache",
  "merge reports", "shard tests", "playwright debug", "playwright ui mode", "record test",
  "run e2e tests with playwright cli", "playwright headed", "playwright retries",
  "update snapshots", "playwright grep", "list playwright tests".
---

# Playwright CLI Skill

Run any `npx playwright` command via the Bash tool. This skill covers test execution,
code generation, browser installation, reporting, tracing, screenshots, PDFs, and debugging.

## Constraints

- Always use `npx playwright` — never assume a global install.
- Playwright must already be installed in the project (`npm i -D @playwright/test` or equivalent).
  If it is not, guide the user to install it first.
- On Windows, some commands behave differently (e.g., `show-report` may not auto-open a browser
  in WSL). Note platform quirks when relevant.
- Commands that launch a GUI (codegen, UI mode, show-report, show-trace, open) require a display.
  In headless CI environments, skip or adapt these.

## Preflight Check

Before running any Playwright command, verify the installation:

```bash
npx playwright --version
```

If this fails:
- **"npx: command not found"** — Node.js / npm is not installed.
- **"Cannot find module '@playwright/test'"** — Playwright is not installed in this project.
  Suggest: `npm install -D @playwright/test`
- **"Executable doesn't exist"** on test run — Browsers not installed.
  Suggest: `npx playwright install` or `npx playwright install chromium`

## Note on Related Skills

This skill (`playwright-cli`) handles **CLI commands** — running tests, codegen, install,
screenshots, traces, etc. via `npx playwright ...` in Bash.

The `playwright-codegen` skill provides a **guided workflow** for recording browser
interactions with codegen and transforming them into structured test suites with assertions
and page objects. Use that skill when the user wants to create new tests from recordings,
not just run codegen.

The separate `e2e-test` skill uses **Playwright MCP browser tools** for interactive,
step-by-step browser automation with screenshot evidence. Use that skill when the user
wants to manually drive a browser session, not run CLI test suites.

## Quick Reference

| Action | Command |
|--------|---------|
| Run all tests | `npx playwright test` |
| Run specific file | `npx playwright test tests/login.spec.ts` |
| Run by grep | `npx playwright test --grep "login"` |
| Run headed | `npx playwright test --headed` |
| Run single browser | `npx playwright test --project=chromium` |
| Debug tests | `npx playwright test --debug` |
| UI mode | `npx playwright test --ui` |
| List tests (dry run) | `npx playwright test --list` |
| Code generation | `npx playwright codegen https://example.com` |
| Install browsers | `npx playwright install` |
| Install one browser | `npx playwright install chromium` |
| Install system deps | `npx playwright install-deps` |
| Show HTML report | `npx playwright show-report` |
| Show trace viewer | `npx playwright show-trace trace.zip` |
| Take screenshot | `npx playwright screenshot https://example.com shot.png` |
| Generate PDF | `npx playwright pdf https://example.com page.pdf` |
| Open URL in Chromium | `npx playwright open https://example.com` |
| Open URL in Firefox | `npx playwright ff https://example.com` |
| Open URL in WebKit | `npx playwright wk https://example.com` |
| Clear browser cache | `npx playwright clear-cache` |
| Merge shard reports | `npx playwright merge-reports ./blob-reports` |
| Update snapshots | `npx playwright test --update-snapshots` |

## Common Patterns

### Run tests matching a pattern

```bash
npx playwright test --grep "checkout" --project=chromium
```

Exclude pattern:

```bash
npx playwright test --grep-invert "slow"
```

### Headed mode with slowdown for observation

```bash
npx playwright test --headed --timeout=60000
```

### Retries and workers

```bash
npx playwright test --retries=2 --workers=4
```

For CI with limited resources:

```bash
npx playwright test --retries=2 --workers=1
```

### Sharding across CI jobs

Job 1 of 4:

```bash
npx playwright test --shard=1/4
```

Merge after all shards complete:

```bash
npx playwright merge-reports ./blob-reports --reporter=html
```

### Code generation with device emulation

```bash
npx playwright codegen --device="iPhone 13" https://example.com
```

With viewport:

```bash
npx playwright codegen --viewport-size="1280,720" https://example.com
```

Record into a file:

```bash
npx playwright codegen --target=javascript -o tests/generated.spec.js https://example.com
```

### Save and reuse authentication state

Save storage state after login:

```bash
npx playwright codegen --save-storage=auth.json https://example.com
```

Reuse it:

```bash
npx playwright codegen --load-storage=auth.json https://example.com
```

Or in open:

```bash
npx playwright open --load-storage=auth.json https://example.com
```

### Trace viewing

If tests were run with tracing enabled (`use: { trace: 'on' }` in config):

```bash
npx playwright show-trace test-results/example-test/trace.zip
```

### Debug a specific test

```bash
npx playwright test tests/login.spec.ts:42 --debug
```

The `:42` targets the test starting at line 42.

### Update visual snapshots

```bash
npx playwright test --update-snapshots
```

### Custom config file

```bash
npx playwright test --config=playwright.ci.config.ts
```

### Reporter selection

```bash
npx playwright test --reporter=dot
npx playwright test --reporter=json > results.json
npx playwright test --reporter=junit > results.xml
npx playwright test --reporter=html
```

Multiple reporters:

```bash
npx playwright test --reporter='list,html'
```

### Run only failed tests from last run

```bash
npx playwright test --last-failed
```

### Screenshot and PDF

```bash
npx playwright screenshot --full-page https://example.com full.png
npx playwright pdf https://example.com output.pdf
```

## Error Handling

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Cannot find module '@playwright/test'` | Not installed | `npm install -D @playwright/test` |
| `Executable doesn't exist at ...` | Browsers not installed | `npx playwright install` |
| `browserType.launch: ...` | Missing system deps | `npx playwright install-deps` (Linux) |
| Tests pass locally, fail in CI | Missing browsers or deps in CI | Add `npx playwright install --with-deps` to CI setup |
| `Error: Timed out ...` | Slow environment | Increase `--timeout` or use `--retries` |
| `ENOMEM` / OOM | Too many workers | Reduce `--workers=1` |
| Trace file not found | Tracing not enabled | Set `use: { trace: 'on' }` in config |
| Report empty after shards | Blob reports not merged | Run `npx playwright merge-reports ./blob-reports` |

## Configuration

Playwright searches for a config file in this order:
1. `--config=<path>` flag
2. `playwright.config.ts` in project root
3. `playwright.config.js` in project root

Key config settings that affect CLI behavior:
- `projects` — defines browser targets (mapped to `--project` flag)
- `retries` — default retry count (overridden by `--retries`)
- `workers` — parallelism (overridden by `--workers`)
- `reporter` — default reporter (overridden by `--reporter`)
- `use.trace` — when to record traces (`'on'`, `'off'`, `'on-first-retry'`, `'retain-on-failure'`)
- `use.baseURL` — base URL for relative navigations
- `testDir` — directory containing test files

## References

For the full flag-by-flag reference of every subcommand, read `references/cli-reference.md`.
