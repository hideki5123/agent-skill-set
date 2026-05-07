// preflight.ts — quick environment check before invoking notion-cli use cases.
//
// Cross-OS. Never reads the token VALUE — only checks resolvability.
//
// Token resolution (first match wins): NOTION_TOKEN → NOTION_API_KEY →
// NOTION_TOKEN_FILE (a path; we stat the file but don't read it).
//
// Run with:
//   deno run --allow-env=NOTION_TOKEN,NOTION_API_KEY,NOTION_TOKEN_FILE,HOME,USERPROFILE \
//            --allow-read --allow-run=mise,deno <this>

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
const workspace = join(home, ".notion-cli");

const checks: Array<[string, boolean, string]> = [];

const m = await run("mise", ["--version"]);
checks.push(["mise", m.ok, m.ok ? m.out : "missing — run setup.ts"]);

const d = await run("deno", ["--version"]);
const denoLine = d.out.split("\n")[0] ?? "";
checks.push([
  "deno",
  d.ok,
  d.ok ? denoLine : "missing — run `mise install` in ~/.notion-cli",
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

// Token resolution check. Prefer NOTION_TOKEN, then NOTION_API_KEY, then
// NOTION_TOKEN_FILE (which we stat but never read).
const directSet = (Deno.env.get("NOTION_TOKEN") ?? "").length > 0;
const aliasSet = (Deno.env.get("NOTION_API_KEY") ?? "").length > 0;
const tokenFile = Deno.env.get("NOTION_TOKEN_FILE") ?? "";
let fileOk = false;
let fileInfo = "";
if (tokenFile.length > 0) {
  try {
    const st = await Deno.stat(tokenFile);
    fileOk = st.isFile && st.size > 0;
    fileInfo = `${tokenFile} (${st.size} bytes)`;
  } catch {
    fileInfo = `${tokenFile} (unreadable — add --allow-read=${tokenFile})`;
  }
}

let tokenSource: string;
let tokenOk: boolean;
if (directSet) {
  tokenSource = "NOTION_TOKEN";
  tokenOk = true;
} else if (aliasSet) {
  tokenSource = "NOTION_API_KEY";
  tokenOk = true;
} else if (fileOk) {
  tokenSource = `NOTION_TOKEN_FILE → ${fileInfo}`;
  tokenOk = true;
} else if (tokenFile.length > 0) {
  tokenSource = `NOTION_TOKEN_FILE → ${fileInfo}`;
  tokenOk = false;
} else {
  tokenSource = "missing — set NOTION_TOKEN / NOTION_API_KEY / NOTION_TOKEN_FILE (see references/auth-setup.md)";
  tokenOk = false;
}
checks.push(["token", tokenOk, tokenSource]);

console.log("preflight:");
for (const [name, ok, info] of checks) {
  console.log(`  ${ok ? "[ok]" : "[fail]"} ${name}: ${info}`);
}

const allOk = checks.every(([_, ok]) => ok);
Deno.exit(allOk ? 0 : 1);
