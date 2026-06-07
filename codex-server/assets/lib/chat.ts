// chat.ts — codex-server client entrypoint.
//
// Subcommands:
//   new "<prompt>" [--model M] [--cwd PATH] [--schema FILE] [--image P]...
//                  [--skip-git-check]
//   continue [--last | --thread <id>] "<prompt>" [...same flags as new]
//   tail <turn-id> [--follow]
//   wait <turn-id> [--timeout S]
//   status <turn-id>
//   list-turns [--limit N]
//   list                          # list recent threads from ~/.codex/sessions/
//   show <thread-id>              # print thread metadata + last items
//
// Architecture: `new`/`continue` forks worker.ts detached and returns turn-id
// in <1s. The actual codex SDK call runs in the worker. Bash's 2-min timeout
// does not apply because the client invocation exits immediately. Claude Code
// uses the Monitor tool on the returned out_path to follow streaming.
//
// Run with:
//   deno run --allow-read --allow-write --allow-env=PATH,HOME,USERPROFILE \
//            --allow-run=<codex-path>,<deno-path>,kill --allow-net=api.openai.com <this> <subcommand> ...
// <deno-path> (= Deno.execPath()): new/continue fork a detached deno worker.
// kill: wait/tail/status liveness-check the worker via `kill -0`.

import { join } from "jsr:@std/path@1";
import { parseArgs } from "jsr:@std/cli@1/parse-args";
import {
  authReady,
  codexSessionsDir,
  loadLatestThreadId,
  loginGuide,
  pathExists,
  readConfig,
  readTurnMeta,
  turnDir,
  turnsDir,
  turnState,
  writeTurnMeta,
} from "./helpers.ts";

function usage(): never {
  console.error(`usage: chat.ts <subcommand> [args]
subcommands:
  new "<prompt>" [--model M] [--cwd PATH] [--schema FILE] [--image P]... [--skip-git-check]
  continue [--last | --thread <id>] "<prompt>" [flags as in new]
  tail <turn-id> [--follow]
  wait <turn-id> [--timeout SECS]
  status <turn-id>
  list-turns [--limit N]
  list
  show <thread-id>`);
  Deno.exit(64);
}

async function preflightAuthOrExit(): Promise<void> {
  if (!(await authReady())) {
    console.error(loginGuide());
    Deno.exit(2);
  }
}

function denoPath(): string {
  const p = Deno.execPath();
  return p;
}

async function workerSelf(): Promise<string> {
  // worker.ts lives next to chat.ts in ~/.codex-server/lib/.
  // import.meta.url resolves correctly under deno regardless of cwd.
  return new URL("worker.ts", import.meta.url).pathname;
}

async function forkWorker(opts: {
  turnId: string;
  cwd: string;
  promptFile: string;
  threadId?: string;
  images?: string[];
  schemaFile?: string;
  model?: string;
  skipGitCheck?: boolean;
}): Promise<number> {
  const cfg = await readConfig();
  // NOTE on --allow-env scope (worker only):
  // The @openai/codex-sdk loads through deno's Node compat layer, which
  // probes several Node-internal env vars (NODE_V8_COVERAGE, NODE_OPTIONS,
  // NODE_NO_WARNINGS, …) plus codex-specific ones. Enumerating them is
  // fragile across SDK upgrades, so the worker uses unscoped --allow-env.
  //
  // ChatGPT-subscription-only guarantee is unchanged because:
  // 1. `buildEnv()` (helpers.ts) only forwards PATH/HOME/USERPROFILE to the
  //    SDK's `env` option, which is what reaches the spawned codex binary.
  // 2. Even if deno can read OPENAI_API_KEY, codex never receives it.
  // 3. The codex binary authenticates via ~/.codex/auth.json (ChatGPT login).
  // The client (chat.ts) keeps its tight --allow-env because it doesn't load
  // the SDK — only the worker does.
  const args: string[] = [
    "run",
    "--allow-read",
    "--allow-write",
    "--allow-env",
    `--allow-run=${cfg.codexPath}`,
    "--allow-net=api.openai.com",
    await workerSelf(),
    "--turn-id",
    opts.turnId,
    "--cwd",
    opts.cwd,
    "--prompt-file",
    opts.promptFile,
  ];
  if (opts.threadId) args.push("--thread-id", opts.threadId);
  if (opts.images?.length) args.push("--images", opts.images.join(","));
  if (opts.schemaFile) args.push("--schema-file", opts.schemaFile);
  if (opts.model) args.push("--model", opts.model);
  if (opts.skipGitCheck) args.push("--skip-git-check");

  const child = new Deno.Command(denoPath(), {
    args,
    stdin: "null",
    stdout: "null",
    stderr: "null",
  }).spawn();
  // Disown — let the worker keep running after we exit.
  child.unref();
  return child.pid;
}

