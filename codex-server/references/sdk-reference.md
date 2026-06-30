# `@openai/codex-sdk` quick reference

**Read only when extending the skill or debugging SDK behavior.** Not loaded
during normal operation.

Source: https://github.com/openai/codex/tree/main/sdk/typescript

The SDK pin is **machine-adaptive** (v1.3.0+): `setup.ts` reads the local
`codex --version`, derives `sdkSpec = npm:@openai/codex-sdk@^<minor>.0`, and
stores it in `~/.codex-server/config.json`; the worker imports that spec
dynamically. The `import { Codex } from "npm:@openai/codex-sdk@^0.142.4"` form
below is illustrative — the actual version tracks whatever codex is installed.
The SDK spawns the local `codex` binary and communicates JSONL events over its
stdio.

## Client construction

```ts
import { Codex } from "npm:@openai/codex-sdk@^0.142.4";

const codex = new Codex({
  codexPathOverride: "/abs/path/to/codex", // pinned at setup
  env: {                                    // scope codex's env
    PATH: "...",
    HOME: "...",
  },
  config: {
    approval_policy: "on-failure",
    sandbox_workspace_write: { network_access: true },
    model: "gpt-5.4",                       // optional
  },
});
```

- `codexPathOverride` — absolute path to the codex binary. We resolve this at
  setup (via `which codex`) and persist in `~/.codex-server/config.json` to
  avoid relying on PATH at runtime.
- `env` — passed to the spawned codex process. We deliberately do not include
  `OPENAI_API_KEY` (auth is via `~/.codex/auth.json` anyway, and the env var
  is not in deno's `--allow-env`).
- `config` — forwarded as repeated `--config key=value` flags to codex. Dotted
  paths supported (`sandbox_workspace_write.network_access`).

## Threads

```ts
const thread = codex.startThread({
  workingDirectory: "/abs/path",
  skipGitRepoCheck: false,
});
// or:
const thread = codex.resumeThread("<thread-id>", {
  workingDirectory: "/abs/path",
  skipGitRepoCheck: false,
});
```

Notes on `resumeThread`:
- Takes an optional `ThreadOptions` arg (`workingDirectory`, `skipGitRepoCheck`)
  as of codex-sdk ≥0.131. The worker passes the turn's cwd + skip-git-check, so
  a resumed turn can run in a non-git directory directly. (On the old 0.130 pin
  this arg did not exist and was silently ignored — see the v1.2.0 SDK bump.)
- Alternatively, add the directory to codex's trusted-projects config in
  `~/.codex/config.toml` ahead of time.

`thread.id` is populated only after the first turn starts — capture it from the
`thread.started` event in the runStreamed event stream (the worker also reads
`thread.id` opportunistically right after `runStreamed`).

## Turns

```ts
// Buffered:
const { finalResponse, items } = await thread.run(input, options);

// Streamed:
const { events } = await thread.runStreamed(input, options);
for await (const ev of events) {
  // ev is a ThreadEvent — see streaming-protocol.md for types.
}
```

### `input`

Either a plain `string` or an array of input items:

```ts
[
  { type: "text", text: "Describe these screenshots" },
  { type: "local_image", path: "./ui.png" },
  { type: "local_image", path: "./diagram.jpg" },
]
```

### `options`

- `outputSchema?: object` — JSON schema for structured output. The final
  agent_message will conform.

## Event shape (high-level)

```ts
type ThreadEvent =
  | { type: "item.started";   item: ThreadItem }
  | { type: "item.updated";   item: ThreadItem }
  | { type: "item.completed"; item: ThreadItem }
  | { type: "turn.completed"; usage: TurnUsage }
  | { type: "turn.failed";    error: { message: string } };
```

`ThreadItem` discriminator field `type` includes:
- `agent_message`     — has `text: string`
- `reasoning`         — has `text: string`
- `command_execution` — has `command: string`, `status: string`, optional `exit_code`
- `file_change`       — has `changes: Array<{ kind, path }>`
- `todo_list`         — has `items: Array<{ completed: boolean, text: string }>`

See `streaming-protocol.md` for the full enumeration.

## Auth resolution (SDK perspective)

The SDK does not handle auth itself — it just spawns the `codex` binary. The
binary reads `~/.codex/auth.json` (ChatGPT login) or `OPENAI_API_KEY` env
(API-key auth). Because our skill never sets `OPENAI_API_KEY`, only the
auth.json path is exercised — guaranteeing zero API-key billing.

## Where the source lives

- Upstream README: https://github.com/openai/codex/tree/main/sdk/typescript
- Samples: https://github.com/openai/codex/tree/main/sdk/typescript/samples
- App Server docs: https://developers.openai.com/codex/app-server
