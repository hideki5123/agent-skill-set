# Feedback Log

<!-- Append new entries at the top. Do not edit previous entries. -->

## 2026-06-09T14:27:43Z
- **Skill Version**: 1.1.0
- **Task**: create grill-to-impl skill (grill→brief→codex-server review loop→claude-bg prd-council launch)
- **Outcome**: success
- **Rating**: 5/5
- **Corrections**: none — design converged via grill-me-style interview; the user's free-text answers redefined the spawn mechanism to the ccb/claude-bg background remote-control launcher (emulated on PATH, not hardcoded).
- **Issues**: install_skill.py `strip_comments` used `re.sub(r'//.*','')`, which also stripped the `//` inside an `"http://..."` mcp-server URL in the user's settings.json — corrupting it and crashing the "enable in settings.json" step on round 1. Fixed with a string-aware comment scanner (commit 4e47c4e). Lesson: naive `//` comment stripping breaks any JSONC config containing URL string values; read_json now skips comments only outside strings.
- **User Note**: —
---

## 2026-05-12T04:10:00Z (smoke-test follow-up to the codex-server creation)
- **Skill Version**: (factory v current)
- **Task**: end-to-end smoke test of codex-server v1.0.0 (user request: "実際に使ってテストして")
- **Outcome**: partial-success — flow works after fixing 3 bugs caught only by running it
- **Rating**: — (no explicit rating; this entry is the lessons-learned record)
- **Bugs found at runtime that planning + code-only review missed**:
  1. Worker spawn's `--allow-env=PATH,HOME,USERPROFILE` was too tight — `@openai/codex-sdk` runs through deno's Node compat layer which probes `NODE_V8_COVERAGE`, `NODE_OPTIONS`, `NODE_NO_WARNINGS`, and others. First turn failed with "Requires env access to NODE_V8_COVERAGE". Resolved by broadening worker's --allow-env to unscoped; the ChatGPT-subscription guarantee is preserved at the env-INJECTION boundary (buildEnv only forwards PATH/HOME/USERPROFILE to codex) rather than the env-READ boundary.
  2. `thread.id` is NOT populated synchronously after `codex.startThread()` in SDK v0.130. The thread-id arrives via the `thread.started` event in the stream. The worker's `if (thread.id) writeMeta(...)` ran with `undefined`, so meta.json kept `thread_id: null`.
  3. `loadLatestThreadId` / `cmdListThreads` / `cmdShow` used a regex that matched a non-existent top-level `"thread_id"` key. Codex session JSONL stores the id under `payload.id` inside a `session_meta` first line. Continue --last reported "no previous thread found" even when one obviously existed.
- **SDK limitation discovered**: `resumeThread()` in v0.130 does NOT take a second options arg — no `workingDirectory` / `skipGitRepoCheck`. Resumed turns must execute in a trusted/git-tracked cwd. Documented in error-handling.md.
- **Factory-improvement requests added by this run**:
  - "Plan approval" without runtime smoke is NOT enough — factory should default to a smoke-test phase BEFORE marking the work complete. The plan claimed the design was solid, but three bugs showed up in 60 seconds of actual use.
  - When the skill wraps an external SDK, the plan should include verifying the SDK's actual surface (sync vs async fields, available options on each method) against the upstream README + a sample run, not just trusting an LLM-summarized README.
  - Document SDK version assumptions in the skill — `@openai/codex-sdk@^0.130.0` shape is what we coded against; future bumps may need adapter code.
  - When designing scoped `--allow-env`, account for npm:-imported SDKs that go through deno's Node compat layer. The minimal-permissions principle is sound but needs an "or wide-open and filter at the spawn boundary" escape hatch documented up front.
- **User note**: "すでにログインしてあるはずなので、実際に使ってテストして" — confirms the user wants real e2e verification, not just compile-success or `claude -p` listing.
---

## 2026-05-12T03:45:00Z
- **Skill Version**: (factory v current)
- **Task**: create codex-server skill (App Server + @openai/codex-sdk on deno); also narrow codex-cli to batch niche
- **Outcome**: partial-success (skill works, but design process should have been better)
- **Rating**: 3/5
- **Rating reason (user, verbatim, Japanese)**:
  「Gerkinがまさかメインのdeskに入ってると思わなかった、トークン消費量とかを機にすべきだし、設計も機にするべき。あと、ユーザーへの問い回数はもっと多くてもいいくらいでした」
- **Process gaps (translated from rating reason)**:
  1. Putting Gherkin BDD scenarios in the main SKILL.md body was unexpected to the user — they assumed obviously not. The factory's default should be: BDD lives in a separate `.feature` file outside the runtime-loaded body.
  2. Token-consumption implications of every authoring choice should be considered up front — every `references/` file needs an explicit "WHEN TO READ" guard, and SKILL.md body weight should be optimized from draft 1, not after the user flags it.
  3. Architectural decisions (auth flow, async invocation, etc.) should be reasoned through more carefully before showing the user a plan. The first plan understated the streaming/timeout question and proposed API-key auth alongside ChatGPT subscription — both were wrong-shaped enough that the user had to push back multiple times.
  4. The factory under-asked: the user explicitly said they would have preferred MORE clarifying questions, not fewer. Auto-mode's "minimize interruptions" should not extend to architectural Q&A — those questions are cheap and avoid worse rework.
