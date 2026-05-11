// setup.ts — bootstrap the codex-server workspace at ~/.codex-server/.
//
// Cross-OS: macOS, Linux. (Windows out of scope for v1.0.0 due to detached-
// process semantics; mise/deno work on Windows but detachment isn't tested.)
// No bash.
//
// Run with:
//   deno run --allow-read --allow-write --allow-env --allow-run=mise,codex,which <this>

import { join } from "jsr:@std/path@1";
import {
  authReady,
  codexAuthPath,
  configPath,
  gcOldTurns,
  loginGuide,
  turnsDir,
  workspaceDir,
  writeConfig,
} from "./helpers.ts";

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
  return "  curl https://mise.run | sh";
}

const workspace = workspaceDir();
const libDir = join(workspace, "lib");
const miseToml = join(workspace, ".mise.toml");

console.log(`workspace: ${workspace}`);

// 1. Verify mise.
const miseCheck = await run("mise", ["--version"]);
if (!miseCheck.ok) {
  console.error("ERROR: mise is not installed or not on PATH.");
  console.error("Install mise:");
  console.error(platformInstallHint());
  console.error("Then re-run this setup.");
  Deno.exit(1);
}
console.log(`[ok] mise: ${miseCheck.out.trim()}`);

// 2. Verify codex binary.
const which = await run("which", ["codex"]);
let codexPath = which.out.trim();
if (!which.ok || codexPath.length === 0) {
  console.error("ERROR: `codex` is not installed or not on PATH.");
  console.error("Install codex:");
  console.error("  macOS:  brew install codex");
  console.error("  npm:    npm install -g @openai/codex");
  console.error("Then re-run this setup.");
  Deno.exit(1);
}
const ver = await run(codexPath, ["--version"]);
console.log(
  `[ok] codex: ${ver.out.trim() || "(version unknown)"} @ ${codexPath}`,
);

// 3. Ensure workspace dirs.
await Deno.mkdir(workspace, { recursive: true });
await Deno.mkdir(libDir, { recursive: true });
await Deno.mkdir(turnsDir(), { recursive: true });
console.log(`[ok] dirs: ${workspace}, lib/, turns/`);

// 4. Copy mise.toml template (skip if user already edited theirs).
let templateWritten = false;
try {
  await Deno.stat(miseToml);
  console.log(`[ok] .mise.toml already present (preserving user edits)`);
} catch {
  const templateUrl = new URL("../mise.toml", import.meta.url);
  const template = await Deno.readTextFile(templateUrl);
  await Deno.writeTextFile(miseToml, template);
  console.log(`[ok] wrote ${miseToml}`);
  templateWritten = true;
}

// 5. Copy lib scripts (always overwrite — skill-controlled).
for (const name of ["setup.ts", "helpers.ts", "chat.ts", "worker.ts"]) {
  const srcUrl = new URL(name, import.meta.url);
  const dest = join(libDir, name);
  const src = await Deno.readTextFile(srcUrl);
  await Deno.writeTextFile(dest, src);
  console.log(`[ok] wrote ${dest}`);
}

// 6. mise trust (only after writing template).
if (templateWritten) {
  const trust = await run("mise", ["trust", miseToml]);
  if (!trust.ok) {
    console.error(`mise trust failed:\n${trust.err}`);
    Deno.exit(1);
  }
  console.log(`[ok] mise trust`);
}

// 7. mise install (idempotent).
const install = await run("mise", ["install"]);
if (!install.ok) {
  console.error(`mise install failed:\n${install.err}`);
  Deno.exit(1);
}
console.log(`[ok] mise install`);

// 8. Persist config (codex path + version).
await writeConfig({
  codexPath,
  codexVersion: ver.out.trim(),
  setupDate: new Date().toISOString(),
});
console.log(`[ok] wrote ${configPath()}`);

// 9. Check ChatGPT login. This skill is ChatGPT-subscription-only by design —
//    if ~/.codex/auth.json is absent, fail fast with the login guide. No
//    API-key fallback is offered. Note: setup itself is allowed to succeed
//    even without auth, so the user can run setup once and then `codex login`
//    afterwards — but we still print the guide as a heads-up.
if (await authReady()) {
  console.log(`[ok] auth: ${codexAuthPath()} (ChatGPT subscription)`);
} else {
  console.log(`[warn] auth: ${codexAuthPath()} missing`);
  console.log(loginGuide());
}

// 10. Housekeeping: GC turn-dirs older than 7 days.
const removed = await gcOldTurns(7);
if (removed > 0) console.log(`[ok] gc: removed ${removed} stale turn-dir(s)`);

console.log("\nSetup complete.");
console.log(
  `Next: complete \`codex login\` if you haven't, then invoke the skill normally.`,
);
