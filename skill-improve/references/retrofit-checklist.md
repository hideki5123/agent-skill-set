# Retrofit Checklist

Step-by-step process for adding OIAE components to an existing skill. Read `my-skill-factory/references/skill-improvement-guide.md` for the templates referenced below.

## Pre-check

Before modifying, verify what's already present:

| Component | How to check | Required for |
|-----------|-------------|--------------|
| `version:` in frontmatter | Search between `---` markers | All levels |
| `### Retrospective` section | Search SKILL.md body | Observe, Full |
| `### Feedback Check` section | Search SKILL.md body | Full only |
| `feedback/` directory | Check directory existence | Created at runtime |

## Step 1: Add Version to Frontmatter

If the frontmatter has no `version:` field, add it:

```yaml
---
name: skill-name
description: ...
version: 1.0.0          # ← Add this line
---
```

Insert after the `description` field (or after `name` if description is a multi-line `>` block).

## Step 2: Assess Opt-in Level

| Level | Criteria | Components to add |
|-------|----------|-------------------|
| **Full** | Multi-phase workflow, >5 expected uses, complex output, known quality issues | Feedback Check + Retrospective |
| **Observe** | Uncertain usage, simpler workflow, want to gather data first | Retrospective only |
| **None** | One-shot skill, CLI wrapper, deterministic utility, <5 expected uses | Nothing (version only) |

Present the assessment to the user before proceeding.

## Step 3: Add Feedback Check (Full level only)

**Placement**: Insert immediately after one of these (in priority order):
1. `### Phase 0` or `### Preflight` section (if it exists)
2. The first `##` heading in the workflow
3. After the arguments table

**Template** (from skill-improvement-guide.md):

```markdown
### Feedback Check

If `feedback/log.md` exists and has 5 or more entries, read the last 10 entries.
If a pattern is apparent (same issue in 3+ entries, or average rating below 3):
- Tell the user: "Recurring feedback detected: [brief pattern]. Consider running `/skill-improve --skill <skill-name>`."
- Continue with normal execution.
```

Replace `<skill-name>` with the actual skill name.

## Step 4: Add Retrospective (Observe or Full)

**Placement**: Insert at the end of the workflow, specifically:
1. Before `## Behavior Scenarios` section (if it exists)
2. Before `## References` section (if it exists)
3. At the very end of the file (if neither section exists)

**Template** (from skill-improvement-guide.md):

```markdown
### Retrospective

After completing the workflow, reflect on the entire execution session:

1. Consider: Were there mid-session corrections? Rejected outputs? Plan changes? Errors?
2. Ask the user: "Quick feedback on this run? (1-5 rating, note any issues, or press enter to skip)"
3. If the user provides feedback OR if corrections/issues occurred during this session:
   a. Create `feedback/` directory if it does not exist
   b. Read `feedback/log.md` (create with `# Feedback Log` header if it does not exist)
   c. Prepend a new entry after the header using the log format from `my-skill-factory/references/skill-improvement-guide.md`
   d. Fill in: current timestamp, skill version from frontmatter, task description, outcome assessment,
      corrections that occurred during the session, issues encountered, user's note
4. If the user skips AND no corrections or issues occurred, end without recording.
```

## Step 5: Verify

After adding components:
1. Read the modified SKILL.md to verify sections are correctly placed
2. Run the install script to update the marketplace
3. Confirm the skill still loads correctly in a new session
