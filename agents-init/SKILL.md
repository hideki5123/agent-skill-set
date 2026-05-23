---
name: agents-init
version: 1.0.0
description: Generate AGENTS.md (cross-tool agent context — Codex CLI, Aider, Cursor, etc.) and wire CLAUDE.md as a symlink so Claude Code reads the same file. Delegates content generation to Claude's built-in /init when needed, then renames + symlinks. Idempotent. Triggers — /agents-init, "generate agents.md", "create agents.md", "share claude and codex context", "set up agents file", "init agents", "agents-init", "cross-tool agent context", "wire claude and agents".
---

# agents-init

Wire `AGENTS.md` (the cross-vendor agent-context convention) as the single source of truth, with `CLAUDE.md` as a symlink so Claude Code reads the same file. Idempotent — re-running on an already-wired repo is a no-op.

All filesystem mutation lives in `scripts/wire_agents.py`. Never use Bash `mv` / `ln` / `cp` / `rm` to manipulate `CLAUDE.md` or `AGENTS.md` directly — always invoke the script.

## Resolve the script path once

At the start of every invocation, resolve the script path (handles version bumps):

```bash
SCRIPT="$(ls -d ~/.claude/plugins/cache/hideki-plugins/agents-init/*/skills/agents-init/scripts/wire_agents.py 2>/dev/null | sort -V | tail -1)"
```

If `$SCRIPT` is empty, the skill is not installed correctly — tell the user and stop.

## Workflow

### Step 1: Detect state

From the project root the user wants to wire (do NOT change directory away from the user's cwd):

```bash
python "$SCRIPT" --detect
```

Stdout is one JSON line. For `conflict`, a unified diff is also printed to stderr.

```json
{"state": "...", "platform": "linux|darwin|windows", "claude_is_symlink": false, "symlink_target": null, "claude_real_file": false, "agents_exists": false}
```

Possible `state` values: `needs-init`, `ready-claude`, `ready-agents`, `identical`, `conflict`, `wired`, `foreign-symlink`.

### Step 2: Branch on `state`

| `state` | LLM action |
| --- | --- |
| `needs-init` | Invoke Claude's built-in `/init` to populate CLAUDE.md. Once it returns, run `python "$SCRIPT" --wire` (state will now be `ready-claude`). |
| `ready-claude` | Confirm via `AskUserQuestion`: "Rename existing CLAUDE.md → AGENTS.md and add a CLAUDE.md symlink?". On confirm, run `python "$SCRIPT" --wire`. Do NOT re-run `/init` — the user's content is preserved. |
| `ready-agents` | Run `python "$SCRIPT" --wire` directly (no confirmation — only adds a symlink). |
| `identical` | Run `python "$SCRIPT" --wire` directly. |
| `conflict` | Show the diff (already on stderr from step 1) to the user. `AskUserQuestion`: "Keep AGENTS.md (discard CLAUDE.md), keep CLAUDE.md (back up AGENTS.md), or abort?". Then `python "$SCRIPT" --wire --prefer=agents` or `--prefer=claude`. |
| `wired` | No-op. Tell user "CLAUDE.md → AGENTS.md is already wired" and stop. |
| `foreign-symlink` | STOP. The detect output has `symlink_target`. `AskUserQuestion`: "CLAUDE.md currently symlinks to `<target>`. Repoint it to AGENTS.md?". On confirm, `python "$SCRIPT" --wire --force`. |

When the script is invoked in `--wire` mode against a `needs-init` state, it returns an error — that's intentional, /init must run first.

### Step 3: Report

The `--wire` output is one JSON line with:

- `actions` — literal shell-style commands the script ran (e.g. `mv CLAUDE.md AGENTS.md`, `ln -s AGENTS.md CLAUDE.md`).
- `warnings` — any `.gitignore` issues.
- `suggested_git` — the commit command to recommend.

Relay all three to the user in a short message. Do NOT execute the git commit yourself — print it as a suggestion.

If `actions` contains a `WARNING: file copy used` line, surface it prominently — the user is on Windows and must re-run the skill after editing AGENTS.md.

## Rules

- **Never commit on behalf of the user.** Print the suggested git command; let them run it.
- **Never duplicate the script's filesystem logic in Bash.** Every mutation goes through `$SCRIPT`.
- **Never modify `.gitignore`.** The script only warns when a file is ignored.
- **Stay in the user's cwd.** The script operates on `./CLAUDE.md` and `./AGENTS.md` — wherever the user invoked the skill from.

## References

- `references/state-matrix.md` — full decision table with rationale per state. **WHEN TO READ:** only when you're unsure how to handle an edge case or want to confirm a branch's behavior. Routine invocations do not need it.
- `references/scenarios.feature` — Gherkin behavior spec. **WHEN TO READ:** only when auditing or amending this skill. Not needed for normal execution.

### Retrospective

After completing the workflow, reflect on this run:

1. Were there mid-session corrections, rejected outputs, or errors during `/init` or wiring?
2. Ask the user: "Quick feedback on this run? (1-5 rating, note any issues, or press enter to skip)"
   **If rating < 5, ALWAYS follow up**: "Why this rating? (concrete details help me improve)" — record verbatim as `Rating reason`.
3. If the user provides feedback OR corrections occurred:
   - Create `feedback/log.md` next to this SKILL.md if missing (header `# Feedback Log` then a blank line and `<!-- Append new entries at the top. Do not edit previous entries. -->`).
   - Prepend a new entry per the format in `references/skill-improvement-guide.md` of the my-skill-factory skill: timestamp, Skill Version (from frontmatter), Task, Outcome, Rating, Rating reason, Corrections, Issues, User Note.
4. If the user skips AND no corrections or issues occurred, end without recording.
