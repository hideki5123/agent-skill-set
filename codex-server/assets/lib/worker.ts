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
  appendEvent,
  appendOut,
  buildEnv,
  readConfig,
  readTurnMeta,
  touchMarker,
  turnDir,
  writeTurnMeta,
} from "./helpers.ts";

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
    | "turn.failed";
  thread_id?: string;
  item?: ThreadItem;
  usage?: {
    input_tokens?: number;
    cached_input_tokens?: number;
    output_tokens?: number;
    reasoning_output_tokens?: number;
  };
  error?: { message?: string };
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

// Update meta with our pid so chat.ts status can liveness-check us.
const existingMeta = await readTurnMeta(turnId);
if (!existingMeta) {
  console.error(`worker.ts: turn-dir for ${turnId} not initialized by client`);
  Deno.exit(64);
}
existingMeta.pid = Deno.pid;
await writeTurnMeta(existingMeta);

// Catch-all guarantee: even on uncaught throw, mark the turn errored so it
// doesn't appear "still running" forever.
let markerWritten = false;
async function failWith(reason: string): Promise<void> {
  if (markerWritten) return;
  markerWritten = true;
  await appendOut(turnId!, `\n[turn.failed] ${reason}\n`);
  await touchMarker(turnId!, "error");
}

globalThis.addEventListener("unhandledrejection", (e) => {
  void failWith(`unhandledrejection: ${e.reason}`);
});

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

  // Resolve the codex binary path pinned at setup.
  const cfg = await readConfig();

  // Dynamic import of the SDK. Using a dynamic import keeps the import error
  // (if any) catchable so we can still write the error marker.
  // deno-lint-ignore no-explicit-any
  const sdk: any = await import("npm:@openai/codex-sdk@^0.130.0");
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
    thread = codex.resumeThread(args["thread-id"]);
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

  for await (const ev of events) {
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
