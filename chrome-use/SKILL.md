---
name: chrome-use
description: >-
  Drive the user's already-running, LOGGED-IN Chrome via the Chrome DevTools
  Protocol (chrome-devtools-mcp --autoConnect) ON DEMAND — navigate, read page
  content, run JS, take a11y snapshots, click/fill, screenshot, inspect network,
  and profile performance against the user's REAL session (cookies/auth/open
  tabs), with the browser left open and NO profile copy and NO restart. The
  DevTools backend is spawned only while a command runs and torn down after, so
  NOTHING stays resident between commands or sessions (no idle process per ccb).
  Use when the task needs the existing logged-in session reused as-is. Trigger
  phrases: "chrome-use", "ブラウザから取得", "ログイン済みの Chromeで", "ブラウザを操作して",
  "このページ読んで", "Xのスレッド読んで", "ログインしたまま取得", "自分のセッションでスクレイプ",
  "read this page in my browser", "scrape with my session", "drive my chrome",
  "execute JS in my (logged-in) browser", "automate my logged-in browser",
  "devtools", "dev-tool", "CDP". Requires Chrome 144+ and Node. NOT for
  isolated/throwaway automation where login reuse is unneeded — use playwright-cli
  for that.
version: 2.0.0
---

# chrome-use

Drive the user's **already-open, logged-in** Chrome through the **Chrome DevTools
Protocol**, via `chrome-devtools-mcp --autoConnect` spawned **on demand**. The
browser stays open, the profile is never copied, the existing session
(cookies/auth/tabs) is reused as-is — and the DevTools backend runs **only for the
duration of each command**, then exits. There is no idle resident process.

> v2 replaced the old macOS-AppleScript bridge with CDP. The CLI is
> `node scripts/chrome-use.mjs` (zero npm dependencies — Node builtins only; Node
> is already required because the DevTools MCP server is a Node package).

## Why on-demand (and what it implies)

Registering `chrome-devtools` as a global MCP server keeps an idle Node process in
**every** Claude session (including each background `ccb`). This skill instead
spawns the server per command and kills it after — zero idle footprint.

Consequence: **each command is a fresh CDP session.** State that lives in the
DevTools session does NOT persist across separate invocations:

- The "currently selected page" resets on each connect (defaults to the active
  tab). `evaluate_script`, `take_snapshot`, etc. act on that page.
- `uid`s from `take_snapshot` are only valid **within the same session**, so a
  `snapshot → click → fill → submit` chain must run in **one** invocation.

Therefore: bundle a flow into a single `run` (navigate → wait → js → snapshot →
screenshot share one connection), or use `batch` for uid-based interaction
sequences. For one-off DOM reads/actions, `evaluate_script` is self-contained and
targets the active page — the most robust pattern under the on-demand model.

## When to use this vs playwright-cli

- **chrome-use** — you NEED the real logged-in session: reading content behind a
  login (X/Twitter, internal dashboards, Gmail-style apps), acting on the user's
  open tabs, or anything where re-authenticating in a fresh browser is impractical.
- **playwright-cli / e2e-test** — isolated, reproducible automation where a fresh
  browser context is fine; scriptable test suites with video/trace.

If login reuse is not required, prefer playwright-cli.

## Safety (read before driving)

This skill operates the user's **fully-privileged logged-in session** — it can read
cookie-scoped data, act (post/click/submit/buy) as the user, and see everything the
user can. Therefore:

- Never run JS or multi-step flows from an untrusted source.
- For any **state-changing** action on a sensitive site (sending, posting,
  deleting, purchasing, changing settings), confirm with the user first.
- Default to read-only extraction unless the user asked for an action.
- Navigation changes the user's real tab. Prefer `--new-tab` (opens a new tab) when
  you must navigate but shouldn't disturb the current one; read-only
  `evaluate_script` on the active page disturbs nothing.

## Prerequisites (one-time)

