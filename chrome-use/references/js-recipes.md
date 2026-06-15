# chrome-use JavaScript & interaction recipes

WHEN TO READ: load this when you need ready-made extraction or interaction snippets,
or the worked X/Twitter example. Each JS recipe is fed to
`node scripts/chrome-use.mjs run --js -` (or saved to a file and passed by path),
and runs via the DevTools `evaluate_script` tool against the **active page**.

## Conventions

- `evaluate_script` takes a **function**. You may hand the CLI a full function
  (`() => { … }`, `async () => { … }`, `(el) => …`) or a **bare expression**
  (`document.title`) — the CLI wraps a bare expression for you. Use `--expr` to
  force expression-wrapping for ambiguous one-liners.
- The function's return value is serialized to JSON on stdout. Return objects
  directly — no manual `JSON.stringify` needed (though it's harmless).
- **async works**: `async () => { const r = await fetch('/api'); return r.json(); }`
  resolves properly (unlike the old AppleScript bridge).
- Each invocation is a fresh CDP session on the active tab. To act on a specific
  URL, prefix with `--url` (same `run`) so navigation + JS share one connection.

## Extraction

Visible text of the page:

```js
() => document.body.innerText
```

innerText of a specific selector:

```js
() => (document.querySelector('main') || document.body).innerText
```

All links (href + text):

```js
() => [...document.querySelectorAll('a[href]')].map(a => ({ href: a.href, text: a.innerText.trim() }))
```

All image URLs:

```js
() => [...document.images].map(i => i.currentSrc || i.src).filter(Boolean)
```

A table to rows:

```js
() => [...document.querySelectorAll('table tr')].map(tr => [...tr.children].map(td => td.innerText.trim()))
```

Page metadata:

```js
() => ({ title: document.title, url: location.href, desc: (document.querySelector('meta[name=description]') || {}).content || '' })
```

## Interaction — two ways

### A) DOM via evaluate_script (self-contained, no uid)

Best under the on-demand model: each call is independent and targets the active
page. Use for clicks/fills that you can express as DOM operations.

Click the first element matching a selector:

```js
() => { const e = document.querySelector('button[type=submit]'); if (!e) return 'not found'; e.click(); return 'clicked'; }
```

Set an input value and fire the events React/Vue listen for:

```js
() => {
  const el = document.querySelector('input[name=q]'); if (!el) return 'no input';
  const set = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  set.call(el, 'hello world');
  el.dispatchEvent(new Event('input', { bubbles: true }));
  el.dispatchEvent(new Event('change', { bubbles: true }));
  return el.value;
}
```

Submit a form:

```js
() => { const f = document.querySelector('form'); if (!f) return 'no form'; f.requestSubmit ? f.requestSubmit() : f.submit(); return 'submitted'; }
```

Scroll to the bottom (call repeatedly to lazy-load):

```js
() => { window.scrollTo(0, document.body.scrollHeight); return document.body.scrollHeight; }
```

### B) Native tools via batch (uid-based, one session)

When you want the DevTools-native `click`/`fill`/`fill_form` (robust hit-testing,
real input events), drive them with uids from `take_snapshot` — all in one `batch`
so the uids stay valid:

```bash
node scripts/chrome-use.mjs batch --steps - <<'JSON'
[
  {"tool":"navigate_page","args":{"type":"url","url":"https://example.com/login"}},
  {"tool":"take_snapshot","args":{}}
]
JSON
# read the uids from the snapshot, then:
node scripts/chrome-use.mjs batch --steps - <<'JSON'
[
  {"tool":"fill_form","args":{"elements":[{"uid":"<user-uid>","value":"me@example.com"},{"uid":"<pass-uid>","value":"…"}]}},
  {"tool":"click","args":{"uid":"<submit-uid>"}}
]
JSON
```

`fill_form` fills multiple fields in one call — prefer it over several `fill`/`click`.

## Infinite-scroll collection (across runs)

1. `run --js -` with the extraction snippet to grab what's currently rendered.
2. `run --js -` with the scroll snippet.
3. Repeat 1–2 until the count stops growing; dedupe in your own logic.

Keep the active tab on the target page between calls (each invocation reconnects to
the active tab). For a long single flow, prefer one `batch` with repeated
`evaluate_script` steps so it shares a session.

## Worked example: X/Twitter thread extraction

Save as a file and run with `--url` + `--wait`:

```js
() => {
  const arts = [...document.querySelectorAll('article')];
  return arts.map((a, i) => {
    let who = (a.querySelector('[data-testid="User-Name"]') || {}).innerText || '';
    who = who.replace(/\n+/g, ' ').trim();
    const t = (a.querySelector('[data-testid="tweetText"]') || {}).innerText || '';
    const tm = (a.querySelector('time') || {}).getAttribute?.('datetime') || '';
    const imgs = [...a.querySelectorAll('[data-testid="tweetPhoto"] img')].map(im => im.src);
    return { i: i + 1, who, tm, imgs, text: t };
  });
}
```

Invocation:

```bash
node scripts/chrome-use.mjs run \
  --url "https://x.com/USER/status/ID" \
  --wait 'tweetText' --wait '@' \
  --js /path/to/xtweet.js --out /tmp/thread.json
```

Scroll first (repeat the scroll recipe) to pull in more of a long thread before
extracting. This is an *example application of the generic recipes*, not a
maintained site-specific extractor — X's DOM (`data-testid` values) changes over
time; adjust selectors if it breaks.
