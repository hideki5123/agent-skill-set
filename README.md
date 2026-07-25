# agent-skill-set

A collection of agent skills and tools for Claude Code and Cursor.

> **Upstream skill workflow:** several skills are vendored from
> [mattpocock/skills](https://github.com/mattpocock/skills) and form a composable
> workflow (align → specify → build → improve). See
> [docs/upstream-skill-workflow.md](docs/upstream-skill-workflow.md).

## Skills

| Skill | Description |
|-------|-------------|
| [confluence](confluence/) | Read, search, create, update, move, and delete Confluence pages via `confluence-cli` |
| [dev-workflow](dev-workflow/) | **⚠️ DEPRECATED** (disabled; superseded by upstream `grill-me`→`to-prd`→`tdd`→`improve-codebase-architecture`). End-to-end TDD development workflow with multi-agent team review |
| [jira-cli](jira-cli/) | View, search, create, update, and delete Jira issues, comments, sprints via `@pchuri/jira-cli` |
| [e2e-test](e2e-test/) | Run frontend E2E tests via `npx playwright test`, generated from a scenario CSV, with video/screenshot evidence |
| [my-skill-factory](my-skill-factory/) | Create, build, and install custom skills into the local marketplace |
| [orch-qa](orch-qa/) | QA/QC engineer that evaluates codebases for test quality and writes missing tests |
| [playwright-cli](playwright-cli/) | Run Playwright CLI commands for test execution, codegen, reporting, and debugging — including the guided codegen-to-test-suite workflow |
| [pm-review](pm-review/) | Review local changes from a PMBOK-based product management perspective |
| [postmortem](postmortem/) | Blameless incident report from a Slack thread — subagents collect evidence from Slack/GitHub/Jira, claims are fact-checked against the sources, then published to Confluence |
| [pr-review](pr-review/) | Review a teammate's pull request from multiple expert perspectives |
| [review-local](review-local/) | Review local git changes from 8 expert perspectives as a pre-commit quality gate |
| [scenario-gen](scenario-gen/) | Generate test scenarios from git branch changes with screenshot evidence |
| [self-pr-review](self-pr-review/) | Self-review loop: request AI reviews (Copilot + Gemini), apply fixes, repeat until clean |
| [session-handover](session-handover/) | Auto-generate session handover via PreCompact hook (install once, works forever) |
| [slack-cli](slack-cli/) | Operate Slack from the terminal via `slack-cli` — messages, unreads, search, uploads |
| [subagent-gen](subagent-gen/) | Generate PROJECT-KNOWLEDGE.md profiles for subagent deep domain expertise |
| [well-arch-security](well-arch-security/) | Review changes / docs against the Security pillar of Google's Well-Architected Framework, with per-risk Accept/Mitigate/Defer/Block prompts |
| [well-arch-reliability](well-arch-reliability/) | Review changes / docs against the Reliability pillar of Google's Well-Architected Framework, with per-risk Accept/Mitigate/Defer/Block prompts |
| [well-arch-cost](well-arch-cost/) | Review changes / docs against the Cost Optimization pillar of Google's Well-Architected Framework, with per-risk Accept/Mitigate/Defer/Block prompts |

### Supporting directories

| Directory | Description |
|-----------|-------------|
| [my-marketplace](my-marketplace/) | Local skill marketplace (generated plugin artifacts) |
| [scripts](scripts/) | Sync, install, and hook scripts |

## Dependencies

Some skills require external CLI tools. Install them before use.

| Tool | Install | Required by |
|------|---------|-------------|
| [Node.js / npm](https://nodejs.org/) | OS package manager | All npm-based tools below |
| [GitHub CLI (gh)](https://cli.github.com/) | OS package manager | dev-workflow, pr-review, self-pr-review |
| npm dependencies | `npm install` | confluence, jira-cli, slack-cli, playwright-cli, e2e-test, scenario-gen |

## Authoring Workflow

- Treat each skill root as source of truth (`<skill>/SKILL.md`, `<skill>/references/*`).
- Do not hand-edit `my-marketplace/plugins/*/skills/*`; those are generated artifacts.
- Generated trees under `my-marketplace/plugins/*/skills/*` are build artifacts and are gitignored.

### Vendoring Upstream Skills (on-demand)

Pull individual skills from an upstream GitHub repo on demand — no package
manager, no install-time code execution, pinned to a commit. Only the skills
you choose enter this repo; everything is plain file copies you can review in
the resulting diff.

```bash
# List what's available upstream (default repo: mattpocock/skills)
python scripts/vendor_skill.py --list

# Vendor one skill into a top-level <name>/ dir (auto-locates the upstream path)
python scripts/vendor_skill.py handoff

# Pin to a specific commit / tag / branch
python scripts/vendor_skill.py handoff --ref e3b90b5

# Vendor, then install into the local marketplace in one step
python scripts/vendor_skill.py handoff --install

# Use a different upstream repo / explicit path
python scripts/vendor_skill.py foo --repo owner/repo --path skills/foo
```

Each vendored skill gets a `LICENSE` file recording provenance (upstream URL,
source path, resolved commit SHA, retrieval date). The fetch step does not run
`install_skill.py` unless `--install` is passed — review the files first, then
install. To re-pull a newer upstream version, re-run with a later `--ref`.

### Sync Marketplace Artifacts

```bash
python scripts/sync_marketplace.py
```

Sync selected skills only:

```bash
python scripts/sync_marketplace.py --skills dev-workflow review-pr
```

### Validate Drift

```bash
python scripts/sync_marketplace.py --validate
```

Use this in CI or before publishing to ensure source and generated plugin skills are in sync.

### Unified Sync (Claude + Codex)

```bash
python scripts/sync_skills.py
```

Sync selected skills only:

```bash
python scripts/sync_skills.py --skills dev-workflow review-pr
```

Sync a single target:

```bash
python scripts/sync_skills.py --targets claude
python scripts/sync_skills.py --targets codex
```

Validate drift for selected targets:

```bash
python scripts/sync_skills.py --validate
```

Optional Codex home override:

```bash
python scripts/sync_skills.py --targets codex --codex-home "D:/path/to/.codex"
```

`scripts/sync_skills.py` syncs marketplace artifacts under `my-marketplace/` and Codex skills under `$CODEX_HOME/skills` (fallback: `~/.codex/skills`). It does not update `~/.claude` install state.

### Install a Single Skill Globally

```bash
python my-skill-factory/scripts/install_skill.py <skill-dir>/
```

This handles the full pipeline: marketplace structure, plugin cache, `installed_plugins.json`, and `settings.json`. See the next section for the git hooks that run this automatically.

## Multi-Machine Model & Git Hooks

Skill *sources* travel through git, but Claude Code's install state — the
plugin cache at `~/.claude/plugins/cache/`, the `installed_plugins.json`
ledger, and `enabledPlugins` in `~/.claude/settings.json` — is **per-machine**
and never leaves the box. A skill that exists in the repo stays invisible to
Claude Code sessions until it is installed on that machine. (The Codex side is
different: `sync_skills.py` writes `~/.codex/skills` directly, so it is always
current after a local sync run.)

Two non-blocking git hooks keep the Claude side reconciled. They live in the
tracked `scripts/hooks/` directory and are wired up via `core.hooksPath`.
Enable them **once per machine** after cloning:

```bash
bash scripts/setup_hooks.sh
```

| Hook | Fires on | What it does |
|------|----------|--------------|
| `pre-push` | `git push` | Refreshes the plugin cache for skills changed in the pushed commits (`--cache-only`). Skip with `git push --no-verify`. |
| `post-merge` | `git pull` / merge | Audits every skill against the install ledger: full-installs missing or version-bumped skills at their **committed** version, cache-refreshes skills whose source changed, and restores the generated `my-marketplace/` churn so a plain pull leaves the tree clean. |

Caveats:

- `post-merge` does not fire on `git fetch` + `git reset` — after that flow,
  run `scripts/hooks/post-merge` directly to reconcile.
- When running `install_skill.py` by hand, always pass
  `--version <version from my-marketplace/plugins/<name>/.claude-plugin/plugin.json>`.
  The flag defaults to `1.0.0`, which silently **downgrades** version-bumped
  skills and re-dirties the tracked marketplace metadata.
- Plugins explicitly disabled in `enabledPlugins` (e.g. the deprecated
  `dev-workflow`) are respected — the hooks never re-enable them.
- New skills and updates load in **new** Claude Code sessions only; already
  running sessions keep their skill set.
