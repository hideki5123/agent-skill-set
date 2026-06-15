---
name: chrome-use
description: >-
  Drive an already-running, LOGGED-IN Chromium browser on macOS via AppleScript —
  navigate, click, fill forms, scroll, and extract page content from the user's
  REAL session, with the browser left open and NO profile copy and NO restart.
  Use when the task needs the existing logged-in session (cookies, auth, current
  tabs) reused as-is. Trigger phrases: "chrome-use", "ブラウザから取得", "ログイン済みの
  Chromeで", "ブラウザを操作して", "このページ読んで", "Xのスレッド読んで", "ログインしたまま取得",
  "自分のセッションでスクレイプ", "read this page in my browser", "scrape with my session",
  "drive my chrome", "execute JS in my (logged-in) browser", "automate my logged-in
  browser". Chromium family (Chrome default; Brave/Edge/Arc/Vivaldi via --app).
  NOT for isolated/throwaway automation where login reuse is unneeded — use
  playwright-cli for that. macOS only.
version: 1.0.0
---

# chrome-use

Drive the user's **already-open, logged-in** Chromium browser through AppleScript's
`execute javascript` bridge. The browser stays open, the profile is never copied,
and the existing session (cookies/auth/tabs) is reused as-is.

## When to use this vs playwright-cli

- **chrome-use** — you NEED the real logged-in session: reading content behind a
  login (X/Twitter, internal dashboards, Gmail-style apps), acting on tabs the user
  already has open, or anything where re-authenticating in a fresh browser is
  impractical. macOS, Chromium family.
- **playwright-cli / e2e-test** — isolated, reproducible automation where a fresh
  browser context is fine. Cross-platform, scriptable test suites.

If login reuse is not required, prefer playwright-cli.

## Safety (read before driving)

This skill executes arbitrary JavaScript in the user's **fully-privileged logged-in
session** — it can read cookies-scoped data, post/click/submit as the user, and see
everything the user can. Therefore:

- Never run JS or multi-step flows from an untrusted source.
- For any **state-changing** action on a sensitive site (sending, posting, deleting,
  purchasing, changing settings), confirm with the user first.
- Default to read-only extraction unless the user asked for an action.

## Platform & prerequisites

macOS only (`osascript`). Two one-time grants are required; `check` detects both:

1. **Automation consent** — the first time anything controls the browser, macOS shows
   a "… wants to control <App>" dialog. It can only be approved in the **foreground**;
   a background job cannot trigger/approve it (the AppleEvent just times out, -1712).
   Run `check` interactively once and approve.
2. **Allow JavaScript from Apple Events** — `<App>` menu → View → Developer → Allow
   JavaScript from Apple Events. This toggle **cannot be flipped by a script** (UI
   `click`/`AXPress` do not register it); the user must enable it manually once.

System Events fallbacks (menu/native-UI automation) additionally require Accessibility
permission for the controlling process.

## Quick start

Always preflight first:

```bash
scripts/chrome-use.sh check
```

If it reports both grants OK, run JS against the live tab. Pass JS via a file or stdin
(stdin avoids shell-escaping for complex scripts):

```bash
# read the active tab's title
echo "document.title" | scripts/chrome-use.sh run --js -

# open/activate a URL, wait for a selector, run an extraction file, save output
scripts/chrome-use.sh run --url "https://x.com/user/status/123" \
  --wait 'article [data-testid="tweetText"]' --js /path/extract.js --out /tmp/out.txt

# Brave instead of Chrome
scripts/chrome-use.sh run --app "Brave Browser" --js - <<'JS'
JSON.stringify([...document.querySelectorAll('a')].map(a=>a.href).slice(0,20))
JS
```

## How `run` works (and the hard constraints behind it)

The helper encapsulates the AppleScript gotchas — you usually don't need to touch them,
but know them:

- **Active-tab only.** `execute javascript` reliably works on the **active tab of the
  front window** only; non-active tabs raise -1723. `run` therefore finds the target
  tab (by URL substring), activates it, brings its window to front, then executes.
