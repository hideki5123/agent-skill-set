# Evidence Capture Tools

Reference for evidence capture during QA analysis. Two tiers: baseline evidence
(always captured, zero dependencies) and recording evidence (tool-dependent,
optional enhancement).

## Tier 1: Baseline Evidence (Zero Dependency)

These artifacts are always generated using only built-in shell and file-reading
capabilities. No external tools required.

### Execution Evidence

Capture test runner stdout+stderr to `execution/test-output.txt`:

```bash
<test-command> 2>&1 | tee ./qa-evidence/<timestamp>/execution/test-output.txt
```

Generate `execution/test-summary.json` by parsing the test output:

```json
{
  "runner": "<detected runner command>",
  "timestamp": "<ISO 8601>",
  "duration_seconds": 0,
  "total": 0,
  "passed": 0,
  "failed": 0,
  "skipped": 0,
  "exit_code": 0,
  "failures": [
    {
      "test_name": "<full test name>",
      "file": "<file:line>",
      "error_message": "<first line of error>",
      "evidence_dir": "failures/001-<test-name>"
    }
  ]
}
```

### Failure Evidence Folders

For each failing test, create `failures/NNN-<test-name>/` containing:

| File | Contents | How to generate |
|------|----------|-----------------|
| `error-output.txt` | Full error message + stack trace | Extract from test runner output |
| `source-context.txt` | Source code around the failing line (+/- 10 lines) | Read the file referenced in the stack trace |
| `test-code.txt` | The complete failing test function/block | Read the test file at the referenced location |
| `rerun-output.txt` | Output from rerunning the single test (flaky check) | Rerun the specific test and capture output |
| `screenshot.png` | Browser screenshot of the page under test | Playwright CLI (browser tests only, see below) |

For browser tests with a known URL, capture a screenshot:
```bash
npx playwright screenshot <base-url><route> failures/NNN-<name>/screenshot.png --full-page --wait-for-timeout=2000
```

### Gap Proof Files

For each gap finding, create `gaps/gap-NNN-<lens>-<severity>.md`:

```markdown
# Gap: <brief title>

**Lens:** <lens name>
**Severity:** <critical/high/medium/low>
**Confidence:** <high/medium/low>
**Source:** `<file:line>`

## Source Code

```<language>
<full function/method containing the pattern, with line numbers>
```

## Why This Is a Gap

<Explanation of what's untested and why it matters>

## Pattern Matched

<The specific pattern detected — e.g., "unvalidated user input passed to SQL query">

## Suggested Test

<Description of what a test should verify, with example test name>
```

For browser apps (`--app-type=browser` or auto-detected), also capture a screenshot
of the related UI page/component:

```bash
npx playwright screenshot <base-url><route> gaps/gap-NNN-screenshot.png --full-page --wait-for-timeout=2000
```

Or use browser MCP tools (claude-in-chrome, Playwright MCP) if available in the
current session.

### Remediation Evidence

For each remediation (when `--fix` is enabled), create `remediation/NNN-<test-file>/`:

| File | Contents | How to generate |
|------|----------|-----------------|
| `added-tests.diff` | Diff of added test code | `git diff` on the test file after writing tests |
| `test-output.txt` | Output from running the new tests | Run the test file and capture output |

## Tier 2: Recording Evidence (Tool-Dependent)

Optional enhancement when recording tools are available. Artifacts are saved to
`./qa-evidence/<timestamp>/recordings/`.

### Tool Requirements

| Tool | Purpose | Install (Windows) | Install (macOS) | Install (Linux) |
|------|---------|-------------------|-----------------|-----------------|
| VHS | Terminal recording | `scoop install vhs` | `brew install vhs` | `brew install vhs` or snap |
| ffmpeg | Screen recording + GIF conversion | `scoop install ffmpeg` | `brew install ffmpeg` | `apt install ffmpeg` |
| Playwright | Browser screenshots + video | `npx playwright install` (project-local) | same | same |

VHS depends on `ttyd` and `ffmpeg` — both are installed automatically by package managers.

### VHS Tape File Syntax

