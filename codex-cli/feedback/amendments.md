# Amendment History

## AMD-002 — 2026-05-02
- **Pattern**: Self-evaluation of AMD-001 surfaced two implementation gaps:
  1. `### Retrospective` was h3 placed AFTER Behavior Scenarios; the retrofit-checklist mandates h2 BEFORE Behavior Scenarios.
  2. Pattern A polling loop was unbounded: `until [ -s /tmp/codex-out.txt ]; do sleep 5; done` runs forever if codex crashes silently (network drop, OOM, killed) — recreating the original "agent gives up" failure mode under a different cause.
- **Evidence**: 2026-05-02 self-evaluation triggered by user ("evaluate the update"), confirmed and approved by user ("Apply the fixes now").
- **Change**:
  - Promoted Retrospective from `### Retrospective` (h3, after Behavior Scenarios) to `## Retrospective` (h2, before Behavior Scenarios) per retrofit-checklist option 1
  - Replaced unbounded `until [ -s file ]; do sleep 5; done` with bounded `for i in $(seq 1 120); do [ -s file ] && break; sleep 5; done` + post-loop crash check that surfaces a clear error if codex produced no output within 10 minutes
  - Updated Pattern A docs to explicitly state why the bound matters and warn against unbounded waits
  - Added a `pgrep` caveat noting that `pgrep -f "codex exec"` matches all running codex processes (concurrent-call edge case)
  - Updated the "Long-running Codex query" Behavior Scenario to use the bounded pattern
- **Files Modified**:
  - `codex-cli/SKILL.md` — Pattern A polling loop, Behavior Scenario, Retrospective section placement and heading level
- **Version Bump**: 1.1.0 → 1.1.1
- **Git Commit**: b0ba1a0
- **Status**: applied — monitoring
---

## AMD-001 — 2026-05-02
- **Pattern**: Codex CLI calls take 2–10 minutes, exceeding the Bash tool's 2-minute default timeout. The previous SKILL.md treated `run_in_background` as a niche tip "for long tasks", so the agent defaulted to foreground execution and got killed by the timeout, giving up before any response arrived.
- **Evidence**: 2026-05-02 user feedback — "the response was always really slow then the agent always give up to receive response"
- **Change**:
  - Added `version: 1.1.0` to frontmatter (retrofit OIAE)
  - Added a new **Constraint** mandating background execution (or explicit `timeout: 600000`)
  - Added a new top-level **Adaptive Execution** section with two patterns (Pattern A: background + Monitor on the `-o` file; Pattern B: foreground with `timeout: 600000`) and a "Tune for speed" lever table (`model_reasoning_effort=low`, smaller `-m`, drop `--search`, tighter prompt, `read-only`)
  - Promoted the `run_in_background` Agent Tip from "for long tasks" to "by default" with explicit guidance
  - Added a "Tune reasoning effort for latency" Agent Tip
  - Added a Quick Reference note pointing every command to Adaptive Execution; added a "Fast/low-latency query" row
  - Expanded the **Error Handling** "timed out" row with concrete remediation
  - Added two new Behavior Scenarios (long-running query, latency-sensitive query)
  - Added the OIAE **Retrospective** section so future feedback can be tracked
- **Files Modified**:
  - `codex-cli/SKILL.md` — frontmatter, Constraints, new Adaptive Execution section, Quick Reference, Agent Tips, Error Handling, Behavior Scenarios, new Retrospective section
  - `codex-cli/feedback/log.md` — created with seed entry
- **Version Bump**: (none) → 1.1.0
- **Git Commit**: fbbb638
- **Status**: applied — monitoring
---
