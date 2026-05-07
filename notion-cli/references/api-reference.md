# API reference — example invocations

All examples assume preflight has succeeded and the workspace is at `~/.notion-cli/`.

The base permission set is:

```
--allow-env=NOTION_TOKEN,NOTION_API_KEY,NOTION_TOKEN_FILE --allow-net=api.notion.com --allow-read=$HOME/.notion-cli --allow-write=$HOME/.notion-cli
```

When the token source is `NOTION_TOKEN_FILE` (route (c) of the auth flow — agenix, sops-nix, 1Password CLI mounts, etc.), append exactly that one extra path:

```
--allow-read=$NOTION_TOKEN_FILE
```

Below the full permission set is abbreviated as `<perms>`.

## Auth / smoke test

```sh
deno run <perms> ~/.notion-cli/lib/notion.ts auth
```

Output (JSON): bot user object including `bot.workspace_name`. Use this any time you suspect a token problem.

## Search

```sh
# Free-text search across pages and databases
deno run <perms> ~/.notion-cli/lib/notion.ts search "weekly review"

# Limit to databases
deno run <perms> ~/.notion-cli/lib/notion.ts search --filter databases

# Limit to pages, return at most 10 results
deno run <perms> ~/.notion-cli/lib/notion.ts search "OKR" --filter pages --limit 10

# Compact text output (1 line per result)
deno run <perms> ~/.notion-cli/lib/notion.ts search --format text
```

Notes:

- The Notion `/search` endpoint sorts by `last_edited_time` descending and only filters by `object: page|database`. For property-level filtering, use `db query`.
- An empty result list means no matching item is shared with the integration. The query syntax does not support `AND`/`OR` — it's a substring match.

## Pages

### Get a page

```sh
deno run <perms> ~/.notion-cli/lib/notion.ts page get <page-id>

# Also fetch the top-level child blocks
deno run <perms> ~/.notion-cli/lib/notion.ts page get <page-id> --with-blocks
```

To recurse into nested blocks, take the returned block ids and call `blocks list` on each block whose `has_children` is true.

### Create a page in a database

```sh
deno run <perms> ~/.notion-cli/lib/notion.ts page create \
  --parent-db <database-id> \
  --title "Q1 Plan"
```

For databases, the title goes into the database's **title-typed property** (most often called `Name`). The CLI auto-detects the title property from the database's schema. To set additional properties at create time, pipe a JSON `properties` object via `--stdin`:

```sh
echo '{
  "properties": {
    "Status": { "status": { "name": "In progress" } },
    "Priority": { "select": { "name": "High" } },
    "Due": { "date": { "start": "2026-06-01" } }
  }
}' | deno run <perms> ~/.notion-cli/lib/notion.ts page create \
       --parent-db <database-id> --title "Q1 Plan" --stdin
```

### Create a sub-page under another page

```sh
deno run <perms> ~/.notion-cli/lib/notion.ts page create \
  --parent-page <page-id> \
  --title "Sub-page"
```

Pages under page parents have a single `title` property (no schema), so only `--title` matters. Body content is set via `--stdin` with a `children` array of blocks (see `property-types.md`).

### Update page properties

```sh
echo '{
  "properties": {
    "Status": { "status": { "name": "Done" } }
  }
}' | deno run <perms> ~/.notion-cli/lib/notion.ts page update <page-id>
```

### Archive a page (soft delete — confirm first)

```sh
deno run <perms> ~/.notion-cli/lib/notion.ts page archive <page-id>
```

Reversible from the Notion trash for 30 days, then permanent.

## Databases

### Retrieve schema (use this to discover property names)

```sh
deno run <perms> ~/.notion-cli/lib/notion.ts db get <database-id>
```

The `properties` map shows each property's name and type — what to reference when constructing filters or update bodies.

### Query rows

```sh
# All rows
deno run <perms> ~/.notion-cli/lib/notion.ts db query <database-id>

# Filter: Status = "Done"
deno run <perms> ~/.notion-cli/lib/notion.ts db query <database-id> \
  --filter '{"property":"Status","status":{"equals":"Done"}}'

# Filter + sort
deno run <perms> ~/.notion-cli/lib/notion.ts db query <database-id> \
  --filter '{"property":"Status","status":{"equals":"In progress"}}' \
  --sorts '[{"property":"Due","direction":"ascending"}]'

# Cap at 25 rows
deno run <perms> ~/.notion-cli/lib/notion.ts db query <database-id> --limit 25
```

