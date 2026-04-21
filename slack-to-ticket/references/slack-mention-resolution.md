# Slack Mention Resolution

Slack message text often contains placeholder syntax that is not human-readable. Before composing a Jira ticket (or any human-facing document) from fetched Slack messages, resolve all placeholders to real names and handles. Never let raw IDs like `<@U04EURM2DPT>` or `<!subteam^S0769EQKP5E>` land in a ticket description.

## What to look for

Scan every message body returned by `slack-cli history`, `slack-cli search`, or any other fetch for these patterns:

| Placeholder | Meaning |
|-------------|---------|
| `<@UXXXXXXX>` | User mention |
| `<#CXXXXXXX>` or `<#CXXXXXXX\|channel-name>` | Channel mention |
| `<!subteam^SXXXXXXX>` or `<!subteam^SXXXXXXX\|@handle>` | User-group mention |
| `<!here>` / `<!channel>` / `<!everyone>` | Broadcast mention |
| `<https://...>` or `<https://...\|label>` | URL (sometimes with display label) |

## Resolution rules

### `<@UXXXXXXX>` — user

```bash
slack-cli users info -u UXXXXXXX --format json
```

Use fields in this priority: `display_name` → `real_name` → `name`. Render as the bare display name (e.g., `Makihara`), not `@<handle>`, because the ticket description convention is to use display names.

### `<#CXXXXXXX>` or `<#CXXXXXXX|channel-name>` — channel

```bash
slack-cli channel info -c CXXXXXXX --format json
```

Use the `name` field and render as `#<name>` (e.g., `#store-operation`). If the placeholder already carries `|channel-name`, that value is a Slack-cached label — it is usually correct but can go stale after a channel rename. Re-resolve via the API when accuracy matters.

### `<!subteam^SXXXXXXX>` or `<!subteam^SXXXXXXX|@handle>` — user group

`slack-cli` with a standard bot token does **not** expose user-group lookups (`usergroups.list` requires a user token or `usergroups:read` scope that bots typically lack). Strategy:

1. If the placeholder contains `|@handle`, use that handle directly.
2. Otherwise, ask the user: "The thread mentions user group `SXXXXXXX`. What is its handle (e.g., `@biz-cx-team`)?" Cache the answer and reuse it throughout the draft.

When rendering in the ticket, show both the handle and the Slack ID on first mention so the implementer can wire the mention without re-discovery:

```
`@biz-cx-team` user group (Slack ID `S0769EQKP5E`)
```

Subsequent mentions can be just `@biz-cx-team`.

### `<!here>` / `<!channel>` / `<!everyone>` — broadcast

Render literally as `@here`, `@channel`, `@everyone`. No API lookup needed.

### `<https://...>` or `<https://...|label>` — URL

Strip the angle brackets. If `|label` is present, render as a markdown link: `[label](url)`. Otherwise render the URL bare.

## Batch resolution

For a thread with many mentions, do NOT resolve inside a loop. Collect every unique `UXXX` / `CXXX` first, then run one lookup per unique ID. This avoids burning API calls on duplicates and keeps the run fast.

Pseudo-flow:

```
1. Regex-scan all message texts for <@U...>, <#C...>, <!subteam^S...>
2. Deduplicate IDs into a set
3. For each user ID: slack-cli users info → cache display_name
4. For each channel ID: slack-cli channel info → cache #name
5. For each subteam ID: use |handle if present; else prompt user once; cache
6. Replace all placeholders in message bodies in a single pass
```

## Output-shape checklist

Before handing the resolved text off to the drafting phase, verify:

- No `<@U...>`, `<#C...>`, or `<!subteam^S...>` remain in the text.
- User mentions are bare display names (`Makihara`), not `@handle`.
- Channel mentions are `#name` format.
- User-group first-mention includes both handle and Slack ID.
- Broadcast mentions are `@here` / `@channel` / `@everyone`.
- URLs are either bare or markdown links — never angle-bracketed.

If any placeholder still remains after resolution, stop and surface the unresolved ID to the user rather than letting it flow into the ticket.
