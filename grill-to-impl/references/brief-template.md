# Implementation Brief — Template

The brief is the **only** thing the spawned session inherits. It must stand alone:
no "as we discussed", no references to the current chat. Mirror the depth of a
strong engineering handoff. Keep it skimmable; prefer tables and `file:line`
anchors over prose.

Write to `<target>/docs/design/<slug>-impl-brief.md`.

---

```markdown
# Implementation Brief — <Feature title>

**Status:** Ready for prd-council (design agreed)
**Codex review:** <APPROVED (round N) | DEGRADED (Claude-only)>
**Target repo(s):** <repo names / paths>
**Scope:** <one line>

## 1. Problem & Goal
<2-4 sentences: what's broken / needed and the outcome. Preserve the user's
original framing verbatim where it sharpens intent (quote it if non-English).>

## 2. Non-goals
- <explicit exclusions decided during the grill — these prevent scope creep in
  the autonomous session. Be specific; "NOT X (because Y)".>

## 3. Branch setup (DO THIS FIRST)
- Do NOT commit on any design/doc branch or PR branch.
- Create a fresh implementation branch off the integration branch, e.g.
  `git fetch origin && git checkout -b feat/<slug> origin/<base>`.
- If the design note lives on an unmerged branch, read it without switching:
  `git show origin/<doc-branch>:<path>`.
- For multi-repo work, state the branch + base for EACH repo and the order.

## 4. Locked decisions
| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | … | … | … |
<every decision resolved during the grill — this is the spine of the brief.>

## 5. Approach / data flow
<optional: a short diagram or step list showing how the pieces connect.>

## 6. Concrete steps (with anchors)
<ordered, per-repo if multi-repo. Each step cites real paths and `file:line`
anchors so a cold agent can navigate. Name the exact functions/methods to touch.>

## 7. Constraints & acceptance
- <platform / safety / read-only / perf constraints>
- **Acceptance:** <observable criteria — tests green, a specific log line appears,
  a device-verify step, etc. Make "done" checkable.>

## 8. Risks
- <known risks, collisions with other in-flight work, things to verify on real hardware>

## 9. Deliverable
<the concrete artifacts/PRs expected, and how they stay separate from any design PR.>

---

## Seed for prd-council
This brief is the finalized, already-grilled and Codex-reviewed requirements set.
When you (the spawned session) run `/prd-council`:
- Treat sections 1-9 as the agreed requirements — **do not re-grill from scratch**.
- Only ask the user if a genuine blocking gap remains.
- Emit the execution-ready doc set + `tasks.md` under `docs/prd/<slug>/`, then begin
  implementation per `tasks.md`, following the Branch setup in §3.
```

---

## Authoring notes

- **Fidelity over brevity for decisions.** Dropping a non-goal or constraint is the
  most damaging failure — an autonomous agent will happily build the excluded thing.
  Section 4 + 2 are load-bearing.
- **Every step needs an anchor.** If you cannot cite a path/symbol, the spawned
  agent cannot either — go find it now, or mark it explicitly as "investigate".
- **Language:** honor `--lang`. `auto` = the grilled session's language. Keep code
  identifiers, paths, and commit messages in English regardless.
- **Multi-repo:** make the order explicit (what merges first) and carry each repo's
  base branch. Dependency direction usually dictates order.