async function cmdNew(rest: string[], resume?: { threadId: string }): Promise<void> {
  const parsed = parseArgs(rest, {
    string: ["model", "cwd", "schema"],
    boolean: ["skip-git-check"],
    collect: ["image"],
    alias: { c: "cwd", m: "model" },
  });
  const prompt = (parsed._[0] ?? "").toString();
  if (!prompt) {
    console.error("error: prompt is required");
    Deno.exit(64);
  }
  await preflightAuthOrExit();

  const turnId = crypto.randomUUID();
  const dir = turnDir(turnId);
  await Deno.mkdir(dir, { recursive: true });
  const promptFile = join(dir, "prompt.txt");
  await Deno.writeTextFile(promptFile, prompt);

  const cwd = parsed.cwd ?? Deno.cwd();
  const meta = {
    turn_id: turnId,
    thread_id: null,
    started_at: new Date().toISOString(),
    cwd,
    model: parsed.model ?? null,
    pid: 0, // placeholder; overwritten with the real worker pid below
    resumed_from: resume?.threadId ?? null,
  };
  // Write a placeholder first so the detached worker always finds meta.json to
  // read and augment (it exits 64 otherwise).
  await writeTurnMeta(meta);

  // deno-lint-ignore no-explicit-any
  const images = (parsed.image as any) as string[] | undefined;

  const pid = await forkWorker({
    turnId,
    cwd,
    promptFile,
    threadId: resume?.threadId,
    images,
    schemaFile: parsed.schema ?? undefined,
    model: parsed.model ?? undefined,
    skipGitCheck: !!parsed["skip-git-check"],
  });
  // Record the real worker pid synchronously, so a `wait`/`tail`/`status` that
  // races in right after `new` liveness-checks the worker instead of pid 0.
  // The worker also writes its own Deno.pid (the same value) once it boots.
  meta.pid = pid;
  await writeTurnMeta(meta);

  console.log(
    JSON.stringify({
      turn_id: turnId,
      out_path: join(dir, "out.txt"),
      events_path: join(dir, "events.jsonl"),
      done_marker: join(dir, "done"),
      error_marker: join(dir, "error"),
      meta_path: join(dir, "meta.json"),
    }),
  );
}

async function cmdContinue(rest: string[]): Promise<void> {
  // Two flag forms: --last (most recent thread in this cwd), --thread <id>.
  const parsed = parseArgs(rest, {
    string: ["thread", "model", "cwd", "schema"],
    boolean: ["last", "skip-git-check"],
    collect: ["image"],
  });
  const prompt = (parsed._[0] ?? "").toString();
  if (!prompt) {
    console.error("error: prompt is required");
    Deno.exit(64);
  }
  await preflightAuthOrExit();

  let threadId: string | null = parsed.thread ?? null;
  const cwd = parsed.cwd ?? Deno.cwd();
  if (!threadId && parsed.last) {
    threadId = await loadLatestThreadId(cwd);
    if (!threadId) {
      console.error("error: no previous thread found for cwd " + cwd);
      Deno.exit(65);
    }
  }
  if (!threadId) {
    console.error("error: pass --last or --thread <id>");
    Deno.exit(64);
  }
  // Reuse cmdNew with the resume hint by rebuilding the argv minus the
  // continue-specific flags. Simpler: call into the same flow manually.
  const rebuilt: string[] = [prompt];
  if (parsed.model) rebuilt.push("--model", parsed.model);
  if (parsed.cwd) rebuilt.push("--cwd", parsed.cwd);
  if (parsed.schema) rebuilt.push("--schema", parsed.schema);
  if (parsed["skip-git-check"]) rebuilt.push("--skip-git-check");
  // deno-lint-ignore no-explicit-any
  const images = (parsed.image as any) as string[] | undefined;
  for (const img of images ?? []) rebuilt.push("--image", img);

  await cmdNew(rebuilt, { threadId });
}

