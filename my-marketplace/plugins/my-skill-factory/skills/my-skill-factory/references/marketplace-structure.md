# Hideki's Marketplace Structure

## Directory Layout

```
D:\Shared\agents\my-skills\
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
│                   ├── SKILL.md
│                   └── references\
├── <skill-name>\                            # Skill source (working copy)
│   ├── SKILL.md
│   └── references\
└── my-skill-factory\                        # This skill
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
