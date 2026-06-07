// helpers.ts — shared utilities for codex-server.
//
// Cross-OS. No bash. Auth lives in ~/.codex/auth.json — never read by deno;
// only existence-checked. OPENAI_API_KEY is structurally unreadable (not in
// --allow-env), by design.

import { join } from "jsr:@std/path@1";

export function homeDir(): string {
  const h = Deno.env.get("HOME") ?? Deno.env.get("USERPROFILE");
  if (!h) throw new Error("HOME/USERPROFILE not set in environment");
  return h;
}

export function workspaceDir(): string {
  return join(homeDir(), ".codex-server");
}

export function turnsDir(): string {
  return join(workspaceDir(), "turns");
}

export function turnDir(turnId: string): string {
  return join(turnsDir(), turnId);
}

export function codexAuthPath(): string {
  return join(homeDir(), ".codex", "auth.json");
}

export function codexSessionsDir(): string {
  return join(homeDir(), ".codex", "sessions");
}

export function configPath(): string {
  return join(workspaceDir(), "config.json");
}

export interface SkillConfig {
  codexPath: string;
  codexVersion: string;
  setupDate: string;
}

export async function readConfig(): Promise<SkillConfig> {
  const raw = await Deno.readTextFile(configPath());
  return JSON.parse(raw) as SkillConfig;
}

export async function writeConfig(cfg: SkillConfig): Promise<void> {
  await Deno.mkdir(workspaceDir(), { recursive: true });
  await Deno.writeTextFile(
    configPath(),
    JSON.stringify(cfg, null, 2) + "\n",
  );
}

export async function pathExists(p: string): Promise<boolean> {
  try {
    await Deno.stat(p);
    return true;
  } catch {
    return false;
  }
}

export async function isProcessAlive(pid: number): Promise<boolean> {
  // Reject non-positive pids. `kill -0 0` targets the *caller's* process group
  // and spuriously succeeds, so pid 0 — the placeholder a turn briefly carries
  // between fork and the worker recording its real pid — would look alive.
  if (!Number.isInteger(pid) || pid <= 0) return false;
  // Posix-ish liveness probe: signal 0 = check only, no actual signal sent.
  // deno's Deno.kill doesn't accept 0; use Deno.Command("kill", ["-0", pid]).
  // Requires `kill` in the caller's --allow-run (see SKILL.md "Required deno
  // permissions"); without it this throws NotCapable and we report not-alive.
  try {
    const r = await new Deno.Command("kill", {
      args: ["-0", String(pid)],
      stdout: "null",
      stderr: "null",
    }).output();
    return r.code === 0;
  } catch {
    return false;
  }
}

export async function authReady(): Promise<boolean> {
  return await pathExists(codexAuthPath());
}

export function loginGuide(): string {
  return [
    "",
    "Codex needs ChatGPT login (no API-key billing will be used).",
    "",
    "Steps:",
    "  1. Run `codex login` in your terminal.",
    "  2. A browser opens — sign in with your ChatGPT Plus / Pro / Team account.",
    "  3. Return here and re-invoke this skill.",
    "",
    "This skill is ChatGPT-subscription-only by design. OPENAI_API_KEY is NOT",
    "supported — even if exported in your shell, it's not in --allow-env and",
    "deno cannot see it.",
    "",
    `See references/auth-setup.md for the full walkthrough.`,
    "",
  ].join("\n");
}

export interface TurnMeta {
  turn_id: string;
  thread_id: string | null;
  started_at: string;
  cwd: string;
  model: string | null;
  pid: number;
  resumed_from: string | null;
}

export async function readTurnMeta(turnId: string): Promise<TurnMeta | null> {
  const p = join(turnDir(turnId), "meta.json");
  try {
    const raw = await Deno.readTextFile(p);
    return JSON.parse(raw) as TurnMeta;
  } catch {
    return null;
  }
}

export async function writeTurnMeta(meta: TurnMeta): Promise<void> {
  const dir = turnDir(meta.turn_id);
  await Deno.mkdir(dir, { recursive: true });
  await Deno.writeTextFile(
    join(dir, "meta.json"),
    JSON.stringify(meta, null, 2) + "\n",
  );
}

export type TurnState =
  | "running"
  | "complete"
  | "failed"
  | "abandoned"
  | "missing";

// Grace window after `started_at` during which a marker-less turn is reported
// "running" even if its pid can't yet be confirmed alive. `new`/`continue`
// create the turn-dir and fork the worker detached; the worker records its real
// pid and begins streaming a beat later. Without this window a poll landing in
// that gap would see no marker and a not-yet-live pid and wrongly say
// "abandoned" — the bug this guards against.
const STARTUP_GRACE_MS = 10_000;

