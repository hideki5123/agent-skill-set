---
name: agents-init
version: 1.1.0
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

> **Critical — do not stop after `/init`.** The deliverable of this skill is a `CLAUDE.md` symlink pointing to `AGENTS.md`, not a freshly-generated `CLAUDE.md`. When the `needs-init` branch delegates to `/init`, that's an *intermediate* step — `/init` returns control to you, and you MUST continue with `--wire` and the final verification in the same turn. The skill is complete only after Step 4 confirms the symlink exists.

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
| `needs-init` | **Two-part action — see "needs-init detail" below.** Step 1: invoke Claude's built-in `/init` to populate CLAUDE.md. Step 2 (mandatory, same turn): run `python "$SCRIPT" --wire`. |
| `ready-claude` | Confirm via `AskUserQuestion`: "Rename existing CLAUDE.md → AGENTS.md and add a CLAUDE.md symlink?". On confirm, run `python "$SCRIPT" --wire`. Do NOT re-run `/init` — the user's content is preserved. |
| `ready-agents` | Run `python "$SCRIPT" --wire` directly (no confirmation — only adds a symlink). |
| `identical` | Run `python "$SCRIPT" --wire` directly. |
| `conflict` | Show the diff (already on stderr from step 1) to the user. `AskUserQuestion`: "Keep AGENTS.md (discard CLAUDE.md), keep CLAUDE.md (back up AGENTS.md), or abort?". Then `python "$SCRIPT" --wire --prefer=agents` or `--prefer=claude`. |
| `wired` | No-op. Tell user "CLAUDE.md → AGENTS.md is already wired" and stop. Skip Step 4 (already verified by detect). |
| `foreign-symlink` | STOP. The detect output has `symlink_target`. `AskUserQuestion`: "CLAUDE.md currently symlinks to `<target>`. Repoint it to AGENTS.md?". On confirm, `python "$SCRIPT" --wire --force`. |

When the script is invoked in `--wire` mode against a `needs-init` state, it returns an error — that's intentional, /init must run first.

#### needs-init detail (high-risk path — read every time)

The `/init` call is a multi-turn detour that can take significant work (codebase exploration, writing CLAUDE.md). When `/init` returns, the temptation is to treat the new CLAUDE.md as the deliverable and stop. **Do not.** That leaves the repo in `ready-claude` state — not the goal.

Required sequence, in the **same skill invocation**:

1. Run `python "$SCRIPT" --detect` → state is `needs-init`.
2. Invoke `/init`. Wait for it to return.
3. **Immediately** run `python "$SCRIPT" --wire`. This renames the just-created `CLAUDE.md` → `AGENTS.md` and creates the `CLAUDE.md` symlink.
4. Continue to Step 3 (Report) and Step 4 (Verify). Do not end your turn between any of these.

If you find yourself about to send a message to the user that says "CLAUDE.md created" without having run `--wire` first, you are about to fail this skill — go back and run `--wire`.

### Step 3: Report

The `--wire` output is one JSON line with:

- `actions` — literal shell-style commands the script ran (e.g. `mv CLAUDE.md AGENTS.md`, `ln -s AGENTS.md CLAUDE.md`).
- `warnings` — any `.gitignore` issues.
- `suggested_git` — the commit command to recommend.

Relay all three to the user in a short message. Do NOT execute the git commit yourself — print it as a suggestion.

If `actions` contains a `WARNING: file copy used` line, surface it prominently — the user is on Windows and must re-run the skill after editing AGENTS.md.

### Step 4: Verify wired (mandatory before declaring done)

After any successful `--wire`, re-run detection to confirm the end state:

```bash
python "$SCRIPT" --detect
```

The JSON state must be `"wired"`. If it is anything else (`ready-claude`, `needs-init`, etc.), the wiring did not complete — surface the actual state to the user and stop; do not report success.

This step is non-negotiable on the `needs-init` path. It is the guardrail that catches the failure mode of "ran `/init`, forgot to wire". Skip only on `wired` (already verified in Step 1) and on aborted/`foreign-symlink`-declined runs.

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