async function cmdTail(rest: string[]): Promise<void> {
  const parsed = parseArgs(rest, { boolean: ["follow"] });
  const turnId = (parsed._[0] ?? "").toString();
  if (!turnId) {
    console.error("error: turn-id required");
    Deno.exit(64);
  }
  const outPath = join(turnDir(turnId), "out.txt");
  let pos = 0;
  const dec = new TextDecoder();
  while (true) {
    try {
      const f = await Deno.open(outPath, { read: true });
      try {
        await f.seek(pos, Deno.SeekMode.Start);
        const buf = new Uint8Array(64 * 1024);
        while (true) {
          const n = await f.read(buf);
          if (n === null) break;
          pos += n;
          await Deno.stdout.write(buf.subarray(0, n));
        }
      } finally {
        f.close();
      }
    } catch {
      // out.txt may not exist yet
    }
    const st = await turnState(turnId);
    if (st === "complete" || st === "failed" || st === "abandoned") {
      Deno.exit(st === "complete" ? 0 : 1);
    }
    if (!parsed.follow) {
      Deno.exit(0);
    }
    await new Promise((r) => setTimeout(r, 250));
  }
}

async function cmdWait(rest: string[]): Promise<void> {
  const parsed = parseArgs(rest, { string: ["timeout"] });
  const turnId = (parsed._[0] ?? "").toString();
  if (!turnId) {
    console.error("error: turn-id required");
    Deno.exit(64);
  }
  const timeoutMs = parsed.timeout ? Number(parsed.timeout) * 1000 : 0;
  const start = Date.now();
  while (true) {
    const st = await turnState(turnId);
    if (st === "complete") {
      try {
        const out = await Deno.readTextFile(join(turnDir(turnId), "out.txt"));
        await Deno.stdout.write(new TextEncoder().encode(out));
      } catch { /* ignore */ }
      Deno.exit(0);
    }
    if (st === "failed" || st === "abandoned" || st === "missing") {
      console.error(`turn ${turnId}: state=${st}`);
      try {
        const out = await Deno.readTextFile(join(turnDir(turnId), "out.txt"));
        await Deno.stderr.write(new TextEncoder().encode(out));
      } catch { /* ignore */ }
      Deno.exit(1);
    }
    if (timeoutMs > 0 && Date.now() - start > timeoutMs) {
      console.error(`turn ${turnId}: timeout after ${parsed.timeout}s`);
      Deno.exit(2);
    }
    await new Promise((r) => setTimeout(r, 250));
  }
}

async function cmdStatus(rest: string[]): Promise<void> {
  const turnId = rest[0];
  if (!turnId) {
    console.error("error: turn-id required");
    Deno.exit(64);
  }
  const meta = await readTurnMeta(turnId);
  const state = await turnState(turnId);
  let lastEventAt: string | null = null;
  try {
    const st = await Deno.stat(join(turnDir(turnId), "events.jsonl"));
    if (st.mtime) lastEventAt = st.mtime.toISOString();
  } catch { /* no events yet */ }
  console.log(
    JSON.stringify(
      {
        turn_id: turnId,
        state,
        thread_id: meta?.thread_id ?? null,
        cwd: meta?.cwd ?? null,
        started_at: meta?.started_at ?? null,
        last_event_at: lastEventAt,
        pid: meta?.pid ?? null,
      },
      null,
      2,
    ),
  );
}

