# Evidence Capture Tools

Reference for evidence capture during test execution. Covers terminal recording,
browser screenshots/video, native desktop screen recording, and GIF conversion.

## Tool Requirements

| Tool | Purpose | Install (Windows) | Install (macOS) | Install (Linux) |
|------|---------|-------------------|-----------------|-----------------|
| VHS | Terminal recording | `scoop install vhs` | `brew install vhs` | `brew install vhs` or snap |
| ffmpeg | Screen recording + GIF conversion | `scoop install ffmpeg` | `brew install ffmpeg` | `apt install ffmpeg` |
| Playwright | Browser screenshots + video | `npx playwright install` (project-local) | same | same |

VHS depends on `ttyd` and `ffmpeg` — both are installed automatically by package managers.

## VHS Tape File Syntax

VHS uses declarative `.tape` files. Generate one per test run:

```tape
Output ./qa-reports/evidence/terminal-run-001.gif
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

## Playwright CLI Screenshots

Capture screenshots of specific pages without a full test run:

```bash
npx playwright screenshot <url> <output.png> --full-page --wait-for-timeout=2000
```

Useful flags: `--full-page`, `--wait-for-timeout=<ms>`, `--viewport-size=<w>,<h>`,
`--device="iPhone 13"`, `--browser=chromium|firefox|webkit`.

## Playwright Video Config

Enable video recording in `playwright.config.ts`:

```typescript
use: {
  video: 'retain-on-failure',  // or 'on' for --evidence=all
}
```

Videos saved as `.webm` in `test-results/` directory per test.

For Cypress, set `video: true` in `cypress.config.ts`.

## ffmpeg Screen Recording

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

## ffmpeg GIF Conversion

High-quality two-pass palette method:

```bash
ffmpeg -y -i input.webm -vf "fps=10,scale=800:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" output.gif
```

Works for both `.webm` (Playwright video) and `.mp4` (native screen recording).
Adjust `fps=10` (lower = smaller file), `scale=800` (width in px).

## Platform-Native Screenshot Fallbacks

When ffmpeg is unavailable, use OS-native tools for single screenshots:

| Platform | Command |
|----------|---------|
| Windows | `powershell -c "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Screen]::PrimaryScreen"` + .NET screenshot |
| macOS | `screencapture -x screenshot.png` |
| Linux | `scrot screenshot.png` or `maim screenshot.png` |

## Evidence Directory Layout

All evidence is stored in the project's `qa-reports/` directory:

```
./qa-reports/
  qa-report-YYYY-MM-DD-HHmm.md
  evidence/
    terminal-run-NNN.gif          # VHS terminal recording (already GIF)
    ui-failure-NNN-<name>.webm    # Playwright video
    ui-screenshot-NNN-<name>.png  # Playwright screenshot
    native-run-NNN.mp4            # ffmpeg screen recording
    gif/                          # User-approved GIFs for PR
      terminal-run-NNN.gif        # Copy (already GIF from VHS)
      ui-failure-NNN-<name>.gif   # Converted from .webm
      native-run-NNN.gif          # Converted from .mp4
```

Naming convention: `<type>-<context>-<NNN>-<test-name>.<ext>`
