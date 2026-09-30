# Amendment History

## AMD-001 — 2026-05-12
- **Pattern**: BDD scenarios were embedded inline in the factory-generated SKILL.md body by default, which surprised the user and bloated the always-loaded body weight.
- **Evidence**: `feedback/log.md` entry 2026-05-12T03:45:00Z ("Gerkinがまさかメインのdeskに入ってると思わなかった")
- **Change**: SKILL.md `### SKILL.md body` section now defaults to a 1-line pointer to `references/scenarios.feature` (on-demand only, never auto-loaded). Inline BDD becomes the exception requiring justification. Also strengthened: "WHEN TO READ: ..." guidance is now mandatory on every `references/` file mention.
- **Files Modified**: `my-skill-factory/SKILL.md` — `### SKILL.md body` (Step 4 area).
- **Version Bump**: 1.0.0 → 1.1.0
- **Git Commit**: 71449f2
- **Status**: applied — monitoring
- **Evaluation (2026-09-30)**: insufficient data — only 2 post-amendment entries (2026-06-09 rated 5/5; 2026-07-12 unrated). No BDD-inline complaint recurred (the 2026-07-12 run shipped scenarios in a separate file).
---

## AMD-002 — 2026-05-12
- **Pattern**: Authoring choices in Step 2 (Design) were made without considering Claude's token cost. SKILL.md bodies trended large; `references/` files lacked explicit "WHEN TO READ" guards and risked auto-loading.
- **Evidence**: `feedback/log.md` entry 2026-05-12T03:45:00Z (rating reason: "トークン消費量とかを機にすべきだし、設計も機にするべき")
- **Change**: Added a new "Token-cost contract" bullet to Step 2's Decide list. It mandates: estimate SKILL.md body weight; mark every `references/` file with explicit "WHEN TO READ: ..." gating; explicitly exclude BDD scenarios, long worked examples, and detailed protocol docs from auto-load.
- **Files Modified**: `my-skill-factory/SKILL.md` — `## Step 2: Design the Skill` (Decide list).
- **Version Bump**: 1.0.0 → 1.1.0
- **Git Commit**: 71449f2
- **Status**: applied — monitoring
- **Evaluation (2026-09-30)**: insufficient data — only 2 post-amendment entries (2026-06-09 rated 5/5; 2026-07-12 unrated). No token-cost complaint recurred.
---

## AMD-003 — 2026-05-12
- **Pattern**: Step 1 questions mixed architecture (auth, sync/async) with stack/runtime concerns, leading users to answer inconsistent combinations of options.
- **Evidence**: `feedback/log.md` entry 2026-05-12T03:45:00Z (rating reason "設計も機にするべき"; corrections list: "Architectural intent ambiguity in early Q&A: user picked X AND Y — they're inconsistent")
- **Change**: Restructured Step 1 into two ordered blocks: "Architecture questions (always ask unless answered)" followed by "Stack/runtime questions (after architecture is clear)". Architecture block calls out auth mode (with billing-implication surfacing), sync vs async, batch vs streaming, and user-facing names.
- **Files Modified**: `my-skill-factory/SKILL.md` — `## Step 1: Gather Requirements`.
- **Version Bump**: 1.0.0 → 1.1.0
- **Git Commit**: 71449f2
- **Status**: applied — monitoring
- **Evaluation (2026-09-30)**: insufficient data — only 2 post-amendment entries (2026-06-09 rated 5/5; 2026-07-12 unrated). The 2026-06-09 run converged its design through a structured interview.
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
- **Evaluation (2026-09-30)**: insufficient data — only 2 post-amendment entries (2026-06-09 rated 5/5; 2026-07-12 unrated). The 2026-06-09 run records no under-asking; design converged via interview.
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
- **Evaluation (2026-09-30)**: insufficient data — only 2 post-amendment entries (2026-06-09 rated 5/5; 2026-07-12 unrated). Positive signal — on 2026-07-12 the runtime smoke caught 3 bugs that review missed.
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
- **Evaluation (2026-09-30)**: insufficient data — only 2 post-amendment entries (2026-06-09 rated 5/5; 2026-07-12 unrated). The 2026-07-12 rating is still pending, so the WHY follow-up has not been exercised.
---

## AMD-007 — 2026-09-30
- **Pattern**: The factory's improvement loop was purely inward. OIAE only learns from this skill's own feedback, so ecosystem changes (new Claude Code / Codex releases, model launches, skill-spec changes, new tooling such as `claude plugin eval` and `claude plugin details`) never reached the factory's guidance unless a user happened to hit them. On 2026-09-30 the factory still told authors to *estimate* token cost by hand, although the installed CLI reports projected token cost.
- **Source**: user request (2026-09-30) plus a feedback theme
- **Evidence**: user request via /skill-improve on 2026-09-30 (「クロードやコードックスがアップデートされるたびに…自発的に改善されるようなループを作りたい」). Supporting stale-knowledge entries: 2026-05-12T04:10:00Z ("verify the SDK's actual surface… not just trusting an LLM-summarized README") and 2026-07-12T00:00:00Z (CLI flags copied from sibling-skill house style were wrong for the installed binaries).
- **Change**: New outward-facing Ecosystem Refresh loop.
  - `scripts/ecosystem_check.py` runs on every invocation. It is a cheap gate (two `--version` calls plus a state read), with state in `feedback/ecosystem-state.json`.
  - When the check is due, a background subagent researches a fixed list of primary sources while Step 1 proceeds.
  - Every proposal needs the user's approval, even in auto-mode. Approved items are used in-context in Step 2, and written back after Step 5 as a separate amendment-recorded commit.
  - The new `references/ecosystem-practices.md` is a sourced, dated, size-capped knowledge base that Step 2 reads on every run.
  - `skill-improvement-guide.md` documents this loop as the one sanctioned self-amendment and adds a `Source` field to the amendment format.
  - Due policy (`refresh_reasons`): a refresh is due when any installed CLI is *newer* than the recorded version. The user chose this on 2026-10-01 over a draft with a 7-day cooldown and a 30-day max age, because the two only differ when factory runs cluster within days. "Newer" rather than "different" keeps synced hosts with older CLIs from flip-flopping the shared state.
  - Deferred TODOs are tracked in SKILL.md: impact scan, scheduled refresh, cooldown/max-age knobs, Codex-native path.
