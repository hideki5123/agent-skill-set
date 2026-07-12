# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A collection of agent skills (Claude Code "plugins" / slash commands) plus the
tooling that installs them locally and syncs them to other machines. Each
top-level directory (e.g. `notion-cli/`, `dev-workflow/`, `grill-me/`) is one
skill whose **source of truth is `<skill>/SKILL.md`** (with optional
`references/`, `assets/`, `scripts/`, `agents/`, and `feedback/` subdirs).

## Common commands

```bash
# Install / update ONE skill into the local marketplace + ~/.claude (full pipeline)
python my-skill-factory/scripts/install_skill.py <skill-dir>/

# Regenerate marketplace plugin artifacts from skill sources
python scripts/sync_marketplace.py                 # all skills
python scripts/sync_marketplace.py --skills a b     # selected
python scripts/sync_marketplace.py --validate       # CI drift check (source vs generated)

# Unified sync: marketplace artifacts + Codex skills ($CODEX_HOME/skills, fallback ~/.codex/skills)
python scripts/sync_skills.py [--targets claude|codex] [--skills ...] [--validate]

# Vendor a skill from an upstream GitHub repo (default: mattpocock/skills), pinned to a commit
python scripts/vendor_skill.py --list
python scripts/vendor_skill.py <name> [--ref <sha>] [--install]

# Sync skills to SSH hosts listed in .claude/sync-targets
# (invoke the /sync-skills skill)

# One-time after clone: enable the pre-push auto-install hook
bash scripts/setup_hooks.sh
```

There is no test suite or build step. `sync_*.py --validate` is the closest
thing to CI — it fails when generated artifacts drift from skill sources.

## Architecture

### Authoring vs. generated artifacts

- **Skill source** lives at the repo top level: `<skill>/SKILL.md` (+ subdirs).
- **`my-marketplace/`** is a local Claude Code marketplace. `install_skill.py` /
  `sync_*.py` generate `my-marketplace/plugins/<name>/` from each skill source.
- `my-marketplace/plugins/*/skills/*` are **build artifacts and gitignored** —
  never hand-edit them. The tracked parts are `my-marketplace/.claude-plugin/marketplace.json`
  (the catalog) and each plugin's `.claude-plugin/{plugin.json,marketplace.json}`.

### Install pipeline (`my-skill-factory/scripts/install_skill.py`)

One skill dir → (1) marketplace plugin structure, (2) registration in the root
`marketplace.json`, (3) copy into `~/.claude/plugins/cache/hideki-plugins/<name>/<version>/`,
(4) `~/.claude/plugins/installed_plugins.json`, (5) enable in `~/.claude/settings.json`.
Disabling a skill = set its `enabledPlugins["<name>@hideki-plugins"]` to `false`
in `~/.claude/settings.json` (reversible). The marketplace name is `hideki-plugins`.

### Two skill toolchains

- **npm-based CLI skills** (`jira-cli`, `slack-cli`, `confluence`, `playwright-*`,
  `e2e-test`, `scenario-gen`) depend on the root `package.json` (`npm install`).
- **deno-based skills** (`notion-cli`, `openai-cli`) ship `assets/mise.toml` +
  `assets/lib/*.ts` and run on a mise + deno two-tool stack — no `node_modules`.
  Secrets are existence-checked only and scoped via deno `--allow-env` /
  `--allow-net` flags; never read `.env` files or print tokens.

### Vendored upstream skills

Several skills are copied from [mattpocock/skills](https://github.com/mattpocock/skills)
via `scripts/vendor_skill.py`, pinned to a commit, each carrying a `LICENSE`
provenance file (upstream URL, source path, commit SHA, retrieval date). They
form a composable workflow documented in
[docs/upstream-skill-workflow.md](docs/upstream-skill-workflow.md). The homegrown
`dev-workflow` skill is deprecated/disabled in favor of that workflow.

`adversarial-panel/` comes from a different upstream
([makinux/adversarial-panel](https://github.com/makinux/adversarial-panel)) whose
`SKILL.md` sits at the repo root, so `vendor_skill.py` (which only scans
`skills/<category>/<name>/`) cannot fetch it. It was placed by hand at commit
`6b1061b`, and its frontmatter is **modified**, not verbatim — see its `LICENSE`
for the diff summary. Re-vendoring means re-applying that frontmatter.

### Other moving parts

- **Pre-push hook** (`scripts/hooks/pre-push`, enabled via `setup_hooks.sh`)
  auto-installs changed skills on `git push`; non-blocking, skip with `--no-verify`.
- **`.gitattributes`** forces `eol=lf` on text files — important: stray CRLF
  leaks into shell pipelines and breaks `install_skill.py`'s cache-dir naming.
- Each skill may keep a `feedback/log.md` (newest entry on top) recording
  per-run retrospectives.

## Conventions

- **Commit messages are always in English**, regardless of the session language
  (subject and body).
- **No ASCII-art diagrams in documentation.** Use a real, renderable format —
  Mermaid fenced code blocks (` ```mermaid `) in Markdown. ASCII layout is only
  acceptable in ephemeral, non-document UI (e.g. an interactive prompt preview).
- **Never hand-edit generated artifacts** under `my-marketplace/plugins/*/skills/*`;
  edit the skill source and re-run a sync/install script.
- **Minimize dependencies.** Prefer no-install or deno over adding npm packages;
  challenge each new tool. Keep secrets out of agent reach (existence checks,
  scoped runtime flags).
- **Isolate file-mutating work in a git worktree**, then merge to `master`.
- **No pull requests. Ship straight to `master`.** Do not open a PR, do not ask
  whether to open one, and do not leave work parked on a branch waiting for
  review. Merge to `master` and push. Delete the branch afterwards — a merged
  branch left on the remote is just a second copy of `master`.
  The worktree rule above still applies: isolate, merge, push, delete. The
  worktree is for isolation, not for review.
  Before deleting any branch, confirm `git log --oneline origin/master..<branch>`
  is empty. A branch that still holds unique commits is not a leftover.