async function cmdListTurns(rest: string[]): Promise<void> {
  const parsed = parseArgs(rest, { string: ["limit"] });
  const limit = parsed.limit ? Number(parsed.limit) : 20;
  const root = turnsDir();
  if (!(await pathExists(root))) {
    console.log("[]");
    return;
  }
  const entries: Array<{ name: string; mtime: number }> = [];
  for await (const e of Deno.readDir(root)) {
    if (!e.isDirectory) continue;
    const st = await Deno.stat(join(root, e.name));
    entries.push({ name: e.name, mtime: st.mtime?.getTime() ?? 0 });
  }
  entries.sort((a, b) => b.mtime - a.mtime);
  const out = [];
  for (const e of entries.slice(0, limit)) {
    const meta = await readTurnMeta(e.name);
    const state = await turnState(e.name);
    out.push({
      turn_id: e.name,
      state,
      thread_id: meta?.thread_id ?? null,
      started_at: meta?.started_at ?? null,
      cwd: meta?.cwd ?? null,
    });
  }
  console.log(JSON.stringify(out, null, 2));
}

async function cmdListThreads(): Promise<void> {
  const root = codexSessionsDir();
  if (!(await pathExists(root))) {
    console.log("[]");
    return;
  }
  const all: Array<{ path: string; mtime: number }> = [];
  async function walk(dir: string): Promise<void> {
    for await (const entry of Deno.readDir(dir)) {
      const p = join(dir, entry.name);
      if (entry.isDirectory) await walk(p);
      else if (entry.isFile && entry.name.endsWith(".jsonl")) {
        try {
          const st = await Deno.stat(p);
          all.push({ path: p, mtime: st.mtime?.getTime() ?? 0 });
        } catch { /* skip */ }
      }
    }
  }
  await walk(root);
  all.sort((a, b) => b.mtime - a.mtime);
  const out = [];
  for (const { path, mtime } of all.slice(0, 50)) {
    try {
      const text = await Deno.readTextFile(path);
      const firstLine = text.split("\n", 1)[0];
      let tid: string | null = null;
      let cwd: string | null = null;
      try {
        // deno-lint-ignore no-explicit-any
        const parsed = JSON.parse(firstLine) as any;
        tid = parsed?.payload?.id ?? null;
        cwd = parsed?.payload?.cwd ?? null;
      } catch { /* skip */ }
      out.push({
        thread_id: tid,
        path,
        cwd,
        mtime: new Date(mtime).toISOString(),
      });
    } catch { /* skip */ }
  }
  console.log(JSON.stringify(out, null, 2));
}

async function cmdShow(rest: string[]): Promise<void> {
  const threadId = rest[0];
  if (!threadId) {
    console.error("error: thread-id required");
    Deno.exit(64);
  }
  const root = codexSessionsDir();
  if (!(await pathExists(root))) {
    console.error("no codex sessions directory");
    Deno.exit(1);
  }
  let match: string | null = null;
  async function walk(dir: string): Promise<void> {
    for await (const entry of Deno.readDir(dir)) {
      if (match) return;
      const p = join(dir, entry.name);
      if (entry.isDirectory) await walk(p);
      else if (entry.isFile && entry.name.endsWith(".jsonl")) {
        try {
          const head = await Deno.readTextFile(p);
          const firstLine = head.split("\n", 1)[0];
          // session-meta payload.id is the thread-id; not the top-level
          // "thread_id" field (which only appears on later stream events).
          try {
            // deno-lint-ignore no-explicit-any
            const parsed = JSON.parse(firstLine) as any;
            if (parsed?.payload?.id === threadId) match = p;
          } catch { /* skip */ }
        } catch { /* skip */ }
      }
    }
  }
  await walk(root);
  if (!match) {
    console.error(`thread ${threadId} not found`);
    Deno.exit(1);
  }
  const lines = (await Deno.readTextFile(match)).split("\n").filter((l) => l);
  const head = lines[0] ?? "";
  const tail = lines.slice(-10);
  console.log(JSON.stringify({ thread_id: threadId, path: match, head, tail }, null, 2));
}

const sub = Deno.args[0];
const rest = Deno.args.slice(1);
switch (sub) {
  case "new":
    await cmdNew(rest);
    break;
  case "continue":
    await cmdContinue(rest);
    break;
  case "tail":
    await cmdTail(rest);
    break;
  case "wait":
    await cmdWait(rest);
    break;
  case "status":
    await cmdStatus(rest);
    break;
  case "list-turns":
    await cmdListTurns(rest);
    break;
  case "list":
    await cmdListThreads();
    break;
  case "show":
    await cmdShow(rest);
    break;
  default:
    usage();
}
