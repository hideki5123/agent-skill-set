// worker.ts — detached SDK runner. Spawned by chat.ts new/continue and
// disowned via .unref(). Lives for the entire turn duration. Streams events
// to the per-turn directory under ~/.codex-server/turns/<turn-id>/.
//
// Args: --turn-id <id> --cwd <path> [--thread-id <id>]
//       [--prompt-file <path>] [--images <comma-separated paths>]
//       [--schema-file <path>] [--model <name>] [--skip-git-check]
//
// Run with:
//   deno run --allow-read --allow-write --allow-env \
//            --allow-run=<codex-path> --allow-net=api.openai.com <this>
//
// --allow-env is unscoped here because @openai/codex-sdk loads through
// deno's Node compat layer, which probes many Node-internal env vars.
// The ChatGPT-subscription-only guarantee is preserved at the *env
// injection* boundary: buildEnv() only forwards PATH/HOME/USERPROFILE to
// the SDK's env option, so the spawned codex binary never sees
// OPENAI_API_KEY regardless of what deno can read.

import { join } from "jsr:@std/path@1";
import { parseArgs } from "jsr:@std/cli@1/parse-args";
import {
  appendDiag,
  appendEvent,
  appendOut,
  buildEnv,
  FALLBACK_SDK_SPEC,
  readConfig,
  readTurnMeta,
  touchMarker,
  turnDir,
  writeTurnMeta,
} from "./helpers.ts";

// Idle watchdog: if the SDK event stream produces no event for this many
// seconds, the turn is presumed hung (network drop, app-server protocol stall,
// wedged child) and is aborted with an `error` marker so it stops reading as
// "running" forever. Each emitted event resets the clock, so legitimate long
// reasoning — which still surfaces item.* events — is never killed. Override
// via CODEX_SERVER_IDLE_SECS (the worker uses unscoped --allow-env).
const IDLE_SECS = Number(Deno.env.get("CODEX_SERVER_IDLE_SECS") ?? "180") ||
  180;

interface ThreadItem {
  type: string;
  text?: string;
  command?: string;
  exit_code?: number;
  status?: string;
  changes?: Array<{ kind: string; path: string }>;
  items?: Array<{ completed: boolean; text: string }>;
}

interface ThreadEvent {
  type:
    | "thread.started"
    | "turn.started"
    | "item.started"
    | "item.updated"
    | "item.completed"
    | "turn.completed"
    | "turn.failed"
    | "error";
  thread_id?: string;
  item?: ThreadItem;
  usage?: {
    input_tokens?: number;
    cached_input_tokens?: number;
    output_tokens?: number;
    reasoning_output_tokens?: number;
  };
  error?: { message?: string };
  // ThreadErrorEvent (type: "error") carries its message at the top level, not
  // under `error` — a fatal, unrecoverable stream error.
  message?: string;
}

const args = parseArgs(Deno.args, {
  string: [
    "turn-id",
    "cwd",
    "thread-id",
    "prompt-file",
    "images",
    "schema-file",
    "model",
  ],
  boolean: ["skip-git-check"],
});

const turnId = args["turn-id"];
const cwd = args["cwd"];
if (!turnId || !cwd) {
  console.error("worker.ts: --turn-id and --cwd are required");
  Deno.exit(64);
}

// Boot heartbeat: written before anything else can fail, so a post-mortem can
// tell "worker never started" (no worker.log) from "worker started then died"
// (worker.log present but no done/error marker).
await appendDiag(
  turnId,
  `[boot] pid=${Deno.pid} idle_watchdog=${IDLE_SECS}s started=${new Date().toISOString()}\n`,
);

// Catch-all guarantee: even on uncaught throw, mark the turn errored so it
// doesn't appear "still running" forever. Defined before the pid-recording
// below so a failure *there* (the ef8d1a7c pid:0 signature — worker died
// before recording its real pid) is also captured rather than left silent.
let markerWritten = false;
async function failWith(reason: string): Promise<void> {
  if (markerWritten) return;
  markerWritten = true;
  await appendDiag(turnId!, `[fail] ${reason}\n`);
  await appendOut(turnId!, `\n[turn.failed] ${reason}\n`);
  await touchMarker(turnId!, "error");
}

