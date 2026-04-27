# Setup — cross-OS, two-tool stack

The whole skill needs **two tools**: `mise` (declarative version manager) and `deno` (TypeScript runtime). Mise installs deno; deno does everything else. No bash, no PowerShell scripts, no `node_modules`, no `pnpm install`.

## 1. Install mise

| OS | Command |
|----|---------|
| macOS | `brew install mise` |
| Linux | `curl https://mise.run \| sh` |
| Windows | `winget install jdx.mise` (or `scoop install mise`) |

Then `mise --version` should succeed in a new shell.

The skill **does not auto-install mise**. If `lib/setup.ts` finds it missing, it prints the platform-aware hint and exits.

## 2. Run setup.ts (one-time)

When Claude orchestrates the skill, it runs:

```
deno run --allow-read --allow-write --allow-env --allow-run=mise ${CLAUDE_PLUGIN_ROOT}/skills/openai-cli/assets/lib/setup.ts
```

`${CLAUDE_PLUGIN_ROOT}` is set automatically inside Claude. From a plain user shell, resolve the absolute path:

```
deno run --allow-read --allow-write --allow-env --allow-run=mise ~/.claude/plugins/cache/hideki-plugins/openai-cli/1.0.0/skills/openai-cli/assets/lib/setup.ts
```

(The `1.0.0` may differ if you bump the skill version — check with `ls ~/.claude/plugins/cache/hideki-plugins/openai-cli/`.)

This:
1. Verifies `mise --version`.
2. Creates `~/.openai-cli/{,.cache,tmp,lib}/` (cross-platform via `Deno.env.get("HOME") ?? Deno.env.get("USERPROFILE")`).
3. Copies the bundled `assets/mise.toml` template to `~/.openai-cli/.mise.toml` (skips if present — preserves user edits).
4. **Copies all skill scripts** (`setup.ts`, `preflight.ts`, `resolveModel.ts`) into `~/.openai-cli/lib/` (overwrites — these are skill-controlled). After this, every subsequent command uses `~/.openai-cli/lib/<script>.ts`, a stable path independent of the skill version.
5. Runs `mise trust` and `mise install` inside the workspace — installs deno at the pinned version.
6. Existence-checks `OPENAI_API_KEY` (never reads or prints the value).

`mise.toml` content (intentionally minimal):
```toml
[tools]
deno = "2"
```

## 3. Export OPENAI_API_KEY in your shell rc

The skill **only** reads the key from the environment. No `.env` files, no skill-managed secret storage.

| Shell | rc file | Add this line |
|-------|---------|---------------|
| zsh | `~/.zshrc` | `export OPENAI_API_KEY=sk-...` |
| bash | `~/.bashrc` or `~/.bash_profile` | `export OPENAI_API_KEY=sk-...` |
| fish | `~/.config/fish/config.fish` | `set -gx OPENAI_API_KEY sk-...` |
| PowerShell | `$PROFILE` | `$env:OPENAI_API_KEY = 'sk-...'` |

Even better — use a secret manager that injects it on shell start (1Password CLI, Doppler, sops):

```sh
# zsh + 1Password CLI example
export OPENAI_API_KEY="$(op read 'op://Personal/OpenAI/api-key' 2>/dev/null)"
```

Reload your shell (`exec $SHELL -l`) and verify with `lib/preflight.ts`.

## 4. Initialize models.json (one-time, requires API key)

After the API key is set, use the stable workspace path (setup.ts already copied the script there):

```
deno run --allow-env=OPENAI_API_KEY --allow-net=api.openai.com --allow-read --allow-write ~/.openai-cli/lib/resolveModel.ts --init
```

This calls `client.models.list()`, picks the newest stable per family using the heuristics in `references/models.md`, and writes `~/.openai-cli/models.json`. From here on, every call resolves against this file (with a 1-hour TTL cache for the underlying model list).

## 5. Preflight (run before every use case)

```
deno run --allow-env=OPENAI_API_KEY --allow-read --allow-run=mise,deno ~/.openai-cli/lib/preflight.ts
```

Output is one line per check (`[ok]` / `[fail]`). Exit 0 if all clean.

## Why this stack (and not Node/pnpm/bun)

- **deno** is TS-native and consumes `npm:openai@5` directly — no `pnpm install`, no `node_modules`, no `package.json` to maintain.
- **mise** declares the deno version once in `.mise.toml` — reproducible across machines, cross-OS, no `curl | sh` chains.
- Adding bun + pnpm + Node would mean managing two package surfaces (pnpm's npm + bun's bun.lockb) for zero functional gain. The user's hard rule was: minimize dependencies; collapse stacks where possible.
- deno's runtime permissions (`--allow-env=ONE_VAR`, `--allow-net=one.host`) provide *runtime-enforced* secret/network isolation — defense in depth on top of the "no secrets to AI agents" policy.

## Workspace layout (after setup)

```
~/.openai-cli/
├── .mise.toml             # tool pin (deno = "2")
├── models.json            # persisted preferred model per family
├── lib/
│   ├── setup.ts           # bootstrap (copy of skill cache)
│   ├── preflight.ts       # env check (copy of skill cache)
│   └── resolveModel.ts    # model resolver CLI (copy of skill cache)
├── .cache/
│   └── models-list.json   # TTL cache of client.models.list() (1h)
└── tmp/
    └── chat-*.ts          # per-call TS files Claude generates and runs
```

The `lib/` copies are overwritten by `setup.ts` on every run — re-run `setup.ts` after a skill version bump to refresh.
