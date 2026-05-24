# Amendment History

## AMD-001 — 2026-05-25
- **Pattern**: On the `needs-init` branch, the LLM stops after `/init` returns and never runs `python "$SCRIPT" --wire`, leaving the repo in `ready-claude` state. Root cause: the post-`/init` continuation instruction lived in a single line of a state table; after `/init`'s long, content-heavy detour the outer skill workflow lost salience.
- **Evidence**: log.md entry 2026-05-25T01:14+09:00 (rating 1/5, user had to manually trigger `--wire`).
- **Change**:
  1. Added a top-of-workflow callout: "Critical — do not stop after `/init`. The deliverable is the symlink, not a generated CLAUDE.md."
  2. Promoted the `needs-init` branch out of the table into a dedicated `needs-init detail` subsection with a numbered, mandatory same-turn sequence (detect → `/init` → `--wire` → report → verify). Includes an explicit "if you're about to message the user without having run --wire, go back" guardrail.
  3. Added a new "Step 4: Verify wired" — a mandatory final `--detect` whose JSON state must be `"wired"` before the skill reports success. Catches the failure mode at the post-condition level regardless of which branch was taken.
  4. Updated the `wired` row to note Step 4 is already satisfied (avoid redundant re-detect on no-op runs).
- **Files Modified**: `SKILL.md` (frontmatter version, Workflow callout, Step 2 table, new `needs-init detail` subsection, new Step 4).
- **Version Bump**: 1.0.0 → 1.1.0
- **Git Commit**: (pending — user will commit)
- **Status**: applied — monitoring
---
