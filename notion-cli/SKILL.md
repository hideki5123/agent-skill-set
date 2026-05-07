---
name: notion-cli
description: >
  Operate Notion from the terminal via the official Notion REST API on
  TypeScript + deno — search workspace, get/create/update/archive pages,
  query databases with filters and sorts, list/append/delete blocks, list and
  retrieve users, list databases, retrieve page comments. Two-tool stack:
  mise + deno (no node_modules, no pnpm, no bash). Token stays outside the
  agent: existence-only check, scoped
  `--allow-env=NOTION_TOKEN,NOTION_API_KEY,NOTION_TOKEN_FILE` and
  `--allow-net=api.notion.com` flags only, no `.env` files, never echo or
  print the token. Token resolved in order: NOTION_TOKEN → NOTION_API_KEY →
  contents of the file at NOTION_TOKEN_FILE (suits agenix / sops-nix /
  1Password CLI mounts). Walks first-time users through creating a Notion
  Internal Integration and sharing pages with it.
  Trigger patterns (match any variation):
  notion / Notion / notion-cli / notion cli / notion api /
  notion page / notion pages / notion database / notion db /
  notion search / search notion / find in notion /
  create notion page / new notion page /
  update notion page / edit notion page /
  archive notion page / delete notion page /
  notion blocks / list blocks / append blocks /
  notion users / list notion users / notion workspace users /
  query notion database / list notion db / notion db query /
  get notion page / show notion page / read notion page /
  notion workspace / notion integration / notion token /
  /notion-cli.
---

# notion-cli

Call the Notion REST API from the terminal. Implementation: TypeScript on **deno** with the official `@notionhq/client` SDK (consumed via `npm:@notionhq/client@2` — no `pnpm install`, no `node_modules`). Tool versions pinned via **mise**. Total stack: 2 tools.

## Hard rules

1. **Never read or print the token.** Use existence checks only. Forbidden: `echo $NOTION_TOKEN`, `echo $NOTION_API_KEY`, `printenv | grep -i notion`, `cat ~/.zshrc`, `cat .env`, `cat $NOTION_TOKEN_FILE` (or any file used as a token source), logging `Authorization` headers. See `references/security.md`.
2. **Always use scoped deno permissions.** Base perms for every CLI invocation: `--allow-env=NOTION_TOKEN,NOTION_API_KEY,NOTION_TOKEN_FILE --allow-net=api.notion.com --allow-read=$HOME/.notion-cli --allow-write=$HOME/.notion-cli`. When the user resolves their token via `NOTION_TOKEN_FILE`, also add `--allow-read=$NOTION_TOKEN_FILE` (just that one path — never a broader read scope). Add `--allow-read=<input-file>` only when the user passes another file path as an argument. Never blanket `--allow-read` / `--allow-net`.
3. **Cross-OS only.** All non-trivial logic lives in `assets/lib/*.ts`. No bash, no PowerShell, no shell heredocs.
4. **Confirm destructive ops.** Before `page archive`, `blocks delete`, or `db update` calls that drop properties, summarize what will change and ask the user before sending.
5. **Never invent page or database IDs.** Always derive them from a Notion URL the user supplies, from `notion search`, or from a known reference. If you cannot, ask.

## Path conventions

- **Skill cache** (read-only, version-pinned): `${CLAUDE_PLUGIN_ROOT}/skills/notion-cli/assets/lib/*.ts`. Use this only for the very first `setup.ts` invocation. `${CLAUDE_PLUGIN_ROOT}` is set when Claude orchestrates the skill; in a plain user shell, resolve to `~/.claude/plugins/cache/hideki-plugins/notion-cli/<version>/skills/notion-cli/assets/lib/`.
- **User workspace** (stable, version-independent): `~/.notion-cli/lib/*.ts`. After `setup.ts` runs once, every command runs from this stable path.

## Preflight (before every call)

```
deno run --allow-env=NOTION_TOKEN,NOTION_API_KEY,NOTION_TOKEN_FILE,HOME,USERPROFILE --allow-read --allow-run=mise,deno ~/.notion-cli/lib/preflight.ts
```

