# Examples — worked invocations

**Read only when the user requests an example or you need an unfamiliar
invocation pattern.** Not loaded during normal operation.

All examples assume:

- `codex login` has been completed (`~/.codex/auth.json` exists)
- `setup.ts` has been run once
- You're invoking from `~/.codex-server/lib/chat.ts`

Throughout, the deno permission set is the same:

```
--allow-read --allow-write --allow-env=PATH,HOME,USERPROFILE \
--allow-run=<codex-path>,<deno-path>,kill --allow-net=api.openai.com
```

For brevity below it's abbreviated as `--allow-...`.

## 1. Ask a one-off question

```bash
deno run --allow-... ~/.codex-server/lib/chat.ts new "Summarize the README in 3 bullets"
```

Output (in <1 s):

```json
{
  "turn_id": "abc-...",
  "out_path": "$HOME/.codex-server/turns/abc-.../out.txt",
  "events_path": "...",
  "done_marker": "...",
  "error_marker": "...",
  "meta_path": "..."
}
```

Then watch `out_path` via Monitor (Claude Code) or `tail -f` (manual).
When the `done` marker appears, read `out_path` for the final answer.

## 2. Follow up on the most recent thread (in this cwd)

```bash
deno run --allow-... ~/.codex-server/lib/chat.ts continue --last "Now rewrite the README to be 1 paragraph"
```

`continue --last` walks `~/.codex/sessions/` and picks the newest session
whose `cwd` matches the current directory. Returns turn-id in <1 s as above.

## 3. Continue a specific thread by ID

```bash
TID="11111111-2222-3333-4444-555555555555"
deno run --allow-... ~/.codex-server/lib/chat.ts continue --thread "$TID" "What was the conclusion?"
```

## 4. Stream the output to your own terminal

After `new`/`continue`, in a second terminal:

```bash
deno run --allow-... ~/.codex-server/lib/chat.ts tail <turn-id> --follow
```

Prints bytes as they arrive in `out.txt`, exits 0 on `done` / 1 on `error`.

## 5. Wait synchronously and print the final answer

```bash
deno run --allow-... ~/.codex-server/lib/chat.ts wait <turn-id>
# Or with a timeout (seconds):
deno run --allow-... ~/.codex-server/lib/chat.ts wait <turn-id> --timeout 600
```

Blocks until the marker file appears; prints full `out.txt`. Exit 0 on
success, 1 on error, 2 on timeout.

## 6. Check status without blocking

```bash
deno run --allow-... ~/.codex-server/lib/chat.ts status <turn-id>
```

Output:

```json
{
  "turn_id": "abc-...",
  "state": "running",
  "thread_id": "11111111-...",
  "cwd": "/path/to/project",
  "started_at": "2026-05-12T10:23:45.123Z",
  "last_event_at": "2026-05-12T10:24:01.456Z",
  "pid": 54321
}
```

`state` is one of: `running`, `complete`, `failed`, `abandoned`, `missing`.

## 7. List recent turns

```bash
deno run --allow-... ~/.codex-server/lib/chat.ts list-turns --limit 10
```

Returns JSON array sorted by mtime, newest first.

## 8. List recent codex threads

```bash
deno run --allow-... ~/.codex-server/lib/chat.ts list
```

Walks `~/.codex/sessions/`, returns up to 50 most recent threads with
`{thread_id, path, cwd, mtime}`.

## 9. Show a thread's metadata

```bash
deno run --allow-... ~/.codex-server/lib/chat.ts show <thread-id>
```

## 10. Structured output via JSON schema

Save a schema as `~/tmp/schema.json`:

```json
{
  "type": "object",
  "properties": {
    "summary": { "type": "string" },
    "status":  { "type": "string", "enum": ["ok", "action_required"] }
  },
  "required": ["summary", "status"],
  "additionalProperties": false
}
```

Then:

```bash
deno run --allow-... ~/.codex-server/lib/chat.ts new \
  --schema ~/tmp/schema.json "Summarize the repo status"
```

The final `agent_message` in `out.txt` will be JSON conforming to the schema.

## 11. Attach images

```bash
deno run --allow-... ~/.codex-server/lib/chat.ts new \
  --image ~/Desktop/ui.png \
  --image ~/Desktop/diagram.jpg \
  "Describe these screenshots and any inconsistencies"
```

## 12. Specify model

```bash
deno run --allow-... ~/.codex-server/lib/chat.ts new --model gpt-5.4 "..."
```

(Defaults to whatever `~/.codex/config.toml` configures.)

## 13. Run in a non-git directory

```bash
deno run --allow-... ~/.codex-server/lib/chat.ts new --skip-git-check --cwd /tmp/scratch "..."
```

## 14. Cancel an in-flight turn

```bash
# Find the worker pid from meta.json:
cat ~/.codex-server/turns/<turn-id>/meta.json | jq .pid
# Then:
kill <pid>
# Once past the ~10s startup grace, the next `status` call reports state="abandoned".
```

## 15. Wipe state for one turn

```bash
rm -rf ~/.codex-server/turns/<turn-id>
```

Future turns are unaffected. The codex-side session in `~/.codex/sessions/`
is untouched — to discard it too, see codex's own docs.
