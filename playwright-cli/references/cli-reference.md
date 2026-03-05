# Playwright CLI Reference

Exhaustive flag and option reference for all `npx playwright` subcommands.

## playwright test

Run tests.

```
npx playwright test [test-filter...] [options]
```

| Flag | Description |
|------|-------------|
| `test-filter` | Positional args — file paths, directory paths, or file:line patterns |
| `--config <path>` | Path to config file (default: `playwright.config.ts` or `.js`) |
| `--project <name...>` | Run only tests from specified projects (can repeat) |
| `--grep <regex>` | Only run tests matching this regex (against test title) |
| `--grep-invert <regex>` | Skip tests matching this regex |
| `--headed` | Run tests in headed browser mode |
| `--debug` | Run tests with Playwright Inspector for step-by-step debugging |
| `--ui` | Open interactive UI mode for running/watching tests |
| `--ui-host <host>` | Host for UI mode server (default: `localhost`) |
| `--ui-port <port>` | Port for UI mode server |
| `--browser <name>` | Browser to use: `chromium`, `firefox`, `webkit` (overrides config) |
| `--reporter <name>` | Reporter: `list`, `dot`, `line`, `json`, `junit`, `html`, `blob`, `github` |
| `--workers <count>` | Number of parallel workers (number or percentage like `50%`) |
| `--retries <count>` | Maximum retry count for flaky tests |
| `--timeout <ms>` | Test timeout in milliseconds (default: 30000) |
| `--max-failures <count>` | Stop after N test failures (`-x` is alias for `--max-failures=1`) |
| `-x` | Stop on first failure (alias for `--max-failures=1`) |
| `--output <dir>` | Directory for test artifacts (default: `test-results`) |
| `--repeat-each <count>` | Run each test N times (useful for flake detection) |
| `--shard <current/total>` | Shard tests, e.g. `--shard=1/4` |
| `--update-snapshots` | Update expected screenshots / snapshot files |
| `--ignore-snapshots` | Skip snapshot expectations (both comparison and update) |
| `--list` | List all tests without running them (dry run) |
| `--global-timeout <ms>` | Overall timeout for the entire test run |
| `--forbid-only` | Fail if `test.only` is found (useful in CI) |
| `--fully-parallel` | Run all tests in parallel regardless of config |
| `--last-failed` | Re-run only tests that failed in the previous run |
| `--pass-with-no-tests` | Exit 0 even if no tests were found |
| `--quiet` | Suppress stdio from tests |
| `--trace <mode>` | Force trace recording: `on`, `off`, `retain-on-failure` |
| `--no-deps` | Do not run project dependencies |
| `--only-changed [ref]` | Only run tests affected by uncommitted changes (or changes since `ref`) |
| `--tsconfig <path>` | Path to a custom tsconfig for test files |

## playwright codegen

Record user interactions and generate test code.

```
npx playwright codegen [options] [url]
```

| Flag | Description |
|------|-------------|
| `url` | URL to open (optional, starts with blank page if omitted) |
| `--target <language>` | Language for generated code: `javascript` (default), `python`, `python-async`, `java`, `csharp` |
| `-o, --output <file>` | Save generated script to file |
| `--browser <name>` | Browser to use: `chromium`, `firefox`, `webkit` |
| `--channel <channel>` | Chromium channel: `chrome`, `msedge`, etc. |
| `--color-scheme <scheme>` | Emulate color scheme: `light`, `dark`, `no-preference` |
| `--device <name>` | Emulate device, e.g. `"iPhone 13"`, `"Pixel 5"` |
| `--geolocation <lat,long>` | Emulate geolocation, e.g. `"37.819722,-122.478611"` |
| `--ignore-https-errors` | Ignore HTTPS errors |
| `--load-storage <file>` | Load authentication state from file |
| `--save-storage <file>` | Save authentication state to file on exit |
| `--lang <language>` | Emulate browser locale, e.g. `"en-US"` |
| `--proxy-server <url>` | Proxy server URL |
| `--timezone <tz>` | Emulate timezone, e.g. `"America/New_York"` |
| `--viewport-size <w,h>` | Viewport size, e.g. `"1280,720"` |
| `--block-service-workers` | Block service workers |
| `--save-har <file>` | Save HAR file of network activity |
| `--save-har-glob <glob>` | Filter HAR entries by URL pattern |

## playwright install

Install browsers and optionally OS dependencies.

```
npx playwright install [browser...] [options]
```

| Flag | Description |
|------|-------------|
| `browser` | Specific browser(s): `chromium`, `firefox`, `webkit`, `chrome`, `msedge` |
| `--with-deps` | Also install system dependencies (Linux) |
| `--dry-run` | Print what would be installed without downloading |
| `--force` | Force reinstall even if already present |

## playwright install-deps

Install system dependencies for browsers (Linux only).

```
npx playwright install-deps [browser...]
```

| Flag | Description |
|------|-------------|
| `browser` | Specific browser(s) to install deps for (installs all if omitted) |

## playwright uninstall

Remove installed browsers.

```
npx playwright uninstall [options]
```

| Flag | Description |
|------|-------------|
| `--all` | Remove all ever-installed Playwright browsers |

## playwright show-report

Open the HTML test report.

```
npx playwright show-report [report-dir] [options]
```

| Flag | Description |
|------|-------------|
| `report-dir` | Path to report directory (default: `playwright-report`) |
| `--host <host>` | Host to serve report on (default: `localhost`) |
| `--port <port>` | Port to serve report on (default: `9323`) |

