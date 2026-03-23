# Input Parsing Reference

## Slack Permalink URL (Primary Input Mode)

### URL Patterns

**Standard message permalink:**
```
https://<workspace>.slack.com/archives/<channel_id>/p<timestamp_no_dot>
```
Example: `https://myteam.slack.com/archives/C0123ABCDEF/p1711234567890123`

**Thread permalink (message within a thread):**
```
https://<workspace>.slack.com/archives/<channel_id>/p<timestamp_no_dot>?thread_ts=<thread_ts_no_dot>&cid=<channel_id>
```
Example: `https://myteam.slack.com/archives/C0123ABCDEF/p1711234567890123?thread_ts=1711200000000000&cid=C0123ABCDEF`

### Extracting Channel ID and Thread TS

1. **Channel ID**: The segment after `/archives/` — starts with `C` (public), `G` (private), or `D` (DM)
2. **Timestamp**: The `p` prefix is removed, then insert a dot before the last 6 digits
   - URL: `p1711234567890123` → TS: `1711234567.890123`
3. **Thread TS**: If `thread_ts` query param exists, use it (same dot conversion). Otherwise use the message TS as the thread root.

### Parsing Logic (pseudocode)

```
input = user's URL or text

if input matches https://*.slack.com/archives/<channel>/p<ts>:
    channel_id = extract <channel>
    raw_ts = extract <ts> (digits after 'p')
    message_ts = raw_ts[0:-6] + "." + raw_ts[-6:]

    if URL has ?thread_ts=<thread_ts>:
        thread_ts = thread_ts[0:-6] + "." + thread_ts[-6:]
    else:
        thread_ts = message_ts  # treat message as thread root

    → fetch: slack-cli history -c <channel_id> --thread <thread_ts> --with-link --format json
```

## Channel Name Input (Fallback Mode B)

When user provides `#channel-name` or just `channel-name`:
- Strip leading `#` if present
- Fetch recent messages: `slack-cli history -c <channel-name> -n 30 --with-link --format json`
- Present messages and ask user to confirm scope or narrow down

## Search Query Input (Fallback Mode C)

When user provides a search query:
- Pass directly to: `slack-cli search -q "<query>" --format json`
- Supports Slack search modifiers: `in:channel`, `from:@user`, `has:link`, `before:date`, `after:date`
- Present grouped results for user to select relevant messages

## Channel + Date Range Input (Fallback Mode D)

When user specifies a channel with a date:
- Fetch: `slack-cli history -c <channel-name> --since "<ISO-date>" --with-link --format json`
- ISO date format: `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS`

## Input Detection Heuristic

| Input contains... | Mode |
|-------------------|------|
| `slack.com/archives/` | A — Permalink URL |
| `#channel` or channel name without URL | B — Channel name |
| `search` keyword + quoted text | C — Search query |
| Channel name + date/time reference | D — Channel + date range |
