# Amendment History

## AMD-001 — 2026-04-22
- **Pattern**: Skill used a fixed generic description template and ignored project-specific board templates, forcing the user to redirect the draft to match the project's conventions.
- **Evidence**: 2026-04-22 log entry ("follow the board template of Engineering Task Description").
- **Change**: Phase 3 now fetches the project's per-issue-type default description via `getJiraIssueTypeMetaWithFields` (reading `fields[description].defaultValue`) and uses it as the outer skeleton. Generic `references/description-template.md` is explicitly marked fallback-only.
- **Files Modified**: `SKILL.md` (Phase 3, References), `references/description-template.md` (fallback framing, formatting notes).
- **Version Bump**: 1.0.0 → 1.1.0
- **Git Commit**: 58a55d4
- **Status**: applied — monitoring
---

## AMD-002 — 2026-04-22
- **Pattern**: Slack mention placeholders (`<@UXXX>`, `<#CXXX>`, `<!subteam^SXXX>`) flowed into the ticket draft unresolved, leaking raw IDs and forcing the user to explain the syntax and supply a human-readable handle.
- **Evidence**: 2026-04-22 log entry ("what do you mean subteam?" / "please add surface info of user group @biz-cx-team").
- **Change**: New `references/slack-mention-resolution.md` spells out resolution rules for `<@U…>` / `<#C…>` / `<!subteam^S…>` / broadcast mentions / URLs. Phase 2 now requires resolution before Phase 3 and instructs the skill to prompt for a user-group handle when the placeholder is bot-unresolvable. `description-template.md` formatting notes forbid raw IDs in ticket text.
- **Files Modified**: new `references/slack-mention-resolution.md`; `SKILL.md` (Phase 2, References); `references/description-template.md` (formatting notes).
- **Version Bump**: covered by AMD-001 bump (1.0.0 → 1.1.0)
- **Git Commit**: 58a55d4
- **Status**: applied — monitoring
---

## AMD-003 — 2026-04-22
- **Pattern**: Draft presented proposed labels with no indication of whether each label already existed in the target project, prompting the user to ask.
- **Evidence**: 2026-04-22 log entry ("Is the label existing already?").
- **Change**: Phase 3 now annotates every proposed label inline as `(existing)` or `(NEW — needs approval)`. The pre-existing "approval before creating a new label" constraint is preserved; this amendment only surfaces it at draft time.
- **Files Modified**: `SKILL.md` (Phase 3 "Present draft(s)" and label-approval block).
- **Version Bump**: covered by AMD-001 bump (1.0.0 → 1.1.0)
- **Git Commit**: 58a55d4
- **Status**: applied — monitoring
---

## AMD-004 — 2026-04-22
- **Pattern**: Conversation Excerpt was included by default and duplicated information already captured under Decisions / Action Items.
- **Evidence**: 2026-04-22 log entry ("I don't think Conversation Excerpt is necessary.").
- **Change**: `Conversation Excerpt` removed from the default template skeleton and reclassified as opt-in — only included when a specific quote captures a non-obvious decision, trade-off, or nuance Decisions / Action Items cannot convey.
- **Files Modified**: `references/description-template.md` (template skeleton, Section Guidelines row).
- **Version Bump**: covered by AMD-001 bump (1.0.0 → 1.1.0)
- **Git Commit**: 58a55d4
- **Status**: applied — monitoring
---