- **Nested-tell form only.** Use `tell active tab of front window to execute javascript
  "…"`. The `execute javascript "…" in tab N of window M` form fails with -1723.
- **Complex JS via file.** `run` reads JS from a file as UTF-8 (`read … as «class
  utf8»`), sidestepping AppleScript string-escaping. Write your JS to a temp file (or
  pipe via `--js -`) rather than inlining quotes.
- **Tab lifecycle.** If `run` had to OPEN a tab for `--url`, it closes that tab when
  done (unless `--keep-tab`). Tabs the user already had open are never closed.
- **Return values.** The JS expression's result is returned on stdout. For structured
  data, end your JS with `JSON.stringify(...)` so it serializes cleanly.

## CLI reference

```
chrome-use.sh check [--app NAME]
  Preflight: verifies Automation consent and the JS-from-Apple-Events toggle.
  Prints Japanese guidance for whatever is missing.

chrome-use.sh run [--app NAME] [--url URL] --js FILE|- [--wait SELECTOR] [--out PATH] [--keep-tab]
  --app       Chromium app name (default "Google Chrome"; e.g. "Brave Browser",
              "Microsoft Edge", "Arc", "Vivaldi").
  --url       If given, find a tab whose URL contains this; activate it, else open it.
              Omit to operate on the current active tab.
  --js FILE|- JS source file, or "-" to read from stdin. The result prints to stdout.
  --wait SEL  Poll until document.querySelector(SEL) exists (hard error on timeout).
  --out PATH  Write the result to PATH instead of stdout.
  --keep-tab  Do not close a tab that run opened.

chrome-use.sh screenshot [--app NAME] [--out PATH]
  Best-effort: activates the app and screencaptures its front-window region.
```

Errors are mapped to Japanese guidance: toggle-off (error 12), -1723 (access denied),
-1712 (consent pending / unresponsive), -1743 (not authorized).

## JavaScript recipes

WHEN TO READ: read `references/js-recipes.md` when you need ready-made extraction or
interaction snippets (text/links/images/tables, click, fill, submit, infinite-scroll,
wait-for-selector) or the worked X/Twitter thread example. Not needed for simple
one-off expressions.

## Clipboard fallback (toggle un-enableable)

If "Allow JavaScript from Apple Events" cannot be enabled in some environment, fall
back to: have the user open DevTools console on the tab, paste a snippet that calls
`copy(...)`, then read the result with `pbpaste`. See `references/js-recipes.md`.

## Feedback Check

Before executing, check accumulated feedback on this skill:

- If `feedback/log.md` exists next to this SKILL.md and has 5+ entries, read the last 10.
- If a pattern is apparent (same issue keyword in 3+ entries, or average rating < 3),
  tell the user (in Japanese): 「過去のフィードバックで類似パターンを検出: [簡潔に]。
  `/skill-improve --skill chrome-use` で改善案を分析できます。」
- Continue either way. If `feedback/log.md` does not exist, skip silently.

## Retrospective

After completing a chrome-use task, reflect:

1. Were there mid-task corrections, permission/setup friction, selector breakage, or
   wrong-tab issues?
2. Ask the user (in Japanese): 「今回のフィードバック (1-5評価、気になった点、なければEnter)」
   If the rating is < 5, ALWAYS follow up: 「なぜその評価ですか？ (具体的に)」 and record
   the answer verbatim as `Rating reason`.
3. If feedback is given OR issues actually occurred, append an entry to `feedback/log.md`
   (create it with a `# Feedback Log` header if missing), prepended after the header:

   ```markdown
   ## <ISO-8601 timestamp>
   - **Skill Version**: <version from frontmatter>
   - **Task**: <brief>
   - **Outcome**: success | partial-success | failure | error
   - **Rating**: <N>/5 (or "—")
   - **Rating reason**: <verbatim, or "—">
   - **Corrections**: <or "none">
   - **Issues**: <or "none">
   - **User Note**: <verbatim, or "—">
   ---
   ```
4. If the user skips AND nothing went wrong, end without recording.

## BDD spec

BDD spec lives in `references/scenarios.feature`. Read only when auditing or amending
the skill; not needed for normal execution.