globalThis.addEventListener("unhandledrejection", (e) => {
  void failWith(`unhandledrejection: ${e.reason}`);
});
globalThis.addEventListener("error", (e) => {
  void failWith(`uncaught error: ${e.message}`);
});

// Update meta with our pid so chat.ts status can liveness-check us.
const existingMeta = await readTurnMeta(turnId);
if (!existingMeta) {
  await failWith(`turn-dir for ${turnId} not initialized by client`);
  Deno.exit(64);
}
existingMeta.pid = Deno.pid;
await writeTurnMeta(existingMeta);

try {
  const promptPath = args["prompt-file"];
  if (!promptPath) throw new Error("--prompt-file required");
  const promptText = await Deno.readTextFile(promptPath);

  // Build the input array per @openai/codex-sdk's structured-input format.
  const input: Array<
    { type: "text"; text: string } | { type: "local_image"; path: string }
  > = [{ type: "text", text: promptText }];
  if (args["images"]) {
    for (const p of args["images"].split(",").map((s) => s.trim())) {
      if (p.length > 0) input.push({ type: "local_image", path: p });
    }
  }

  // Optional JSON schema for structured output.
  let outputSchema: unknown = undefined;
  if (args["schema-file"]) {
    const raw = await Deno.readTextFile(args["schema-file"]);
    outputSchema = JSON.parse(raw);
  }

  // Resolve the codex binary path + SDK spec pinned at setup.
  const cfg = await readConfig();

  // Dynamic import of the SDK from the machine-adaptive spec resolved at setup
  // (falls back for pre-v1.3.0 configs). A computed specifier still resolves at
  // runtime — verified — and keeps the import error catchable so we can still
  // write the error marker.
  const sdkSpec = cfg.sdkSpec ?? FALLBACK_SDK_SPEC;
  await appendDiag(turnId, `[sdk] importing ${sdkSpec}\n`);
  // deno-lint-ignore no-explicit-any
  const sdk: any = await import(sdkSpec);
  const Codex = sdk.Codex;

  const sdkConfig: Record<string, unknown> = {
    approval_policy: "on-failure",
    sandbox_workspace_write: { network_access: true },
  };
  if (args["model"]) sdkConfig.model = args["model"];

  const codex = new Codex({
    codexPathOverride: cfg.codexPath,
    env: buildEnv(),
    config: sdkConfig,
  });

  let thread;
  if (args["thread-id"]) {
    // resumeThread gained a ThreadOptions arg in codex-sdk ≥0.131; passing the
    // cwd + skip-git-check lets a resumed turn run in a non-git directory
    // without pre-trusting it in ~/.codex/config.toml (it was ignored, and
    // documented as unsupported, on the old 0.130 pin).
    thread = codex.resumeThread(args["thread-id"], {
      workingDirectory: cwd,
      skipGitRepoCheck: !!args["skip-git-check"],
    });
    existingMeta.resumed_from = args["thread-id"];
  } else {
    thread = codex.startThread({
      workingDirectory: cwd,
      skipGitRepoCheck: !!args["skip-git-check"],
    });
  }

  const runOpts: Record<string, unknown> = {};
  if (outputSchema !== undefined) runOpts.outputSchema = outputSchema;

  const streamed = await thread.runStreamed(input, runOpts);
  const events: AsyncIterable<ThreadEvent> = streamed.events;

  // Best-effort: capture thread.id synchronously if the SDK populates it.
  // For new threads, the id arrives via the `thread.started` stream event
  // below.
  if (thread.id) {
    existingMeta.thread_id = thread.id;
    await writeTurnMeta(existingMeta);
  }

  // Drive the async iterator manually so each pull can race an idle timer.
  // A plain `for await` offers no way to time out a stalled stream — the
  // structural reason a hung turn used to read as "running" forever.
  const iter = events[Symbol.asyncIterator]();
  const IDLE_MS = IDLE_SECS * 1000;
  const IDLE = Symbol("idle-watchdog");

  while (true) {
    let timer: number | undefined;
    const idleGuard = new Promise<typeof IDLE>((resolve) => {
      timer = setTimeout(() => resolve(IDLE), IDLE_MS);
    });
    let res: IteratorResult<ThreadEvent> | typeof IDLE;
    try {
      res = await Promise.race([iter.next(), idleGuard]);
    } finally {
      if (timer !== undefined) clearTimeout(timer);
    }

    if (res === IDLE) {
      await failWith(`idle watchdog: no stream event for ${IDLE_SECS}s`);
      // Best-effort graceful close of the SDK stream (signals codex to abort),
      // then hard-exit. Exiting closes the worker's stdio pipes to the spawned
      // `codex app-server`, so the child tears down too instead of orphaning a
      // wedged turn. Without this exit the dangling iter.next() would keep the
      // worker — and the "running" state — alive indefinitely.
      try {
        await iter.return?.(undefined);
      } catch { /* ignore */ }
      Deno.exit(1);
    }

    if (res.done) break;
    const ev = res.value;
    await appendEvent(turnId, ev);

    if (ev.type === "thread.started" && ev.thread_id) {
      existingMeta.thread_id = ev.thread_id;
      await writeTurnMeta(existingMeta);
      continue;
    }
    if (ev.type === "turn.started") continue;

    if (ev.type === "item.completed" && ev.item) {
      const it = ev.item;
      switch (it.type) {
        case "agent_message":
          if (typeof it.text === "string") await appendOut(turnId, it.text + "\n");
          break;
        case "reasoning":
          if (typeof it.text === "string") {
            await appendOut(turnId, `\n[reasoning] ${it.text}\n`);
          }
          break;
        case "command_execution": {
          const ec = it.exit_code !== undefined ? ` (exit ${it.exit_code})` : "";
          const cmd = it.command ?? "(unknown)";
          await appendOut(turnId, `\n[command] ${cmd}${ec}\n`);
          break;
        }
        case "file_change":
          if (it.changes) {
            for (const c of it.changes) {
              await appendOut(turnId, `[file_change] ${c.kind} ${c.path}\n`);
            }
          }
          break;
      }
    } else if (ev.type === "item.updated" && ev.item?.type === "todo_list") {
      const items = ev.item.items ?? [];
      await appendOut(turnId, "\n[todo]\n");
      for (const t of items) {
        await appendOut(turnId, `  [${t.completed ? "x" : " "}] ${t.text}\n`);
      }
    } else if (ev.type === "turn.completed") {
      const u = ev.usage ?? {};
      const summary =
        `\n[turn.completed] input=${u.input_tokens ?? "?"} cached=${u.cached_input_tokens ?? "?"} output=${u.output_tokens ?? "?"} reasoning=${u.reasoning_output_tokens ?? "?"}\n`;
      await appendOut(turnId, summary);
      markerWritten = true;
      await touchMarker(turnId, "done");
    } else if (ev.type === "turn.failed") {
      const msg = ev.error?.message ?? "(no message)";
      await appendOut(turnId, `\n[turn.failed] ${msg}\n`);
      markerWritten = true;
      await touchMarker(turnId, "error");
    } else if (ev.type === "error") {
      // ThreadErrorEvent: a fatal, unrecoverable stream error. Surface it now
      // rather than waiting for the stream to end or the watchdog to trip.
      await failWith(`stream error: ${ev.message ?? "(no message)"}`);
      break;
    }
  }

  // If we exited the loop without an explicit completion marker, mark failed.
  if (!markerWritten) await failWith("stream ended without turn.completed");
} catch (err) {
  const msg = err instanceof Error ? err.message : String(err);
  await failWith(msg);
}

// Cleanup: drop the prompt-file in turn-dir so it doesn't dangle.
try {
  const p = args["prompt-file"];
  if (p && p.startsWith(turnDir(turnId))) {
    // It's inside our turn-dir — keep it as a record (don't delete).
  }
} catch { /* ignore */ }
