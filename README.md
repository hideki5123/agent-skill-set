# agent-skill-set

A collection of agent skills and tools for Claude Code and Cursor.

## Skills

| Skill | Description |
|-------|-------------|
| [confluence](confluence/) | Read, search, create, update, move, and delete Confluence pages via `confluence-cli` |
| [dev-workflow](dev-workflow/) | End-to-end TDD development workflow with multi-agent team review |
| [jira-cli](jira-cli/) | View, search, create, update, and delete Jira issues, comments, sprints via `@pchuri/jira-cli` |
| [e2e-test](e2e-test/) | Run frontend E2E tests using Playwright MCP browser tools with screenshot evidence |
| [multi-agent-council](multi-agent-council/) | Multi-LLM council for architecture decisions and code reviews (submodule) |
| [my-skill-factory](my-skill-factory/) | Create, build, and install custom skills into the local marketplace |
| [orch-qa](orch-qa/) | QA/QC engineer that evaluates codebases for test quality and writes missing tests |
| [playwright-cli](playwright-cli/) | Run Playwright CLI commands for test execution, codegen, reporting, and debugging |
| [playwright-codegen](playwright-codegen/) | Record browser interactions with Playwright codegen and transform into test suites |
| [pm-review](pm-review/) | Review local changes from a PMBOK-based product management perspective |
| [pr-review](pr-review/) | Review a teammate's pull request from multiple expert perspectives |
| [review-local](review-local/) | Review local git changes from 8 expert perspectives as a pre-commit quality gate |
| [scenario-gen](scenario-gen/) | Generate test scenarios from git branch changes with screenshot evidence |
| [self-pr-review](self-pr-review/) | Self-review loop: request AI reviews (Copilot + Gemini), apply fixes, repeat until clean |
| [session-handover](session-handover/) | Auto-generate session handover via PreCompact hook (install once, works forever) |
| [slack-cli](slack-cli/) | Operate Slack from the terminal via `slack-cli` — messages, unreads, search, uploads |
| [subagent-gen](subagent-gen/) | Generate PROJECT-KNOWLEDGE.md profiles for subagent deep domain expertise |
| [address-pr-comments](address-pr-comments/) | Autonomously fetch and apply AI reviewer comments on a GitHub PR |

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
| [GitHub CLI (gh)](https://cli.github.com/) | OS package manager | dev-workflow, pr-review, self-pr-review, address-pr-comments |
| npm dependencies | `npm install` | confluence, jira-cli, slack-cli, playwright-cli, playwright-codegen, e2e-test, scenario-gen |

## Authoring Workflow

- Treat each skill root as source of truth (`<skill>/SKILL.md`, `<skill>/references/*`).
- Do not hand-edit `my-marketplace/plugins/*/skills/*`; those are generated artifacts.
- Generated trees under `my-marketplace/plugins/*/skills/*` are build artifacts and are gitignored.

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

This handles the full pipeline: marketplace structure, plugin cache, `installed_plugins.json`, and `settings.json`. A pre-push hook also auto-installs changed skills on `git push`.
