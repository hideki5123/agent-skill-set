---
name: session-handover
description: >
  Install a PreCompact hook that auto-generates .agent/local/HANDOVER.md before context compaction,
  plus a SessionStart hook that restores context from a previous handover. Run once to install,
  then it works automatically forever. Use when the user says "handover", "setup handover",
  "install handover hook", or wants seamless context transfer between sessions.
---

# Session Handover

Install PreCompact + SessionStart hooks into the project so session handover happens automatically.
Run this skill once -- after that, the hooks fire on their own.

## Installation Workflow

When this skill is triggered:

1. **Ensure `.claude/` directory exists** -- create if missing
2. **Read or create `.claude/settings.local.json`**
3. **Merge the hook config** below into the existing `hooks` object (preserve any existing hooks)
4. **Ensure `.agent/local/` is gitignored**:
   - Check `.gitignore` for `.agent/local/`
   - If missing, append:
     ```
     # AI agent local files (ephemeral, not for version control)
     .agent/local/
     ```
5. **Confirm** to the user that hooks are installed

### Hook Config to Install

Merge this into `.claude/settings.local.json`:

```json
{
  "hooks": {
    "PreCompact": [
      {
        "matcher": "auto",
        "hooks": [
          {
            "type": "agent",
            "prompt": "Before context compaction, generate a session handover. Create .agent/local/ if it doesn't exist. Write .agent/local/HANDOVER.md with: timestamp, current git branch, then these sections (omit if empty): What Was Done, In Progress, Decisions Made, Abandoned Approaches, Bugs & Fixes, Lessons Learned, Open Questions, Next Steps (as checkboxes), Key Files (as table). Use bullet points only. Be concise. If .agent/local/HANDOVER.md already exists, overwrite it.",
            "timeout": 120
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "startup|resume",
        "hooks": [
          {
            "type": "agent",
            "prompt": "Check if .agent/local/HANDOVER.md exists. If it does, read it and briefly summarize the previous session state: key decisions, in-progress work, and next steps. If it does not exist, do nothing.",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

### Merge Rules

- If `.claude/settings.local.json` doesn't exist, create it with the config above
- If it exists but has no `hooks` key, add the `hooks` key
- If it has `hooks` but no `PreCompact`/`SessionStart`, add them
- If `PreCompact` or `SessionStart` already have entries, **append** the new hook entries to the existing arrays (don't replace)
- Preserve all other settings in the file

## How It Works After Installation

1. **Context fills up** → Claude Code fires `PreCompact` → agent writes `.agent/local/HANDOVER.md`
2. **Compaction proceeds** normally
3. **Next session starts** → `SessionStart` hook reads the handover → context restored

No manual action needed. Fully automatic.

## HANDOVER.md Structure

The generated handover follows this format:

~~~markdown
# Session Handover

Generated: {timestamp}
Branch: {current branch name}

## What Was Done
- {Completed work items}

## In Progress
- {Partially completed work -- what's done, what remains}

## Decisions Made
- {Design decisions with reasoning}

## Abandoned Approaches
- {Approaches rejected and why}

## Bugs & Fixes
- {Bugs encountered and resolutions}

## Lessons Learned
- {Gotchas, quirks, workarounds}

## Open Questions
- {Unresolved decisions needing user input}

## Next Steps
- [ ] {Prioritized, actionable tasks}

## Key Files
| File | Role |
|------|------|
| {path} | {description} |
~~~

## Manual Trigger

Even after installation, you can manually generate a handover anytime:
- "generate handover"
- "wrap up session"

Write to `.agent/local/HANDOVER.md` using the same template.

## Uninstall

Remove the `PreCompact` and `SessionStart` entries from `.claude/settings.local.json`,
or delete the file if it only contains these hooks.
