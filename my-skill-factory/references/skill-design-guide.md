# Skill Design Quick Reference

## Frontmatter

```yaml
---
name: skill-name
description: What it does + all trigger phrases and contexts. This is the ONLY thing Claude sees before the skill loads, so include ALL "when to use" info here.
---
```

## Skill Structure

```
skill-name/
├── SKILL.md           (required — workflow + instructions)
├── references/        (optional — loaded on demand)
├── scripts/           (optional — deterministic operations)
├── assets/            (optional — templates, images, fonts)
└── feedback/          (optional — execution log and amendment history)
```

## Body Guidelines

- Use imperative form ("Extract data", not "This skill extracts data")
- Keep under 500 lines; split into references/ when approaching limit
- Only include what Claude doesn't already know
- Prefer concise examples over verbose explanations

## Freedom Levels

| Level | When | Example |
|-------|------|---------|
| High (text instructions) | Multiple valid approaches | "Review code for issues" |
| Medium (pseudocode) | Preferred pattern exists | "Use this template for output" |
| Low (exact scripts) | Fragile/critical operations | "Run this exact script to rotate PDF" |

## Progressive Disclosure

1. **Metadata** (name + description) — always loaded (~100 words)
2. **SKILL.md body** — loaded when skill triggers (<5k words)
3. **references/** — loaded on demand by Claude (unlimited)

## Common Patterns

### Workflow-based (sequential steps)
```markdown
## Step 1: Gather input
## Step 2: Process
## Step 3: Generate output
```

### Task-based (different operations)
```markdown
## Quick Start
## Task A: Create
## Task B: Edit
## Task C: Analyze
```

## Behavior Scenarios

Define 3-5 Given/When/Then scenarios before writing the SKILL.md body. These act as acceptance criteria for the skill's design.

```gherkin
Scenario: <descriptive name>
  Given <trigger context>
  When <user action>
  Then <skill output>
```

Include a `## Behavior Scenarios` section in the generated SKILL.md. See `references/bdd-skill-scenarios.md` for full templates by skill type, update-delta guidance, and anti-patterns.

## Output Templates

When the skill produces structured output, provide the exact template:

```markdown
## Output Format

Use this structure:
\`\`\`markdown
# Title
## Summary
<content>
## Findings
<content>
\`\`\`
```

## Self-Improvement Support

For skills expected to be used repeatedly, include a feedback loop. Read `references/skill-improvement-guide.md` for the full protocol.

| Opt-in Level | What to add | When to use |
|-------------|-------------|-------------|
| **None** | Nothing | One-shot skills, simple utilities, CLI wrappers, <5 expected uses |
| **Observe** | `### Retrospective` final step only | New skills gathering initial data |
| **Full** | `### Retrospective` + `### Feedback Check` | Complex workflows, frequent use, known quality issues |

Assess the level during Step 2 (Design the Skill):
- Will this skill be used more than 5 times? → at least Observe
- Does this skill have a complex multi-phase workflow? → Full
- Is this a one-shot install-and-forget skill? → None

### Skill Versioning

Add a `version` field to the SKILL.md frontmatter:

```yaml
---
name: skill-name
description: ...
version: 1.0.0
---
```

- Starts at `1.0.0` on creation
- Patch bump (`1.0.x`) for minor instruction tweaks
- Minor bump (`1.x.0`) for workflow changes or new steps
- Incremented by the factory's "Improve" workflow on each amendment

## What NOT to Include

- README.md, CHANGELOG.md, INSTALLATION_GUIDE.md
- "When to use this skill" sections in the body (put in description)
- Information Claude already knows (basic language syntax, common patterns)
- Deeply nested reference hierarchies (keep one level deep)
