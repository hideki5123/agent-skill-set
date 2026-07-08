---
name: parallel-investigate
description: >
  Fans out multiple agents in parallel via the Workflow tool to investigate a
  codebase question — bug root cause tracing, cross-file or cross-repository
  behavior tracing, "why does X happen for some cases but not others" questions —
  then synthesizes a ranked, file:line-cited answer in chat. The point of this
  skill is explicitness: it announces the investigation dimensions and agent
  count before launching, narrates progress, and reports a structured synthesis,
  rather than leaving multi-agent orchestration as an implicit background
  behavior the user can't see into. Supports investigations that span more than
  one local repository on disk (e.g. a backend service and a client app that
  talks to it). Investigation only — does not edit code or fix anything; pair
  with another skill or a follow-up request for that. Use when the user wants to
  investigate a bug, trace behavior across files or repositories, understand why
  something happens under some conditions but not others, or explicitly asks for
  a parallel/multi-agent investigation. Trigger phrases: "parallel-investigate",
  "/parallel-investigate", "並列で調査して", "並列調査", "複数エージェントで調べて",
  "複数エージェントで並列調査して", "investigate this in parallel", "fan out and
  investigate", "investigate across repos", "trace this across repositories".
version: 1.0.0
---

# Parallel Investigate

Investigate a codebase question by fanning out multiple Workflow agents across
independent dimensions, then synthesizing their findings into one ranked, cited
answer. Always run this via the `Workflow` tool directly — never simulate the
fan-out with sequential `Agent` calls, and never hide the orchestration from the
user. Explicitness is the entire value of this skill over ad hoc investigation.

## Feedback Check

If `feedback/log.md` exists next to this SKILL.md and has 5 or more entries, read
the last 10. If a pattern is apparent (the same issue in 3+ entries, or average
rating below 3), tell the user (in Japanese): 「過去のフィードバックで類似パターン
を検出: [簡潔に]。`/skill-improve --skill parallel-investigate` で改善案を分析でき
ます。」Continue with normal execution either way. If `feedback/log.md` does not
exist, skip silently.

## Step 1: Scope the Question

1. **Guard against overkill first.** If the question can be answered by reading
   one file or a single targeted grep, say so briefly and just answer it
   directly — do not launch a Workflow for it. This applies even when the skill
   was triggered by natural language, not just the slash command.
2. **Guard against vagueness.** If the request has no concrete subject or
   codebase area ("調べて" with nothing else, no symptom, no file/module named),
   ask 1-2 clarifying questions before proceeding. Do not guess dimensions from a
   request with nothing to decompose.
3. **Decompose into investigation dimensions.** For genuinely multi-faceted
   questions, read `references/decomposition-patterns.md` for the by-layer,
   by-repository, and by-hypothesis decomposition strategies (with a worked
   example) before picking dimensions. Aim for 3-5 dimensions.
4. **Check for cross-repository scope.** If the codebase references an external
   component whose source is not present in the current repo, do not conclude
   it's simply unavailable — follow the repo-discovery steps in
   `decomposition-patterns.md` (check common sibling-repo roots, then ask the
   user) before ruling it out.

## Step 2: Announce the Plan

Before launching anything, tell the user in one short paragraph: how many
dimensions/agents, what each will investigate, and that this runs in the
background. Never launch silently — the whole point of this skill is that the
user can see the investigation happening, not just receive a final answer.

## Step 3: Launch the Workflow

Read `references/workflow-template.md` for the exact script pattern (Explore
phase with one parallel agent per dimension, then a Synthesize phase). Read
`references/synthesis-format.md` for the exact instructions to give the
Synthesize agent (ranking, CONFIRMED/PLAUSIBLE confidence tags, contradiction
resolution, convergence notes, a concrete next step, ~900-word cap).

Rules that apply regardless of the specific question:
- Every Explore-phase agent prompt must be fully self-contained — agents share
  no context with you or each other. Restate the symptom/question, name the
  exact files/dirs (and repo path, if not the current one), and specify exactly
  what to report back with file:line citations.
- Label every agent (`explore:<dimension>`, `synthesis`) so progress in
  `/workflows` is legible.
- Use `parallel()` as the barrier between Explore and Synthesize — synthesis
  genuinely needs every finding at once to cross-reference and rank them. Do not
  use `pipeline()` here even though it's the general default for multi-stage
  Workflow scripts.
- Before reading any repository you didn't already have open (see Step 1's
  cross-repo case), check `git status` first. If it's on a non-default branch
  with uncommitted changes, investigate the working tree read-only; do not
  switch branches, stash, or pull without asking.

## Step 4: Report Back

Relay the Synthesize agent's output to the user in chat, organized and cited.
This skill's default output is chat-only — do not write a report file unless the
user separately asks for one to be saved.

## Behavior Scenarios

BDD spec lives in `references/scenarios.feature`. Read only when auditing or
amending this skill; not needed for normal execution.

## Retrospective

After Step 4 completes, reflect on the investigation:

1. Consider: was the initial decomposition wrong and had to be redone? Did a
   dimension turn out irrelevant or a needed one get missed? Any Workflow
   errors, or an agent that returned nothing useful?
2. Ask the user (in Japanese): 「今回の調査のフィードバック (1-5の評価、気になった
   点、または何もなければEnter)」 **If the user provides a rating < 5, ALWAYS
   follow up** with: 「なぜその評価ですか？ (改善のために具体的に教えてください)」
   Record the response verbatim as `Rating reason`.
3. If the user provides feedback OR corrections/issues actually occurred:
   a. Create `feedback/` next to this SKILL.md if it does not exist.
   b. Read `feedback/log.md` (create with `# Feedback Log` header followed by a
      blank line and the comment
      `<!-- Append new entries at the top. Do not edit previous entries. -->`
      if it does not exist).
   c. Prepend a new entry directly after the header:

      ```markdown
      ## <ISO-8601 timestamp>
      - **Skill Version**: 1.0.0
      - **Task**: <the question investigated, 1 line>
      - **Outcome**: success | partial-success | failure | error
      - **Rating**: <N>/5 (or "—" if not provided)
      - **Rating reason**: <verbatim WHY answer, or "—" if rating was 5 or not provided>
      - **Corrections**: <decomposition redone, dimension added/removed, or "none">
      - **Issues**: <specific problems, or "none">
      - **User Note**: <user's verbatim feedback, or "—">
      ---
      ```

   d. Confirm in one short Japanese sentence.
4. If the user skips AND no corrections or issues occurred, end without
   recording.

## References

- `references/decomposition-patterns.md` — WHEN TO READ: during Step 1, when
  deciding how to split the question into investigation dimensions (by layer, by
  repository, by hypothesis) and how to locate a referenced-but-missing repo.
- `references/workflow-template.md` — WHEN TO READ: during Step 3, as the
  starting script pattern to adapt for the real investigation.
- `references/synthesis-format.md` — WHEN TO READ: during Step 3, when writing
  the Synthesize-phase agent's prompt.
- `references/scenarios.feature` — WHEN TO READ: only when auditing or amending
  this skill.