VHS uses declarative `.tape` files. Generate one per test run:

```tape
Output ./qa-evidence/<timestamp>/recordings/terminal-run.gif
Set Width 1200
Set Height 600
Set FontSize 14
Set Theme "Monokai"
Type "<test-command>"
Enter
Sleep <timeout>s
```

Key settings: `Output` (path + format), `Set Width/Height` (terminal size),
`Set FontSize`, `Sleep` (wait for command to finish). VHS outputs `.gif` directly.

Run with: `vhs <tape-file>`

### Playwright CLI Screenshots

Capture screenshots of specific pages without a full test run:

```bash
npx playwright screenshot <url> <output.png> --full-page --wait-for-timeout=2000
```

Useful flags: `--full-page`, `--wait-for-timeout=<ms>`, `--viewport-size=<w>,<h>`,
`--device="iPhone 13"`, `--browser=chromium|firefox|webkit`.

### Playwright Video Config

Enable video recording in `playwright.config.ts`:

```typescript
use: {
  video: 'retain-on-failure',  // or 'on' for --evidence=all
}
```

Videos saved as `.webm` in `test-results/` directory per test.

For Cypress, set `video: true` in `cypress.config.ts`.

### ffmpeg Screen Recording

Platform-specific commands for native desktop app testing:

**Windows (gdigrab):**
```bash
ffmpeg -f gdigrab -framerate 15 -i desktop -c:v libx264 -preset fast -pix_fmt yuv420p output.mp4
```
Target a specific window: `-i title="My App Window"`

**macOS (avfoundation):**
```bash
ffmpeg -f avfoundation -framerate 15 -i 1 -c:v libx264 output.mp4
```

**Linux (x11grab):**
```bash
ffmpeg -f x11grab -framerate 15 -i :0.0 -c:v libx264 output.mp4
```

Start as background process before tests; stop with SIGINT (`kill -INT <pid>`)
or `taskkill /PID <pid>` on Windows.

### ffmpeg GIF Conversion

High-quality two-pass palette method:

```bash
ffmpeg -y -i input.webm -vf "fps=10,scale=800:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" output.gif
```

Works for both `.webm` (Playwright video) and `.mp4` (native screen recording).
Adjust `fps=10` (lower = smaller file), `scale=800` (width in px).

### Platform-Native Screenshot Fallbacks

When ffmpeg is unavailable, use OS-native tools for single screenshots:

| Platform | Command |
|----------|---------|
| Windows | `powershell -c "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Screen]::PrimaryScreen"` + .NET screenshot |
| macOS | `screencapture -x screenshot.png` |
| Linux | `scrot screenshot.png` or `maim screenshot.png` |

## Evidence Package Directory Layout

All evidence is stored in a timestamped directory under `qa-evidence/`:

```
./qa-evidence/<YYYY-MM-DD-HHmm>/
  REPORT.md                           # Index linking to all evidence
  execution/
    test-output.txt                   # Raw stdout+stderr (always captured)
    test-summary.json                 # Parsed: pass/fail/skip/duration
  failures/
    001-<test-name>/
      error-output.txt                # Full error + stack trace
      source-context.txt              # Source code around failing line (+/- 10 lines)
      test-code.txt                   # The failing test code
      rerun-output.txt                # Rerun attempt (flaky check)
      screenshot.png                  # (browser tests, if available)
  gaps/
    gap-001-<lens>-<severity>.md      # Code snippet + explanation
    gap-001-screenshot.png            # Browser screenshot (when app-type=browser)
  remediation/                        # (when --fix)
    001-<test-file>/
      added-tests.diff
      test-output.txt
  recordings/                         # (when --evidence != off, tools available)
    terminal-run.gif
    ui-*.webm / ui-*.png
    native-*.mp4
    gif/
```

Naming conventions:
- Failures: `NNN-<sanitized-test-name>` (zero-padded 3 digits)
- Gaps: `gap-NNN-<lens>-<severity>` (zero-padded 3 digits)
- Remediation: `NNN-<sanitized-test-file-name>` (zero-padded 3 digits)
- Recordings: `<type>-<context>.<ext>`
