---
name: recap-to-notion
version: 1.0.1
description: >
  Sync a session-recap directory (summary.md + note.md + meta.json) to Notion under the
  explicit "My Agent Notes / Session Recaps" database via the notion-cli skill. The Notion
  target is fixed by design — the value of this skill is being explicit about its
  destination, not configurable. Appends to the shared session-recap manifest on success
  and retries previously-failed uploads on next invocation. Cleanup and retention are
  owned by session-recap, not this skill. Standalone — pass a recap dir path, or invoke
  in retry-only mode. Auto-invoked by session-recap via the chain in its
  ~/.claude/session-recaps/.recap-config.json. Use when the user says "recap to notion" /
  "Notionに recap を上げて" / "recap upload" / "/recap-to-notion" / "recap retry" /
  "再アップロード" / "Notion同期".
---

# recap-to-notion

Take a session-recap directory and sync it into the Notion database
**`My Agent Notes / Session Recaps`** as a single page (one DB row per session). Idempotent
upserts keyed by `Session ID`. Failures are retried on the next invocation.

This skill assumes:
- `notion-cli` skill (>= 1.1.0) is installed and `NOTION_TOKEN` is configured.
- A page titled exactly `My Agent Notes` exists in the Notion workspace and is shared
  with the integration.
- The session-recap directory layout is the contract owned by `session-recap`.

Cleanup of confirmed-old local recap dirs is **not** this skill's job — it belongs to
`session-recap` (the manifest owner). This skill only appends manifest entries on
successful uploads.

## Calling notion-cli