1. **Chrome 144+** running (the user's normal logged-in window). `--autoConnect`
   attaches to its default profile; it launches no browser of its own.
2. **Local remote debugging enabled once**: in Chrome open
   `chrome://inspect/#remote-debugging` and allow incoming local debugging
   connections (persists across restarts). On first connect Chrome also shows a
   per-connection approval dialog — approve it.
3. **Node** on PATH (already required; the DevTools MCP server runs on Node via
   `npx`). First run downloads `chrome-devtools-mcp` into the npx cache.

Display OFF is fine (Chrome renders offscreen). System **sleep** is not — keep the
machine awake (e.g. `caffeinate`) for unattended runs.

Run `check` to verify the connection; it prints Japanese guidance if any of the
above is missing.

## Quick start

```bash
# verify the connection + list open tabs
node scripts/chrome-use.mjs check

# read the active tab (bare expression is auto-wrapped into a function)
echo "document.title" | node scripts/chrome-use.mjs run --js -

# open a URL in a NEW tab, wait for text, extract structured data to a file
node scripts/chrome-use.mjs run --new-tab --url "https://example.com" \
  --wait "Example Domain" --js /path/extract.js --out /tmp/out.json

# a11y snapshot (gives uids for click/fill), and a screenshot
node scripts/chrome-use.mjs snapshot --out /tmp/snap.txt
node scripts/chrome-use.mjs screenshot --out /tmp/page.png --full-page
```

## CLI reference

```
chrome-use.mjs check
  Spawn the DevTools backend, connect via autoConnect, list open pages.
  Prints Japanese guidance (Chrome running? chrome://inspect enabled?) on failure.

chrome-use.mjs run [--url URL] [--new-tab] [--wait TEXT]... [--js FILE|-] [--expr]
                   [--snapshot] [--screenshot PATH] [--full-page] [--out PATH]
  One connection, steps run in order:
    --url URL       navigate the active tab to URL (navigate_page type=url)
    --new-tab       open URL in a new tab instead (new_page) — leaves current tab
    --wait TEXT     wait until TEXT appears (repeatable; resolves on any match)
    --js FILE|-     evaluate JavaScript on the selected page; result to stdout/--out
    --expr          force-wrap --js source as an expression `() => ( … )`
    --snapshot      print the a11y-tree snapshot (element uids for click/fill)
    --screenshot P  save a screenshot to P
    --full-page     full-page screenshot (with --screenshot)
    --out PATH      write the js/snapshot result to PATH instead of stdout

chrome-use.mjs snapshot   [--out PATH] [--verbose]
chrome-use.mjs screenshot [--out PATH] [--full-page] [--format png|jpeg|webp]

chrome-use.mjs tools
  List the underlying DevTools tools (29: navigate/evaluate/snapshot/click/fill/
  network/performance/…).

chrome-use.mjs call <tool> [--params JSON | --params-file PATH | --params -]
  Escape hatch: call ANY DevTools tool directly with JSON arguments.

chrome-use.mjs batch [--steps JSON | --steps-file PATH | --steps -] [--out PATH]
  Run a JSON array of {tool, args} in ONE session — required for uid-based
  interaction chains (take_snapshot → click → fill → submit).
```

### JS for `--js` / `evaluate_script`

The DevTools `evaluate_script` tool takes a **function declaration**. This skill:

- passes a function through unchanged: `() => { return document.title }`,
  `async () => { return await fetch('/api').then(r=>r.json()) }` (async works!),
  `(el) => el.innerText` (args are element uids, passed via the tool's `args`);
- auto-wraps a **bare expression** you pipe in (`document.title`) into a function;
- `--expr` forces expression-wrapping for ambiguous one-liners.

End extraction logic with the value you want (objects are returned as JSON).

### Interaction: snapshot → uid → click/fill

Native interaction tools take a `uid` from `take_snapshot`. Because uids are
session-scoped, do the whole chain in one `batch`:

```bash
node scripts/chrome-use.mjs batch --steps - <<'JSON'
[
  {"tool":"navigate_page","args":{"type":"url","url":"https://example.com/login"}},
  {"tool":"take_snapshot","args":{}},
  {"tool":"fill","args":{"uid":"<uid-from-snapshot>","value":"me@example.com"}},
  {"tool":"click","args":{"uid":"<submit-uid>"}}
]
JSON
```

In practice: run `take_snapshot` first, read the uids, then issue the
`fill`/`click` batch. Or skip uids entirely and act through `evaluate_script` DOM
calls (self-contained per invocation) — see `references/js-recipes.md`.

## Configuration (env)

- `CHROME_DEVTOOLS_MCP_VERSION` — pinned server version (default `1.2.0`).
- `CHROME_DEVTOOLS_MCP_CHANNEL` — `canary|dev|beta|stable` to target a non-default
  Chrome channel.
- `CHROME_USE_TIMEOUT_MS` — per-call timeout (default 60000).

## JavaScript recipes

WHEN TO READ: read `references/js-recipes.md` for ready-made extraction/interaction
snippets (text/links/images/tables, click, fill, submit, infinite-scroll) and the
worked X/Twitter thread example. Not needed for simple one-off expressions.

## Feedback Check

Before executing, check accumulated feedback on this skill:

- If `feedback/log.md` exists next to this SKILL.md and has 5+ entries, read the last 10.
- If a pattern is apparent (same issue keyword in 3+ entries, or average rating < 3),
  tell the user (in Japanese): 「過去のフィードバックで類似パターンを検出: [簡潔に]。
  `/skill-improve --skill chrome-use` で改善案を分析できます。」
- Continue either way. If `feedback/log.md` does not exist, skip silently.

## Retrospective

After completing a chrome-use task, reflect:

1. Were there mid-task corrections, connection/setup friction, selector breakage, or
   wrong-tab/wrong-page issues (the on-demand fresh-session model)?
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
