# Slack CLI Command Reference

Exhaustive flag and option reference for all `slack-cli` subcommands.

## config set

Configure a profile's Slack Bot Token.

```
slack-cli config set [options]
```

| Flag | Description |
|------|-------------|
| `--profile <name>` | Profile name (default: `default`) |
| `--token-stdin` | Read token from stdin instead of interactive prompt |

Token is encrypted with AES-256-GCM before storage.

## config profiles

List all configured profiles.

```
slack-cli config profiles
```

No flags.

## config use

Set the default active profile.

```
slack-cli config use <name>
```

| Flag | Description |
|------|-------------|
| `name` | Profile name to activate (positional, required) |

## config current

Show the currently active profile name.

```
slack-cli config current
```

No flags.

## config get

Show configuration details for a profile.

```
slack-cli config get [options]
```

| Flag | Description |
|------|-------------|
| `--profile <name>` | Profile to inspect (default: active profile) |

## config clear

Remove a profile and its stored token.

```
slack-cli config clear [options]
```

| Flag | Description |
|------|-------------|
| `--profile <name>` | Profile to remove (required) |

---

## send

Send a message to a channel, thread, or user.

```
slack-cli send [options]
```

| Flag | Description |
|------|-------------|
| `-c, --channel <name>` | Channel name or ID |
| `-m, --message <text>` | Message text (supports `\n` for newlines) |
| `-f, --file <path>` | Read message body from a file |
| `--thread <ts>` | Reply to a thread (message timestamp) |
| `--user <@username>` | Send DM by username (e.g. `@alice`) |
| `--email <address>` | Send DM by email address |
| `--at <ISO8601>` | Schedule message at absolute time |
| `--after <minutes>` | Schedule message N minutes from now |
| `--profile <name>` | Use a specific workspace profile |
| `--format <type>` | Output format: `table`, `simple`, `json` |

One of `-c`/`--user`/`--email` is required.
One of `-m`/`-f` is required.

## edit

Edit an existing message.

```
slack-cli edit [options]
```

| Flag | Description |
|------|-------------|
| `-c, --channel <name>` | Channel name or ID (required) |
| `--ts <timestamp>` | Message timestamp to edit (required) |
| `-m, --message <text>` | New message text (required) |
| `--profile <name>` | Workspace profile |

## delete

Delete a message.

```
slack-cli delete [options]
```

| Flag | Description |
|------|-------------|
| `-c, --channel <name>` | Channel name or ID (required) |
| `--ts <timestamp>` | Message timestamp to delete (required) |
| `--profile <name>` | Workspace profile |

---

## channels

List channels in the workspace.

```
slack-cli channels [options]
```

| Flag | Description |
|------|-------------|
| `--type <type>` | Channel type filter (e.g. `public`, `private`) |
| `--include-archived` | Include archived channels |
| `--limit <n>` | Maximum number of channels to return |
| `--format <type>` | Output format: `table`, `simple`, `json` |
| `--profile <name>` | Workspace profile |

## channel info

Show detailed information about a channel.

```
slack-cli channel info [options]
```

| Flag | Description |
|------|-------------|
| `-c, --channel <name>` | Channel name or ID (required) |
| `--format <type>` | Output format: `table`, `simple`, `json` |
| `--profile <name>` | Workspace profile |

## channel set-topic

Set a channel's topic.

```
slack-cli channel set-topic [options]
```

| Flag | Description |
|------|-------------|
| `-c, --channel <name>` | Channel name or ID (required) |
| `--topic <text>` | New topic text (required) |
| `--profile <name>` | Workspace profile |

## channel set-purpose

Set a channel's purpose.

```
slack-cli channel set-purpose [options]
```

| Flag | Description |
|------|-------------|
| `-c, --channel <name>` | Channel name or ID (required) |
| `--purpose <text>` | New purpose text (required) |
| `--profile <name>` | Workspace profile |

---

## history

Retrieve message history from a channel.

```
slack-cli history [options]
```

| Flag | Description |
|------|-------------|
| `-c, --channel <name>` | Channel name or ID (required) |
| `-n, --count <number>` | Number of messages to retrieve |
| `--since <date>` | Retrieve messages since this date (ISO 8601 or natural date) |
| `--thread <ts>` | Retrieve thread replies for a specific message |
| `--with-link` | Include permalink for each message |
| `--format <type>` | Output format: `table`, `simple`, `json` |
| `--profile <name>` | Workspace profile |

## unread

View unread messages across channels.

```
slack-cli unread [options]
```

| Flag | Description |
|------|-------------|
| `-c, --channel <name>` | Check unreads for a specific channel only |
| `--count-only` | Show only unread counts, not message content |
| `--mark-read` | Mark messages as read after displaying |
| `--limit <n>` | Maximum number of channels to check |
| `--format <type>` | Output format: `table`, `simple`, `json` |
| `--profile <name>` | Workspace profile |

## search

Search messages across the workspace.

```
slack-cli search [options]
```

| Flag | Description |
|------|-------------|
| `-q, --query <text>` | Search query (required). Supports Slack modifiers: `in:channel`, `from:@user`, `has:link`, `before:date`, `after:date` |
| `--sort <field>` | Sort field: `score` (default), `timestamp` |
| `--sort-dir <dir>` | Sort direction: `desc` (default), `asc` |
| `-n, --count <number>` | Number of results per page |
| `--page <number>` | Page number for pagination |
| `--format <type>` | Output format: `table`, `simple`, `json` |
| `--profile <name>` | Workspace profile |

---

## upload

Upload a file or code snippet to a channel.

