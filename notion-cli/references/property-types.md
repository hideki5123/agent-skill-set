# Property and block JSON shapes

Quick reference for the most common Notion property values (used in `page create` / `page update`) and block shapes (used in `blocks append`).

For the canonical, exhaustive list see <https://developers.notion.com/reference/page-property-values> and <https://developers.notion.com/reference/block>.

## Property values

### title (the page title in a database row)

```json
{ "Name": { "title": [{ "type": "text", "text": { "content": "Hello" } }] } }
```

For pages whose parent is another page (not a database), use the special key `title`:

```json
{ "title": [{ "type": "text", "text": { "content": "Sub-page" } }] }
```

### rich_text

```json
{ "Notes": { "rich_text": [{ "type": "text", "text": { "content": "free-form notes" } }] } }
```

Annotations (bold, italic, color) live under `annotations`:

```json
{
  "Notes": {
    "rich_text": [
      { "type": "text", "text": { "content": "important" }, "annotations": { "bold": true, "color": "red" } }
    ]
  }
}
```

### number

```json
{ "Estimate": { "number": 3.5 } }
```

### select

```json
{ "Priority": { "select": { "name": "High" } } }
```

(Notion auto-creates the option if it doesn't exist; respect the database's existing palette where possible.)

### multi_select

```json
{ "Tags": { "multi_select": [{ "name": "infra" }, { "name": "p1" }] } }
```

### status

```json
{ "Status": { "status": { "name": "In progress" } } }
```

Status values are predefined per database — you can't invent new ones via API. Use `db get` first to see allowed values.

### date

```json
{ "Due": { "date": { "start": "2026-06-01" } } }
```

With end date:

```json
{ "Sprint": { "date": { "start": "2026-06-01", "end": "2026-06-14" } } }
```

With time:

```json
{ "Meeting": { "date": { "start": "2026-06-01T10:00:00.000-07:00" } } }
```

### checkbox

```json
{ "Done": { "checkbox": true } }
```

### url / email / phone_number

```json
{ "Link": { "url": "https://example.com" } }
{ "Contact": { "email": "person@example.com" } }
{ "Phone": { "phone_number": "+1-555-0100" } }
```

### people

```json
{ "Owner": { "people": [{ "id": "<user-id>" }] } }
```

### relation

```json
{ "Project": { "relation": [{ "id": "<related-page-id>" }] } }
```

The related database must be shared with the integration too.

### files (read-only on most plans)

Reading works; writing files via API typically fails on free workspaces. For external URLs:

```json
{ "Attachments": { "files": [{ "name": "doc", "external": { "url": "https://..." } }] } }
```

## Block shapes

All blocks share the envelope:

```json
{ "object": "block", "type": "<type>", "<type>": { ... } }
```

### paragraph

```json
{ "object": "block", "type": "paragraph",
  "paragraph": { "rich_text": [{ "type": "text", "text": { "content": "hello" } }] } }
```

### heading_1 / heading_2 / heading_3

```json
{ "object": "block", "type": "heading_2",
  "heading_2": { "rich_text": [{ "type": "text", "text": { "content": "Section" } }] } }
```

Add `"is_toggleable": true` inside `heading_2` to make it toggleable.

### bulleted_list_item / numbered_list_item

```json
{ "object": "block", "type": "bulleted_list_item",
  "bulleted_list_item": { "rich_text": [{ "type": "text", "text": { "content": "item" } }] } }
```

### to_do

```json
{ "object": "block", "type": "to_do",
  "to_do": { "rich_text": [{ "type": "text", "text": { "content": "task" } }], "checked": false } }
```

### toggle

```json
{ "object": "block", "type": "toggle",
  "toggle": {
    "rich_text": [{ "type": "text", "text": { "content": "Click to expand" } }],
    "children": [
      { "object": "block", "type": "paragraph",
        "paragraph": { "rich_text": [{ "type": "text", "text": { "content": "hidden" } }] } }
    ]
  } }
```

### code

```json
{ "object": "block", "type": "code",
  "code": {
    "rich_text": [{ "type": "text", "text": { "content": "console.log('hi')" } }],
    "language": "typescript"
  } }
```

Allowed `language` values are an enum — see Notion docs for the full list (typescript, javascript, python, json, plain text, etc.).

### quote

```json
{ "object": "block", "type": "quote",
  "quote": { "rich_text": [{ "type": "text", "text": { "content": "Quoted text" } }] } }
```

### callout

```json
{ "object": "block", "type": "callout",
  "callout": {
    "rich_text": [{ "type": "text", "text": { "content": "Heads up" } }],
    "icon": { "type": "emoji", "emoji": "💡" },
    "color": "yellow_background"
  } }
```

### divider

```json
{ "object": "block", "type": "divider", "divider": {} }
```

### bookmark / embed

```json
{ "object": "block", "type": "bookmark",
  "bookmark": { "url": "https://example.com" } }

{ "object": "block", "type": "embed",
  "embed": { "url": "https://example.com" } }
```

### image / video / file (external URL)

```json
{ "object": "block", "type": "image",
  "image": { "type": "external", "external": { "url": "https://..." } } }
```

### table_of_contents

```json
{ "object": "block", "type": "table_of_contents", "table_of_contents": { "color": "default" } }
```

### child_page (read-only)

Returned by `blocks list` for sub-pages; cannot be created via `blocks append` (use `page create` with `--parent-page` instead).

## Tips

- **Rich text is always an array.** Even a single string becomes `[{ "type": "text", "text": { "content": "..." } }]`.
- **Length limits**: a single rich-text content string is 2000 chars. Split long text across multiple rich-text entries in the same array (or across multiple blocks).
- **Nested children**: most container blocks (`toggle`, `quote`, `callout`, `column_list`, `table`) accept a `children` array at create time. After creation, append more via `blocks append <parent-block-id>`.
- **Discover before writing.** If unsure of property names or types, run `db get <id>` first and copy the names verbatim — they are case-sensitive.
