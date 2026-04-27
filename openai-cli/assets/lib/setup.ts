// setup.ts — bootstrap the openai-cli workspace at ~/.openai-cli/.
//
// Cross-OS: macOS, Linux, Windows (PowerShell or WSL). No bash.
//
// Run with:
//   deno run --allow-read --allow-write --allow-env --allow-run=mise <this>

import { join } from "jsr:@std/path@1";

async function run(
  cmd: string,
  args: string[],
): Promise<{ ok: boolean; out: string; err: string }> {
  try {
    const command = new Deno.Command(cmd, {
      args,
      stdout: "piped",
      stderr: "piped",
    });
    const { code, stdout, stderr } = await command.output();
    return {
      ok: code === 0,
      out: new TextDecoder().decode(stdout),
      err: new TextDecoder().decode(stderr),
    };
  } catch (e) {
    return { ok: false, out: "", err: String(e) };
  }
}

function platformInstallHint(): string {
  const os = Deno.build.os;
  if (os === "darwin") return "  brew install mise";
  if (os === "windows") return "  winget install jdx.mise";
  return "  curl https://mise.run | sh";
}

function homeDir(): string {
  const h = Deno.env.get("HOME") ?? Deno.env.get("USERPROFILE");
  if (!h) throw new Error("HOME/USERPROFILE not set in environment");
  return h;
}

const home = homeDir();
const workspace = join(home, ".openai-cli");
const cacheDir = join(workspace, ".cache");
const tmpDir = join(workspace, "tmp");
const libDir = join(workspace, "lib");
const miseToml = join(workspace, ".mise.toml");

console.log(`workspace: ${workspace}`);

// 1. Verify mise
const miseCheck = await run("mise", ["--version"]);
if (!miseCheck.ok) {
  console.error("ERROR: mise is not installed or not on PATH.");
  console.error("Install mise:");
  console.error(platformInstallHint());
  console.error("Then re-run this setup.");
  Deno.exit(1);
}
console.log(`[ok] mise: ${miseCheck.out.trim()}`);

// 2. Ensure workspace dirs
await Deno.mkdir(workspace, { recursive: true });
await Deno.mkdir(cacheDir, { recursive: true });
await Deno.mkdir(tmpDir, { recursive: true });
await Deno.mkdir(libDir, { recursive: true });
console.log(`[ok] dirs: ${workspace}, .cache, tmp, lib`);

// 3. Copy mise.toml template (skip if user already has one)
let templateWritten = false;
try {
  await Deno.stat(miseToml);
  console.log(`[ok] .mise.toml already present (preserving user edits)`);
} catch {
  // assets/mise.toml is one directory up from assets/lib/setup.ts
  const templateUrl = new URL("../mise.toml", import.meta.url);
  const template = await Deno.readTextFile(templateUrl);
  await Deno.writeTextFile(miseToml, template);
  console.log(`[ok] wrote ${miseToml}`);
  templateWritten = true;
}

// 3b. Copy the lib scripts into ~/.openai-cli/lib/ so subsequent commands
// don't depend on the version-pinned skill cache path. Always overwrite —
// these are skill-controlled, not user-edited.
for (const name of ["setup.ts", "preflight.ts", "resolveModel.ts"]) {
  const srcUrl = new URL(name, import.meta.url);
  const dest = join(libDir, name);
  const src = await Deno.readTextFile(srcUrl);
  await Deno.writeTextFile(dest, src);
  console.log(`[ok] wrote ${dest}`);
}

// 4. mise trust (only needed once after writing the template)
if (templateWritten) {
  const trust = await run("mise", ["trust", miseToml]);
  if (!trust.ok) {
    console.error(`mise trust failed:\n${trust.err}`);
    Deno.exit(1);
  }
  console.log(`[ok] mise trust`);
}

// 5. mise install (idempotent)
const install = await run("mise", ["install"]);
if (!install.ok) {
  console.error(`mise install failed:\n${install.err}`);
  Deno.exit(1);
}
console.log(`[ok] mise install`);

// 6. existence-check OPENAI_API_KEY (never read value)
const keySet = Deno.env.get("OPENAI_API_KEY") !== undefined;
console.log(keySet ? "[ok] OPENAI_API_KEY: set" : "[warn] OPENAI_API_KEY: missing");
if (!keySet) {
  console.log(
    "  Export OPENAI_API_KEY in your shell rc and re-run setup.",
  );
  console.log(
    "  zsh/bash: add `export OPENAI_API_KEY=...` to ~/.zshrc or ~/.bashrc",
  );
  console.log(
    "  PowerShell: add `$env:OPENAI_API_KEY = '...'` to $PROFILE",
  );
}

console.log("\nSetup complete.");
console.log(`Next: run resolveModel.ts --init to populate ${join(workspace, "models.json")}`);
