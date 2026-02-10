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
└── assets/            (optional — templates, images, fonts)
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

## What NOT to Include

- README.md, CHANGELOG.md, INSTALLATION_GUIDE.md
- "When to use this skill" sections in the body (put in description)
- Information Claude already knows (basic language syntax, common patterns)
- Deeply nested reference hierarchies (keep one level deep)
