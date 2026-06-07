# Streaming protocol — events and items

**Read only when interpreting unfamiliar event shapes or extending event
rendering.** Not loaded during normal operation.

The worker captures the full `ThreadEvent` stream from
`thread.runStreamed()`. Every event is appended verbatim (one JSON per line)
to `events.jsonl`. The most useful events are also rendered in human-readable
form to `out.txt`.

## Event types

| `event.type`     | Meaning                                                |
| ---------------- | ------------------------------------------------------ |
| `item.started`   | An item is starting (e.g., new agent_message arrives)  |
| `item.updated`   | An item updated incrementally (e.g., `todo_list`)      |
| `item.completed` | An item completed; final shape stable                  |
| `turn.completed` | Turn finished cleanly; carries `usage` token counters  |
| `turn.failed`    | Turn failed; carries `error.message`                   |

## Item types under `event.item.type`

| `item.type`         | Notable fields                                  | Worker rendering to out.txt              |
| ------------------- | ----------------------------------------------- | ---------------------------------------- |
| `agent_message`     | `text: string`                                  | Plain `text` + newline                   |
| `reasoning`         | `text: string`                                  | `[reasoning] <text>`                     |
| `command_execution` | `command`, `status`, `exit_code?`               | `[command] <command> (exit N)`           |
| `file_change`       | `changes: Array<{ kind, path }>`                | `[file_change] <kind> <path>` per change |
| `todo_list`         | `items: Array<{ completed: boolean, text }>`    | `[todo]` block with checkboxes           |

## `turn.completed` usage block

```json
{
  "type": "turn.completed",
  "usage": {
    "input_tokens": 1234,
    "cached_input_tokens": 1000,
    "output_tokens": 567,
    "reasoning_output_tokens": 89
  }
}
```

The worker writes:

```
[turn.completed] input=1234 cached=1000 output=567 reasoning=89
```

## `turn.failed` block

```json
{
  "type": "turn.failed",
  "error": { "message": "sandbox denied write access to /etc/hosts" }
}
```

The worker writes:

```
[turn.failed] sandbox denied write access to /etc/hosts
```

and also touches `error` marker file.

## Marker contract

The worker guarantees exactly one of these terminal states for every turn:

- `done` marker file created → turn finished cleanly (`turn.completed` seen)
- `error` marker file created → turn failed for any reason
  (`turn.failed`, uncaught exception, stream ended without `turn.completed`,
  unhandled rejection)

If **neither** marker is present, the turn is past its ~10s startup grace, and
the worker's pid is no longer alive, the turn is considered **abandoned**
(worker crashed before the catch-all fired). `chat.ts status` reports this as
`state: "abandoned"`. (The liveness check needs `kill` in `--allow-run`; see
SKILL.md "Required deno permissions".)

## Parsing tips

- For the human-facing summary, read `out.txt` (already rendered).
- For programmatic post-processing, read `events.jsonl` line-by-line —
  each line is a complete JSON event.
- Extract the final agent_message:
  ```bash
  jq -r 'select(.type=="item.completed" and .item.type=="agent_message") | .item.text' events.jsonl | tail -1
  ```
- Extract the usage block:
  ```bash
  jq 'select(.type=="turn.completed") | .usage' events.jsonl
  ```

## Edge cases

- Multiple `agent_message` items per turn are normal (e.g., before and after a
  tool call). The worker appends each to `out.txt` in order.
- `item.updated` is only used for `todo_list` in our current rendering; other
  delta-style updates are not yet surfaced to `out.txt`. The full updates are
  always in `events.jsonl`.
- Long turns may exceed `out.txt` viewers' default truncation; prefer
  `cat`/`less` over IDE preview panes for the full picture.
