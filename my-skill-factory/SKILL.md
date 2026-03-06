---
name: my-skill-factory
description: Create, build, and install custom Claude Code skills into Hideki's local marketplace. End-to-end workflow from requirements gathering to a fully installed and usable skill. Use when the user asks to create a new skill, build a skill, make a plugin, add a new capability, or says "make me a skill for X". Also use when updating or reinstalling an existing custom skill. Trigger phrases include "create skill", "make skill", "new skill", "build plugin", "skill for X", "update skill".
---

# Skill Factory

Create custom Claude Code skills and install them into the local `hideki-plugins` marketplace in one workflow.

## Workflow

1. **Gather requirements** — Understand what the skill should do
2. **Design the skill** — Plan structure, references, scripts, assets
3. **Create skill files and install** — Write SKILL.md, supporting resources, then always install immediately
4. **Verify** — Confirm the skill appears in a new session

## Step 1: Gather Requirements

Ask the user:
- What should the skill do? Get 2-3 concrete usage examples.
- What triggers it? (e.g., "review PR", "create diagram")
- Does it need external tools? (gh CLI, APIs, MCP servers)
- What output format? (markdown report, file creation, GitHub actions)

Keep it to 2-3 focused questions max. Skip if the user already provided enough detail.

### Formalize as BDD scenarios

After gathering requirements, write 3-5 Given/When/Then scenarios covering:
1. Primary use case
2. One or two secondary paths
3. An edge case (missing info, invalid input)

Read `references/bdd-skill-scenarios.md` for templates by skill type and anti-patterns.

## Step 2: Design the Skill

Read `references/skill-design-guide.md` for design patterns and structure guidance.

Decide:
- **Freedom level**: High (text guidance) vs Low (exact scripts)
- **References needed?** Detailed checklists, schemas, examples → put in `references/`
- **Scripts needed?** Deterministic operations → put in `scripts/`
- **Assets needed?** Templates, images → put in `assets/`
- **Scenario mapping**: Map each BDD scenario to SKILL.md sections (trigger context → frontmatter, workflow → body, outputs → format/references)

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
- Include a `## Behavior Scenarios` section with the Given/When/Then specs from Step 1

### Supporting files

Place in subdirectories as needed:
- `references/` — Loaded by Claude on demand
- `scripts/` — Executed directly
- `assets/` — Used in output, not loaded into context

### Install into marketplace

**Always run the install script immediately after creating or updating skill files. Do not ask the user — just install.**

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

## Step 4: Verify

Launch a new CLI session to confirm:

```bash
echo "List all available skills. Just list the skill names as a bullet list." | claude -p
```

The new skill should appear as `<skill-name>:<skill-name>` in the output.

## Updating an Existing Skill

1. **Write scenarios for the change** — Define Given/When/Then scenarios for new or modified behavior
2. **Identify the delta** — Compare new scenarios against existing ones; classify as Added, Modified, or Removed
3. **Edit skill files and install** — Update SKILL.md and supporting files, then always run the install script immediately (it overwrites the previous installation)
4. **Validate coverage** — Confirm each new scenario has corresponding content in SKILL.md
5. **Verify** — New sessions will pick up the changes automatically

## Behavior Scenarios

```gherkin
Scenario: Create a new skill from scratch
  Given the user has a clear idea for a new skill
  When the user says "create a skill for X"
  Then the skill gathers requirements, writes BDD scenarios, designs structure, creates files, always installs immediately without asking, and verifies

Scenario: Update an existing skill
  Given a skill is already installed in the marketplace
  When the user says "update the X skill to add Y"
  Then the skill writes change-delta scenarios, identifies added/modified/removed behaviors, edits files, always re-installs immediately without asking, and verifies

Scenario: Vague request
  Given the user provides only a one-line idea without details
  When the user says "make me a skill"
  Then the skill asks 2-3 focused questions to clarify purpose, triggers, and output format

Scenario: Skill with external dependencies
  Given the user needs a skill that relies on CLI tools or MCP servers
  When the user describes the skill's requirements
  Then the skill identifies dependencies, documents them in SKILL.md, and includes setup guidance

Scenario: Re-install without changes
  Given a skill's files have not changed
  When the user re-runs the install script
  Then the script overwrites the previous installation and the skill remains functional
```

## References

- `references/skill-design-guide.md` — Quick reference for skill structure, freedom levels, patterns, and what to include/exclude
- `references/bdd-skill-scenarios.md` — Given/When/Then templates by skill type, update-delta guidance, and anti-patterns
- `references/marketplace-structure.md` — Full directory layout, JSON schemas, and config file locations for the local marketplace
