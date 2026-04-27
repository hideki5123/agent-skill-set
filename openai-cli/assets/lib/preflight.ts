// preflight.ts — quick environment check before invoking openai-cli use cases.
//
// Cross-OS. Never reads the OPENAI_API_KEY value — only checks existence.
//
// Run with:
//   deno run --allow-env=OPENAI_API_KEY --allow-read --allow-run=mise,deno <this>

import { join } from "jsr:@std/path@1";

async function run(
  cmd: string,
  args: string[],
): Promise<{ ok: boolean; out: string }> {
  try {
    const r = await new Deno.Command(cmd, {
      args,
      stdout: "piped",
      stderr: "piped",
    }).output();
    return {
      ok: r.code === 0,
      out: new TextDecoder().decode(r.stdout).trim(),
    };
  } catch {
    return { ok: false, out: "" };
  }
}

function homeDir(): string {
  return Deno.env.get("HOME") ?? Deno.env.get("USERPROFILE") ?? "";
}

const home = homeDir();
const workspace = join(home, ".openai-cli");

const checks: Array<[string, boolean, string]> = [];

const m = await run("mise", ["--version"]);
checks.push(["mise", m.ok, m.ok ? m.out : "missing — run setup.ts"]);

const d = await run("deno", ["--version"]);
const denoLine = d.out.split("\n")[0] ?? "";
checks.push([
  "deno",
  d.ok,
  d.ok ? denoLine : "missing — run `mise install` in ~/.openai-cli",
]);

let workspaceOk = false;
try {
  await Deno.stat(join(workspace, ".mise.toml"));
  workspaceOk = true;
} catch { /* not present */ }
checks.push([
  "workspace",
  workspaceOk,
  workspaceOk ? workspace : "missing — run setup.ts",
]);

const keySet = Deno.env.get("OPENAI_API_KEY") !== undefined;
checks.push(["OPENAI_API_KEY", keySet, keySet ? "set" : "missing"]);

console.log("preflight:");
for (const [name, ok, info] of checks) {
  console.log(`  ${ok ? "[ok]" : "[fail]"} ${name}: ${info}`);
}

const allOk = checks.every(([_, ok]) => ok);
Deno.exit(allOk ? 0 : 1);