## playwright show-trace

Open the trace viewer for a recorded trace.

```
npx playwright show-trace [trace-file...] [options]
```

| Flag | Description |
|------|-------------|
| `trace-file` | One or more trace zip files or directories |
| `--host <host>` | Host for trace viewer server |
| `--port <port>` | Port for trace viewer server |

## playwright screenshot

Capture a screenshot of a web page.

```
npx playwright screenshot [options] <url> <output>
```

| Flag | Description |
|------|-------------|
| `url` | URL to screenshot (required) |
| `output` | Output file path (required) |
| `--browser <name>` | Browser: `chromium`, `firefox`, `webkit` |
| `--channel <channel>` | Chromium channel |
| `--color-scheme <scheme>` | `light`, `dark`, `no-preference` |
| `--device <name>` | Emulate device |
| `--full-page` | Capture full scrollable page |
| `--geolocation <lat,long>` | Emulate geolocation |
| `--ignore-https-errors` | Ignore HTTPS errors |
| `--lang <language>` | Browser locale |
| `--load-storage <file>` | Load storage state |
| `--proxy-server <url>` | Proxy server |
| `--save-storage <file>` | Save storage state |
| `--timezone <tz>` | Emulate timezone |
| `--viewport-size <w,h>` | Viewport size |
| `--wait-for-selector <sel>` | Wait for selector before screenshot |
| `--wait-for-timeout <ms>` | Wait for timeout before screenshot |
| `--block-service-workers` | Block service workers |

## playwright pdf

Generate a PDF of a web page (Chromium only).

```
npx playwright pdf [options] <url> <output>
```

| Flag | Description |
|------|-------------|
| `url` | URL to render (required) |
| `output` | Output PDF file path (required) |
| `--browser <name>` | Must be `chromium` (PDF is Chromium-only) |
| `--channel <channel>` | Chromium channel |
| `--color-scheme <scheme>` | `light`, `dark`, `no-preference` |
| `--device <name>` | Emulate device |
| `--geolocation <lat,long>` | Emulate geolocation |
| `--ignore-https-errors` | Ignore HTTPS errors |
| `--lang <language>` | Browser locale |
| `--load-storage <file>` | Load storage state |
| `--proxy-server <url>` | Proxy server |
| `--save-storage <file>` | Save storage state |
| `--timezone <tz>` | Emulate timezone |
| `--viewport-size <w,h>` | Viewport size |
| `--block-service-workers` | Block service workers |

## playwright open

Open a page in a browser for manual inspection.

```
npx playwright open [options] [url]
```

Aliases for specific browsers:
- `npx playwright cr [url]` — open in Chromium
- `npx playwright ff [url]` — open in Firefox
- `npx playwright wk [url]` — open in WebKit

| Flag | Description |
|------|-------------|
| `url` | URL to open (optional) |
| `--browser <name>` | Browser: `chromium`, `firefox`, `webkit` |
| `--channel <channel>` | Chromium channel |
| `--color-scheme <scheme>` | `light`, `dark`, `no-preference` |
| `--device <name>` | Emulate device |
| `--geolocation <lat,long>` | Emulate geolocation |
| `--ignore-https-errors` | Ignore HTTPS errors |
| `--lang <language>` | Browser locale |
| `--load-storage <file>` | Load storage state |
| `--save-storage <file>` | Save storage state |
| `--proxy-server <url>` | Proxy server |
| `--timezone <tz>` | Emulate timezone |
| `--viewport-size <w,h>` | Viewport size |
| `--block-service-workers` | Block service workers |

## playwright clear-cache

Remove all cached browser binaries, default downloads, and temp data.

```
npx playwright clear-cache
```

No flags. Removes everything in the browsers cache directory.

## playwright merge-reports

Merge blob reports from sharded test runs into a single report.

```
npx playwright merge-reports [options] <dir>
```

| Flag | Description |
|------|-------------|
| `dir` | Directory containing blob report files (required) |
| `--reporter <name>` | Reporter for merged output: `html`, `json`, `junit`, `list`, etc. |
| `--config <path>` | Config file for reporter settings |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `PLAYWRIGHT_BROWSERS_PATH` | Custom path for browser binaries (default: platform-specific cache) |
| `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD` | Set to `1` to skip browser download during `npm install` |
| `PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS` | Skip host requirements validation |
| `DEBUG=pw:api` | Enable Playwright API debug logs |
| `DEBUG=pw:browser` | Enable browser process debug logs |
| `DEBUG=pw:protocol` | Enable CDP protocol debug logs (very verbose) |
| `DEBUG=pw:*` | Enable all Playwright debug logs |
| `PWDEBUG=1` | Enable Playwright Inspector (equivalent to `--debug`) |
| `PWDEBUG=console` | Enable console debugging helpers in browser |
| `CI` | When set, Playwright adjusts defaults for CI (e.g., disables retries prompt) |
| `PLAYWRIGHT_HTML_OPEN` | Control HTML report auto-open: `always`, `never`, `on-failure` |
| `PLAYWRIGHT_HTML_HOST` | Host for HTML report server |
| `PLAYWRIGHT_HTML_PORT` | Port for HTML report server |
| `PLAYWRIGHT_JSON_OUTPUT_NAME` | Output file for JSON reporter |
| `PLAYWRIGHT_JUNIT_OUTPUT_NAME` | Output file for JUnit reporter |
