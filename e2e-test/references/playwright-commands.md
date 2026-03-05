# Playwright MCP Tools Reference

Quick reference for available Playwright MCP tools used during E2E testing.

## Ref-Based Workflow

All interaction tools require a `ref` identifier from the accessibility tree. The workflow is:

1. **Snapshot** — Call `browser_snapshot` to get the current accessibility tree
2. **Find ref** — Parse the tree to locate the element matching your target description
3. **Act** — Pass the `ref` to the interaction tool (click, type, hover, etc.)

### Snapshot caching

Reuse the most recent snapshot if no navigation or DOM-altering action (click, type, form submit) has occurred since the last snapshot. This reduces token usage on complex pages.

### Stale ref recovery

If an action fails because the ref is stale (element was removed/re-rendered):
1. Take a fresh `browser_snapshot`
2. Re-locate the element by its description
3. Retry the action once with the new ref
4. If it fails again, report as an error

## Browser Setup

| Tool | Purpose |
|------|---------|
| `browser_install` | Install browser binaries (replaces `npx playwright install chromium`) |
| `browser_navigate` | Navigate to a URL (also initializes the browser session) |
| `browser_navigate_back` | Go back in history |
| `browser_close` | Close the browser and clean up resources |
| `browser_resize` | Resize browser viewport |

## Interaction Tools

All interaction tools require a `ref` from `browser_snapshot` unless noted otherwise.

### `browser_click`

Click an element.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `ref` | Yes | Element reference from snapshot |
| `doubleClick` | No | Set `true` for double-click (e.g., edit-in-place in TodoMVC) |

### `browser_type`

Type text into a single text input. Use this for individual text fields.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `ref` | Yes | Element reference from snapshot |
| `text` | Yes | Text to type |
| `submit` | No | Set `true` to press Enter after typing (type-then-submit) |
| `slowly` | No | Set `true` to type character by character (for apps with key event handlers) |

**When to use `browser_type` vs `browser_fill_form`**:
- `browser_type` — Single text input. Supports `submit` and `slowly` options
- `browser_fill_form` — Multiple fields at once, or non-text fields (checkboxes, radios, comboboxes, sliders)

### `browser_fill_form`

Fill multiple form fields in a single call. The ONLY tool for non-text field types.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `ref` | Yes | Form element reference |
| Fields vary by form | | Supports text, checkbox, radio, combobox, slider |

### `browser_hover`

Hover over an element to trigger hover states (e.g., reveal hidden buttons).

| Parameter | Required | Description |
|-----------|----------|-------------|
| `ref` | Yes | Element reference from snapshot |

### `browser_press_key`

Press a keyboard key globally. Does NOT need a ref.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `key` | Yes | Key name: `Escape`, `Tab`, `ArrowDown`, `Enter`, etc. |

**Important**: Use this for standalone key presses only (closing dialogs, navigating menus). Do NOT use for type-then-Enter — use `browser_type` with `submit: true` instead.

### `browser_select_option`

Select an option from a dropdown/select element.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `ref` | Yes | Select element reference |
| `values` | Yes | Option values to select |

### `browser_drag`

Drag an element to another location.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `startRef` | Yes | Element to drag |
| `endRef` | Yes | Drop target |

### `browser_file_upload`

Upload files to a file input.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `paths` | Yes | Array of file paths to upload |

### `browser_handle_dialog`

Handle browser alert/confirm/prompt dialogs.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `accept` | Yes | `true` to accept, `false` to dismiss |
| `promptText` | No | Text to enter in prompt dialogs |

**Warning**: Browser dialogs block all further events. Avoid triggering them unintentionally. If you must interact with dialog-triggering elements, use `browser_evaluate` to check for and dismiss dialogs first.

### `browser_tabs`

Manage browser tabs.

| Parameter | Required | Description |
|-----------|----------|-------------|
| Varies | | List tabs, create new tab, close tab, select tab |

## Inspection Tools

### `browser_snapshot`

Get the accessibility tree of the current page. This is the primary tool for:
- Finding element `ref` identifiers before interactions
- Verifying page content and state
- Checking that expected text/elements are present

### `browser_take_screenshot`

Capture a screenshot of the current page.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `type` | **Yes** | `"png"` or `"jpeg"` — this parameter is required |
| `filename` | No | Custom filename for the screenshot |
| `fullPage` | No | Set `true` to capture the full scrollable page |

### `browser_evaluate`

Run JavaScript in the browser context. Use for DOM reads and data checks.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `expression` | Yes | JavaScript expression to evaluate |

Examples:
- `window.location.href` — get current URL
- `document.title` — get page title
- `localStorage.getItem('key')` — read storage

**`browser_evaluate` vs `browser_run_code`**:
- `browser_evaluate` — Runs JS in the browser context (like the DevTools console). For reading DOM state, checking values, simple checks
- `browser_run_code` — Runs Node.js code with Playwright API access (`page`, `context`). For complex page interactions, waiting strategies, iframe access

### `browser_run_code`

Run Node.js code with full Playwright API access. The escape hatch for anything the specialized tools can't do.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `code` | Yes | Async function body: `async (page) => { ... }` |

Use cases:
- `await page.evaluate(() => localStorage.clear())` — clear storage as setup
- `await page.waitForURL('**/dashboard')` — wait for URL change (not supported by `browser_wait_for`)
- `await page.waitForLoadState('networkidle')` — wait for network idle
- `await page.frameLocator('#myframe').locator('button').click()` — interact with iframes
- Computed style checks, complex assertions

### `browser_console_messages`

Read console log/error/warning output from the browser.

### `browser_network_requests`

View network activity (requests and responses).

## Synchronization

### `browser_wait_for`

Wait for a condition before proceeding.

**Supported parameters** (ONLY these three):

| Parameter | Description |
|-----------|-------------|
| `text` | Wait until the specified text appears on the page |
| `textGone` | Wait until the specified text disappears from the page |
| `time` | Wait for a specified number of seconds |

**NOT supported**: selectors, URL changes, network idle, load states. For these, use `browser_run_code`:

```javascript
// Wait for URL change
async (page) => { await page.waitForURL('**/dashboard'); }

// Wait for network idle
async (page) => { await page.waitForLoadState('networkidle'); }

// Wait for a specific selector
async (page) => { await page.waitForSelector('.loaded'); }
```

## Iframe Limitation

Iframes can only be accessed via `browser_run_code` using Playwright's `page.frameLocator(...)` API. The snapshot and interaction tools operate on the main frame only.

## Tips

- Always call `browser_navigate` first — it initializes the browser session
- Always call `browser_snapshot` before any interaction to get fresh `ref` values
- Use `browser_snapshot` (accessibility tree) to verify page content, not just screenshots
- Take screenshots AFTER waits complete, not before
- Use `browser_console_messages` to capture errors on failure
- `browser_take_screenshot` always requires `type: "png"` or `type: "jpeg"`
- Call `browser_close` when done to clean up resources