`page_size` is capped at 100 by Notion. The CLI passes through `next_cursor` in JSON output; pagination across pages is the caller's job (or run again with `--start-cursor <cursor>`).

See `filters.md` for the full filter grammar (compound `and`/`or`, all property types).

### Create a new database under a parent page

The integration must already be connected to the parent page. The schema must include at least one property of type `title`.

```sh
# Minimal: only a title property (default schema if --schema-stdin is omitted)
deno run <perms> ~/.notion-cli/lib/notion.ts db create \
  --parent-page <page-id> \
  --name "My DB"

# Custom schema via stdin
cat <<'JSON' | deno run <perms> ~/.notion-cli/lib/notion.ts db create \
  --parent-page <page-id> \
  --name "Session Recaps" \
  --description "Auto-generated recaps from Claude Code sessions" \
  --schema-stdin
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

Returns the full database object on success (use `--format text` for a one-line summary). The CLI refuses to silently overwrite: if a same-titled database already lives under the same parent, it fails with the existing database id so the caller can decide whether to use that one instead.

## Blocks

### List top-level children of a page or block

```sh
deno run <perms> ~/.notion-cli/lib/notion.ts blocks list <page-id-or-block-id>
deno run <perms> ~/.notion-cli/lib/notion.ts blocks list <id> --limit 25
```

To walk the full tree, recurse on each child whose `has_children` is true.

### Append blocks (stdin: JSON array)

```sh
echo '[
  {
    "object": "block",
    "type": "heading_2",
    "heading_2": { "rich_text": [{ "type": "text", "text": { "content": "Notes" } }] }
  },
  {
    "object": "block",
    "type": "paragraph",
    "paragraph": { "rich_text": [{ "type": "text", "text": { "content": "Body text." } }] }
  }
]' | deno run <perms> ~/.notion-cli/lib/notion.ts blocks append <page-id>
```

See `property-types.md` for block shapes (paragraph, headings, lists, callout, quote, code, divider, to-do, toggle, table-of-contents, embed, image-by-url, etc.).

### Delete a block (confirm first)

```sh
deno run <perms> ~/.notion-cli/lib/notion.ts blocks delete <block-id>
```

## Users

```sh
# Same as `auth` — current bot user
deno run <perms> ~/.notion-cli/lib/notion.ts users me

# List workspace users
deno run <perms> ~/.notion-cli/lib/notion.ts users list

# Get a single user
deno run <perms> ~/.notion-cli/lib/notion.ts users get <user-id>
```

`users list` returns members of the workspace (people, bots, groups) only if the integration's "Read user information" capability is enabled.

## Output formats

| Flag | Output |
|---|---|
| (default) | Pretty-printed JSON. Best for piping into `jq` or saving for later. |
| `--format text` | One-line-per-item compact format with title, id, and url. |

Examples of `--format text`:

```
page  <id>  Q1 Plan                       https://notion.so/...
db    <id>  Tasks                         https://notion.so/...
user  <id>  Hideki Koike (person)
block <id>  paragraph
              Body text here
```

## Pipelines

The CLI is jq-friendly. Examples:

```sh
# IDs of all "In progress" tasks
deno run <perms> ~/.notion-cli/lib/notion.ts db query <db> \
  --filter '{"property":"Status","status":{"equals":"In progress"}}' \
  | jq -r '.results[].id'

# Update each "Done" task with archived = true (loop in shell)
deno run <perms> ~/.notion-cli/lib/notion.ts db query <db> \
  --filter '{"property":"Status","status":{"equals":"Archive me"}}' \
  | jq -r '.results[].id' \
  | while read -r id; do
      deno run <perms> ~/.notion-cli/lib/notion.ts page archive "$id"
    done
```

For destructive bulk loops like the second example, ALWAYS dry-run with `db query` first, present the count to the user, and confirm before piping to `page archive`.