export async function turnState(turnId: string): Promise<TurnState> {
  const dir = turnDir(turnId);
  if (!(await pathExists(dir))) return "missing";
  if (await pathExists(join(dir, "done"))) return "complete";
  if (await pathExists(join(dir, "error"))) return "failed";
  const meta = await readTurnMeta(turnId);
  if (!meta) return "missing";
  const startedMs = Date.parse(meta.started_at);
  if (Number.isFinite(startedMs) && Date.now() - startedMs < STARTUP_GRACE_MS) {
    return "running";
  }
  if (await isProcessAlive(meta.pid)) return "running";
  return "abandoned";
}

export async function appendOut(turnId: string, text: string): Promise<void> {
  const enc = new TextEncoder();
  const f = await Deno.open(join(turnDir(turnId), "out.txt"), {
    append: true,
    create: true,
  });
  try {
    await f.write(enc.encode(text));
  } finally {
    f.close();
  }
}

export async function appendEvent(
  turnId: string,
  ev: unknown,
): Promise<void> {
  const enc = new TextEncoder();
  const f = await Deno.open(join(turnDir(turnId), "events.jsonl"), {
    append: true,
    create: true,
  });
  try {
    await f.write(enc.encode(JSON.stringify(ev) + "\n"));
  } finally {
    f.close();
  }
}

export async function touchMarker(
  turnId: string,
  kind: "done" | "error",
): Promise<void> {
  const p = join(turnDir(turnId), kind);
  const f = await Deno.open(p, { write: true, create: true });
  f.close();
}

export async function gcOldTurns(olderThanDays = 7): Promise<number> {
  const root = turnsDir();
  if (!(await pathExists(root))) return 0;
  const cutoff = Date.now() - olderThanDays * 24 * 60 * 60 * 1000;
  let removed = 0;
  for await (const entry of Deno.readDir(root)) {
    if (!entry.isDirectory) continue;
    const dir = join(root, entry.name);
    try {
      const st = await Deno.stat(dir);
      const mtime = st.mtime?.getTime() ?? 0;
      if (mtime > 0 && mtime < cutoff) {
        await Deno.remove(dir, { recursive: true });
        removed += 1;
      }
    } catch {
      // ignore stat / remove errors; best-effort GC
    }
  }
  return removed;
}

// Return env to pass to the spawned codex via SDK's `env` option.
// IMPORTANT: do NOT forward OPENAI_API_KEY even if it is exported in the
// shell — this skill is ChatGPT-subscription-only by design. The fact that
// the env var is not in --allow-env means deno cannot read it here anyway,
// so this is doubly enforced.
export function buildEnv(): Record<string, string> {
  const env: Record<string, string> = {};
  for (const k of ["PATH", "HOME", "USERPROFILE"]) {
    const v = Deno.env.get(k);
    if (v) env[k] = v;
  }
  return env;
}

interface SessionMeta {
  type?: string;
  payload?: {
    id?: string;
    cwd?: string;
  };
}

export async function loadLatestThreadId(cwd: string): Promise<string | null> {
  // Walk ~/.codex/sessions/YYYY/MM/DD/*.jsonl, newest first, parse each
  // first line as JSON, and return the first session whose `payload.cwd`
  // matches. Falls back to the globally newest session's id if no cwd
  // match is found.
  //
  // Session-file format (first line):
  //   {"timestamp":"...","type":"session_meta","payload":{"id":"<uuid>","cwd":"...",...}}
  const root = codexSessionsDir();
  if (!(await pathExists(root))) return null;

  const all: { path: string; mtime: number }[] = [];
  async function walk(dir: string): Promise<void> {
    for await (const entry of Deno.readDir(dir)) {
      const p = join(dir, entry.name);
      if (entry.isDirectory) {
        await walk(p);
      } else if (entry.isFile && entry.name.endsWith(".jsonl")) {
        try {
          const st = await Deno.stat(p);
          all.push({ path: p, mtime: st.mtime?.getTime() ?? 0 });
        } catch { /* skip */ }
      }
    }
  }
  try {
    await walk(root);
  } catch {
    return null;
  }

  all.sort((a, b) => b.mtime - a.mtime);

  let globalNewest: string | null = null;
  for (const { path } of all) {
    try {
      const text = await Deno.readTextFile(path);
      const firstLine = text.split("\n", 1)[0];
      if (!firstLine) continue;
      let parsed: SessionMeta;
      try {
        parsed = JSON.parse(firstLine) as SessionMeta;
      } catch {
        continue;
      }
      const threadId = parsed.payload?.id;
      if (!threadId) continue;
      if (globalNewest === null) globalNewest = threadId;
      if (parsed.payload?.cwd === cwd) return threadId;
    } catch { /* skip */ }
  }
  return globalNewest;
}
