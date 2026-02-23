# Hideki's Marketplace Structure

## Directory Layout

```
D:\Shared\agents\my-skills\
├── <skill-name>\                            # Canonical source (authoring)
│   ├── SKILL.md
│   └── references\
├── my-marketplace\                          # Local marketplace root
│   ├── .claude-plugin\
│   │   └── marketplace.json                 # Root registry (lists all plugins)
│   └── plugins\
│       └── <plugin-name>\                   # One dir per plugin
│           ├── .claude-plugin\
│           │   ├── plugin.json              # Plugin metadata
│           │   └── marketplace.json         # Per-plugin marketplace ref
│           └── skills\
│               └── <skill-name>\
│                   ├── SKILL.md             # Generated from source
│                   └── references\          # Generated from source
└── my-skill-factory\                        # This skill
```

## Source of Truth and Sync

- Source of truth is the root skill directory (`<skill>/...`).
- Marketplace plugin skills are generated artifacts.
- Regenerate artifacts with:

```bash
python scripts/sync_marketplace.py
```

- Validate no drift between source and generated artifacts:

```bash
python scripts/sync_marketplace.py --validate
```

- Sync a subset:

```bash
python scripts/sync_marketplace.py --skills dev-workflow review-pr
```

## Claude Code Config Files

| File | Purpose |
|------|---------|
| `~/.claude/plugins/known_marketplaces.json` | Registered marketplace sources |
| `~/.claude/plugins/installed_plugins.json` | Plugin install registry (version 2) |
| `~/.claude/settings.json` → `enabledPlugins` | Which plugins are active |
| `~/.claude/plugins/cache/hideki-plugins/<name>/<version>/` | Cached plugin files |

## Plugin Key Format

```
<plugin-name>@hideki-plugins
```

Example: `review-pr@hideki-plugins`

## Root marketplace.json Schema

```json
{
  "name": "hideki-plugins",
  "owner": { "name": "Hideki" },
  "plugins": [
    {
      "name": "<plugin-name>",
      "source": "./plugins/<plugin-name>",
      "description": "<short description>"
    }
  ]
}
```

## Per-plugin plugin.json Schema

```json
{
  "name": "<plugin-name>",
  "version": "1.0.0",
  "description": "<description>",
  "author": { "name": "Hideki" },
  "keywords": ["<keyword>"],
  "license": "MIT",
  "skills": "./skills"
}
```

## Contributor Rule

- Edit skill content only under root source directories.
- Never manually edit files under `my-marketplace/plugins/*/skills/*`.
- Generated files under `my-marketplace/plugins/*/skills/*` are build artifacts and should remain untracked in Git.
- After edits: run `python scripts/sync_marketplace.py`, then `python scripts/sync_marketplace.py --validate`.

## installed_plugins.json Entry Schema

```json
{
  "<name>@hideki-plugins": [{
    "scope": "user",
    "installPath": "C:\\Users\\Hideki\\.claude\\plugins\\cache\\hideki-plugins\\<name>\\<version>",
    "version": "<version>",
    "installedAt": "<ISO timestamp>",
    "lastUpdated": "<ISO timestamp>",
    "gitCommitSha": ""
  }]
}
```