(`HOME` / `USERPROFILE` are needed only by preflight to locate `~/.notion-cli/`. The per-call invocations don't need them — those use `$HOME` shell expansion before deno starts.)

If any check fails:
- `mise` missing → instruct platform install and stop. macOS: `brew install mise`. Linux: `curl https://mise.run | sh`. Windows: `winget install jdx.mise`.
- `deno` missing → `cd ~/.notion-cli && mise install`.
- `workspace` missing → run setup (below).
- `token` missing → walk the user through `references/auth-setup.md`. None of `NOTION_TOKEN`, `NOTION_API_KEY`, or `NOTION_TOKEN_FILE` (file readable + non-empty) is satisfied. **Do not** offer a `.env` fallback.

## First-time setup (run once)

From inside Claude (uses skill cache):

```
deno run --allow-read --allow-write --allow-env --allow-run=mise ${CLAUDE_PLUGIN_ROOT}/skills/notion-cli/assets/lib/setup.ts
```

From a user shell (manual, version-pinned path; replace `<version>` with the installed version):

```
deno run --allow-read --allow-write --allow-env --allow-run=mise ~/.claude/plugins/cache/hideki-plugins/notion-cli/<version>/skills/notion-cli/assets/lib/setup.ts
```

`setup.ts` creates `~/.notion-cli/{lib,.cache,tmp}/`, copies `assets/lib/*.ts` and `mise.toml` into the workspace, runs `mise trust && mise install`, and existence-checks the token sources (`NOTION_TOKEN` / `NOTION_API_KEY` / `NOTION_TOKEN_FILE`).

## Authenticating Notion on the terminal

The user asked how to auth. Walk them through it whenever no token source resolves OR they explicitly ask:

1. **Open the integrations page**: <https://www.notion.so/profile/integrations> (or <https://www.notion.so/my-integrations> on older accounts).
2. **Click "+ New integration"**. Configure:
   - Name: any (e.g. `cli-bot`).
   - Associated workspace: pick the workspace you want CLI access to.
   - Type: **Internal** (recommended). Internal tokens never expire and don't require an OAuth app.
3. **Copy the secret.** Click *Show* under "Internal Integration Secret" and copy. It starts with `ntn_…` (newer) or `secret_…` (older).
4. **Make the secret reachable from your shell** (the user does this themselves — never paste it through the agent). Pick **one** of the following; the CLI tries them in order:

   **(a) Direct env var — simplest.** Append to your shell rc:
   - **zsh / bash** (`~/.zshrc` / `~/.bashrc`):
     ```
     export NOTION_TOKEN="ntn_xxxxxxxxxxxxxxxxxxxx"
     ```
     Then `source ~/.zshrc` (or open a new terminal).
   - **fish** (`~/.config/fish/config.fish`):
     ```
     set -gx NOTION_TOKEN ntn_xxxxxxxxxxxxxxxxxxxx
     ```
   - **PowerShell** (`$PROFILE`):
     ```
     $env:NOTION_TOKEN = 'ntn_xxxxxxxxxxxxxxxxxxxx'
     ```

   **(b) Aliased env var.** If your environment already exports the token under `NOTION_API_KEY` (some Nix / home-manager setups standardize on that name), the CLI accepts it as a fallback. No extra step.

   **(c) Secrets-manager-managed file** — recommended for Nix users with **agenix** or **sops-nix**, and for `1Password` / `pass` users mounting tokens as files. Keep the secret out of plain dotfiles entirely. Set `NOTION_TOKEN_FILE` to a chmod-`0400` file whose contents are exactly the token (no surrounding whitespace):
   ```
   export NOTION_TOKEN_FILE=/run/agenix/notion-api-key   # agenix example
   ```
   When invoking the CLI, also add `--allow-read=$NOTION_TOKEN_FILE` to the deno permission scope so the file is the only path beyond `$HOME/.notion-cli` that the script may read. See `references/auth-setup.md` (Nix / agenix section) for full setup.

5. **Critical: share each page or database with the integration.** A fresh integration sees nothing in the workspace until you grant it. Per page/db:
   - Open the page or database in Notion.
   - Click `•••` (top-right) → **Connections** → **Add connections** → pick your integration.
   - Children of a shared page inherit the connection.
6. **Verify**:
   ```
   deno run --allow-env=NOTION_TOKEN,NOTION_API_KEY,NOTION_TOKEN_FILE --allow-net=api.notion.com --allow-read=$HOME/.notion-cli --allow-write=$HOME/.notion-cli [--allow-read=$NOTION_TOKEN_FILE] ~/.notion-cli/lib/notion.ts auth
   ```
   (Drop the bracketed `--allow-read=$NOTION_TOKEN_FILE` if you used route (a) or (b).)
   On success: prints the bot user JSON. On 401: token wrong or revoked. On empty results from `search`: nothing has been shared with the integration yet.

Full details and the Nix / agenix walk-through: `references/auth-setup.md`.

## Per-call workflow

For every operation:

1. **Preflight** (above). Bail if anything fails.
2. **Decide which subcommand** to run (table below).
3. **Run with scoped permissions**:
   ```
   deno run --allow-env=NOTION_TOKEN,NOTION_API_KEY,NOTION_TOKEN_FILE --allow-net=api.notion.com --allow-read=$HOME/.notion-cli --allow-write=$HOME/.notion-cli [--allow-read=$NOTION_TOKEN_FILE] ~/.notion-cli/lib/notion.ts <command> [args]
   ```
   The bracketed `--allow-read=$NOTION_TOKEN_FILE` is only needed if the user is on route (c) of the auth flow (token is sourced from a file).
4. **Surface the response.** Default output is JSON; pass `--format text` for a compact human-readable summary.
5. **For destructive ops** (`page archive`, `blocks delete`, deletes-via-update), summarize first and confirm before sending.

## Subcommand reference

| Command | Purpose | Notes |
|---|---|---|
| `auth` | Show bot user info; smoke-test the token | Use as a sanity check after first-time setup. |
| `search [query]` | Search pages + databases | `--filter pages` / `--filter databases` to narrow. `--limit N` (max 100). |
| `page get <id>` | Retrieve a page | `--with-blocks` to also fetch top-level children. |
| `page create` | Create a page | Requires `--parent-db <id>` or `--parent-page <id>`. `--title "<text>"`. `--stdin` to read body blocks (JSON array) from stdin. |
| `page update <id>` | Update properties | Reads JSON `{ "properties": {…} }` body from stdin. |
| `page archive <id>` | Soft-delete | Confirm before running. Reversible from the Notion trash. |
| `db get <id>` | Retrieve database schema | Use to discover property names + types before `db query`. |
| `db query <id>` | Query rows | `--filter '<json>'` and `--sorts '<json>'`. See `references/filters.md`. |
| `db create` | Create a database under a parent page | Requires `--parent-page <id>` and `--name "<text>"`. `--description "<text>"` optional. `--schema-stdin` reads JSON `{ "properties": {…} }` from stdin (must include at least one `title`-typed property). Refuses silent overwrite when a same-titled database already exists under the same parent. |
| `blocks list <page-id>` | List top-level children | `--limit N` (max 100). For nested blocks, recurse on each child id. |
| `blocks append <page-id>` | Append blocks | Reads JSON array from stdin. See `references/property-types.md` for block shapes. |
| `blocks delete <id>` | Delete a block | Confirm before running. |
| `users me` | Current bot info | Same as `auth`, kept as alias. |
| `users list` | List workspace users | `--limit N`. |
| `users get <id>` | Get a single user | |

For example invocations of each: `references/api-reference.md`. For property/filter shapes: `references/property-types.md`, `references/filters.md`. For error handling and 404 / 401 / rate-limit recipes: `references/error-handling.md`.

## ID extraction

Notion URLs look like `https://www.notion.so/<workspace>/<title>-<32-char-hex>` or `…?v=<view-id>`. The 32-char hex (with or without dashes) is the page or database id. The CLI accepts both dashed and undashed forms. When the user pastes a URL, extract the trailing hex; do not pass the URL itself.

## Out of scope

The following are **deliberately deferred** from v1. If the user asks, surface this list and explain rather than silently failing:

- [ ] **OAuth public integrations** — only Internal Integrations are supported. OAuth requires a deployed app and redirect URL; not a CLI fit.
- [ ] **File uploads** — Notion's file-upload API is asymmetric (you upload to S3, then attach by URL). The Files attachment property is read-only via API on most plans. Defer.
- [ ] **Comment creation on inline contexts** — page-level comments are supported when needed; inline-block comments are deferred.
- [ ] **Search via custom page-property filters** — Notion's `/search` endpoint only filters by `object: page|database` and sorts by edit time. For property filtering, use `db query` against a known database id.
- [ ] **Realtime / webhooks** — Notion supports webhooks but they require a public callback URL; out of scope for a CLI.
- [ ] **Version pinning of API revision** — defaults to the SDK's bundled `Notion-Version`. Override only if the user asks for a specific date.

## Behavior scenarios

```gherkin
Scenario: First-time auth — no token source resolves
  Given none of NOTION_TOKEN, NOTION_API_KEY, or NOTION_TOKEN_FILE is satisfied
  When the user invokes any subcommand
  Then preflight reports "token: missing" and the skill walks the user through
       creating an Internal Integration, picking a token source (direct env var,
       NOTION_API_KEY alias, or NOTION_TOKEN_FILE pointing at a secrets-manager
       file), and sharing target pages with the integration

Scenario: Token resolved from NOTION_API_KEY alias
  Given NOTION_TOKEN is unset but NOTION_API_KEY is exported with a valid token
  When the user invokes any subcommand
  Then the CLI authenticates using NOTION_API_KEY without prompting, since
       resolution falls through NOTION_TOKEN → NOTION_API_KEY → NOTION_TOKEN_FILE

Scenario: Token resolved from NOTION_TOKEN_FILE (agenix / sops-nix / 1Password)
  Given NOTION_TOKEN and NOTION_API_KEY are both unset, and NOTION_TOKEN_FILE
        points at a chmod-0400 file (e.g. /run/agenix/notion-api-key) whose
        contents are a valid token
  When the caller runs deno with --allow-env=NOTION_TOKEN,NOTION_API_KEY,NOTION_TOKEN_FILE
        and --allow-read=$NOTION_TOKEN_FILE added to the base scope
  Then the CLI reads the file once at startup, trims trailing whitespace,
       authenticates, and never logs the value

Scenario: NOTION_TOKEN_FILE set but file unreadable or missing perm
  Given NOTION_TOKEN_FILE points at a path the deno process cannot read
  When the CLI starts
  Then it fails with code "token_file_unreadable" and a hint to add
       --allow-read=<that-path> or fix the file mode/owner

Scenario: Search the workspace
  Given a token source resolves and the integration has been added to a page
  When the user says "search notion for 'meeting notes'"
  Then the skill runs `notion search "meeting notes"` and prints matching pages and
       databases — empty results trigger a hint to share more pages with the integration

Scenario: Get a page with its content
  Given the user supplies a page URL or id
  When the user says "show this notion page"
  Then the skill extracts the id, runs `notion page get <id> --with-blocks`, and
       returns properties + top-level blocks

Scenario: Query a database
  Given the user references a database that has been shared with the integration
  When the user says "list completed tasks in this db"
  Then the skill first runs `notion db get <id>` to discover property names if unknown,
       constructs a Notion filter JSON, and runs `notion db query <id> --filter '<json>'`

Scenario: Create a page in a database
  Given the user wants a new row in a known database
  When the user says "create a Notion page titled 'Q1 Plan' in <db-id>"
  Then the skill runs `notion page create --parent-db <id> --title "Q1 Plan"` and
       returns the new page url

Scenario: Append blocks
  Given a page id and user-supplied content
  When the user says "add this paragraph to the page"
  Then the skill builds a Notion blocks JSON array, pipes it to
       `notion blocks append <page-id>` via stdin, and reports the appended block ids

Scenario: Create a new database under a parent page
  Given the integration has been added to the parent page
  When the user supplies --parent-page <id>, --name "<text>", and a schema on stdin
  Then the skill runs `notion db create --parent-page <id> --name "<text>" --schema-stdin`
       and returns the new database id and url

Scenario: db create rejects when --parent-page is missing
  When the user runs db create without --parent-page
  Then the CLI exits with a clear error explaining --parent-page is required

Scenario: db create rejects when stdin schema JSON is malformed
  Given --schema-stdin is passed but stdin contains invalid JSON or no `properties` object
  When the CLI runs db create
  Then it surfaces a clear parse/validation error and does not call the Notion API

Scenario: db create rejects when a same-titled database already exists under the parent
  Given a database with the requested name is already a child of the same parent page
  When the user runs db create
  Then the CLI fails with an error including the existing database id, refusing to silently overwrite

Scenario: Archive a page (destructive — confirm)
  Given the user wants to archive a page
  When the user says "archive this notion page"
  Then the skill summarizes the page (title, url) and asks the user to confirm before
       running `notion page archive <id>`

Scenario: Token set but target page not shared
  Given the token is valid but the page has not been shared with the integration
  When the skill calls `page get <id>`
  Then the API returns 404 / object_not_found, and the skill explains how to share
       the page in the Notion UI (••• → Connections → Add connection)

Scenario: User asks the agent to print or echo the token
  When the user asks to reveal NOTION_TOKEN, NOTION_API_KEY, or the contents of
        NOTION_TOKEN_FILE
  Then the skill refuses, points the user to their own shell, and reminds them that
       leaked tokens should be rotated at https://www.notion.so/profile/integrations

Scenario: User pastes a Notion URL instead of an id
  When the user gives a URL like https://www.notion.so/.../<title>-<32hex>
  Then the skill extracts the trailing 32-char hex and uses it as the id

Scenario: Rate-limited or transient API failure
  When the API returns 429 or 5xx
  Then the skill surfaces a sanitized error (no Authorization header echoed) and
       suggests retry timing per `references/error-handling.md`

Scenario: Public OAuth integration requested
  When the user asks to use OAuth or build a public integration
  Then the skill explains OAuth is out of scope (no public callback URL) and
       recommends an Internal Integration instead
```

## Feedback Check

Before starting work, look for accumulated feedback on this skill:

- If `feedback/log.md` exists next to this SKILL.md and has 5 or more entries, read the last 10.
- If a pattern is apparent (the same issue keyword in 3+ entries, or average rating below 3), tell the user (in Japanese): 「過去のフィードバックで類似パターンを検出: [簡潔に]。`/skill-improve --skill notion-cli` で改善案を分析できます。」
- Continue with normal execution either way.

If `feedback/log.md` does not exist, skip silently.

## Retrospective

After a non-trivial task (any create/update/archive, any multi-step query, any first-time setup), reflect:

1. Consider: were there mid-session corrections, 401/403/404 errors, missed shared-page steps, or surprising responses?
2. Ask the user (in Japanese): 「今回のNotion操作のフィードバック (1-5の評価、気になった点、または何もなければEnter)」
3. If the user provides feedback OR if real corrections/issues occurred:
   a. Create `feedback/` next to this SKILL.md if missing (resolve via `git rev-parse --show-toplevel` from this skill's source dir, then append `/notion-cli/feedback/`).
   b. Read `feedback/log.md` (create with `# Feedback Log\n\n<!-- Append new entries at the top. Do not edit previous entries. -->\n` if missing).
   c. Prepend an entry directly after the header:

      ```markdown
      ## <ISO-8601 timestamp>
      - **Skill Version**: <version from this skill's plugin.json>
      - **Task**: <which subcommand, brief description>
      - **Outcome**: success | partial-success | failure | error
      - **Rating**: <N>/5 (or "—" if not provided)
      - **Corrections**: <mid-session corrections, or "none">
      - **Issues**: <specific problems, or "none">
      - **User Note**: <user's verbatim feedback, or "—">
      ---
      ```

   d. Confirm in one short Japanese sentence.
4. If the user skips AND no corrections or issues occurred, end without recording.

## References

- `references/auth-setup.md` — Detailed first-time auth walkthrough (Internal Integration creation, sharing pages, troubleshooting).
- `references/api-reference.md` — Example invocations for every subcommand.
- `references/property-types.md` — Notion property and block JSON shapes (title, rich_text, select, multi_select, date, relation, paragraph, heading, bulleted_list_item, etc.).
- `references/filters.md` — Database-query filter and sort JSON syntax with examples.
- `references/security.md` — Token handling rules; what NEVER to do.
- `references/error-handling.md` — 401 / 403 / 404 / 409 / 429 recipes and sanitized error surfacing.
