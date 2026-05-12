# Amendment History

## AMD-001 — 2026-05-12
- **Pattern**: BDD scenarios were embedded inline in the factory-generated SKILL.md body by default, which surprised the user and bloated the always-loaded body weight.
- **Evidence**: `feedback/log.md` entry 2026-05-12T03:45:00Z ("Gerkinがまさかメインのdeskに入ってると思わなかった")
- **Change**: SKILL.md `### SKILL.md body` section now defaults to a 1-line pointer to `references/scenarios.feature` (on-demand only, never auto-loaded). Inline BDD becomes the exception requiring justification. Also strengthened: "WHEN TO READ: ..." guidance is now mandatory on every `references/` file mention.
- **Files Modified**: `my-skill-factory/SKILL.md` — `### SKILL.md body` (Step 4 area).
- **Version Bump**: 1.0.0 → 1.1.0
- **Git Commit**: 71449f2
- **Status**: applied — monitoring
---

## AMD-002 — 2026-05-12
- **Pattern**: Authoring choices in Step 2 (Design) were made without considering Claude's token cost. SKILL.md bodies trended large; `references/` files lacked explicit "WHEN TO READ" guards and risked auto-loading.
- **Evidence**: `feedback/log.md` entry 2026-05-12T03:45:00Z (rating reason: "トークン消費量とかを機にすべきだし、設計も機にするべき")
- **Change**: Added a new "Token-cost contract" bullet to Step 2's Decide list. It mandates: estimate SKILL.md body weight; mark every `references/` file with explicit "WHEN TO READ: ..." gating; explicitly exclude BDD scenarios, long worked examples, and detailed protocol docs from auto-load.
- **Files Modified**: `my-skill-factory/SKILL.md` — `## Step 2: Design the Skill` (Decide list).
- **Version Bump**: 1.0.0 → 1.1.0
- **Git Commit**: 71449f2
- **Status**: applied — monitoring
---

## AMD-003 — 2026-05-12
- **Pattern**: Step 1 questions mixed architecture (auth, sync/async) with stack/runtime concerns, leading users to answer inconsistent combinations of options.
- **Evidence**: `feedback/log.md` entry 2026-05-12T03:45:00Z (rating reason "設計も機にするべき"; corrections list: "Architectural intent ambiguity in early Q&A: user picked X AND Y — they're inconsistent")
- **Change**: Restructured Step 1 into two ordered blocks: "Architecture questions (always ask unless answered)" followed by "Stack/runtime questions (after architecture is clear)". Architecture block calls out auth mode (with billing-implication surfacing), sync vs async, batch vs streaming, and user-facing names.
- **Files Modified**: `my-skill-factory/SKILL.md` — `## Step 1: Gather Requirements`.
- **Version Bump**: 1.0.0 → 1.1.0
- **Git Commit**: 71449f2
- **Status**: applied — monitoring
---

## AMD-004 — 2026-05-12
- **Pattern**: The "Keep it to 2-3 focused questions max" cap, combined with auto-mode's "minimize interruptions", caused the factory to under-ask. Specifically, user-facing names were chosen unilaterally and architectural ambiguity was left unresolved.
- **Evidence**: `feedback/log.md` entries:
  - 2026-05-04T14:52:59Z (my-gdrive: "Naming chosen without confirmation — auto-mode interpreted 'minimize interruptions' too broadly for a user-visible label")
  - 2026-05-12T03:45:00Z (codex-server: "The factory under-asked: the user explicitly said they would have preferred MORE clarifying questions")
  - 2026-05-12T04:10:00Z (codex-server smoke: implicit — no smoke-offer question was asked either)
- **Change**: Removed the "2-3 questions max" cap. Replaced with explicit guidance: ask as many clarifying questions as needed; "minimize interruptions" does NOT apply to user-visible names/labels (always confirm) or architectural Q&A (ask freely). Skip a question only when explicitly answered.
- **Files Modified**: `my-skill-factory/SKILL.md` — `## Step 1: Gather Requirements` (tail paragraph).
- **Version Bump**: 1.0.0 → 1.1.0
- **Git Commit**: 71449f2
- **Status**: applied — monitoring
- **Recurrence threshold met**: this is the only amendment in this batch motivated by 3+ feedback entries.
---

## AMD-005 — 2026-05-12
- **Pattern**: Step 5 (Verify) only required `claude -p` listing, which does not exercise the skill's actual runtime. Multiple runtime-only bugs slipped through this gate.
- **Evidence**: `feedback/log.md` entry 2026-05-12T04:10:00Z — 3 distinct bugs (worker --allow-env scoping, thread.id sync assumption, session-meta regex shape) were caught only by actually running the skill end-to-end against `@openai/codex-sdk`. Quote: "Plan approval without runtime smoke is NOT enough — factory should default to a smoke-test phase BEFORE marking the work complete."
- **Change**: Step 5 renamed to "Verify and Smoke Test". Split into 5a (listing check, unchanged) and 5b (runtime smoke, REQUIRED). For wrapper skills (CLI/SDK/API), 5b mandates at least one happy-path execution + one error-path. For other skill kinds, the primary entry point must be exercised. Treats any bug found here as a smoke-discovered fix to commit before reporting completion.
- **Files Modified**: `my-skill-factory/SKILL.md` — `## Step 5: Verify and Smoke Test`.
- **Version Bump**: 1.0.0 → 1.1.0
- **Git Commit**: 71449f2
- **Status**: applied — monitoring
---

## AMD-006 — 2026-05-12
- **Pattern**: Retrospective collected ratings but did not collect the "why" behind low ratings, losing the strongest improvement signal.
- **Evidence**: `feedback/log.md` entry 2026-05-12T03:45:00Z, factory-improvement requests bullet: "When asking the user to rate, ALWAYS follow up by asking WHY for any rating < 5. The factory should not assume a 3/5 means 'fine' — it means 'the user wants something improved, ask what.'"
- **Change**:
  1. SKILL.md Retrospective step 2 now requires a WHY follow-up for any rating < 5, even in auto-mode.
  2. Log-format template (both in `SKILL.md` step 3c and in `references/skill-improvement-guide.md`) now includes a `Rating reason` field, populated verbatim from the user's WHY response.
  3. Retrospective template inside `skill-improvement-guide.md` (the boilerplate this factory embeds into generated skills) also got the same WHY-follow-up requirement.
- **Files Modified**: `my-skill-factory/SKILL.md` — `## Retrospective`; `my-skill-factory/references/skill-improvement-guide.md` — log format table + Retrospective Step Template.
- **Version Bump**: 1.0.0 → 1.1.0
- **Git Commit**: 71449f2
- **Status**: applied — monitoring
---
