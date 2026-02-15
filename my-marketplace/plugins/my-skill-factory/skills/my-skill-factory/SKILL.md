---
name: my-skill-factory
description: Create, build, and install custom Claude Code skills into Hideki's local marketplace. End-to-end workflow from requirements gathering to a fully installed and usable skill. Use when the user asks to create a new skill, build a skill, make a plugin, add a new capability, or says "make me a skill for X". Also use when updating or reinstalling an existing custom skill. Trigger phrases include "create skill", "make skill", "new skill", "build plugin", "skill for X", "update skill".
---

# Skill Factory

Create custom Claude Code skills and install them into the local `hideki-plugins` marketplace in one workflow.

## Workflow

1. **Gather requirements** — Understand what the skill should do
2. **Design the skill** — Plan structure, references, scripts, assets
3. **Create skill files** — Write SKILL.md and supporting resources
4. **Install into marketplace** — Register, cache, and enable the plugin
5. **Verify** — Confirm the skill appears in a new session

## Step 1: Gather Requirements

Ask the user:
- What should the skill do? Get 2-3 concrete usage examples.
- What triggers it? (e.g., "review PR", "create diagram")
- Does it need external tools? (gh CLI, APIs, MCP servers)
- What output format? (markdown report, file creation, GitHub actions)

Keep it to 2-3 focused questions max. Skip if the user already provided enough detail.

## Step 2: Design the Skill

Read `references/skill-design-guide.md` for design patterns and structure guidance.

Decide:
- **Freedom level**: High (text guidance) vs Low (exact scripts)
- **References needed?** Detailed checklists, schemas, examples → put in `references/`
- **Scripts needed?** Deterministic operations → put in `scripts/`
- **Assets needed?** Templates, images → put in `assets/`

## Step 3: Create Skill Files

Create the skill directory at `D:\Shared\agents\my-skills\<skill-name>\`.

### SKILL.md frontmatter

```yaml
---
name: <skill-name>
description: <What it does + ALL trigger phrases. This is the only text Claude sees before loading the skill body.>
---
```

The description is critical — it controls when the skill triggers. Include:
- What the skill does (1 sentence)
- All contexts/scenarios when to use it
- Specific trigger phrases

### SKILL.md body

- Use imperative form
- Keep under 500 lines
- Only include knowledge Claude doesn't already have
- Reference any `references/` files with clear "read this when..." guidance

### Supporting files

Place in subdirectories as needed:
- `references/` — Loaded by Claude on demand
- `scripts/` — Executed directly
- `assets/` — Used in output, not loaded into context

## Step 4: Install into Marketplace

Run the installation script:

```bash
python "D:\Shared\agents\my-skills\my-skill-factory\scripts\install_skill.py" "D:\Shared\agents\my-skills\<skill-name>"
```

For a specific version:

```bash
python "D:\Shared\agents\my-skills\my-skill-factory\scripts\install_skill.py" "D:\Shared\agents\my-skills\<skill-name>" --version 1.1.0
```

The script handles everything:
- Creates marketplace plugin structure under `my-marketplace/plugins/<name>/`
- Registers in root `marketplace.json`
- Caches to `~/.claude/plugins/cache/hideki-plugins/<name>/<version>/`
- Adds entry to `installed_plugins.json`
- Enables in `settings.json`

Read `references/marketplace-structure.md` for full details on the file layout and JSON schemas.

## Step 5: Verify

Launch a new CLI session to confirm:

```bash
echo "List all available skills. Just list the skill names as a bullet list." | claude -p
```

The new skill should appear as `<skill-name>:<skill-name>` in the output.

## Updating an Existing Skill

To update an already-installed skill:

1. Edit the skill files in `D:\Shared\agents\my-skills\<skill-name>\`
2. Re-run the install script (it overwrites the previous installation)
3. New sessions will pick up the changes automatically

## References

- `references/skill-design-guide.md` — Quick reference for skill structure, freedom levels, patterns, and what to include/exclude
- `references/marketplace-structure.md` — Full directory layout, JSON schemas, and config file locations for the local marketplace
