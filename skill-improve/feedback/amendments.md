# Amendment History

## AMD-001 — 2026-05-13
- **Pattern**: 11 Gherkin scenarios were embedded inline in skill-improve's SKILL.md body (~60 lines of always-loaded content), the same anti-pattern that was just fixed in my-skill-factory.
- **Evidence**: my-skill-factory feedback log entry 2026-05-12T03:45:00Z ("Gerkinがまさかメインのdeskに入ってると思わなかった") — the user's complaint about BDD-in-body applies identically to skill-improve. User direct instruction 2026-05-13: 「同じような変更を /skill-improve:skill-improve にも実施して」.
- **Change**: Moved the entire `## Behavior Scenarios` block to `references/scenarios.feature`. SKILL.md body now carries only a 1-line pointer indicating the file is for audit/amendment use, not normal execution. Added a 12th scenario covering the new smoke-check requirement (AMD-003).
- **Files Modified**: `skill-improve/SKILL.md` — `## Behavior Scenarios`; new `skill-improve/references/scenarios.feature`.
- **Version Bump**: 1.0.0 → 1.1.0
- **Git Commit**: 858a1c6
- **Status**: applied — monitoring
---

## AMD-002 — 2026-05-13
- **Pattern**: References section listed files without explicit "WHEN TO READ" guidance, leaving Claude unsure whether to auto-load them. Same token-cost issue as my-skill-factory AMD-002.
- **Evidence**: my-skill-factory feedback log entry 2026-05-12T03:45:00Z (rating reason "トークン消費量とかを機にすべき") — applies symmetrically here.
- **Change**: References section now opens with "Read these on-demand only — they are not auto-loaded." Each entry carries an explicit "WHEN TO READ: ..." marker stating exactly which phase / situation justifies loading the file.
- **Files Modified**: `skill-improve/SKILL.md` — `## References` section.
- **Version Bump**: 1.0.0 → 1.1.0
- **Git Commit**: 858a1c6
- **Status**: applied — monitoring
---

## AMD-003 — 2026-05-13
- **Pattern**: Phase 2 (retrofit) and Phase 3 (amendment) both ended at `install + commit + push` with no verification that the modified skill actually loads. skill-improve modifies OTHER skills, so a broken edit could ship undetected. Same gap class as my-skill-factory AMD-005.
- **Evidence**: my-skill-factory feedback log entry 2026-05-12T04:10:00Z (codex-server smoke test caught 3 runtime-only bugs that code-only review missed). The user's direct instruction 2026-05-13 confirms the smoke-check principle should propagate to skill-improve.
- **Change**:
  1. **Phase 2 retrofit** — inserted a new step 6 "Smoke check (REQUIRED before reporting completion)" between install and commit. Verifies `claude -p` listing, frontmatter version, and path-discipline grep.
  2. **Phase 3 amendment** — split the old step 9 ("Install and commit") into separate step 9 (install), step 10 (smoke check, REQUIRED before commit/push), and step 11 (commit and push). Step 10 adds an extra check for skills with scripts/lib (deno `--check` equivalent).
  3. Added a new Gherkin scenario "Smoke check after retrofit or amendment" to `references/scenarios.feature`.
- **Files Modified**: `skill-improve/SKILL.md` — Phase 2 (retrofit) and Phase 3 (analyze feedback) sections; `skill-improve/references/scenarios.feature`.
- **Version Bump**: 1.0.0 → 1.1.0
- **Git Commit**: 858a1c6
- **Status**: applied — monitoring
- **Self-test note**: this very amendment session followed its own new rule — smoke-checked skill-improve v1.1.0 after install, before commit. The smoke confirmed: listing OK, cached plugin.json version 1.1.0 OK, frontmatter 1.1.0 OK.
---

## AMD-004 — 2026-05-13
- **Pattern**: Retrospective collected ratings but did not collect the "why" behind low ratings — same gap as my-skill-factory AMD-006.
- **Evidence**: my-skill-factory feedback log entry 2026-05-12T03:45:00Z (explicit user request that the factory always ask WHY for rating < 5). Propagated to skill-improve for consistency.
- **Change**:
  1. SKILL.md Retrospective step 2 now requires a WHY follow-up for any rating < 5, even in auto-mode.
  2. Log-format template embedded at step 3c now includes a `Rating reason` field, populated verbatim from the user's WHY response.
  3. Added a Gherkin scenario "Retrospective with low rating triggers WHY follow-up" to `references/scenarios.feature`.
- **Files Modified**: `skill-improve/SKILL.md` — `### Retrospective`; `skill-improve/references/scenarios.feature`.
- **Version Bump**: 1.0.0 → 1.1.0
- **Git Commit**: 858a1c6
- **Status**: applied — monitoring
---
