# agent-skill-set

A collection of agent skills and tools for Claude Code and Cursor.

## Skills

| Skill | Description |
|-------|-------------|
| [multi-agent-council](multi-agent-council/) | Multi-LLM council for architecture decisions and code reviews (submodule) |
| [dev-workflow](dev-workflow/) | End-to-end development workflow: plan, implement, commit, and PR |
| [review-pr](review-pr/) | Detailed code review on GitHub pull requests |
| [my-skill-factory](my-skill-factory/) | Create, build, and install custom skills |
| [my-marketplace](my-marketplace/) | Local skill marketplace |

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
