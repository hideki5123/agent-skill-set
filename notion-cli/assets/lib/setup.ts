// setup.ts — bootstrap the notion-cli workspace at ~/.notion-cli/.
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
const workspace = join(home, ".notion-cli");
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

// 3b. Copy the lib scripts into ~/.notion-cli/lib/ so subsequent commands
// don't depend on the version-pinned skill cache path. Always overwrite —
// these are skill-controlled, not user-edited.
for (const name of ["setup.ts", "preflight.ts", "notion.ts"]) {
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

// 6. existence-check token sources (never read the value).
//    Resolution order: NOTION_TOKEN → NOTION_API_KEY → NOTION_TOKEN_FILE.
const directSet = (Deno.env.get("NOTION_TOKEN") ?? "").length > 0;
const aliasSet = (Deno.env.get("NOTION_API_KEY") ?? "").length > 0;
const tokenFile = Deno.env.get("NOTION_TOKEN_FILE") ?? "";
let fileOk = false;
let fileNote = "";
if (tokenFile.length > 0) {
  try {
    const st = await Deno.stat(tokenFile);
    fileOk = st.isFile && st.size > 0;
    fileNote = fileOk
      ? `${tokenFile} (${st.size} bytes)`
      : `${tokenFile} (file empty)`;
  } catch {
    fileNote = `${tokenFile} (unreadable — add --allow-read=${tokenFile})`;
  }
}

if (directSet) {
  console.log("[ok] token source: NOTION_TOKEN");
} else if (aliasSet) {
  console.log("[ok] token source: NOTION_API_KEY");
} else if (fileOk) {
  console.log(`[ok] token source: NOTION_TOKEN_FILE → ${fileNote}`);
} else if (tokenFile.length > 0) {
  console.log(`[warn] NOTION_TOKEN_FILE set but unusable: ${fileNote}`);
} else {
  console.log("[warn] no token source resolves");
  console.log(
    "  Pick one and re-run setup. See references/auth-setup.md for the full walk-through.",
  );
  console.log(
    "  (a) zsh/bash: add `export NOTION_TOKEN=ntn_...` to ~/.zshrc or ~/.bashrc",
  );
  console.log(
    "      fish:     add `set -gx NOTION_TOKEN ntn_...` to ~/.config/fish/config.fish",
  );
  console.log(
    "      PowerShell: add `$env:NOTION_TOKEN = 'ntn_...'` to $PROFILE",
  );
  console.log(
    "  (b) Already exporting NOTION_API_KEY? The CLI accepts it as a fallback.",
  );
  console.log(
    "  (c) Nix / agenix / sops-nix users: export NOTION_TOKEN_FILE pointing at",
  );
  console.log(
    "      the chmod-0400 secret file (e.g. /run/agenix/notion-api-key).",
  );
}

console.log("\nSetup complete.");
console.log(
  `Next: smoke-test with \`deno run --allow-env=NOTION_TOKEN,NOTION_API_KEY,NOTION_TOKEN_FILE --allow-net=api.notion.com --allow-read=$HOME/.notion-cli --allow-write=$HOME/.notion-cli [--allow-read=$NOTION_TOKEN_FILE if used] ${
    join(libDir, "notion.ts")
  } auth\``,
);
