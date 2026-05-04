# Database query filters and sorts

Notion's `databases.query` endpoint takes optional `filter` and `sorts` payloads. These are passed to the CLI as JSON strings via `--filter '<json>'` and `--sorts '<json>'`.

For exhaustive coverage see <https://developers.notion.com/reference/post-database-query-filter>.

## Single-property filters

A filter is a property condition: `{ "property": "<name>", "<type>": { "<operator>": <value> } }`.

The `<type>` key MUST match the property's type from `db get`. Status, select, and multi-select all look similar but are not interchangeable.

### Common operators by type

| Type | Operators |
|---|---|
| `title` / `rich_text` | `equals`, `does_not_equal`, `contains`, `does_not_contain`, `starts_with`, `ends_with`, `is_empty`, `is_not_empty` |
| `number` | `equals`, `does_not_equal`, `greater_than`, `less_than`, `greater_than_or_equal_to`, `less_than_or_equal_to`, `is_empty`, `is_not_empty` |
| `checkbox` | `equals`, `does_not_equal` |
| `select` / `status` | `equals`, `does_not_equal`, `is_empty`, `is_not_empty` |
| `multi_select` | `contains`, `does_not_contain`, `is_empty`, `is_not_empty` |
| `date` | `equals`, `before`, `after`, `on_or_before`, `on_or_after`, `past_week`, `past_month`, `past_year`, `next_week`, `next_month`, `next_year`, `this_week`, `is_empty`, `is_not_empty` |
| `people` / `relation` | `contains`, `does_not_contain`, `is_empty`, `is_not_empty` |
| `formula` | nested: `{ "formula": { "string": { "equals": "..." } } }`, also `number`, `checkbox`, `date` |

### Examples

Status equals:
```json
{ "property": "Status", "status": { "equals": "Done" } }
```

Title contains:
```json
{ "property": "Name", "title": { "contains": "OKR" } }
```

Number greater than:
```json
{ "property": "Estimate", "number": { "greater_than": 5 } }
```

Multi-select contains:
```json
{ "property": "Tags", "multi_select": { "contains": "p1" } }
```

Date next week:
```json
{ "property": "Due", "date": { "next_week": {} } }
```

Date on/after a specific day (ISO 8601):
```json
{ "property": "Due", "date": { "on_or_after": "2026-05-01" } }
```

Person contains:
```json
{ "property": "Owner", "people": { "contains": "<user-id>" } }
```

Empty / not empty (note the `true` value):
```json
{ "property": "Notes", "rich_text": { "is_empty": true } }
```

## Compound filters

Combine with `and` / `or`. Each takes an array of conditions, which can themselves be compound (nested up to 2 levels).

```json
{
  "and": [
    { "property": "Status", "status": { "equals": "In progress" } },
    { "property": "Due", "date": { "on_or_before": "2026-05-31" } }
  ]
}
```

Mixed:
```json
{
  "and": [
    { "property": "Status", "status": { "does_not_equal": "Done" } },
    {
      "or": [
        { "property": "Priority", "select": { "equals": "P0" } },
        { "property": "Priority", "select": { "equals": "P1" } }
      ]
    }
  ]
}
```

CLI:
```sh
deno run <perms> ~/.notion-cli/lib/notion.ts db query <db-id> --filter '{
  "and": [
    {"property":"Status","status":{"does_not_equal":"Done"}},
    {"or":[
      {"property":"Priority","select":{"equals":"P0"}},
      {"property":"Priority","select":{"equals":"P1"}}
    ]}
  ]
}'
```

## Sorts

`sorts` is an array of `{ property | timestamp, direction }` items applied in order.

By a property:
```json
[{ "property": "Due", "direction": "ascending" }]
```

By a timestamp (no `property` key):
```json
[{ "timestamp": "last_edited_time", "direction": "descending" }]
```

Multiple keys (priority then due date):
```json
[
  { "property": "Priority", "direction": "ascending" },
  { "property": "Due",      "direction": "ascending" }
]
```

CLI:
```sh
deno run <perms> ~/.notion-cli/lib/notion.ts db query <db-id> \
  --sorts '[{"property":"Due","direction":"ascending"}]'
```

## Pagination

Notion's max `page_size` is 100 (the default the CLI uses). When the returned object has `has_more: true`, capture `next_cursor` and pass it back:

```sh
deno run <perms> ~/.notion-cli/lib/notion.ts db query <db-id> \
  --filter '<json>' --start-cursor <cursor>
```

Repeat until `has_more` is false. For most ad-hoc queries, prefer narrowing with a filter to avoid pagination loops.

## Common mistakes

- **Wrong type key.** A property whose type is `select` will reject `{ "status": {...} }` and vice-versa. Always confirm with `db get`.
- **Status values invented client-side.** Status options are defined per-database; an unknown name silently returns no rows (it doesn't error).
- **`equals` on multi-select.** Multi-select uses `contains`, not `equals`.
- **Stale property names after a rename.** Run `db get` again — the API uses the current name.
- **Date string format.** Use ISO 8601. `2026-05-01` is fine; `5/1/2026` is not.
