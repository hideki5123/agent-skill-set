# Document Templates

**WHEN TO READ:** Phase 2 (PRD), Phase 4 (Technical PRDs), Phase 5 (tasks).
Write document bodies in the session language (`--lang`); keep section keys as
shown so downstream tooling can parse them. Use Mermaid for any diagram —
**never ASCII art**.

---

## 1. PRD template (`prd.md`) — Phase 2

Adapted from the `to-prd` skill, with an explicit **UseCases** section (the
backbone of every later artifact).

```markdown
# PRD: <feature title>

## Problem Statement
The problem the user faces, from the user's perspective.

## Solution
The solution, from the user's perspective.

## UseCases
A numbered list of the distinct UseCases this feature comprises. Each becomes a
per-UseCase Technical PRD in Phase 4. For each:
1. **<UseCase name>** — actor, trigger, main flow (1–3 lines), primary edge case.

## User Stories
A LONG numbered list, format: "As an <actor>, I want <feature>, so that <benefit>."
Extensive — cover all aspects of the feature.

## Implementation Decisions
Modules built/modified, their interfaces, technical clarifications, architectural
decisions, schema changes, API contracts, specific interactions. No file paths or
code snippets (they go stale) — except a small snippet that encodes a decision
more precisely than prose (state machine, schema, type shape), trimmed to the
decision-rich part.

## Testing Decisions
What makes a good test here (test external behavior, not implementation details),
which modules are tested, and prior art (similar tests in the codebase).

## Out of Scope
What is explicitly not part of this PRD.

## Further Notes
Anything else.
```

---

## 2. Technical PRD — overall summary (`technical-prd-summary.md`) — Phase 4

```markdown
# Technical PRD (Summary): <feature title>

## Overview
Goal and the technical strategy in a paragraph. Link to `prd.md`.

## Architecture
Components and how they fit. A Mermaid diagram.

## Agent Roster
The roster resolved in Phase 4 (see role-taxonomy.md). One row per selected role.

| Role | Bound agent | Responsibilities | Inputs | Outputs / contracts |
|------|-------------|------------------|--------|---------------------|
| PdM | (this skill / future PdM agent) | Distributes tasks, manages dependencies, tracks done criteria | Technical PRDs, tasks.md | Assignment + progress |
| <role> | `@agent-…` or "(generic <role>)" | … | … | … |

## Cross-Cutting Concerns
Security/permissions, performance, observability, data/migrations, compatibility —
and which role owns each.

## UseCase Index
| # | UseCase | Primary agent(s) | Doc |
|---|---------|------------------|-----|
| 1 | <name> | <role(s)> | `technical-prd-<usecase>.md` |

## Cross-UseCase Dependency Graph
A Mermaid graph of dependencies between UseCases (and shared modules).

## Sequencing / Milestones
Suggested order of execution and natural milestones.

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation | Owner role |
```

---

## 3. Technical PRD — per UseCase (`technical-prd-<usecase>.md`) — Phase 4

One file per UseCase. `<usecase>` is a kebab-case slug of the UseCase name.

```markdown
# Technical PRD — UseCase <#>: <name>

## Scope & Non-Goals
What this UseCase covers and explicitly does not.

## Assigned Agent(s)
Which role(s) own this UseCase and the responsibility split. Reference the bound
subagent if one was resolved.

## Interfaces & Contracts
Inputs, outputs, API/event/schema contracts this UseCase produces or consumes.

## Data / Schema Touchpoints
Tables, migrations, or data shapes affected.

## Test Seams & Strategy
The seam(s) at which this UseCase is tested (prefer existing, highest seam) and
what good tests look like here.

## Dependencies
Other UseCases or shared work this depends on, by UseCase # / task id.

## Done Criteria (Acceptance)
A checklist the assigned agent must satisfy to call this UseCase complete.
- [ ] <criterion>
```

---

## 4. Task list (`tasks.md`) — Phase 5

Derived from the Technical PRDs. Grouped by UseCase; every task is assignable,
ordered by dependency, and independently verifiable.

```markdown
# Tasks: <feature title>

> Each task: `id` · assigned role · depends-on · acceptance. Links back to the
> relevant Technical PRD section. A PdM agent consumes this to distribute work.

## UseCase 1: <name>
- [ ] **T1.1** <task title> — _role:_ <role/agent> · _depends:_ — · _ref:_ technical-prd-<usecase>.md#…
  - **Acceptance:** <verifiable condition>
- [ ] **T1.2** <task title> — _role:_ <role/agent> · _depends:_ T1.1 · _ref:_ …
  - **Acceptance:** <…>

## UseCase 2: <name>
- [ ] **T2.1** … — _role:_ <role/agent> · _depends:_ T1.2 · _ref:_ …
  - **Acceptance:** <…>

## Dependency Overview
A Mermaid graph of task dependencies across UseCases (optional but recommended
when tasks cross UseCase boundaries).
```