```
slack-cli upload [options]
```

| Flag | Description |
|------|-------------|
| `-c, --channel <name>` | Channel name or ID (required) |
| `-f, --file <path>` | Local file path to upload |
| `--content <text>` | Text content to upload as a snippet |
| `--filename <name>` | Filename for the snippet (e.g. `hello.js`) |
| `--filetype <type>` | File type / syntax highlighting (e.g. `javascript`, `python`) |
| `-t, --thread <ts>` | Upload to a specific thread |
| `--profile <name>` | Workspace profile |

One of `-f`/`--content` is required.

---

## reaction add

Add an emoji reaction to a message.

```
slack-cli reaction add [options]
```

| Flag | Description |
|------|-------------|
| `-c, --channel <name>` | Channel name or ID (required) |
| `-t, --timestamp <ts>` | Message timestamp (required) |
| `-e, --emoji <name>` | Emoji name without colons (required, e.g. `thumbsup`) |
| `--profile <name>` | Workspace profile |

## reaction remove

Remove an emoji reaction from a message.

```
slack-cli reaction remove [options]
```

| Flag | Description |
|------|-------------|
| `-c, --channel <name>` | Channel name or ID (required) |
| `-t, --timestamp <ts>` | Message timestamp (required) |
| `-e, --emoji <name>` | Emoji name without colons (required) |
| `--profile <name>` | Workspace profile |

---

## pin add

Pin a message in a channel.

```
slack-cli pin add [options]
```

| Flag | Description |
|------|-------------|
| `-c, --channel <name>` | Channel name or ID (required) |
| `-t, --timestamp <ts>` | Message timestamp to pin (required) |
| `--profile <name>` | Workspace profile |

## pin remove

Unpin a message from a channel.

```
slack-cli pin remove [options]
```

| Flag | Description |
|------|-------------|
| `-c, --channel <name>` | Channel name or ID (required) |
| `-t, --timestamp <ts>` | Message timestamp to unpin (required) |
| `--profile <name>` | Workspace profile |

## pin list

List pinned messages in a channel.

```
slack-cli pin list [options]
```

| Flag | Description |
|------|-------------|
| `-c, --channel <name>` | Channel name or ID (required) |
| `--format <type>` | Output format: `table`, `simple`, `json` |
| `--profile <name>` | Workspace profile |

---

## users list

List workspace users.

```
slack-cli users list [options]
```

| Flag | Description |
|------|-------------|
| `--limit <n>` | Maximum number of users to return |
| `--format <type>` | Output format: `table`, `simple`, `json` |
| `--profile <name>` | Workspace profile |

## users info

Get detailed information about a user by ID.

```
slack-cli users info [options]
```

| Flag | Description |
|------|-------------|
| `--id <user_id>` | Slack user ID (required, e.g. `U01ABCDEF`) |
| `--format <type>` | Output format: `table`, `simple`, `json` |
| `--profile <name>` | Workspace profile |

## users lookup

Look up a user by email address.

```
slack-cli users lookup [options]
```

| Flag | Description |
|------|-------------|
| `--email <address>` | Email address to look up (required) |
| `--format <type>` | Output format: `table`, `simple`, `json` |
| `--profile <name>` | Workspace profile |

---

## scheduled list

List scheduled messages.

```
slack-cli scheduled list [options]
```

| Flag | Description |
|------|-------------|
| `-c, --channel <name>` | Filter by channel |
| `--limit <n>` | Maximum number of scheduled messages |
| `--format <type>` | Output format: `table`, `simple`, `json` |
| `--profile <name>` | Workspace profile |

## scheduled cancel

Cancel a scheduled message.

```
slack-cli scheduled cancel [options]
```

| Flag | Description |
|------|-------------|
| `-c, --channel <name>` | Channel name or ID (required) |
| `--id <message_id>` | Scheduled message ID (required) |
| `--profile <name>` | Workspace profile |

---

## canvas read

Read the content of a Slack Canvas.

```
slack-cli canvas read [options]
```

| Flag | Description |
|------|-------------|
| `-i, --id <canvas_id>` | Canvas ID (required) |
| `--format <type>` | Output format: `table`, `simple`, `json` |
| `--profile <name>` | Workspace profile |

## canvas list

List canvases in a channel.

```
slack-cli canvas list [options]
```

| Flag | Description |
|------|-------------|
| `-c, --channel <name>` | Channel name or ID (required) |
| `--format <type>` | Output format: `table`, `simple`, `json` |
| `--profile <name>` | Workspace profile |

---

## Global Options

These flags are available on most commands:

| Flag | Description |
|------|-------------|
| `--profile <name>` | Use a specific workspace profile instead of the default |
| `--format <type>` | Output format: `table` (default), `simple`, `json` |
| `-h, --help` | Show help for a command |
| `--version` | Show slack-cli version |

## Required Slack API Scopes

The Slack Bot Token must have these scopes for full functionality:

| Scope | Used by |
|-------|---------|
| `chat:write` | send, edit, delete, scheduled |
| `channels:read` | channels, channel info |
| `groups:read` | Private channel listing |
| `im:read` | DM channel listing |
| `mpim:read` | Group DM listing |
| `channels:history` | history, unread |
| `groups:history` | Private channel history |
| `im:history` | DM history |
| `users:read` | users list, users info |
| `users:read.email` | users lookup |
| `search:read` | search |
| `reactions:write` | reaction add |
| `reactions:read` | reaction remove |
| `pins:write` | pin add, pin remove |
| `pins:read` | pin list |
| `files:write` | upload |
| `files:read` | upload (snippets) |