`notion-cli` is **not a shell binary** — it is a Claude Code skill whose implementation
lives in `~/.notion-cli/lib/notion.ts` (a deno script created by the skill's `setup.ts`).
All invocations in this workflow run that script with scoped deno permissions.

Define the prefix once at the start of the run:

```bash
NOTION_PERMS="--allow-env=NOTION_TOKEN,NOTION_API_KEY,NOTION_TOKEN_FILE \
  --allow-net=api.notion.com \
  --allow-read=$HOME/.notion-cli --allow-write=$HOME/.notion-cli"
# If the user's token source is NOTION_TOKEN_FILE (agenix / sops-nix / 1Password
# CLI mounts), append exactly that one path to the read scope:
[ -n "$NOTION_TOKEN_FILE" ] && NOTION_PERMS="$NOTION_PERMS --allow-read=$NOTION_TOKEN_FILE"
NOTION="deno run $NOTION_PERMS $HOME/.notion-cli/lib/notion.ts"
```

All later `$NOTION <subcommand> [args]` lines in this SKILL.md expand to that full
deno invocation. Never assume `notion-cli` is on `$PATH` — it is not. If
`~/.notion-cli/lib/notion.ts` is missing (workspace not yet bootstrapped), tell the
user to run notion-cli's `setup.ts` once and exit cleanly without modifying any local
state.

## Workflow

### Feedback Check

If `feedback/log.md` exists alongside this SKILL.md and has 5 or more entries, read the
last 10. If a pattern is apparent (the same issue in 3+ entries, or average rating
below 3):

- Tell the user (UI language): 「過去のフィードバックで類似パターンを検出: [簡潔に]。`/my-skill-factory improve recap-to-notion` で改善できます。」 / English equivalent.
- Continue with normal execution.

### Phase 0 — Mode dispatch

Determine the mode from the invocation:

- **upload mode**: an absolute path to a recap directory was passed as `args` (this is
  what session-recap's chain dispatch sends). Run A → B0 → B for that one dir.
- **retry-only mode**: no dir argument, or the user said "recap retry" / "再試行" /
  similar. Run A → B0.

(Cleanup-only mode lives in `session-recap`, not here. If the user asks for cleanup
in this skill's invocation, redirect them to `/session-recap` with the relevant phrase.)

### Phase A — Notion target resolution

Read `~/.claude/session-recaps/.notion-config.json`:

```json
{
  "database_id": "<id>",
  "parent_page_title": "My Agent Notes",
  "first_configured": "<ISO-8601 with time>"
}
```

If the file is missing or `database_id` is empty:

1. Locate the parent page:
   ```bash
   $NOTION search "My Agent Notes" --filter pages --limit 5 --format json
   ```
   Pick the result with `object == "page"` and a `title` exactly matching
   `My Agent Notes`. Extract its `id`.
   - If 0 matches → tell the user (UI language): 「Notion 上に `My Agent Notes`
     ページを作成し、Internal Integration と共有してください」 / English equivalent.
     Stop. Do not write `.notion-config.json`. Local files stay intact for next retry.
2. Locate or create the database:
   ```bash
   $NOTION search "Session Recaps" --filter databases --limit 5 --format json
   ```
   Find a `database` whose parent is the page from step 1 and whose title is exactly
   `Session Recaps`.
   - If found → save its `id` to `.notion-config.json`.
   - If not found → call:
     ```bash
     cat <<'JSON' | $NOTION db create \
       --parent-page <parent-page-id> \
       --name "Session Recaps" \
       --description "Auto-generated recaps from Claude Code sessions" \
       --schema-stdin --format json
     {
       "properties": {
         "Title":        { "title": {} },
         "Date":         { "date": {} },
         "Session ID":   { "rich_text": {} },
         "Slug":         { "rich_text": {} },
         "CWD":          { "rich_text": {} },
         "Duration":     { "rich_text": {} },
         "Total Events": { "number": { "format": "number" } },
         "Language":     { "select": { "options": [{ "name": "ja" }, { "name": "en" }] } }
       }
     }
     JSON
     ```
     Save the returned `id` to `.notion-config.json`. No user confirmation prompt.
   - If `db create` is rejected as an unknown subcommand (older notion-cli that lacks
     it) → tell the user (UI language): 「Notion 上で `My Agent Notes` 配下に
     `Session Recaps` データベースを手動作成してください (スキーマは README 参照)。
     notion-cli を 1.1.0 以上に上げると自動化されます」 / English equivalent. Stop.

If `.notion-config.json` had a value but Phase B/B0 later returns an
`object_not_found` error from notion-cli, clear the `database_id` and re-run Phase A
once before failing.

### Phase B0 — Retry pending uploads (notion target only)

Goal: catch up any local recap dir that does NOT yet have a `target == "notion"`
manifest entry.

```bash
RECAPS=~/.claude/session-recaps
MANIFEST=$RECAPS/.manifest.jsonl
for dir in "$RECAPS"/[0-9]*_*; do
  [ -d "$dir" ] || continue
  # Already uploaded to notion?
  if [ -f "$MANIFEST" ] && grep -q "\"target\": \"notion\".*\"local_dir\": \"$dir\"" "$MANIFEST"; then
    continue
  fi
  # Otherwise → run Phase B for this dir.
done
```

For each pending dir, call Phase B. Successes append manifest entries; failures are
left for the next invocation (no special handling here).

Other future uploaders (e.g. `recap-to-confluence`) are expected to filter the manifest
by their own `target` value the same way. Each uploader is responsible for its own
target's retry queue — independent of others.

### Phase B — Upsert one recap dir to Notion

Input: absolute path to a recap dir containing `summary.md`, `note.md`, `meta.json`.

1. **Load metadata** from `meta.json`:
   - `session_id`, `short_id`, `slug`, `cwd`, `language`, `started_at`, `ended_at`,
     `duration_seconds`, `total_events`.

2. **Build the Notion page body** by merging summary + note:
   - Read `summary.md` and `note.md`.
   - In the merged content, rewrite cross-file links: every occurrence of
     `(./note.md#<anchor>)` becomes `(#<anchor>)` (same-page anchor inside Notion).
   - Concatenate with a divider:
     ```markdown
     <summary contents>

     ---

     # 詳細ノート (Detailed Notes)
     <note contents>
     ```
     For English-language recaps the detailed-note heading is just `# Detailed Notes`.

3. **Convert markdown to Notion blocks**: pass the merged markdown through whatever
   markdown-to-Notion conversion notion-cli accepts via `blocks append`. Block JSON
   should preserve heading levels, lists, code blocks, and inline links (anchor
   `#x` links → Notion block links to the matching heading).

4. **Compute properties** (Notion DB row schema):

   ```json
   {
     "Title":        { "title":     [{ "type": "text", "text": { "content": "<YYYY-MM-DD> <slug> <short_id>" } }] },
     "Date":         { "date":      { "start": "<started_at>" } },
     "Session ID":   { "rich_text": [{ "type": "text", "text": { "content": "<session_id>" } }] },
     "Slug":         { "rich_text": [{ "type": "text", "text": { "content": "<slug>" } }] },
     "CWD":          { "rich_text": [{ "type": "text", "text": { "content": "<cwd>" } }] },
     "Duration":     { "rich_text": [{ "type": "text", "text": { "content": "<formatted from duration_seconds, e.g. 1h 23m>" } }] },
     "Total Events": { "number":    <total_events> },
     "Language":     { "select":    { "name": "<language>" } }
   }
   ```

5. **Look up an existing page** keyed by `Session ID`:
   ```bash
   $NOTION db query <database-id> --format json \
     --filter '{"property":"Session ID","rich_text":{"equals":"<session_id>"}}'
   ```
   - If `results[]` non-empty → take `results[0].id` as the existing page id; status =
     `"updated"`.
   - Else → status = `"created"`.

6. **Apply the upsert**:

   - **created**: `$NOTION page create --parent-db <database-id> --title "<title>" --stdin` with
     stdin JSON `{ "properties": { ... }, "children": [<merged blocks>] }`.
   - **updated**:
     1. `$NOTION blocks list <existing-page-id> --format json` → collect every
        top-level block id.
     2. For each block id, `$NOTION blocks delete <block-id> --yes` (Notion's
        delete is reversible from trash; we do this to clear stale content before
        re-appending).
     3. `$NOTION blocks append <existing-page-id>` with the merged blocks JSON.
     4. `$NOTION page update <existing-page-id>` with stdin
        `{ "properties": { ... } }` to refresh metadata.

7. **Append a manifest entry** on success:

   ```jsonl
   {"target": "notion", "session_id": "<session_id>", "local_dir": "<absolute path>", "target_id": "<page-id>", "target_url": "<page-url>", "uploaded_at": "<now ISO-8601>", "status": "created"|"updated"}
   ```

   Append to `~/.claude/session-recaps/.manifest.jsonl` (create file if missing).

8. **Report** one line in UI language:
   `[recap-to-notion] uploaded <slug or short_id> → <page-url> (created|updated)`

### Failure handling

- **notion-cli error / network / 401 / 403 / 429 / oversized block / etc.**: keep
  local files intact, do **not** append to manifest, surface a one-line UI-language
  error including the cause. The next invocation's Phase B0 will retry. Do not
  retry inside the same invocation.
- **`object_not_found` from notion-cli during Phase B/B0**: clear
  `.notion-config.json.database_id` and re-run Phase A once. If Phase A succeeds,
  retry the failed step. If the second attempt also fails, surface the error and
  stop — manual intervention required.
- **`.notion-config.json` parse error**: rename to
  `.notion-config.json.bak.<unix-ts>` and re-run Phase A.
- **`~/.notion-cli/lib/notion.ts` missing** (notion-cli workspace not bootstrapped):
  surface a one-line UI-language message instructing the user to run notion-cli's
  `setup.ts` (see notion-cli SKILL.md "First-time setup"). Exit without modifying any
  local state. The user runs setup, then re-invokes recap-to-notion.
- **`db create` not available** (older notion-cli that pre-dates the subcommand):
  handled in Phase A (instruct manual DB creation, exit cleanly).
- **No Notion token resolved** (none of `NOTION_TOKEN` / `NOTION_API_KEY` /
  `NOTION_TOKEN_FILE` set): notion-cli emits a `missing_token` JSON error. Surface
  it and exit cleanly without modifying state. User exports a token and re-invokes.

### Retrospective

After Phase B (or Phase B0 with no pending) returns:

1. Consider: were there mid-session corrections? Did Phase A loop multiple times? Did
   any pending upload fail repeatedly? Were any properties mismapped (e.g. Notion
   schema drift)?
2. Ask the user (UI language): 「今回のNotion同期のフィードバック (1-5の評価、気になった点、または何もなければEnter)」 / English equivalent.
3. If feedback OR corrections occurred:
   a. Create `feedback/` next to this SKILL.md if missing.
   b. Read or create `feedback/log.md` with the standard header.
   c. Prepend a new entry:

      ```markdown
      ## <ISO-8601 timestamp>
      - **Skill Version**: <version from this file's frontmatter>
      - **Task**: <upload mode | retry mode, dir or "—">
      - **Outcome**: success | partial-success | failure | error
      - **Rating**: <N>/5 (or "—")
      - **Corrections**: <session corrections, or "none">
      - **Issues**: <issues, or "none">
      - **User Note**: <verbatim, or "—">
      ---
      ```

4. Skip recording if the user passes AND no corrections/issues occurred.

## Behavior Scenarios

```gherkin
Scenario: Auto-invoked from session-recap chain after generation
  Given session-recap has just written summary.md, note.md, meta.json to a recap dir
  When session-recap dispatches the chain with that dir as args
  Then this skill runs Phase A (resolve target) → B0 (retry pending) → B (upsert
       the new dir) and appends a manifest entry on success.

Scenario: Standalone — pass a recap directory path
  Given the user invokes /recap-to-notion with an absolute recap dir path
  When the skill starts
  Then Phase A → B0 → B run for that dir.

Scenario: Standalone — retry-only mode (no dir argument)
  Given the user invokes /recap-to-notion with no arguments or says "recap retry"
  When the skill starts
  Then Phase A → B0 run, attempting to upload any dir without a notion manifest entry.

Scenario: First-run — auto-create Session Recaps DB under My Agent Notes
  Given .notion-config.json is missing
  And My Agent Notes page exists and is shared with the integration
  And Session Recaps DB does not exist yet
  When Phase A runs
  Then notion-cli db create produces the DB with the documented schema and saves
       the new DB id to .notion-config.json — no AskUserQuestion prompt.

Scenario: First-run — discover existing DB and adopt it
  Given .notion-config.json is missing
  And Session Recaps DB already exists under My Agent Notes
  When Phase A runs
  Then the existing DB id is saved to .notion-config.json without modification.

Scenario: First-run — My Agent Notes page is missing → notify user, skip sync
  Given My Agent Notes page does not exist or is not shared with the integration
  When Phase A runs
  Then the skill emits a UI-language instruction to create / share the page and exits
       without writing .notion-config.json. Local recap files are untouched.

Scenario: notion-cli has no `db create` → notify user, skip sync
  Given notion-cli is installed but the version lacks `db create`
  And Session Recaps DB does not exist
  When Phase A reaches the create step
  Then the skill instructs the user to either upgrade notion-cli or create the DB
       manually with the documented schema, and exits cleanly.

Scenario: Stale DB ID → object_not_found triggers automatic Phase A re-resolution
  Given .notion-config.json points to a database that has been deleted or moved
  When Phase B encounters object_not_found
  Then the skill clears database_id and re-runs Phase A once before retrying.

Scenario: Idempotent re-upload → updates existing page, no duplicates
  Given a recap dir whose Session ID already has a row in the DB
  When Phase B runs
  Then the existing page is updated (blocks cleared and re-appended, properties
       refreshed) and the manifest entry has status: "updated".

Scenario: Notion upsert failure → keep local, manifest not updated
  Given Phase B fails (network, 4xx, 5xx, oversized block, etc.)
  When the skill handles the error
  Then local recap files are kept intact, .manifest.jsonl is not appended to, and
       a one-line UI-language error is surfaced.

Scenario: Next invocation Phase B0 picks up previously failed uploads
  Given a previous invocation left a recap dir without a notion manifest entry
  When this skill runs Phase B0
  Then the missing dir is re-attempted and, on success, the manifest entry is appended.

Scenario: Oversized block in markdown → upsert fails with clear error, no manifest entry
  Given a code block in note.md exceeds the Notion 2000-char-per-block limit
  When notion-cli blocks append rejects the request
  Then the skill surfaces the cause in UI language and does not append a manifest
       entry. The user is advised to shorten the markdown and re-invoke.

Scenario: notion-cli workspace not bootstrapped → skip sync, leave local intact
  Given ~/.notion-cli/lib/notion.ts does not exist (setup.ts has never been run)
  When the skill starts
  Then it emits a UI-language one-line message pointing the user at notion-cli's
       setup.ts and exits without modifying any local state.

Scenario: No Notion token resolved → skip sync, leave local intact
  Given none of NOTION_TOKEN / NOTION_API_KEY / NOTION_TOKEN_FILE is set
  When notion-cli returns a missing_token JSON error from the first call
  Then the skill surfaces the error in UI language and exits without modifying state.
```

## Notes and constraints

- **Fixed target**: the database title (`Session Recaps`) and parent page title
  (`My Agent Notes`) are not configurable. Renaming or relocating them in Notion
  triggers Phase A re-resolution; if either is missing, sync is skipped (local files
  untouched).
- **Manifest schema is owned by session-recap.** This skill only appends. Format:
  ```jsonl
  {"target": "notion", "session_id": "<uuid>", "local_dir": "<absolute path>", "target_id": "<page id>", "target_url": "<url>", "uploaded_at": "<ISO-8601 with time>", "status": "created"|"updated"}
  ```
- **No retention / cleanup here.** That responsibility lives in session-recap. This
  skill never deletes anything from `~/.claude/session-recaps/`.
- **No silent overwrite of Notion DB**: notion-cli's `db create` already refuses to
  recreate a same-titled DB under the same parent; this skill never bypasses that.
- **Page size**: Notion practical page limits are very high; the only realistic failure
  mode is a single block exceeding the per-block character cap (~2000 chars). Such a
  failure is surfaced verbatim and the user shortens the markdown manually. v1.0.0
  does not auto-chunk.
- **Dependency**: `notion-cli >= 1.1.0`, with the workspace bootstrapped at
  `~/.notion-cli/` (run notion-cli's `setup.ts` once). All subcommands are invoked via
  `deno run` against `~/.notion-cli/lib/notion.ts`, never as a `notion-cli` shell
  binary (which does not exist).
- **Read access to recap dir**: this skill reads `summary.md`, `note.md`, `meta.json`.
  It never modifies them.
