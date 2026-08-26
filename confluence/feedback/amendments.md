# Amendment History

## AMD-001 — 2026-08-26
- **Pattern**: Scripted storage-XML edits are fragile: local-id anchors silently vanish after human edits, and concurrent edits get clobbered without a re-fetch.
- **Evidence**: 2026-08-21〜26 sessions (page 3058106393 "Dedicated Escalation Mode"): v12→v13 concurrent edit dropped local-ids and broke an id-anchored edit; literal-text anchors + count==1 asserts recovered it.
- **Change**: Added "Surgical edits on storage XML — safety rules" (re-fetch before update, never anchor on local-id, assert-unique replace pattern, omit local-id on new elements).
- **Files Modified**: SKILL.md (Common Agent Workflows)
- **Version Bump**: (none) → 1.1.0
- **Git Commit**: 6248c83
- **Status**: applied — monitoring
---