- **Factory-improvement requests (from this session)**:
  - When asking the user to rate, ALWAYS follow up by asking WHY for any rating < 5. The factory should not assume a 3/5 means "fine" — it means "the user wants something improved, ask what." Done in this session manually; should be built into the Retrospective template.
  - Default to BDD-in-separate-file. Treat embedding scenarios in SKILL.md as the exception that requires explicit justification.
  - Add an explicit "token-cost contract" step in the design phase: estimate how much each file in `references/` would cost if Claude reads it, and verify the SKILL.md body stays under a target weight.
  - In the initial Q&A, ask architectural questions (auth flow, sync vs async, batch vs streaming) before stack questions. Stack should follow architecture, not the other way around.
- **Corrections**:
  1. Initial plan listed BDD scenarios inline in SKILL.md — user asked to separate scripts and Gherkin into dedicated files. Plan revised: scenarios.feature, execution-patterns.md, examples.md, error-handling.md all separated from SKILL.md.
  2. Initial plan put API key as primary auth with codex login fallback — user corrected: ChatGPT subscription is the whole point of App Server, so this skill should DEFAULT to that.
  3. After codex-login-default revision, user further mandated NO API-key fallback at all — to guarantee zero OPENAI_API_KEY billing. Final design excludes OPENAI_API_KEY from --allow-env so deno cannot read it even if exported.
  4. User asked to elevate "daemon mode / decoupled async invocation" from deferred TODO into v1.0.0 default — to structurally eliminate the Bash 2-minute timeout concern. Plan revised: chat.ts new forks worker.ts detached; returns turn-id in <1s; Claude observes via Monitor on out.txt.
  5. User asked to also edit codex-cli (not just leave it as-is) so codex-server takes priority for chat-like prompts. Plan revised: bump codex-cli to 1.2.0 with narrowed description; chat-trigger phrases stripped.
  6. Stale verification step referenced OPENAI_API_KEY — removed.
  7. User asked factory feedback log to be primed for future improvement (this entry is that seed for the codex-server run).
- **Issues**:
  - Architectural intent ambiguity in early Q&A: user picked "Library/wrapper for advanced JSON-RPC control" AND "TypeScript on deno + @openai/codex-sdk (Recommended)" — the SDK is the higher-abstraction option. Resolved by mid-plan check + WebFetches verifying SDK exists and is thin enough to be the chosen layer; raw JSON-RPC left as deferred TODO.
  - I did not initially flag that the SDK's npm dep `@openai/codex` would duplicate the system codex binary — caught later via npm view and addressed via `codexPathOverride`.
  - I underestimated the streaming/timeout question. User's intuition (streaming should solve it) led me to clarify the Bash 2-min layer carefully, which surfaced the decoupled-async architecture.
- **User Note**: User pushed back five times on plan drafts before approving. Final design is materially better than the initial proposal — particularly the decoupled-async architecture and the ChatGPT-subscription-only stance. The user's followup feedback (rating 3/5) emphasized that the factory should have caught those design issues without needing five rounds of pushback.

### Lessons surfaced for future factory runs
- When a skill wraps a CLI/binary that has multiple auth modes, default to whichever mode avoids billing. Surface billing implications upfront in the design Q&A.
- Separate Gherkin and long worked-examples from SKILL.md by default — every reference file should carry an explicit "WHEN TO READ" marker so Claude can avoid loading it during normal execution.
- For any skill whose underlying work routinely exceeds 2 min, design the invocation pattern around `Bash + Monitor` from the start, not as a post-hoc adaptive pattern (the codex-cli lesson). Decoupled async (detached worker writes to file; client returns in <1s) is the cleanest implementation.
- The factory should ask early about token-budget concerns for references/ so the author thinks about on-demand loading from day 1.
---

## 2026-05-04T14:52:59Z
- **Skill Version**: (factory v current)
- **Task**: Create new skill scoping gdrive-cli to user's private Google Drive
- **Outcome**: partial-success
- **Rating**: 2/5
- **Corrections**:
  - User asked to rename `gdrive-private` → `my-gdrive` after install (skill name was decided unilaterally; should have confirmed naming before file creation given a name like "private" was a judgment call about the public-facing label).
  - User asked for concrete rclone authentication steps for the personal account, given that an existing remote (`tx-gdrive:`) is the user's *company* account. The first version had a generic setup walkthrough without addressing the specific pain point: the browser will auto-pick the already-signed-in company Gmail unless you actively force a different account.
- **Issues**:
  - Naming chosen without confirmation — auto-mode interpreted "minimize interruptions" too broadly for a user-visible label.
  - Auth section was generic Drive-config guidance copy-shaped from gdrive-cli; missed the actual concrete pain (forcing OAuth to a *different* Gmail when one is already authorized to rclone).
- **User Note**: "please change name for my-gdrive. Also give me how authenticate rclone for my private google drive since current auth is only for my company, I suppose."
---
