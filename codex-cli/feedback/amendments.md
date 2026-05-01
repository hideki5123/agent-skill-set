# Amendment History

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
