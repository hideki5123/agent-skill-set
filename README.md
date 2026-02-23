# agent-skill-set

A collection of agent skills and tools for Claude Code and Cursor.

## Skills

| Skill | Description |
|-------|-------------|
| [multi-agent-council](multi-agent-council/) | Multi-LLM council for architecture decisions and code reviews (submodule) |
| [dev-workflow](dev-workflow/) | End-to-end development workflow: plan, implement, commit, and PR (supports multi-agent team) |
| [tdd-team-workflow](tdd-team-workflow/) | Test-Driven Development workflow with multi-agent team discussion |
| [review-pr](review-pr/) | Detailed code review on GitHub pull requests |
| [my-skill-factory](my-skill-factory/) | Create, build, and install custom skills |
| [my-marketplace](my-marketplace/) | Local skill marketplace |
| [session-handover](session-handover/) | Auto-generate session handover via PreCompact hook (install once, works forever) |

## Authoring Workflow

- Treat each skill root as source of truth (`<skill>/SKILL.md`, `<skill>/references/*`).
- Do not hand-edit `my-marketplace/plugins/*/skills/*`; those are generated artifacts.

### Sync Marketplace Artifacts

```bash
python sync_marketplace.py
```

Sync selected skills only:

```bash
python sync_marketplace.py --skills dev-workflow review-pr
```

### Validate Drift

```bash
python sync_marketplace.py --validate
```

Use this in CI or before publishing to ensure source and generated plugin skills are in sync.

### Unified Sync (Claude + Codex)

```bash
python sync_skills.py
```

Sync selected skills only:

```bash
python sync_skills.py --skills dev-workflow review-pr
```

Sync a single target:

```bash
python sync_skills.py --targets claude
python sync_skills.py --targets codex
```

Validate drift for selected targets:

```bash
python sync_skills.py --validate
```

Optional Codex home override:

```bash
python sync_skills.py --targets codex --codex-home "D:/path/to/.codex"
```

`sync_skills.py` syncs marketplace artifacts under `my-marketplace/` and Codex skills under `$CODEX_HOME/skills` (fallback: `~/.codex/skills`). It does not update `~/.claude` install state.