- **Files Modified**: `my-skill-factory/SKILL.md` (Workflow, new `## Ecosystem Check`, Step 2, Updating step 4, References, new Deferred TODOs); new `scripts/ecosystem_check.py`, `references/ecosystem-refresh.md`, `references/ecosystem-practices.md`; `references/skill-improvement-guide.md` (Overview, Amendment Format).
- **Version Bump**: 1.1.0 → 1.2.0
- **Git Commit**: (pending)
- **Status**: applied — monitoring
---

## AMD-008 — 2026-09-30
- **Pattern**: The factory violated its own AMD-001. Its SKILL.md body carried about 80 lines of inline Gherkin (13 scenarios) that were loaded on every trigger, while AMD-001 tells generated skills to keep BDD in `references/scenarios.feature`.
- **Source**: self-audit during the AMD-007 run
- **Evidence**: AMD-001's rule, applied to the factory itself. SKILL.md was 428 lines against the 500-line cap before AMD-007 added a section.
- **Change**: Moved all scenarios to `references/scenarios.feature`, gated with WHEN TO READ, and added 9 Ecosystem Refresh scenarios. The SKILL.md body now carries a one-line pointer, and the file went from 428 to 395 lines despite the new section.
- **Files Modified**: `my-skill-factory/SKILL.md` — `## Behavior Scenarios`; new `references/scenarios.feature`.
- **Version Bump**: 1.1.0 → 1.2.0 (same release as AMD-007)
- **Git Commit**: (pending)
- **Status**: applied — monitoring
---

## AMD-009 — 2026-10-01
- **Pattern**: The knowledge base started empty, and several lines of factory guidance had become wrong against the current ecosystem:
  - "include ALL trigger phrases", although descriptions are capped at 1,024 chars and truncated or dropped when the listing overflows;
  - "estimate" token cost by hand, although `claude plugin details` measures it;
  - skill-design-guide's "<5k words", which is the wrong unit.
  The research also found the factory itself at ~7.5k tokens on invoke, above the recommended 5k.
- **Source**: ecosystem-refresh (the first refresh, which also served as the runtime smoke of AMD-007)
- **Evidence**:
  - Sources: https://agentskills.io/specification, https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices, https://code.claude.com/docs/en/skills, https://code.claude.com/docs/en/sub-agents, https://platform.claude.com/docs/en/about-claude/models/overview, https://developers.openai.com/codex/skills, and the Claude Code CHANGELOG (2.1.218–2.1.285).
  - Commands run: `claude plugin details|eval|validate --help` and `codex debug prompt-input`.
  - The orchestrator re-checked `plugin details` (factory ~7.5k on invoke), `validate`, `codex debug prompt-input`, and the description-length count (13–14 of 56 skills over 1,024 chars).
- **Change**:
  - The user approved all 10 proposals (P1–P10), so there are no declined items. They are seeded into `references/ecosystem-practices.md`: 1 models, 1 tokens, 2 agents, 5 authoring, 1 codex.
  - Contradicted lines are fixed:
    - SKILL.md Step 2 Token-cost contract now says "measure with `claude plugin details`".
    - The SKILL.md Step 4 frontmatter guidance now says "≤1,024 chars, key use case first", and points to the invocation fields.
    - SKILL.md Step 5 gains a pointer to the knowledge base's verification practices.
    - skill-design-guide.md's description line and "<5k words" are corrected.
  - `feedback/ecosystem-state.json` is stamped with claude 2.1.278, codex 0.154.0, 2026-10-01.
  - Per the user's scoping, **other skills are not modified**. The 13–14 over-long descriptions and the 3 skills relying on the fork-background default are left for the deferred impact scan.
- **Files Modified**: `my-skill-factory/references/ecosystem-practices.md`; `my-skill-factory/SKILL.md` (Step 2, Step 4 frontmatter, Step 5); `my-skill-factory/references/skill-design-guide.md` (Frontmatter, Progressive Disclosure); new `my-skill-factory/feedback/ecosystem-state.json`.
- **Version Bump**: shipped inside 1.2.0 together with AMD-007/008. The write-back protocol normally bumps separately, but 1.2.0 had not been released yet, so a 1.2.1 would have had no prior install to follow.
- **Git Commit**: (pending)
- **Status**: applied — monitoring
- **Cost note**: the first refresh took ~222k subagent tokens, 57 tool calls, and ~10 min, because a first run has no version slice to diff against. Later refreshes read only newer changelog sections; compare their cost against this baseline when evaluating AMD-007.
---
